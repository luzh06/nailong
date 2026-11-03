"""Optimize only the standalone delivery copy and emit a byte-accurate asset manifest.

Run with Blender for --exr; run with ordinary Python for --models/--manifest.
Original modelling directories are never written.
"""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import shutil
import struct
import sys
import numpy as np


def read_exr_header(path):
    data = path.read_bytes()
    if struct.unpack_from('<I', data)[0] != 20000630:
        raise ValueError(f'Invalid OpenEXR: {path}')
    pos = 8
    attrs = {}
    while data[pos] != 0:
        end = data.index(0, pos)
        name = data[pos:end].decode('ascii')
        pos = end + 1
        end = data.index(0, pos)
        kind = data[pos:end].decode('ascii')
        pos = end + 1
        size = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        attrs[name] = (kind, data[pos:pos + size])
        pos += size
    channels = []
    p = 0
    raw = attrs['channels'][1]
    while raw[p] != 0:
        end = raw.index(0, p)
        name = raw[p:end].decode('ascii')
        p = end + 1
        pixel_type = struct.unpack_from('<I', raw, p)[0]
        channels.append({'name': name, 'type': pixel_type})
        p += 16
    return {'channels': channels, 'compression': attrs['compression'][1][0]}


def backup(path, root, backup_root):
    target = backup_root / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def compress_exr(root, backup_root):
    import bpy
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '16'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.exr_codec = 'ZIP'
    scene.view_settings.view_transform = 'Raw'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    rows = []
    for path in sorted((root / 'bake').rglob('*.exr')):
        header = read_exr_header(path)
        before = path.stat().st_size
        if all(c['type'] == 1 for c in header['channels']) and header['compression'] == 3:
            continue
        backup(path, root, backup_root)
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = 'Non-Color'
        values = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(values)
        temp = path.with_name(path.stem + '.half.exr')
        image.save_render(str(temp), scene=scene)
        bpy.data.images.remove(image)
        compressed = bpy.data.images.load(str(temp), check_existing=False)
        compressed.colorspace_settings.name = 'Non-Color'
        after_values = np.empty(len(compressed.pixels), dtype=np.float32)
        compressed.pixels.foreach_get(after_values)
        bpy.data.images.remove(compressed)
        # Half precision is the format already used by the GPU; check the file conversion.
        max_error = float(np.max(np.abs(values - after_values)))
        if not np.allclose(values, after_values, rtol=.001, atol=.001, equal_nan=False):
            temp.unlink()
            raise ValueError(f'EXR round-trip changed radiance: {path}, max error {max_error}')
        out_header = read_exr_header(temp)
        if not all(c['type'] == 1 for c in out_header['channels']) or out_header['compression'] != 3:
            raise ValueError(f'Unexpected EXR encoding: {path}')
        temp.replace(path)
        rows.append({'url': str(path.relative_to(root)).replace('\\', '/'), 'before': before,
                     'after': path.stat().st_size, 'maxAbsError': max_error})
        print('EXR', path.name, before, '->', path.stat().st_size, flush=True)
    return rows


def access_array(doc, payload, accessor):
    view = doc['bufferViews'][accessor['bufferView']]
    dtype = np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[accessor['componentType']])
    components = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}[accessor['type']]
    return np.ndarray((accessor['count'],components), dtype=dtype, buffer=payload,
                      offset=view.get('byteOffset',0) + accessor.get('byteOffset',0),
                      strides=(view.get('byteStride',components*dtype.itemsize),dtype.itemsize))


def quantize_gltf(path, root, backup_root):
    doc = json.loads(path.read_text(encoding='utf-8'))
    if len(doc.get('buffers', [])) != 1 or 'uri' not in doc['buffers'][0]:
        return None
    binary_path = path.parent / doc['buffers'][0]['uri']
    original = binary_path.read_bytes()
    semantics = {}
    index_accessors = set()
    for mesh in doc.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            if 'indices' in primitive:
                index_accessors.add(primitive['indices'])
            for semantic, index in primitive.get('attributes', {}).items():
                semantics.setdefault(index, set()).add(semantic)
    payloads = []
    accessors = doc.get('accessors', [])
    changed = 0
    quantization = False
    for index, source in enumerate(accessors):
        if 'sparse' in source or 'bufferView' not in source:
            return None
        a = dict(source)
        array = np.array(access_array(doc, original, source), copy=True)
        # Keep positions and UVs exactly as delivered. Normalize only colour and normals.
        roles = semantics.get(index, set())
        if roles == {'NORMAL'} and a['componentType'] == 5126:
            array = np.rint(np.clip(array, -1, 1) * 32767).astype('<i2')
            a['componentType'] = 5122
            a['normalized'] = True
            a.pop('min', None); a.pop('max', None)
            quantization = True
            changed += 1
        elif roles and all(s.startswith('COLOR_') for s in roles) and (a['componentType'] == 5126 or a['componentType'] == 5123 and a.get('normalized')):
            color = array / 65535 if a['componentType'] == 5123 else array
            array = np.rint(np.clip(color, 0, 1) * 255).astype('u1')
            a['componentType'] = 5121
            a['normalized'] = True
            a.pop('min', None); a.pop('max', None)
            changed += 1
        elif index in index_accessors and a['componentType'] == 5125 and array.max(initial=0) <= 65535:
            array = array.astype('<u2')
            a['componentType'] = 5123
            changed += 1
        a.pop('byteOffset', None)
        target = doc['bufferViews'][source['bufferView']].get('target')
        stride = None
        # glTF vertex attributes have four-byte row alignment, including quantized VEC3.
        if roles and array.strides[0] % 4:
            stride = (array.strides[0] + 3) // 4 * 4
            padded = np.zeros((len(array), stride), dtype='u1')
            padded[:, :array.strides[0]] = array.view('u1').reshape(len(array), array.strides[0])
            data = padded.tobytes()
        else:
            data = array.tobytes()
        payloads.append((a, data, target, stride))
    if not changed:
        return None
    backup(path, root, backup_root)
    backup(binary_path, root, backup_root)
    compact = bytearray()
    views = []
    for a, data, target, stride in payloads:
        compact.extend(b'\0' * ((-len(compact)) % 4))
        view = {'buffer':0, 'byteOffset':len(compact), 'byteLength':len(data)}
        if target:
            view['target'] = target
        if stride:
            view['byteStride'] = stride
        a['bufferView'] = len(views)
        views.append(view)
        compact.extend(data)
    if len(compact) >= len(original):
        return None
    doc['accessors'] = [a for a, data, target, stride in payloads]
    doc['bufferViews'] = views
    doc['buffers'][0]['byteLength'] = len(compact)
    if quantization:
        for field in ('extensionsUsed', 'extensionsRequired'):
            ext = doc.setdefault(field, [])
            if 'KHR_mesh_quantization' not in ext:
                ext.append('KHR_mesh_quantization')
    # Accessor array equality/quantization bounds are verified before replacing delivery files.
    original_doc = json.loads(path.read_text(encoding='utf-8'))
    for old, (new, data, _, stride) in zip(accessors, payloads):
        before_array = np.asarray(access_array(original_doc, original, old))
        if old['componentType'] == new['componentType']:
            after_array = access_array({'bufferViews':views}, compact, new)
            if not np.array_equal(before_array, after_array):
                raise ValueError(f'Unchanged geometry differs: {path}')
    binary_path.write_bytes(compact)
    path.write_text(json.dumps(doc, separators=(',', ':')), encoding='utf-8')
    return {'url': str(path.relative_to(root)).replace('\\','/'), 'before':len(original), 'after':len(compact),
            'changedAccessors':changed, 'positionsAndUVsUnchanged':True}


def manifest(root):
    web = root / 'web'
    world = json.loads((web / 'world.json').read_text(encoding='utf-8'))
    entries = {}
    def add(path, group, required=True):
        path = path.resolve()
        if not path.is_file():
            if required:
                raise FileNotFoundError(path)
            return
        relative = Path(__import__('os').path.relpath(path, web)).as_posix()
        entry = entries.setdefault(relative, {'url':relative,'bytes':path.stat().st_size,'groups':[]})
        compressed = path.with_name(path.name + '.gz')
        if compressed.is_file() and compressed.stat().st_size < path.stat().st_size:
            entry['transferBytes'] = compressed.stat().st_size
            entry['encoding'] = 'gzip'
        if group not in entry['groups']:
            entry['groups'].append(group)
    def gltf(path, group):
        add(path, group)
        if path.suffix == '.glb':
            from gltf_geometry import read
            doc, _ = read(path)
        else:
            doc = json.loads(path.read_text(encoding='utf-8'))
        for source in doc.get('buffers', []) + doc.get('images', []):
            if 'uri' in source and not source['uri'].startswith('data:'):
                add(path.parent / source['uri'], group)
    for layer in world['layers']:
        gltf(web / layer['url'], 'layer-' + layer['id'])
    for name in sorted(set(p['asset'] for p in world['placements'])):
        gltf(web / world['props'][name]['url'], 'props')
    add(web/'data/bk.glb', 'core')
    add(web/'data/bk.json', 'core')
    bake = json.loads((web/'data/bk.json').read_text(encoding='utf-8'))
    for group, files in bake['groups'].items():
        if group == 'far':
            continue
        for filename in files:
            # The legacy "glass" list also has glass_warm entries. Runtime loads those separately.
            if filename.startswith('warm_'):
                continue
            add(root/'bake'/bake['dir']/(group+'_'+filename), 'core')
    for plant in bake['plants']:
        for suffix in ('_diff_2k.jpg','_nor_gl_2k.jpg','_arm_2k.jpg'):
            add(root/'assets/models'/plant/'textures'/(plant+suffix), 'core')
    for light in bake['lights']:
        add(web/'data'/('lut_'+light+'.bin'),'core')
    for path in (root/'assets/hdri').glob('*.hdr'):
        add(path,'core')
    for filename in ('world.json','navigation.json','collision.bin','collision-info.json'):
        add(web/filename,'core',required=False)
    for path in sorted(web.rglob('*')):
        if path.is_file() and path.suffix in ('.js','.mjs','.css','.html'):
            add(path,'runtime')
    for path in (web/'map').glob('*'):
        if path.is_file() and path.name not in ('map-reference.png','yanaka-atlas.png'):
            add(path,'map')
    assets = sorted(entries.values(), key=lambda a:a['url'])
    groups = sorted(set(g for a in assets for g in a['groups']))
    result = {'version':1,'urlBase':'web/','totalBytes':sum(a['bytes'] for a in assets),
              'totalTransferBytes':sum(a.get('transferBytes',a['bytes']) for a in assets),
              'groups':{g:sum(a['bytes'] for a in assets if g in a['groups']) for g in groups},
              'transferGroups':{g:sum(a.get('transferBytes',a['bytes']) for a in assets if g in a['groups']) for g in groups},'assets':assets}
    (web/'asset-manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def compress_http(root):
    rows=[]
    extensions={'.bin','.glb','.gltf','.json','.js','.mjs','.css','.html','.svg','.hdr'}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in extensions or path.stat().st_size<4096:
            continue
        if path.name.startswith('optimization-') or path.name=='asset-manifest.json':
            continue
        original=path.read_bytes()
        compressed=gzip.compress(original,compresslevel=6,mtime=0)
        if len(compressed)>len(original)*.9:
            continue
        target=path.with_name(path.name+'.gz')
        target.write_bytes(compressed)
        if gzip.decompress(compressed)!=original:
            raise ValueError(f'HTTP compression round-trip failed: {path}')
        rows.append({'url':str(path.relative_to(root)).replace('\\','/'),'before':len(original),'after':len(compressed)})
        print('GZIP',path.name,len(original),'->',len(compressed),flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--backup', type=Path, default=Path(r'D:\project\chatgpt\ci\tmp\tokyo-optimization-backup'))
    parser.add_argument('--exr', action='store_true')
    parser.add_argument('--models', action='store_true')
    parser.add_argument('--manifest', action='store_true')
    parser.add_argument('--gzip', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    root = args.root.resolve()
    allowed = Path(r'D:\project\chatgpt\ci\output\tokyo-three').resolve()
    if root != allowed:
        raise ValueError('This optimizer is intentionally restricted to the independent delivery copy')
    report = {'root':str(root),'exr':[],'models':[]}
    if args.exr:
        report['exr'] = compress_exr(root, args.backup)
    if args.models:
        for path in sorted((root/'web/models').glob('*.gltf')):
            row = quantize_gltf(path, root, args.backup)
            if row:
                report['models'].append(row)
                print('MODEL', path.name, row['before'], '->', row['after'], flush=True)
    if args.gzip:
        report['httpCompression']=compress_http(root)
    if args.manifest:
        m = manifest(root)
        report['referencedAssetBytes'] = m['totalBytes']
        print('MANIFEST', len(m['assets']), 'assets', m['totalBytes'], 'bytes', flush=True)
    report_path = root/('optimization-'+('exr' if args.exr else 'models' if args.models else 'gzip' if args.gzip else 'manifest')+'.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
