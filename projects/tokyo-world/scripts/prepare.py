"""Build a standalone offline viewer from local deliveries; sources stay read-only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0, r'D:\project\cijian\work\.pydeps')
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
PACK = Path(r'D:\Cijian\pack')
FILL = Path(r'D:\project\cijian\work\export\blocks')
INTEG = Path(r'D:\Cijian\integ')
PROPS = INTEG / 'src/props/projects/tokyo-props/props'


def unpack(path):
    data = path.read_bytes()
    if data[:4] != b'glTF':
        raise ValueError(f'Not a GLB payload: {path}')
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + size])
    offset = 20 + size
    binary = data[offset + 8:] if offset < len(data) else b''
    return doc, binary


def convert(source, name, out):
    target = out / 'web/models' / (name + '.gltf')
    doc, binary = unpack(source)
    for image in doc.get('images', []):
        if 'bufferView' not in image:
            raise ValueError(f'Unexpected external image: {source}')
        view = doc['bufferViews'][image.pop('bufferView')]
        raw = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
        im = Image.open(io.BytesIO(raw))
        im.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        dest = io.BytesIO()
        transparent = im.mode in ('RGBA', 'LA') or 'transparency' in im.info
        if transparent:
            im.convert('RGBA').save(dest, format='PNG', optimize=True)
            suffix = '.png'
        else:
            im.convert('RGB').save(dest, format='JPEG', quality=88, optimize=True)
            suffix = '.jpg'
        payload = dest.getvalue()
        key = hashlib.sha256(payload).hexdigest()[:24] + suffix
        texture = out / 'web/textures' / key
        if not texture.exists():
            texture.write_bytes(payload)
        image['uri'] = '../textures/' + key
        image.pop('mimeType', None)
    # Drop embedded image bufferViews and compact only geometry bufferViews.
    used = set()
    for accessor in doc.get('accessors', []):
        if 'bufferView' in accessor:
            used.add(accessor['bufferView'])
        for field in ('indices', 'values'):
            if field in accessor.get('sparse', {}):
                used.add(accessor['sparse'][field]['bufferView'])
    rebuilt = bytearray()
    remap = {}
    views = []
    for old in sorted(used):
        view = dict(doc['bufferViews'][old])
        start = view.get('byteOffset', 0)
        rebuilt.extend(b'\0' * ((-len(rebuilt)) % 4))
        remap[old] = len(views)
        view['byteOffset'] = len(rebuilt)
        rebuilt.extend(binary[start:start + view['byteLength']])
        views.append(view)
    for accessor in doc.get('accessors', []):
        if 'bufferView' in accessor:
            accessor['bufferView'] = remap[accessor['bufferView']]
        for field in ('indices', 'values'):
            if field in accessor.get('sparse', {}):
                entry = accessor['sparse'][field]
                entry['bufferView'] = remap[entry['bufferView']]
    doc['bufferViews'] = views
    doc['buffers'] = [{'byteLength': len(rebuilt), 'uri': name + '.bin'}]
    target.with_suffix('.bin').write_bytes(rebuilt)
    target.write_text(json.dumps(doc, separators=(',', ':')), encoding='utf-8')
    print('MODEL', name, source.stat().st_size, '->', len(rebuilt), flush=True)
    return 'models/' + name + '.gltf'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--rebuild-existing', action='store_true', help='Explicitly restore source assets over an optimized package')
    a = ap.parse_args()
    out = a.out.resolve()
    if (out/'optimization-models.json').exists() and not a.rebuild_existing:
        raise ValueError('This package is already optimized. Use a new --out directory; --rebuild-existing explicitly restores larger original assets.')
    out.mkdir(parents=True, exist_ok=True)
    for folder in ('web/models', 'web/textures'):
        (out / folder).mkdir(parents=True, exist_ok=True)
    # Preserve the existing baked lighting, local Three.js and its loaders.
    for folder in ('web', 'assets', 'bake'):
        shutil.copytree(PACK / folder, out / folder, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('game.html','game.js','cards.json','card_*.exr','probe_*.exr'))
    for obsolete in ('web/game.html','web/game.js','bake/t4/cards.json','bake/t4/card_east.exr','bake/t4/card_west.exr','bake/t4/probe_mid.exr'):
        (out / obsolete).unlink(missing_ok=True)
    world = {'name': '谷中 · 此间', 'core': {'modelX': [-40, 40], 'modelY': [-80, 0], 'sizeMetres': [80, 80]},
             'layers': [], 'props': {}, 'placements': []}
    blocks = INTEG / 'src/blocks/projects/tokyo-blocks'
    anchors = []
    for key in 'ABCDE SX'.replace(' ', ''):
        source = blocks / f'block_{key}/block_{key}.glb' if key in 'AB' else FILL / f'block_{key}/block_{key}.glb'
        uri = convert(source, 'block_' + key, out)
        world['layers'].append({'id': key, 'url': uri, 'mode': 'realtime', 'background': key == 'X'})
        if key in 'AB':
            meta = json.loads((blocks / f'block_{key}/block_{key}_anchors.json').read_text(encoding='utf-8'))
        else:
            meta = json.loads((FILL / f'block_{key}/block_{key}_meta.json').read_text(encoding='utf-8'))
        anchors.extend(dict(x, block=key) for x in meta.get('anchors', []))
    # Front-only parts attach outside existing openings. No shell or road overlays.
    propnames = ['bike01', 'vm02', 'pr_aircon', 'pr_gasmeter', 'pr_plants', 'pr_bins']
    for shop in ('sf02', 'sf03', 'sf04', 'sf05', 'sf06', 'sf07', 'sf08'):
        propnames.extend(shop + '_' + part for part in ('front', 'tent', 'goods')
                         if (PROPS / (shop + '_' + part) / (shop + '_' + part + '.glb')).exists()
                         and (PROPS / (shop + '_' + part) / (shop + '_' + part + '.glb')).stat().st_size > 1000)
    for name in propnames:
        source = PROPS / name / (name + '.glb')
        if source.exists() and source.stat().st_size > 1000:
            uri = convert(source, name, out)
            meta = json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
            world['props'][name] = {'url': uri, 'size': meta['size_m']}
    used = {}
    for an in anchors:
        if an['type'] == 'storefront':
            # A/B were delivered as empty shop openings. C/D/E already have a fit-out;
            # keep it intact instead of stacking a second frontage on top.
            if an['block'] not in 'AB':
                continue
            choices = [s for s in ('sf02', 'sf03', 'sf04', 'sf05', 'sf06', 'sf07', 'sf08')
                       if s + '_front' in world['props']
                       and world['props'][s + '_front']['size'][0] <= an.get('width', 4) * 1.04]
            if not choices:
                continue
            shop = min(choices, key=lambda s: (used.get(s, 0), abs(an.get('width', 4) - world['props'][s + '_front']['size'][0])))
            used[shop] = used.get(shop, 0) + 1
            scale = min(1, an.get('height', 2.6) / world['props'][shop + '_front']['size'][2])
            for part in ('front', 'tent', 'goods'):
                name = shop + '_' + part
                if name in world['props']:
                    world['placements'].append(dict(an, asset=name, scale=scale, offset=.025))
        elif an['block'] in 'AB':
            name = {'ac_outdoor': 'pr_aircon', 'gas_meter': 'pr_gasmeter', 'planter': 'pr_plants',
                    'bicycle': 'bike01', 'vending_or_bin': 'vm02'}.get(an['type'])
            if name in world['props']:
                world['placements'].append(dict(an, asset=name, scale=1, offset=.03))
    (out / 'web/world.json').write_text(json.dumps(world, ensure_ascii=False), encoding='utf-8')
    shutil.copytree(HERE / 'web', out / 'web', dirs_exist_ok=True)
    # The independent repair is never copied back into original D/S sources.
    shutil.copy2(HERE/'derived/temple-access.glb',out/'web/models/temple-access.glb')
    shutil.copy2(HERE/'derived/junction/bk-junction.glb',out/'web/data/bk.glb')
    shutil.copy2(HERE/'derived/junction/junction-details.glb',out/'web/models/junction-details.glb')
    shutil.copy2(HERE/'derived/junction/junction-provenance.json',out/'web/data/junction-provenance.json')
    (out / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=web/index.html">', encoding='utf-8')
    # A portable server works without dependencies on the source filesystem.
    shutil.copy2(HERE / 'scripts/serve.py', out / 'serve.py')
    shutil.copy2(HERE / '打开此间.cmd', out / '打开此间.cmd')
    for source in (HERE / 'README.md',):
        if source.exists():
            shutil.copy2(source, out / source.name)
    notices = out / 'licenses'
    notices.mkdir(exist_ok=True)
    for name, source in [('tokyo-fill.csv', Path(r'D:\project\cijian\nailong\projects\tokyo-fill\asset-register.csv')),
                         ('tokyo-props.md', PROPS / 'LICENSES.md')]:
        shutil.copy2(source, notices / name)
    print('READY', out, 'placements', len(world['placements']), flush=True)


if __name__ == '__main__':
    main()
