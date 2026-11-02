"""Sydney Opera House: podium and shells built with Utzon's spherical solution."""
import json
import math
from pathlib import Path

import bmesh
from mathutils import Vector
from shapely.geometry import LineString
from shapely.ops import linemerge, polygonize, unary_union

from meshkit import add_face, add_prism, box_uv, new_object, oriented_rings
from prep_osm import project

ROOT = Path(__file__).resolve().parent.parent

# Sydney Opera House: every shell is a patch of a sphere of radius 75.2 m; highest roof point 67 m
# above sea level; 183 x 120 m (en.wikipedia.org/wiki/Sydney_Opera_House)
OPERA_SPHERE_R = 75.2
OPERA_PODIUM_TOP = 17.0  # no published figure: both reference photos give podium ≈ 0.26–0.29 of 67 m


# ---------------------------------------------------------------- Sydney Opera House
#
# Calibration (2026-11-02):
#  - Plan: hall axes and mouth widths from the two OSM glass-wall parts (ways 690624100 / 690624152),
#    expressed in footprint-local coordinates (a = along the 13.3° axis, north +; b = across, east +).
#  - Side elevation: shell order and set-backs read off the CC BY 3.0 photo
#    "Sydney Opera House - 2013.04 - panoramio.jpg" (rheins, Wikimedia Commons), taken from the
#    bridge's south-east pylon, scaled so the highest roof point sits at 67 m above sea level.
#  - Front view: mouth widths grow towards the tallest (rear) shell, theatre ≈ 0.82 × concert hall
#    height, glazing deep and dark — from "Sydney Opera House from the Kirribilli Lookout,
#    Kirribilli, NSW, 2022 03.jpg" (Kgbo, Wikimedia Commons, CC BY-SA 4.0).

OPERA_AXIS_BEARING = 13.3

# Per hall: across offset of the hall axis, then shells as
# (mouth a, apex set-back, depth, height above podium, mouth half-width, facing: +1 north / -1 south)
OPERA_HALLS = {
    "concert_hall": (-26.0, (
        (63.0, 17.0, 39.0, 30.0, 24.0, 1),
        (43.0, 17.0, 37.0, 40.0, 28.5, 1),
        (29.5, 17.0, 39.0, 50.0, 33.0, 1),
        (-37.0, 4.0, 30.0, 28.0, 26.0, -1),
    )),
    "joan_sutherland": (36.0, (
        (58.0, 15.0, 34.0, 25.0, 19.5, 1),
        (41.0, 15.0, 32.0, 33.0, 23.0, 1),
        (29.0, 15.0, 34.0, 41.0, 27.0, 1),
        (-28.0, 4.0, 26.0, 24.0, 21.0, -1),
    )),
    "bennelong_restaurant": (-30.0, (
        (-75.0, 4.0, 22.0, 15.0, 14.0, -1),
        (-44.0, 4.0, 18.0, 12.0, 11.0, 1),
    )),
}


def opera_footprint():
    with open(ROOT / "data" / "osm_opera.json", encoding="utf8") as fh:
        rel = json.load(fh)["elements"][0]
    lines = [LineString([project(p["lat"], p["lon"]) for p in m["geometry"]])
             for m in rel["members"] if m["type"] == "way" and m["role"] == "outer"]
    return unary_union(list(polygonize(linemerge(lines))))


def sphere_through(p1, p2, p3, radius, outward):
    """Centre of a sphere of `radius` through three points, on the side away from `outward`."""
    a, b = p2 - p1, p3 - p1
    n = a.cross(b)
    circum = p1 + (n.cross(a) * b.length_squared + b.cross(n) * a.length_squared) / (2 * n.length_squared)
    r = (circum - p1).length
    radius = max(radius, r * 1.02)
    offset = math.sqrt(radius * radius - r * r)
    n = n.normalized()
    centre = circum + n * offset
    if ((p1 + p2 + p3) / 3 - centre).dot(outward) < 0:
        centre = circum - n * offset
    return centre, radius


def onto_sphere(point, direction, centre, radius):
    """Move `point` along `direction` onto the sphere, taking the nearer intersection."""
    rel = point - centre
    k = direction.dot(rel)
    disc = k * k - (rel.length_squared - radius * radius)
    if disc < 0:
        return point - direction * k
    root = math.sqrt(disc)
    lam = min((-k + root, -k - root), key=abs)
    return point + direction * lam


def add_shell_half(bm, corners, centre, radius, lift, mat_index, steps=14):
    """Spherical patch over the triangle `corners`, lifted along one shared direction.

    Lifting every point along the same in-plane direction (rather than radially) keeps the
    ridge on the hall's symmetry plane, so the mirrored half meets it without a seam.
    """
    # Metric UVs in the plane of the flat triangle, U along the ridge (apex -> rear), so the
    # chevron tile pattern keeps its real size across the curved surface
    e1 = (corners[1] - corners[0]).normalized()
    normal = (corners[1] - corners[0]).cross(corners[2] - corners[0]).normalized()
    e2 = normal.cross(e1)
    grid, uv = {}, {}
    for i in range(steps + 1):
        for j in range(steps + 1 - i):
            k = steps - i - j
            flat = (corners[0] * i + corners[1] * j + corners[2] * k) / steps
            grid[(i, j)] = bm.verts.new(onto_sphere(flat, lift, centre, radius))
            rel = flat - corners[0]
            uv[(i, j)] = (rel.dot(e1), rel.dot(e2))

    def tri(a, b, c):
        add_face(bm, (grid[a], grid[b], grid[c]), mat_index, (uv[a], uv[b], uv[c]))

    for i in range(steps):
        for j in range(steps - i):
            tri((i, j), (i + 1, j), (i, j + 1))
            if i + j < steps - 1:
                tri((i + 1, j), (i + 1, j + 1), (i, j + 1))


def add_shell(bm, to_world, spec, tile, glass, podium_top):
    """One shell: two mirrored spherical halves meeting on a ridge, with a glazed mouth.

    The mouth corners stand on the podium at the open end; the apex sits `setback` metres
    behind them, and the ridge runs from the apex down to the rear point.
    """
    mouth_a, setback, depth, height, half_width, facing = spec
    apex = to_world(mouth_a - facing * setback, 0, podium_top + height)
    rear = to_world(mouth_a - facing * depth, 0, podium_top)
    corners = [to_world(mouth_a, side * half_width, podium_top) for side in (-1, 1)]
    chord = (rear - apex).normalized()
    up = Vector((0, 0, 1))
    lift = (up - chord * up.dot(chord)).normalized()  # in the symmetry plane, square to the ridge chord

    rims = []
    for side, corner in zip((-1, 1), corners):
        outward = (to_world(0, side, 0) - to_world(0, 0, 0)) + up * 0.6
        centre, radius = sphere_through(apex, rear, corner, OPERA_SPHERE_R, outward)
        add_shell_half(bm, (apex, rear, corner), centre, radius, lift, tile)
        rims.append([onto_sphere(apex.lerp(corner, t / 10), lift, centre, radius) for t in range(11)])

    # Glazing hangs deep under the shell, inset from its edge, so the shell rim reads as a
    # white pointed arch around a dark opening (as in the Kirribilli reference)
    rim = rims[0] + list(reversed(rims[1]))[:-1]
    mouth_mid = (corners[0] + corners[1]) / 2
    hub = mouth_mid.lerp(rear, 0.45) + (apex - mouth_mid) * 0.2
    inset = [p.lerp(hub, 0.12) + (rear - apex).normalized() * 3.0 for p in rim]
    hub = bm.verts.new(hub)
    rim_verts = [bm.verts.new(p) for p in inset]
    for i in range(len(rim_verts)):
        add_face(bm, (hub, rim_verts[i], rim_verts[(i + 1) % len(rim_verts)]), glass)


def build_opera_house(footprint, col, mats):
    centre = footprint.centroid
    bearing = math.radians(OPERA_AXIS_BEARING)
    axis = Vector((math.sin(bearing), math.cos(bearing), 0))
    across = Vector((axis.y, -axis.x, 0))

    bm = bmesh.new()
    tile, glass, granite = 0, 1, 2
    add_prism(bm, oriented_rings(footprint.buffer(-2.0)), 0.0, OPERA_PODIUM_TOP, granite)
    for offset, shells in OPERA_HALLS.values():
        def to_world(a, b, z, off=offset):
            return Vector((centre.x, centre.y, z)) + axis * a + across * (off + b)
        for spec in shells:
            add_shell(bm, to_world, spec, tile, glass, OPERA_PODIUM_TOP)
    box_uv(bm, [f for f in bm.faces if f.material_index == glass])
    top = max(v.co.z for v in bm.verts)
    print(f"opera house: highest roof point {top:.1f} m above water (published: 67 m)")
    return new_object("OperaHouse", bm, [mats["tile"], mats["glass"], mats["podium"]], col)
