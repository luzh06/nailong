"""Harbour-edge detail: timber wharves from OSM piers, and railings along the walkable foreshore."""
import json
from pathlib import Path

import bmesh
import numpy as np
from mathutils import Vector
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from meshkit import add_beam, add_prism, new_object, oriented_rings, rings_to_polygon
from prep_osm import project

ROOT = Path(__file__).resolve().parent.parent

WHARF_DECK_TOP = 2.4     # metres above mean sea level
WHARF_DECK_DEPTH = 0.5
WHARF_PILE_SPACING = 6.0
WHARF_PILE_SIZE = 0.45
PIER_DEFAULT_WIDTH = 3.0  # for piers mapped as a line without a width tag
RAILING_HEIGHT = 1.1
RAILING_POST_SPACING = 2.0
RAILING_INSET = 0.6       # from the walk-zone edge, so the player cannot clip through it
RAILING_SHORE_GAP = 3.0   # only edges this close to the water get a railing


def pier_polygons(land):
    with open(ROOT / "data" / "osm_coast.json", encoding="utf8") as fh:
        elements = json.load(fh)["elements"]
    nodes = {e["id"]: project(e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    shapes = []
    for e in elements:
        tags = e.get("tags", {})
        if e["type"] != "way" or tags.get("man_made") not in ("pier", "breakwater"):
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) < 2:
            continue
        if pts[0] == pts[-1] and len(pts) >= 4:
            shapes.append(Polygon(pts).buffer(0))
        else:
            try:
                width = float(str(tags.get("width", PIER_DEFAULT_WIDTH)).split()[0])
            except ValueError:
                width = PIER_DEFAULT_WIDTH
            shapes.append(LineString(pts).buffer(width / 2, cap_style="flat"))
    # Only the part over water is a wharf; on land it is just ground
    return unary_union(shapes).difference(land)


def build_wharves(scene, col, mats):
    land = unary_union([rings_to_polygon(r) for r in scene["land"]])
    piers = pier_polygons(land)
    bm = bmesh.new()
    count, piles = 0, 0
    up = Vector((0, 0, 1))
    for poly in getattr(piers, "geoms", [piers]):
        if poly.geom_type != "Polygon" or poly.area < 6:
            continue
        count += 1
        add_prism(bm, oriented_rings(poly), WHARF_DECK_TOP - WHARF_DECK_DEPTH, WHARF_DECK_TOP, 0, cap_bottom=True)
        # Timber piles on a grid under the deck, down into the water
        minx, miny, maxx, maxy = poly.bounds
        inner = poly.buffer(-0.5)
        for x in np.arange(minx + 1.0, maxx, WHARF_PILE_SPACING):
            for y in np.arange(miny + 1.0, maxy, WHARF_PILE_SPACING):
                if inner.contains(Point(x, y)):
                    base = Vector((x, y, -3.0))
                    add_beam(bm, base, base + up * (WHARF_DECK_TOP - WHARF_DECK_DEPTH + 3.0),
                             WHARF_PILE_SIZE, WHARF_PILE_SIZE, 1)
                    piles += 1
    print(f"wharves: {count} decks, {piles} piles")
    return new_object("Wharves", bm, [mats["wharf_deck"], mats["wharf_pile"]], col)


def railing_runs(zone, land):
    """Pieces of the walk-zone edge that run along the water, pulled RAILING_INSET inside."""
    water_edge = land.boundary
    inner = zone.buffer(-RAILING_INSET)
    runs = []
    for ring in [inner.exterior] if inner.geom_type == "Polygon" else [g.exterior for g in inner.geoms]:
        coords = list(ring.coords)
        current = []
        for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
            near_water = water_edge.distance(Point((x0 + x1) / 2, (y0 + y1) / 2)) < RAILING_SHORE_GAP + RAILING_INSET
            if near_water:
                if not current:
                    current = [(x0, y0)]
                current.append((x1, y1))
            elif current:
                runs.append(current)
                current = []
        if current:
            runs.append(current)
    return [r for r in runs if LineString(r).length > 4.0]


def build_railings(zone, scene, height_at, col, mats):
    land = unary_union([rings_to_polygon(r) for r in scene["land"]])
    bm = bmesh.new()
    posts = 0
    for run in railing_runs(zone, land):
        line = LineString(run)
        n = max(2, int(line.length / RAILING_POST_SPACING) + 1)
        points = [line.interpolate(i / (n - 1), normalized=True) for i in range(n)]
        tops = []
        for p in points:
            ground = height_at(p.x, p.y)
            base = Vector((p.x, p.y, ground))
            add_beam(bm, base, base + Vector((0, 0, RAILING_HEIGHT)), 0.07, 0.07)
            tops.append(base)
            posts += 1
        for a, b in zip(tops, tops[1:]):
            for h, size in ((RAILING_HEIGHT, 0.06), (RAILING_HEIGHT * 0.5, 0.03)):
                add_beam(bm, a + Vector((0, 0, h)), b + Vector((0, 0, h)), size, size)
    print(f"railings: {posts} posts")
    return new_object("Railings", bm, [mats["railing"]], col)
