"""Build the Sydney Harbour blockout scene in Blender and export it for the web viewer.

Run headless from the sydney/ folder:
    blender.exe -b --factory-startup -P scripts/build_blockout.py

Inputs : data/scene.json (from prep_osm.py), data/osm_opera.json, data/nsw_dem_4m.tif
Outputs: blend/sydney_blockout.blend, web/data/blockout.glb, web/data/scene_meta.json

Blender axes: x = east, y = north, z = up, 1 unit = 1 m, origin = Sydney Opera House.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import shapely  # noqa: E402
from prep_osm import project  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402
from shapely.ops import linemerge, nearest_points, polygonize, unary_union  # noqa: E402
from terrain import Terrain  # noqa: E402

SHORE_MIN = 1.5         # land never drops below this: seawalls stand above harbour water (z = 0)
LAND_BOTTOM = -4.0
GROUND_CELL = 10.0      # terrain mesh resolution, metres
WALK_CELL = 2.5         # finer drape for the walkable strip
WALK_LIFT = 0.08        # walk-zone surface sits just above the ground mesh
HEIGHTFIELD_STEP = 2.0  # resolution of the walk-zone height grid sent to the web viewer
EYE_HEIGHT = 1.65
NEAR_RADIUS = 750.0     # buildings this close to the walk zone get the "near" material
TOWER_HEIGHT = 100.0

# Sydney Harbour Bridge. Heights are metres above mean sea level.
# Sources: [W] en.wikipedia.org/wiki/Sydney_Harbour_Bridge, [P] Pylon Lookout "Bridge facts" (2003),
# [R] railtram.com.au/sydney-harbour-bridge, [I] IStructE "The Sydney Harbour Bridge".
BRIDGE_SPAN = 503.0             # between bearing pins [W][P]
BRIDGE_ARCH_TOP = 134.0         # top of the arch [W][P]
BRIDGE_PANELS = 28              # arch truss panels [W][P]
BRIDGE_TRUSS_DEPTH_CROWN = 18.0  # chord centre to chord centre at mid-span [W]
BRIDGE_TRUSS_DEPTH_ENDS = 57.0   # ... and at the pylons [W]
BRIDGE_PIN_HEIGHT = 4.0         # reasoned: pins sit at the abutment-tower base just above the water
                                # (ground there is 2–4 m); gives top-chord ends ≈ 61 m, about two thirds
                                # up the pylons as in photographs
BRIDGE_CLEARANCE = 49.0         # under the deck at mid-span [W][P]
BRIDGE_DECK_DEPTH = 4.0         # reasoned: 170 ft (51.8 m) headroom to the roadway ("Railway Wonders of
                                # the World") minus 49 m clearance ≈ 3 m, plus surfacing; also makes the
                                # mid-span hanger ≈ 59 m against the published longest hanger of 58.8 m [P]
BRIDGE_APPROACH_GRADE = 1 / 40  # roadway and rail rise at 1 in 40 to a crest on the bridge [R]
BRIDGE_CREST_CURVE = 200.0      # reasoned: parabolic crest joining the two 1:40 grades (offset 1.25 m)
BRIDGE_DECK_WIDTH = 48.8        # [W]
BRIDGE_TRUSS_OFFSET = 14.5      # half the spacing of the two arch trusses
BRIDGE_PYLON_HEIGHT = 89.0      # [W][P]
BRIDGE_TOTAL_LENGTH = 1149.0    # abutment to abutment, including the approach spans [W][P]
BRIDGE_APPROACH_SPANS = 5       # steel approach spans on each side [I]
BRIDGE_PYLON_BASE = (48.0, 68.0)    # abutment tower base, along x across [P]
BRIDGE_PIER_SIZE = 9.0              # square granite approach columns
BRIDGE_PIER_OFFSET = 18.0           # columns stand either side of the axis
BRIDGE_ABUTMENT_LENGTH = 20.0

# Sydney Opera House: every shell is a patch of a sphere of radius 75.2 m; highest roof point 67 m
# above sea level; 183 x 120 m (en.wikipedia.org/wiki/Sydney_Opera_House)
OPERA_SPHERE_R = 75.2
OPERA_PODIUM_TOP = 17.0  # no published figure: both reference photos give podium ≈ 0.26–0.29 of 67 m


# ---------------------------------------------------------------- helpers

def material(name, rgb, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def new_object(name, bm, materials, collection):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in materials:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def add_face(bm, verts, mat_index=0):
    face = bm.faces.new(verts)
    face.material_index = mat_index
    return face


def add_prism(bm, rings, z0, z1, mat_index=0, cap_bottom=False):
    """Extrude a polygon (outer ring + holes, CCW outer / CW holes) between z0 and z1."""
    flat = [Vector((x, y)) for ring in rings for x, y in ring]
    top = [bm.verts.new((v.x, v.y, z1)) for v in flat]
    bottom = [bm.verts.new((v.x, v.y, z0)) for v in flat]
    offset = 0
    for ring in rings:
        n = len(ring)
        for i in range(n):
            a, b = offset + i, offset + (i + 1) % n
            add_face(bm, (bottom[a], bottom[b], top[b], top[a]), mat_index)
        offset += n
    tri_input = [[Vector((x, y, 0.0)) for x, y in ring] for ring in rings]
    for tri in tessellate_polygon(tri_input):
        verts = [top[i] for i in tri]
        if (verts[1].co - verts[0].co).cross(verts[2].co - verts[0].co).z < 0:
            verts.reverse()
        try:
            add_face(bm, verts, mat_index)
            if cap_bottom:
                add_face(bm, [bottom[i] for i in reversed(tri)], mat_index)
        except ValueError:
            pass  # degenerate triangle from duplicated points


def oriented_rings(poly):
    poly = orient(poly, 1.0)
    return [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]


def rings_to_polygon(rings):
    return Polygon(rings["outer"], rings["holes"]).buffer(0)


def add_beam(bm, p0, p1, width, depth, mat_index=0):
    """Box beam from p0 to p1 with a width x depth cross-section."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    if length < 1e-3:
        return
    fwd = axis / length
    ref = Vector((0, 0, 1)) if abs(fwd.z) < 0.95 else Vector((1, 0, 0))
    side = fwd.cross(ref).normalized()
    up = side.cross(fwd).normalized()
    hw, hd = width / 2, depth / 2
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    ring0 = [bm.verts.new(p0 + side * a + up * b) for a, b in corners]
    ring1 = [bm.verts.new(p1 + side * a + up * b) for a, b in corners]
    for i in range(4):
        j = (i + 1) % 4
        add_face(bm, (ring0[i], ring0[j], ring1[j], ring1[i]), mat_index)
    add_face(bm, list(reversed(ring0)), mat_index)
    add_face(bm, ring1, mat_index)


def add_box(bm, center, size, frame, mat_index=0):
    """Axis-aligned box in a local frame (3x3 Matrix whose columns are the local axes)."""
    c = Vector(center)
    hx, hy, hz = (s / 2 for s in size)
    pts = [Vector((sx * hx, sy * hy, sz * hz)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    v = [bm.verts.new(c + frame @ p) for p in pts]
    for idx in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        add_face(bm, [v[i] for i in idx], mat_index)


# ---------------------------------------------------------------- ground and buildings

def land_height(terrain, xs, ys):
    return np.maximum(terrain.sample(xs, ys), SHORE_MIN)


def grid_pieces(region, cell):
    """Square cells covering `region`, each clipped to it. Returns a list of polygons."""
    minx, miny, maxx, maxy = region.bounds
    gx, gy = np.meshgrid(np.arange(math.floor(minx / cell) * cell, maxx, cell),
                         np.arange(math.floor(miny / cell) * cell, maxy, cell))
    boxes = shapely.box(gx, gy, gx + cell, gy + cell).ravel()
    shapely.prepare(region)
    inside = shapely.contains(region, boxes)
    edge = shapely.intersects(region, boxes) & ~inside
    pieces = list(boxes[inside])
    for clipped in shapely.intersection(boxes[edge], region):
        pieces.extend(p for p in getattr(clipped, "geoms", [clipped])
                      if p.geom_type == "Polygon" and p.area > 0.01)
    return pieces


def drape(bm, pieces, heights_fn, mat_indices, lift=0.0):
    """Triangulate polygon pieces and lift every vertex onto the terrain.

    Vertices are shared between neighbouring pieces so the surface is welded and shades smoothly.
    """
    rings_per_piece = [oriented_rings(p) for p in pieces]
    keys = {(round(x, 2), round(y, 2)) for rings in rings_per_piece for ring in rings for x, y in ring}
    keys = list(keys)
    xy = np.array(keys)
    zs = heights_fn(xy[:, 0], xy[:, 1]) + lift
    verts = {k: bm.verts.new((k[0], k[1], float(z))) for k, z in zip(keys, zs)}
    for rings, mat_index in zip(rings_per_piece, mat_indices):
        ring_keys = [[(round(x, 2), round(y, 2)) for x, y in ring] for ring in rings]
        if len(rings) == 1 and len(rings[0]) == 4:
            tris = [(0, 1, 2), (0, 2, 3)]
            flat = ring_keys[0]
        else:
            tris = tessellate_polygon([[Vector((x, y, 0.0)) for x, y in ring] for ring in rings])
            flat = [k for ring in ring_keys for k in ring]
        for tri in tris:
            face_verts = [verts[flat[i]] for i in tri]
            if len(set(face_verts)) < 3:
                continue
            if (face_verts[1].co - face_verts[0].co).cross(face_verts[2].co - face_verts[0].co).z < 0:
                face_verts.reverse()
            try:
                add_face(bm, face_verts, mat_index)
            except ValueError:
                pass  # duplicate face where two pieces share a sliver


def add_seawalls(bm, land, terrain, mat_index):
    """Vertical walls along every land edge, from below the water up to the terrain surface."""
    for poly in getattr(land, "geoms", [land]):
        for ring in oriented_rings(poly):
            pts = np.array(ring)
            tops = land_height(terrain, pts[:, 0], pts[:, 1])
            n = len(ring)
            for i in range(n):
                j = (i + 1) % n
                (x0, y0), (x1, y1) = ring[i], ring[j]
                quad = (bm.verts.new((x0, y0, LAND_BOTTOM)), bm.verts.new((x1, y1, LAND_BOTTOM)),
                        bm.verts.new((x1, y1, float(tops[j]))), bm.verts.new((x0, y0, float(tops[i]))))
                add_face(bm, quad, mat_index)


def build_ground(scene, walk_zone, terrain, col, mats):
    land = unary_union([rings_to_polygon(r) for r in scene["land"]])
    parks = unary_union([rings_to_polygon(r) for r in scene["parks"]])
    shapely.prepare(parks)
    pieces = grid_pieces(land, GROUND_CELL)
    centres = shapely.centroid(pieces)
    in_park = shapely.contains_xy(parks, shapely.get_x(centres), shapely.get_y(centres))

    def heights(xs, ys):
        return land_height(terrain, xs, ys)

    bm = bmesh.new()
    drape(bm, pieces, heights, [1 if p else 0 for p in in_park])
    add_seawalls(bm, land, terrain, 0)
    walk_pieces = grid_pieces(walk_zone, WALK_CELL)
    drape(bm, walk_pieces, heights, [2] * len(walk_pieces), lift=WALK_LIFT)
    print(f"ground: {len(pieces)} terrain cells, {len(walk_pieces)} walk-zone cells")
    obj = new_object("Ground", bm, [mats["land"], mats["park"], mats["walk"]], col)
    # Terrain vertices are welded, so smooth shading lets the exporter share them instead of
    # writing three copies per triangle. Seawall quads own their vertices and stay crisp.
    obj.data.shade_smooth()
    return obj


def build_buildings(scene, walk_zone, hero_footprint, terrain, col, mats):
    bm = bmesh.new()
    for b in scene["buildings"]:
        poly = rings_to_polygon(b)
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        if hero_footprint.contains(poly.representative_point()):
            continue  # unnamed OSM parts of the Opera House are covered by the hero model
        if b["h"] >= TOWER_HEIGHT:
            mat_index = 2
        elif poly.distance(walk_zone) < NEAR_RADIUS:
            mat_index = 0
        else:
            mat_index = 1
        # OSM heights are measured from the ground: stand on the lowest footprint corner and
        # sink the base a little so the uphill side does not float
        pts = np.array(poly.exterior.coords)
        ground = float(land_height(terrain, pts[:, 0], pts[:, 1]).min())
        bottom = ground + b["base"] - (1.0 if b["base"] == 0 else 0.0)
        add_prism(bm, oriented_rings(poly), bottom, ground + b["h"], mat_index)
    return new_object("Buildings", bm, [mats["near"], mats["city"], mats["tower"]], col)


# ---------------------------------------------------------------- Sydney Harbour Bridge

class BridgeLayout:
    """Shared geometry of the bridge: local frame, deck profile and pier positions.

    Local coordinates: s along the axis from the midpoint between the pylon pairs (north +),
    t across (east +), z up.
    """

    def __init__(self, anchors):
        south = Vector((*anchors["bridge_south_pylons"], 0))
        north = Vector((*anchors["bridge_north_pylons"], 0))
        self.mid = (south + north) / 2
        self.u = (north - south).normalized()
        self.v = Vector((self.u.y, -self.u.x, 0))
        self.up = Vector((0, 0, 1))
        self.frame = Matrix((self.u, self.v, self.up)).transposed()
        self.half_pylon_gap = (north - south).length / 2
        self.half_span = BRIDGE_SPAN / 2
        self.end = BRIDGE_TOTAL_LENGTH / 2

    def world(self, s, t, z):
        return self.mid + self.u * s + self.v * t + self.up * z

    def deck_top(self, s):
        """Roadway level: 1:40 grades either side of a parabolic crest at mid-span."""
        crest = BRIDGE_CLEARANCE + BRIDGE_DECK_DEPTH
        half_curve = BRIDGE_CREST_CURVE / 2
        s = abs(s)
        if s <= half_curve:
            return crest - BRIDGE_APPROACH_GRADE * s * s / BRIDGE_CREST_CURVE
        return crest - BRIDGE_APPROACH_GRADE * (s - half_curve / 2)

    def lower_chord(self, s):
        """Centre line of the lower chord: bearing pin at each end, parabolic to the crown."""
        crown = BRIDGE_ARCH_TOP - 1.5 - BRIDGE_TRUSS_DEPTH_CROWN
        return BRIDGE_PIN_HEIGHT + (crown - BRIDGE_PIN_HEIGHT) * (1 - (s / self.half_span) ** 2)

    def upper_chord(self, s):
        """Centre line of the upper chord; its 3 m deep section tops out at the published arch height."""
        ends = BRIDGE_PIN_HEIGHT + BRIDGE_TRUSS_DEPTH_ENDS
        crown = BRIDGE_ARCH_TOP - 1.5
        return ends + (crown - ends) * (1 - (s / self.half_span) ** 2)

    def pier_stations(self):
        """Distances from the midpoint of the approach piers on one side (not pylon or abutment)."""
        first = self.half_pylon_gap + BRIDGE_PYLON_BASE[0] / 2
        step = (self.end - BRIDGE_ABUTMENT_LENGTH - first) / BRIDGE_APPROACH_SPANS
        return [first + step * k for k in range(1, BRIDGE_APPROACH_SPANS)]

    def footprints(self):
        """Ground footprints of everything that stands on land: pylon bases, piers, abutments."""
        boxes = []
        for sign in (-1, 1):
            boxes.append((sign * self.half_pylon_gap, 0.0, *BRIDGE_PYLON_BASE))
            for s in self.pier_stations():
                for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
                    boxes.append((sign * s, t, BRIDGE_PIER_SIZE, BRIDGE_PIER_SIZE))
            boxes.append((sign * (self.end - BRIDGE_ABUTMENT_LENGTH / 2), 0.0,
                          BRIDGE_ABUTMENT_LENGTH, BRIDGE_DECK_WIDTH))
        polys = []
        for s, t, length, width in boxes:
            corners = [self.world(s + a * length / 2, t + b * width / 2, 0)
                       for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            polys.append(Polygon([(c.x, c.y) for c in corners]))
        return polys


def build_bridge(layout, terrain, col, mats):
    world = layout.world
    half = layout.half_span
    lower, upper = layout.lower_chord, layout.upper_chord
    lower_chord_half_depth = 2.25

    def ground(s, t):
        p = world(s, t, 0)
        return float(terrain.sample([p.x], [p.y])[0])

    bm = bmesh.new()
    steel, granite, deck = 0, 1, 2
    panel = BRIDGE_SPAN / BRIDGE_PANELS
    stations = [-half + i * panel for i in range(BRIDGE_PANELS + 1)]
    hangers = []
    for t in (-BRIDGE_TRUSS_OFFSET, BRIDGE_TRUSS_OFFSET):
        for i in range(BRIDGE_PANELS):
            s0, s1 = stations[i], stations[i + 1]
            add_beam(bm, world(s0, t, lower(s0)), world(s1, t, lower(s1)), 3.0, 4.5, steel)
            add_beam(bm, world(s0, t, upper(s0)), world(s1, t, upper(s1)), 2.5, 3.0, steel)
            diag_from, diag_to = (s0, s1) if (i < BRIDGE_PANELS // 2) else (s1, s0)
            add_beam(bm, world(diag_from, t, lower(diag_from)), world(diag_to, t, upper(diag_to)), 1.4, 1.4, steel)
        for s in stations:
            add_beam(bm, world(s, t, lower(s)), world(s, t, upper(s)), 1.6, 1.6, steel)
            hanger = lower(s) - lower_chord_half_depth - layout.deck_top(s)
            if hanger > 2:
                add_beam(bm, world(s, t, layout.deck_top(s)), world(s, t, lower(s)), 0.9, 0.9, steel)
                hangers.append(hanger)
    for s in stations[2:-2]:
        add_beam(bm, world(s, -BRIDGE_TRUSS_OFFSET, upper(s)), world(s, BRIDGE_TRUSS_OFFSET, upper(s)), 1.2, 1.2, steel)
    print(f"bridge hangers {min(hangers):.1f}–{max(hangers):.1f} m (published 7.3–58.8 m), "
          f"top-chord ends {upper(half) + 1.5:.1f} m")

    # Deck follows the roadway profile, sampled finely enough to show the crest curve
    deck_depth = BRIDGE_DECK_DEPTH
    profile = np.linspace(-layout.end, layout.end, 58)
    for s0, s1 in zip(profile, profile[1:]):
        add_beam(bm, world(s0, 0, layout.deck_top(s0) - deck_depth / 2),
                 world(s1, 0, layout.deck_top(s1) - deck_depth / 2), BRIDGE_DECK_WIDTH, deck_depth, deck)

    girder_depth = 7.0
    for sign in (-1, 1):
        # Abutment tower: solid granite from the ground up to the underside of the deck
        s_pylon = sign * layout.half_pylon_gap
        tower_top = layout.deck_top(s_pylon) - deck_depth
        add_box(bm, world(s_pylon, 0, tower_top / 2), (*BRIDGE_PYLON_BASE, tower_top), layout.frame, granite)
        for t in (-25.0, 25.0):
            add_box(bm, world(s_pylon, t, BRIDGE_PYLON_HEIGHT / 2), (26.0, 18.0, BRIDGE_PYLON_HEIGHT),
                    layout.frame, granite)

        # Approach spans: deck trusses under each deck edge, carried on paired granite columns
        s_from, s_to = sign * layout.half_pylon_gap, sign * layout.end
        for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
            add_beam(bm, world(s_from, t, layout.deck_top(s_from) - deck_depth - girder_depth / 2),
                     world(s_to, t, layout.deck_top(s_to) - deck_depth - girder_depth / 2),
                     2.0, girder_depth, steel)
        for s in layout.pier_stations():
            s *= sign
            top = layout.deck_top(s) - deck_depth - girder_depth
            for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
                base = max(ground(s, t), 0.0) - 1.0
                add_box(bm, world(s, t, (base + top) / 2),
                        (BRIDGE_PIER_SIZE, BRIDGE_PIER_SIZE, top - base), layout.frame, granite)

        # Abutment: solid granite block from the deck end down into the ground
        s_abut = sign * (layout.end - BRIDGE_ABUTMENT_LENGTH / 2)
        top = layout.deck_top(s_abut) - deck_depth
        base = min(ground(s_abut, t) for t in (-BRIDGE_DECK_WIDTH / 2, 0, BRIDGE_DECK_WIDTH / 2)) - 1.0
        add_box(bm, world(s_abut, 0, (base + top) / 2),
                (BRIDGE_ABUTMENT_LENGTH, BRIDGE_DECK_WIDTH, top - base), layout.frame, granite)
        print(f"bridge {'north' if sign > 0 else 'south'}: deck at pylon {layout.deck_top(s_pylon):.1f} m, "
              f"at abutment {layout.deck_top(s_to):.1f} m, ground {base + 1:.1f} m")
    print(f"bridge: deck crest {layout.deck_top(0):.1f} m, clearance {layout.deck_top(0) - deck_depth:.1f} m")
    print(f"bridge: pylon centre gap {2 * layout.half_pylon_gap:.1f} m, arch span {BRIDGE_SPAN} m")
    return new_object("HarbourBridge", bm, [mats["steel"], mats["granite"], mats["deck"]], col)


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
    grid = {}
    for i in range(steps + 1):
        for j in range(steps + 1 - i):
            k = steps - i - j
            flat = (corners[0] * i + corners[1] * j + corners[2] * k) / steps
            grid[(i, j)] = bm.verts.new(onto_sphere(flat, lift, centre, radius))
    for i in range(steps):
        for j in range(steps - i):
            add_face(bm, (grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]), mat_index)
            if i + j < steps - 1:
                add_face(bm, (grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]), mat_index)


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
    top = max(v.co.z for v in bm.verts)
    print(f"opera house: highest roof point {top:.1f} m above water (published: 67 m)")
    return new_object("OperaHouse", bm, [mats["tile"], mats["glass"], mats["podium"]], col)


# ---------------------------------------------------------------- walk zone and metadata

def walk_zone_polygon(scene):
    anchors = scene["anchors"]
    land = unary_union([rings_to_polygon(r) for r in scene["land"]])
    route = LineString([anchors["bridge_north_pylons"], anchors["jeffrey_st_wharf"]])
    shoreline = land.boundary.intersection(route.buffer(220))
    zone = land.intersection(shoreline.buffer(45)).intersection(route.buffer(260))
    zone = max(getattr(zone, "geoms", [zone]), key=lambda g: g.area)
    # Solid obstacles become holes: bridge pylon block and any building inside the strip
    blockers = [Point(anchors["bridge_north_pylons"]).buffer(42.0)]
    blockers += [f.buffer(0.5) for f in BridgeLayout(anchors).footprints()]
    blockers += [rings_to_polygon(b).buffer(0.5) for b in scene["buildings"]
                 if rings_to_polygon(b).intersects(zone)]
    zone = zone.difference(unary_union(blockers))
    zone = max(getattr(zone, "geoms", [zone]), key=lambda g: g.area)
    return zone.simplify(1.0)


def to_three(x, y, z=0.0):
    return [round(x, 2), round(z, 2), round(-y, 2)]


def standing_point(zone, target, inset=4.0):
    """Point inside the walk zone closest to `target`, kept `inset` metres from any edge."""
    safe = zone.buffer(-inset)
    return nearest_points(safe, Point(target))[0]


def walk_heightfield(zone, terrain):
    """Ground heights over the walk zone's bounding box, in three.js axes (x east, z south)."""
    minx, miny, maxx, maxy = zone.buffer(HEIGHTFIELD_STEP * 2).bounds
    xs = np.arange(minx, maxx + HEIGHTFIELD_STEP, HEIGHTFIELD_STEP)
    zs = np.arange(-maxy, -miny + HEIGHTFIELD_STEP, HEIGHTFIELD_STEP)
    gx, gz = np.meshgrid(xs, zs)
    heights = land_height(terrain, gx.ravel(), -gz.ravel()) + WALK_LIFT
    grad_z, grad_x = np.gradient(heights.reshape(gz.shape), HEIGHTFIELD_STEP)
    slope = np.degrees(np.arctan(np.hypot(grad_x, grad_z)))
    inside = shapely.contains_xy(zone, gx, -gz)
    print(f"walk zone ground {heights.reshape(gz.shape)[inside].min():.1f}–"
          f"{heights.reshape(gz.shape)[inside].max():.1f} m, "
          f"{(slope[inside] > 35).mean() * 100:.0f}% steeper than 35°")
    return {
        "x0": round(float(xs[0]), 2), "z0": round(float(zs[0]), 2), "step": HEIGHTFIELD_STEP,
        "nx": len(xs), "nz": len(zs), "h": [round(float(h), 2) for h in heights],
    }


def write_meta(scene, zone, terrain):
    anchors = scene["anchors"]
    spawn = standing_point(zone, anchors["jeffrey_st_wharf"])
    # Bridge view: on the foreshore east of the north abutment tower, looking up at the arch crown
    # (standing right beside the tower would fill the frame with granite)
    layout = BridgeLayout(anchors)
    beside_tower = layout.world(layout.half_pylon_gap - 25.0, BRIDGE_PYLON_BASE[1] / 2 + 35.0, 0)
    bridge = standing_point(zone, (beside_tower.x, beside_tower.y))
    crown = layout.world(0, 0, BRIDGE_ARCH_TOP - 30.0)

    def eye(p):
        return terrain_height(terrain, p) + WALK_LIFT + EYE_HEIGHT

    zone = orient(zone, 1.0)
    meta = {
        "units": "metres; three.js axes (x east, y up, -z north); origin Sydney Opera House",
        "eyeHeight": EYE_HEIGHT,
        "ground": walk_heightfield(zone, terrain),
        "walkZone": [to_three(x, y)[::2] for x, y in list(zone.exterior.coords)[:-1]],
        "walkHoles": [[to_three(x, y)[::2] for x, y in list(r.coords)[:-1]] for r in zone.interiors],
        "views": {
            # ~26° west of south from the wharf: Opera House on the left, bridge on the right
            "spawn": {"pos": to_three(spawn.x, spawn.y, eye(spawn)),
                      "look": to_three(spawn.x - 350.0, spawn.y - 720.0, 35.0)},
            "bridge": {"pos": to_three(bridge.x, bridge.y, eye(bridge)),
                       "look": to_three(crown.x, crown.y, crown.z)},
        },
        "anchors": {k: to_three(*v) for k, v in anchors.items()},
        "extent": scene["extent"],
        "attribution": "Buildings & shoreline © OpenStreetMap contributors (ODbL) · "
                       "Elevation © State of New South Wales (Spatial Services)",
    }
    (ROOT / "web" / "data" / "scene_meta.json").write_text(json.dumps(meta, separators=(",", ":")),
                                                         encoding="utf8")
    print(f"walk zone area {zone.area:.0f} m², holes {len(meta['walkHoles'])}, views {meta['views']}")


def terrain_height(terrain, point):
    return float(land_height(terrain, [point.x], [point.y])[0])


# ---------------------------------------------------------------- main

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = json.loads((ROOT / "data" / "scene.json").read_text(encoding="utf8"))
    mats = {
        "land": material("land_sandstone", (0.55, 0.50, 0.42), 0.95),
        "park": material("park_grass", (0.30, 0.42, 0.20), 0.95),
        "walk": material("walk_zone", (0.62, 0.58, 0.48), 0.9),
        "near": material("bld_near", (0.78, 0.72, 0.64), 0.85),
        "city": material("bld_city", (0.70, 0.71, 0.73), 0.8),
        "tower": material("bld_tower_glass", (0.46, 0.55, 0.62), 0.25, 0.3),
        "steel": material("bridge_steel", (0.36, 0.38, 0.38), 0.6, 0.6),
        "granite": material("bridge_granite", (0.63, 0.57, 0.48), 0.9),
        "deck": material("bridge_deck", (0.28, 0.28, 0.29), 0.85),
        "tile": material("opera_tile", (0.93, 0.91, 0.86), 0.3),
        "glass": material("opera_glass_bronze", (0.10, 0.085, 0.07), 0.3, 0.3),
        "podium": material("opera_podium", (0.55, 0.38, 0.30), 0.85),
    }
    terrain = Terrain()
    zone = walk_zone_polygon(scene)
    build_ground(scene, zone, terrain, new_collection("L0_Ground"), mats)
    build_bridge(BridgeLayout(scene["anchors"]), terrain, new_collection("L1_Bridge"), mats)
    opera = opera_footprint()
    build_opera_house(opera, new_collection("L1_OperaHouse"), mats)
    build_buildings(scene, zone, opera, terrain, new_collection("L2_Buildings"), mats)
    write_meta(scene, zone, terrain)

    (ROOT / "blend").mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blend" / "sydney_blockout.blend"))
    bpy.ops.export_scene.gltf(
        filepath=str(ROOT / "web" / "data" / "blockout.glb"),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        # Quantisation is set far above the defaults (14 / 10 bits) so compression is visually
        # lossless: 20 bits keeps positions within ~2 mm across the 4.5 km ground mesh, well under
        # the 8 cm walk-zone lift; 14-bit normals avoid banding on the smooth terrain.
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=10,
        export_draco_position_quantization=20,
        export_draco_normal_quantization=14,
    )
    for obj in bpy.data.objects:
        print(f"{obj.name:16s} tris={sum(len(p.vertices) - 2 for p in obj.data.polygons):>8d}")


main()
