"""Download the CC0 textures and skies the web viewer uses, and build their web versions.

    python scripts/fetch_assets.py

Sources: Poly Haven (https://polyhaven.com, CC0) textures and HDRIs; three.js water normals (MIT).
Originals are kept in assets_src/ (not served); web-sized copies go to web/assets/ with fixed names
(<id>/diff.jpg, nor.jpg, arm.jpg). web/assets/ASSETS.csv records source, authors and licence.
Existing files are skipped, so the script is safe to re-run.
"""
import csv
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))

from PIL import Image  # noqa: E402

SRC = ROOT / "assets_src"
WEB = ROOT / "web" / "assets"
API = "https://api.polyhaven.com"
USER_AGENT = "cijian-sydney/0.2"

MAPS = {"Diffuse": "diff", "nor_gl": "nor", "arm": "arm"}  # arm = AO, roughness, metalness
JPEG_QUALITY = {"diff": 84, "nor": 92, "arm": 86}

# id -> (download resolution, web size in px, used for)
TEXTURES = {
    "metal_plate": ("1k", 1024, "Harbour Bridge painted steel"),
    "sandstone_blocks_08": ("1k", 1024, "Bridge pylons, granite ashlar (tinted)"),
    "sandstone_blocks_05": ("2k", 2048, "Harbour seawalls"),
    "gravel_embedded_concrete": ("1k", 1024, "Opera House podium aggregate panels"),
    "leafy_grass": ("2k", 1024, "Parks and lawns"),
    "asphalt_02": ("1k", 1024, "Roads and bridge deck"),
    "pavement_02": ("2k", 2048, "Foreshore promenade"),
    "coast_sand_01": ("2k", 1024, "Sand"),
    "rock_pitted_mossy": ("1k", 1024, "Sandstone foreshore and hillsides"),
    "concrete_wall_008": ("1k", 1024, "Building walls (masonry)"),
    "concrete_floor_worn_001": ("1k", 1024, "Flat roofs and paving"),
    "ceramic_roof_01": ("1k", 1024, "Terracotta house roofs"),
    "wood_planks_grey": ("1k", 1024, "Wharf decks and piles"),
}

# id -> (lighting resolution, used for)
SKIES = {
    "kloofendal_48d_partly_cloudy_puresky": ("1k", "Day"),
    "belfast_sunset_puresky": ("1k", "Golden hour"),
    "qwantani_dusk_2_puresky": ("1k", "Blue hour"),
}
BACKDROP_WIDTH = 6144  # visible sky from the tonemapped JPG: about 17 px per degree

# ambientCG (https://ambientcg.com, CC0): id -> (zip resolution, web size, used for, web name)
AMBIENTCG = {
    "Grass001": ("1K-JPG", 1024, "Lawns and parks (Poly Haven has no plain lawn)", "lawn"),
}

WATER_NORMALS = ("https://raw.githubusercontent.com/mrdoob/three.js/r170/examples/textures/waternormals.jpg",
                 "three.js authors", "MIT")


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSfL", "-m", "300", "--retry", "3", "-A", USER_AGENT, "-o", str(dest), url],
                   check=True)


def api(path):
    out = subprocess.run(["curl", "-sSfL", "-m", "60", "-A", USER_AGENT, f"{API}/{path}"],
                         check=True, capture_output=True)
    return json.loads(out.stdout)


def authors(info):
    return "; ".join(f"{name} ({role})" for name, role in info.get("authors", {}).items())


def web_copy(src, dest, size, quality):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        if img.width != size:
            img = img.resize((size, size), Image.LANCZOS)
        img.save(dest, quality=quality, optimize=True, progressive=True)


def build_textures(rows):
    for asset_id, (res, size, use) in TEXTURES.items():
        files, info = api(f"files/{asset_id}"), api(f"info/{asset_id}")
        for map_name, short in MAPS.items():
            url = files[map_name][res]["jpg"]["url"]
            original = SRC / "textures" / asset_id / Path(url).name
            fetch(url, original)
            dest = WEB / "textures" / asset_id / f"{short}.jpg"
            web_copy(original, dest, size, JPEG_QUALITY[short])
            rows.append([dest.relative_to(ROOT).as_posix(), f"https://polyhaven.com/a/{asset_id}",
                         authors(info), "CC0", use])
        print(f"texture {asset_id}: {res} source, {size}px web")


def build_ambientcg(rows):
    """ambientCG ships a zip per material; repack Color / NormalGL / AO+Roughness as diff, nor, arm."""
    for asset_id, (variant, size, use, name) in AMBIENTCG.items():
        archive = SRC / "textures" / asset_id / f"{asset_id}_{variant}.zip"
        fetch(f"https://ambientcg.com/get?file={asset_id}_{variant}.zip", archive)
        out = WEB / "textures" / name
        with zipfile.ZipFile(archive) as zf:
            members = {Path(n).stem.split("_")[-1]: n for n in zf.namelist() if n.lower().endswith(".jpg")}

            def image(key, mode):
                with zf.open(members[key]) as fh:
                    return Image.open(io.BytesIO(fh.read())).convert(mode).resize((size, size), Image.LANCZOS)

            out.mkdir(parents=True, exist_ok=True)
            image("Color", "RGB").save(out / "diff.jpg", quality=JPEG_QUALITY["diff"], optimize=True)
            image("NormalGL", "RGB").save(out / "nor.jpg", quality=JPEG_QUALITY["nor"], optimize=True)
            rough = image("Roughness", "L")
            ao = image("AmbientOcclusion", "L") if "AmbientOcclusion" in members else Image.new("L", rough.size, 255)
            Image.merge("RGB", (ao, rough, Image.new("L", rough.size, 0))).save(
                out / "arm.jpg", quality=JPEG_QUALITY["arm"], optimize=True)
        for short in MAPS.values():
            rows.append([(out / f"{short}.jpg").relative_to(ROOT).as_posix(),
                         f"https://ambientcg.com/view?id={asset_id}", "ambientCG (Lennart Demes)", "CC0", use])
        print(f"texture {asset_id} -> {name} (ambientCG)")


def build_skies(rows):
    for asset_id, (res, use) in SKIES.items():
        files, info = api(f"files/{asset_id}"), api(f"info/{asset_id}")
        hdr_src = SRC / "sky" / f"{asset_id}_{res}.hdr"
        fetch(files["hdri"][res]["hdr"]["url"], hdr_src)
        hdr = WEB / "sky" / hdr_src.name
        hdr.parent.mkdir(parents=True, exist_ok=True)
        if not hdr.exists():
            shutil.copyfile(hdr_src, hdr)
        backdrop = WEB / "sky" / f"{asset_id}_backdrop.jpg"
        backdrop_src = SRC / "sky" / f"{asset_id}_backdrop.jpg"
        if not backdrop_src.exists():
            full = SRC / "sky" / f"{asset_id}_tonemapped_full.jpg"
            fetch(files["tonemapped"]["url"], full)
            with Image.open(full) as img:
                img.convert("RGB").resize((BACKDROP_WIDTH, BACKDROP_WIDTH // 2), Image.LANCZOS) \
                    .save(backdrop_src, quality=88, optimize=True, progressive=True)
            full.unlink()
        if not backdrop.exists():
            shutil.copyfile(backdrop_src, backdrop)
        for path in (hdr, backdrop):
            rows.append([path.relative_to(ROOT).as_posix(), f"https://polyhaven.com/a/{asset_id}",
                         authors(info), "CC0", f"{use} sky"])
        print(f"sky {asset_id}")


def main():
    rows = []
    build_textures(rows)
    build_ambientcg(rows)
    build_skies(rows)
    url, author, licence = WATER_NORMALS
    dest = WEB / "water" / "waternormals.jpg"
    fetch(url, dest)
    rows.append([dest.relative_to(ROOT).as_posix(), url, author, licence, "Harbour water normals"])
    with open(WEB / "ASSETS.csv", "w", newline="", encoding="utf8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["file", "source", "authors", "licence", "used for"])
        writer.writerows(rows)
    print(f"{len(rows)} files recorded in {WEB / 'ASSETS.csv'}")


if __name__ == "__main__":
    main()
