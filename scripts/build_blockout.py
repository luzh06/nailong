"""Build the Sydney Harbour scene in Blender and export it for the web viewer.

Run headless from the sydney/ folder:
    blender.exe -b --factory-startup -P scripts/build_blockout.py

Inputs : data/scene.json (prep_osm.py), data/osm_opera.json, data/nsw_dem_4m.tif
Outputs: blend/sydney_blockout.blend, web/data/blockout.glb, web/data/scene_meta.json

Blender axes: x = east, y = north, z = up, 1 unit = 1 m, origin = Sydney Opera House.
Geometry lives in ground.py, bridge.py and opera.py; this file assembles, exports and writes metadata.
"""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402
from shapely.ops import nearest_points, unary_union  # noqa: E402

from bridge import (BRIDGE_ARCH_TOP, BRIDGE_PANELS, BRIDGE_PYLON_BASE, BRIDGE_PYLON_HEIGHT,  # noqa: E402
                    BRIDGE_SPAN, BRIDGE_TRUSS_OFFSET, BridgeLayout, build_bridge)
from ground import WALK_LIFT, build_buildings, build_ground, land_height  # noqa: E402
from meshkit import material, new_collection, rings_to_polygon  # noqa: E402
from opera import build_opera_house, opera_footprint  # noqa: E402
from terrain import Terrain  # noqa: E402

HEIGHTFIELD_STEP = 2.0  # resolution of the walk-zone height grid sent to the web viewer
EYE_HEIGHT = 1.65


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


def write_meta(scene, zone, terrain, extra):
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
        "attribution": "Buildings, roads & land cover © OpenStreetMap contributors (ODbL) · "
                       "Elevation © State of New South Wales (Spatial Services) · "
                       "Textures & skies: Poly Haven (CC0)",
        **extra,
    }
    (ROOT / "web" / "data" / "scene_meta.json").write_text(json.dumps(meta, separators=(",", ":")),
                                                         encoding="utf8")
    print(f"walk zone area {zone.area:.0f} m², holes {len(meta['walkHoles'])}, views {meta['views']}")


def terrain_height(terrain, point):
    return float(land_height(terrain, [point.x], [point.y])[0])


def bridge_lights(layout):
    """Night lamps: along both upper chords at every panel point, and on each pylon top."""
    lamps = []
    panel = BRIDGE_SPAN / BRIDGE_PANELS
    for i in range(BRIDGE_PANELS + 1):
        s = -layout.half_span + i * panel
        for t in (-BRIDGE_TRUSS_OFFSET, BRIDGE_TRUSS_OFFSET):
            p = layout.world(s, t, layout.upper_chord(s) + 2.0)
            lamps.append(to_three(p.x, p.y, p.z))
    for sign in (-1, 1):
        for t in (-25.0, 25.0):
            p = layout.world(sign * layout.half_pylon_gap, t, BRIDGE_PYLON_HEIGHT + 1.0)
            lamps.append(to_three(p.x, p.y, p.z))
    return lamps


def export_glb():
    bpy.ops.export_scene.gltf(
        filepath=str(ROOT / "web" / "data" / "blockout.glb"),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_vertex_color="ACTIVE",  # building style/seed attribute for the façade shader
        # Quantisation far above the defaults keeps compression visually lossless: 20-bit positions
        # (~2 mm over the 4.5 km ground, well under the 8 cm walk-zone lift), 14-bit normals
        # (no banding on smooth terrain), 18-bit metric UVs (~2 cm over a 5 km range).
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=10,
        export_draco_position_quantization=20,
        export_draco_normal_quantization=14,
        export_draco_texcoord_quantization=18,
        export_draco_color_quantization=12,
    )


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = json.loads((ROOT / "data" / "scene.json").read_text(encoding="utf8"))
    # Base colours are fallbacks; the web viewer replaces these materials by name
    mats = {
        "terrain": material("ground_terrain", (0.55, 0.50, 0.42), 0.95),
        "seawall": material("seawall_sandstone", (0.66, 0.55, 0.40), 0.9),
        "walk": material("walk_promenade", (0.62, 0.58, 0.48), 0.9),
        "facade": material("building_facade", (0.74, 0.72, 0.70), 0.8),
        "steel": material("bridge_steel", (0.36, 0.38, 0.38), 0.6, 0.6),
        "granite": material("bridge_granite", (0.63, 0.57, 0.48), 0.9),
        "deck": material("bridge_deck", (0.28, 0.28, 0.29), 0.85),
        "tile": material("opera_tile", (0.93, 0.91, 0.86), 0.3),
        "glass": material("opera_glass", (0.10, 0.085, 0.07), 0.3, 0.3),
        "podium": material("opera_podium", (0.55, 0.38, 0.30), 0.85),
    }
    terrain = Terrain()
    zone = walk_zone_polygon(scene)
    build_ground(scene, zone, terrain, new_collection("L0_Ground"), mats)
    layout = BridgeLayout(scene["anchors"])
    build_bridge(layout, terrain, new_collection("L1_Bridge"), mats)
    opera = opera_footprint()
    build_opera_house(opera, new_collection("L1_OperaHouse"), mats)
    build_buildings(scene, opera, terrain, new_collection("L2_Buildings"), mats)
    write_meta(scene, zone, terrain, {"bridgeLamps": bridge_lights(layout)})

    (ROOT / "blend").mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blend" / "sydney_blockout.blend"))
    export_glb()
    for obj in bpy.data.objects:
        print(f"{obj.name:16s} tris={sum(len(p.vertices) - 2 for p in obj.data.polygons):>8d}")


main()
