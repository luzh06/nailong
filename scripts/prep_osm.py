"""Convert raw Overpass JSON into a compact local-metre scene description.

Run with any Python 3.10+ that can import shapely, e.g. the Blender bundled one:
    python scripts/prep_osm.py
Output: data/scene.json  (x = east, y = north, metres, origin = Sydney Opera House)
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))

from shapely import STRtree  # noqa: E402
from shapely.geometry import LineString, Polygon, box, mapping  # noqa: E402
from shapely.ops import linemerge, polygonize, unary_union  # noqa: E402

ORIGIN_LAT, ORIGIN_LON = -33.85681, 151.21514  # Sydney Opera House
EARTH_R = 6378137.0
COS_LAT0 = math.cos(math.radians(ORIGIN_LAT))

# Scene extent in local metres (west, south, east, north)
EXTENT = (-1900.0, -2500.0, 1500.0, 2000.0)
LEVEL_HEIGHT = 3.4
ROOF_ALLOWANCE = 2.0
DEFAULT_HEIGHT = 9.0
# Buildings with neither height nor levels (~3,200 here) get a height from their type instead of
# a flat 9 m: sheds and garages are single storey, Sydney houses one to two storeys, and
# `building=roof` is a canopy with no walls, so it floats as a thin slab.
TYPE_HEIGHTS = {  # (min_height, height) in metres
    "garage": (0.0, 3.0), "garages": (0.0, 3.0), "shed": (0.0, 3.0), "carport": (2.4, 3.0),
    "service": (0.0, 3.5), "kiosk": (0.0, 3.5), "toilets": (0.0, 3.5),
    "roof": (3.5, 4.5),
    "house": (0.0, 7.0), "detached": (0.0, 7.0), "semidetached_house": (0.0, 7.0),
    "terrace": (0.0, 8.0), "bungalow": (0.0, 5.0), "boathouse": (0.0, 5.0),
    "residential": (0.0, 10.0), "apartments": (0.0, 14.0),
}
MIN_AREA = 12.0  # m², drop sheds and slivers

WATER_RELATION_NAMES = {"Port Jackson", "Sydney Harbour"}
# Replaced by hand-built hero models
HERO_NAME_PATTERN = re.compile(r"Sydney Opera House|Sydney Harbour Bridge")
HERO_RELATION_IDS = {9596872}


def project(lat, lon):
    x = math.radians(lon - ORIGIN_LON) * EARTH_R * COS_LAT0
    y = math.radians(lat - ORIGIN_LAT) * EARTH_R
    return (round(x, 2), round(y, 2))


def parse_metres(value):
    if value is None:
        return None
    match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", str(value))
    return float(match.group(1)) if match else None


def building_heights(tags):
    height = parse_metres(tags.get("height"))
    levels = parse_metres(tags.get("building:levels"))
    if height is None and levels is None and "min_height" not in tags:
        return TYPE_HEIGHTS.get(tags.get("building"), (0.0, DEFAULT_HEIGHT))[::-1]
    if height is None:
        height = levels * LEVEL_HEIGHT + ROOF_ALLOWANCE if levels else DEFAULT_HEIGHT
    base = parse_metres(tags.get("min_height"))
    if base is None:
        min_level = parse_metres(tags.get("building:min_level"))
        base = min_level * LEVEL_HEIGHT if min_level else 0.0
    return max(height, base + 2.0), base


def load_elements(*names):
    elements = []
    for name in names:
        with open(ROOT / "data" / name, encoding="utf8") as fh:
            elements.extend(json.load(fh)["elements"])
    nodes = {e["id"]: project(e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    ways = {}
    for e in elements:
        if e["type"] == "way":
            # Keep the tagged copy when a way appears both tagged and as a skeleton
            if e["id"] not in ways or e.get("tags"):
                ways[e["id"]] = e
    relations = [e for e in elements if e["type"] == "relation"]
    return nodes, ways, relations


def way_coords(way, nodes):
    return [nodes[n] for n in way.get("nodes", []) if n in nodes]


def assemble_multipolygon(relation, ways, nodes):
    def rings(role):
        lines = [
            LineString(way_coords(ways[m["ref"]], nodes))
            for m in relation["members"]
            if m["type"] == "way" and m.get("role", "outer") == role and m["ref"] in ways
            and len(way_coords(ways[m["ref"]], nodes)) >= 2
        ]
        return list(polygonize(linemerge(lines))) if lines else []

    outer = unary_union(rings("outer"))
    inner = rings("inner")
    return outer.difference(unary_union(inner)) if inner else outer


def polygon_parts(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]


def to_rings(poly, simplify=0.0):
    poly = poly.simplify(simplify, preserve_topology=True) if simplify else poly
    return {
        "outer": [list(p) for p in poly.exterior.coords[:-1]],
        "holes": [[list(p) for p in ring.coords[:-1]] for ring in poly.interiors],
    }


def build_water(ways, nodes, relations, clip):
    water = [
        assemble_multipolygon(r, ways, nodes)
        for r in relations
        if r.get("tags", {}).get("name") in WATER_RELATION_NAMES
    ]
    water = unary_union(water).buffer(0).intersection(clip)
    land = clip.difference(water)
    return water, land


def collect_buildings(ways, nodes, relations, clip):
    hero_way_ids = {
        m["ref"] for r in relations if r["id"] in HERO_RELATION_IDS for m in r["members"]
    }
    outlines, parts = [], []
    for way in ways.values():
        tags = way.get("tags", {})
        if not ("building" in tags or "building:part" in tags):
            continue
        if way["id"] in hero_way_ids or HERO_NAME_PATTERN.search(tags.get("name", "")):
            continue
        coords = way_coords(way, nodes)
        if len(coords) < 4:
            continue
        poly = Polygon(coords).buffer(0)
        target = parts if "building:part" in tags and "building" not in tags else outlines
        target.append((poly, tags))
    for rel in relations:
        tags = rel.get("tags", {})
        if "building" in tags and rel["id"] not in HERO_RELATION_IDS:
            outlines.append((assemble_multipolygon(rel, ways, nodes).buffer(0), tags))

    # Simple 3D Buildings rule: an outline that has parts is drawn by its parts only
    part_tree = STRtree([p.representative_point() for p, _ in parts]) if parts else None
    kept = []
    for poly, tags in outlines:
        if part_tree is not None and len(part_tree.query(poly, predicate="contains")):
            continue
        kept.append((poly, tags))
    kept.extend(parts)

    result = []
    for geom, tags in kept:
        for poly in polygon_parts(geom.intersection(clip)):
            if poly.area < MIN_AREA:
                continue
            height, base = building_heights(tags)
            result.append({
                "h": round(height, 1),
                "base": round(base, 1),
                "name": tags.get("name", ""),
                **to_rings(poly, simplify=0.3),
            })
    return result


def collect_parks(ways, nodes, land):
    parks = []
    for way in ways.values():
        if way.get("tags", {}).get("leisure") != "park":
            continue
        coords = way_coords(way, nodes)
        if len(coords) >= 4:
            for poly in polygon_parts(Polygon(coords).buffer(0).intersection(land)):
                parks.append(to_rings(poly, simplify=1.0))
    return parks


def main():
    nodes, ways, relations = load_elements("osm_raw.json", "osm_coast.json", "osm_landmarks.json")
    clip = box(*EXTENT)
    water, land = build_water(ways, nodes, relations, clip)
    buildings = collect_buildings(ways, nodes, relations, clip)
    scene = {
        "origin": {"lat": ORIGIN_LAT, "lon": ORIGIN_LON},
        "extent": EXTENT,
        "land": [to_rings(p, simplify=1.5) for p in polygon_parts(land)],
        "parks": collect_parks(ways, nodes, land),
        "buildings": buildings,
        "anchors": {name: project(lat, lon) for name, (lat, lon) in {
            "bridge_south_pylons": (-33.85445, 151.20940),
            "bridge_north_pylons": (-33.84995, 151.21220),
            "opera_house": (ORIGIN_LAT, ORIGIN_LON),
            "jeffrey_st_wharf": (-33.84870, 151.21590),
            "kirribilli_point": (-33.84960, 151.21720),
        }.items()},
    }
    out = ROOT / "data" / "scene.json"
    out.write_text(json.dumps(scene, separators=(",", ":")), encoding="utf8")
    tall = sorted(buildings, key=lambda b: -b["h"])[:12]
    print(f"land={len(scene['land'])} parks={len(scene['parks'])} buildings={len(buildings)} "
          f"water_area_km2={water.area / 1e6:.2f} -> {out}")
    for b in tall:
        print(f"  {b['h']:6.1f} m  {b['name'] or '-'}")


if __name__ == "__main__":
    main()
