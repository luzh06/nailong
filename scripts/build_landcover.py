"""Rasterise OSM land cover into a blend mask for the ground shader, and list tree instances.

    python scripts/build_landcover.py

Outputs
  web/assets/ground/landcover.webp  RGBA mask over the scene extent:
                                    R vegetation, G asphalt road, B sand, A sandstone rock
                                    (no channel set = urban paving)
  web/data/trees.json               tree instances in three.js axes
"""
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import shapely  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.ops import linemerge, polygonize, unary_union  # noqa: E402

from prep_osm import project  # noqa: E402
from terrain import Terrain  # noqa: E402

MASK_RES = 1.25          # metres per mask pixel
MASK_BLUR = 0.8          # pixels; softens edges so linear filtering blends cleanly
SCRUB_TREE_SPACING = 9.0  # metres between scattered trees in mapped woodland and scrub

ROAD_WIDTHS = {  # carriageway width in metres by highway class
    "motorway": 22.0, "trunk": 16.0, "primary": 14.0, "secondary": 12.0, "tertiary": 10.0,
    "residential": 8.0, "unclassified": 7.0, "living_street": 6.0, "service": 4.5,
}
PATH_WIDTHS = {"pedestrian": 6.0, "footway": 2.5, "cycleway": 2.5, "path": 2.0, "steps": 2.5}
VEGETATION = {("natural", "wood"), ("natural", "scrub"), ("landuse", "grass"), ("landuse", "forest"),
              ("leisure", "garden"), ("leisure", "pitch"), ("leisure", "park")}
SAND = {("natural", "beach"), ("natural", "sand")}
ROCK = {("natural", "bare_rock"), ("natural", "rock")}

# Tree kinds understood by the web viewer: 0 broadleaf, 1 Moreton Bay fig, 2 eucalypt, 3 palm
GENUS_KIND = {"ficus": 1, "eucalyptus": 2, "corymbia": 2, "angophora": 2, "lophostemon": 0,
              "phoenix": 3, "washingtonia": 3, "archontophoenix": 3, "livistona": 3, "syagrus": 3}
DEFAULT_TREE_HEIGHT = {0: 11.0, 1: 16.0, 2: 18.0, 3: 12.0}


def load(name):
    with open(ROOT / "data" / f"{name}.json", encoding="utf8") as fh:
        elements = json.load(fh)["elements"]
    nodes = {e["id"]: e for e in elements if e["type"] == "node"}
    ways = {e["id"]: e for e in elements if e["type"] == "way"}
    rels = [e for e in elements if e["type"] == "relation"]
    return nodes, ways, rels


def way_line(way, nodes):
    pts = [project(nodes[n]["lat"], nodes[n]["lon"]) for n in way.get("nodes", []) if n in nodes]
    return pts if len(pts) >= 2 else None


def area_geometry(element, nodes, ways):
    if element["type"] == "way":
        pts = way_line(element, nodes)
        return Polygon(pts).buffer(0) if pts and len(pts) >= 4 and pts[0] == pts[-1] else None
    lines = [LineString(way_line(ways[m["ref"]], nodes)) for m in element["members"]
             if m["type"] == "way" and m["ref"] in ways and m.get("role", "outer") == "outer"
             and way_line(ways[m["ref"]], nodes)]
    return unary_union(list(polygonize(linemerge(lines)))) if lines else None


def classify_areas(nodes, ways, rels):
    groups = {"veg": [], "sand": [], "rock": []}
    for element in list(ways.values()) + rels:
        tags = element.get("tags", {})
        pairs = {(k, tags.get(k)) for k in ("natural", "landuse", "leisure")}
        group = "veg" if pairs & VEGETATION else "sand" if pairs & SAND else "rock" if pairs & ROCK else None
        if group:
            geom = area_geometry(element, nodes, ways)
            if geom is not None and not geom.is_empty:
                groups[group].append((geom, tags))
    return groups


def road_geometry(nodes, ways):
    roads, paths = [], []
    for way in ways.values():
        tags = way.get("tags", {})
        kind = tags.get("highway")
        if kind is None or tags.get("bridge") or tags.get("tunnel") or tags.get("layer", "0") not in ("0", ""):
            continue  # elevated and underground carriageways are not on the ground surface
        pts = way_line(way, nodes)
        if not pts:
            continue
        closed_area = tags.get("area") == "yes" and pts[0] == pts[-1] and len(pts) >= 4
        if kind in ROAD_WIDTHS:
            roads.append(LineString(pts).buffer(ROAD_WIDTHS[kind] / 2, cap_style="flat"))
        elif kind in PATH_WIDTHS:
            paths.append(Polygon(pts).buffer(0) if closed_area else
                         LineString(pts).buffer(PATH_WIDTHS[kind] / 2, cap_style="flat"))
    return unary_union(roads), unary_union(paths)


class Raster:
    def __init__(self, extent):
        self.x0, self.y0, x1, y1 = extent
        self.width = int(math.ceil((x1 - self.x0) / MASK_RES))
        self.height = int(math.ceil((y1 - self.y0) / MASK_RES))

    def pixel(self, x, y):
        return ((x - self.x0) / MASK_RES, (self.y0 + self.height * MASK_RES - y) / MASK_RES)

    def draw(self, geom):
        image = Image.new("L", (self.width, self.height), 0)
        pen = ImageDraw.Draw(image)
        for poly in getattr(geom, "geoms", [geom]):
            if poly.geom_type != "Polygon" or poly.is_empty:
                continue
            pen.polygon([self.pixel(x, y) for x, y in poly.exterior.coords], fill=255)
            for ring in poly.interiors:
                pen.polygon([self.pixel(x, y) for x, y in ring.coords], fill=0)
        return image.filter(ImageFilter.GaussianBlur(MASK_BLUR))


def tree_kind(tags):
    genus = (tags.get("genus") or tags.get("species", "").split(" ")[0]).lower()
    if genus in GENUS_KIND:
        return GENUS_KIND[genus]
    return 3 if tags.get("leaf_type") == "palm" else 0


def collect_trees(nodes, groups, land, buildings, terrain):
    rng = random.Random(1788)
    blocked = unary_union(buildings).buffer(1.5)
    shapely.prepare(land)
    shapely.prepare(blocked)
    trees = []
    for node in nodes.values():
        tags = node.get("tags", {})
        if tags.get("natural") != "tree":
            continue
        x, y = project(node["lat"], node["lon"])
        kind = tree_kind(tags)
        height = tags.get("height")
        try:
            height = float(str(height).split()[0]) if height else DEFAULT_TREE_HEIGHT[kind]
        except ValueError:
            height = DEFAULT_TREE_HEIGHT[kind]
        trees.append((x, y, height * rng.uniform(0.85, 1.15), kind))
    for geom, tags in groups["veg"]:
        if tags.get("natural") not in ("wood", "scrub") and tags.get("landuse") != "forest":
            continue
        scrub = tags.get("natural") == "scrub"
        minx, miny, maxx, maxy = geom.bounds
        spacing = SCRUB_TREE_SPACING * (0.8 if scrub else 1.0)
        for gx in np.arange(minx, maxx, spacing):
            for gy in np.arange(miny, maxy, spacing):
                x, y = gx + rng.uniform(-3, 3), gy + rng.uniform(-3, 3)
                if geom.contains(Point(x, y)):
                    kind = 2 if rng.random() < 0.6 else 0
                    height = (rng.uniform(3, 6) if scrub else DEFAULT_TREE_HEIGHT[kind] * rng.uniform(0.7, 1.2))
                    trees.append((x, y, height, kind))
    xs = np.array([t[0] for t in trees])
    ys = np.array([t[1] for t in trees])
    keep = shapely.contains_xy(land, xs, ys) & ~shapely.contains_xy(blocked, xs, ys)
    ground = np.maximum(terrain.sample(xs, ys), 1.5)
    out = [(round(float(x), 1), round(float(g), 2), round(float(-y), 1), round(h, 1), k)
           for (x, y, h, k), g, ok in zip(trees, ground, keep) if ok]
    return out


def main():
    scene = json.loads((ROOT / "data" / "scene.json").read_text(encoding="utf8"))
    land = unary_union([Polygon(r["outer"], r["holes"]).buffer(0) for r in scene["land"]])
    buildings = [Polygon(b["outer"], b["holes"]).buffer(0) for b in scene["buildings"]]
    road_nodes, road_ways, _ = load("osm_roads")
    nature_nodes, nature_ways, nature_rels = load("osm_nature")

    groups = classify_areas(nature_nodes, nature_ways, nature_rels)
    # Large parks (Royal Botanic Garden, The Domain, Hyde Park ...) are multipolygon relations
    park_groups = classify_areas(*load("osm_parks"))
    parks = unary_union([Polygon(r["outer"], r["holes"]).buffer(0) for r in scene["parks"]])
    vegetation = unary_union([g for g, _ in groups["veg"] + park_groups["veg"]] + [parks])
    roads, paths = road_geometry(road_nodes, road_ways)
    vegetation = vegetation.difference(paths).difference(roads).intersection(land)
    sand = unary_union([g for g, _ in groups["sand"]]).intersection(land)
    rock = unary_union([g for g, _ in groups["rock"]]).intersection(land)
    roads = roads.intersection(land)

    raster = Raster(scene["extent"])
    channels = [raster.draw(g) for g in (vegetation, roads, sand, rock)]
    out_dir = ROOT / "web" / "assets" / "ground"
    out_dir.mkdir(parents=True, exist_ok=True)
    mask_path = out_dir / "landcover.webp"
    # exact=True keeps RGB where alpha (rock) is 0; WebP discards it otherwise
    Image.merge("RGBA", channels).save(mask_path, lossless=True, method=6, exact=True)

    trees = collect_trees(nature_nodes, groups, land, buildings, Terrain())
    tree_path = ROOT / "web" / "data" / "trees.json"
    tree_path.write_text(json.dumps({
        "fields": ["x", "y", "z", "height", "kind"],
        "kinds": ["broadleaf", "fig", "eucalypt", "palm"],
        "trees": trees,
    }, separators=(",", ":")), encoding="utf8")

    meta_path = out_dir / "landcover.json"
    meta_path.write_text(json.dumps({
        "extent": scene["extent"], "metresPerPixel": MASK_RES,
        "size": [raster.width, raster.height],
        "channels": ["vegetation", "road", "sand", "rock"],
    }, indent=1), encoding="utf8")
    kinds = np.bincount([t[4] for t in trees], minlength=4)
    print(f"mask {raster.width}x{raster.height} -> {mask_path.name} "
          f"({mask_path.stat().st_size / 1e6:.1f} MB); areas km²: veg {vegetation.area / 1e6:.2f}, "
          f"road {roads.area / 1e6:.2f}, sand {sand.area / 1e6:.3f}, rock {rock.area / 1e6:.3f}")
    print(f"trees {len(trees)} (broadleaf {kinds[0]}, fig {kinds[1]}, eucalypt {kinds[2]}, palm {kinds[3]})")


if __name__ == "__main__":
    main()
