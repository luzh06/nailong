"""Terrain, seawalls, the walkable foreshore and the OSM buildings."""
import math
import random

import bmesh
import numpy as np
import shapely
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from shapely.ops import unary_union

from meshkit import add_face, add_prism, new_object, oriented_rings, rings_to_polygon

SHORE_MIN = 1.5         # land never drops below this: seawalls stand above harbour water (z = 0)
LAND_BOTTOM = -4.0
GROUND_CELL = 10.0      # terrain mesh resolution, metres
WALK_CELL = 2.5         # finer drape for the walkable strip
WALK_LIFT = 0.08        # walk-zone surface sits just above the ground mesh

# Façade styles understood by the web shader (stored in the building colour attribute)
STYLE_GLASS_TOWER, STYLE_OFFICE, STYLE_SANDSTONE, STYLE_BRICK = 0, 1, 2, 3
STYLE_RENDERED, STYLE_HOUSE, STYLE_UTILITY, STYLE_SHED = 4, 5, 6, 7
STYLE_COUNT = 8
UTILITY_KINDS = {"garage", "garages", "shed", "carport", "service", "kiosk", "toilets", "roof"}
HOUSE_KINDS = {"house", "detached", "semidetached_house", "bungalow", "terrace"}
SHED_KINDS = {"industrial", "warehouse", "hangar", "boathouse", "transportation", "train_station"}
RESIDENTIAL_KINDS = {"apartments", "residential", "hotel", "dormitory"}
HEIGHT_NORMALISER = 300.0


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
    The ground shaders work in world space, so no UVs are written.
    """
    rings_per_piece = [oriented_rings(p) for p in pieces]
    keys = list({(round(x, 2), round(y, 2)) for rings in rings_per_piece for ring in rings for x, y in ring})
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
    """Vertical sandstone walls along every land edge, from below the water up to the terrain.

    U runs along the shoreline and V is height, so the block courses stay level.
    """
    for poly in getattr(land, "geoms", [land]):
        for ring in oriented_rings(poly):
            pts = np.array(ring)
            tops = land_height(terrain, pts[:, 0], pts[:, 1])
            n = len(ring)
            run = 0.0
            for i in range(n):
                j = (i + 1) % n
                (x0, y0), (x1, y1) = ring[i], ring[j]
                length = math.hypot(x1 - x0, y1 - y0)
                quad = (bm.verts.new((x0, y0, LAND_BOTTOM)), bm.verts.new((x1, y1, LAND_BOTTOM)),
                        bm.verts.new((x1, y1, float(tops[j]))), bm.verts.new((x0, y0, float(tops[i]))))
                uvs = ((run, LAND_BOTTOM), (run + length, LAND_BOTTOM),
                       (run + length, float(tops[j])), (run, float(tops[i])))
                add_face(bm, quad, mat_index, uvs)
                run += length


def build_ground(scene, walk_zone, terrain, col, mats):
    land = unary_union([rings_to_polygon(r) for r in scene["land"]])
    pieces = grid_pieces(land, GROUND_CELL)

    def heights(xs, ys):
        return land_height(terrain, xs, ys)

    bm = bmesh.new()
    drape(bm, pieces, heights, [0] * len(pieces))
    add_seawalls(bm, land, terrain, 1)
    walk_pieces = grid_pieces(walk_zone, WALK_CELL)
    drape(bm, walk_pieces, heights, [2] * len(walk_pieces), lift=WALK_LIFT)
    print(f"ground: {len(pieces)} terrain cells, {len(walk_pieces)} walk-zone cells")
    obj = new_object("Ground", bm, [mats["terrain"], mats["seawall"], mats["walk"]], col)
    # Terrain vertices are welded, so smooth shading lets the exporter share them instead of
    # writing three copies per triangle. Seawall quads own their vertices and stay crisp.
    obj.data.shade_smooth()
    return obj


def building_style(b, rng):
    kind, mat, h = b.get("kind", ""), b.get("mat", ""), b["h"]
    if kind in UTILITY_KINDS:
        return STYLE_UTILITY
    if kind in HOUSE_KINDS:
        return STYLE_HOUSE
    if kind in SHED_KINDS:
        return STYLE_SHED
    if mat == "glass" or h >= 110 or (h >= 60 and rng.random() < 0.55):
        return STYLE_GLASS_TOWER
    if mat in ("sandstone", "stone"):
        return STYLE_SANDSTONE
    if mat == "brick":
        return STYLE_BRICK
    if h >= 35:
        return STYLE_OFFICE
    if kind in RESIDENTIAL_KINDS:
        return STYLE_RENDERED if rng.random() < 0.6 else STYLE_BRICK
    # Untagged low-rise in the old city: a mix of sandstone, brick and rendered fronts
    roll = rng.random()
    return STYLE_SANDSTONE if roll < 0.3 else STYLE_BRICK if roll < 0.6 else STYLE_RENDERED


def build_buildings(scene, hero_footprint, terrain, col, mats):
    """One mesh, one material: the façade shader reads the style and seed from the colour attribute.

    Colour attribute: R = per-building random seed, G = style / STYLE_COUNT,
    B = height / HEIGHT_NORMALISER, A = 1.
    """
    rng = random.Random(1932)
    bm = bmesh.new()
    counts = [0] * STYLE_COUNT
    for b in scene["buildings"]:
        poly = rings_to_polygon(b)
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        if hero_footprint.contains(poly.representative_point()):
            continue  # unnamed OSM parts of the Opera House are covered by the hero model
        style = building_style(b, rng)
        counts[style] += 1
        color = (rng.random(), (style + 0.5) / STYLE_COUNT, min(b["h"] / HEIGHT_NORMALISER, 1.0), 1.0)
        # OSM heights are measured from the ground: stand on the lowest footprint corner and
        # sink the base a little so the uphill side does not float
        pts = np.array(poly.exterior.coords)
        ground = float(land_height(terrain, pts[:, 0], pts[:, 1]).min())
        bottom = ground + b["base"] - (1.0 if b["base"] == 0 else 0.0)
        add_prism(bm, oriented_rings(poly), bottom, ground + b["h"], 0, color=color)
    print("buildings by style (glass, office, sandstone, brick, rendered, house, utility, shed):", counts)
    return new_object("Buildings", bm, [mats["facade"]], col)
