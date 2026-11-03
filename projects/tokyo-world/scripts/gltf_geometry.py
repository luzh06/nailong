"""Read static glTF geometry in its final world coordinates without loading images."""
import json
from pathlib import Path
import struct
import numpy as np


def outside_box(triangles, bounds):
    """Clip triangles to the complement of the runtime fragment-discard box."""
    x0,x1,z0,z1=bounds
    result=[]
    for tri in triangles:
        lo=tri.min(axis=0);hi=tri.max(axis=0)
        if hi[0]<=x0 or lo[0]>=x1 or hi[2]<=z0 or lo[2]>=z1:
            result.append(tri);continue
        remaining=[p for p in tri]
        for axis,value,sign in [(0,x0,1),(0,x1,-1),(2,z0,1),(2,z1,-1)]:
            if not remaining:break
            inside=[];outside=[]
            for p,q in zip(remaining,remaining[1:]+remaining[:1]):
                d=(p[axis]-value)*sign;e=(q[axis]-value)*sign
                (inside if d>=0 else outside).append(p)
                if (d>=0)!=(e>=0):
                    point=p+(q-p)*d/(d-e);inside.append(point);outside.append(point)
            for i in range(1,len(outside)-1):result.append([outside[0],outside[i],outside[i+1]])
            remaining=inside
    return np.asarray(result,dtype='f4').reshape(-1,3,3)


def read(path):
    path = Path(path)
    if path.suffix == '.glb':
        data = path.read_bytes()
        if data[:4] != b'glTF':
            raise ValueError(f'Missing GLB payload: {path}')
        length = struct.unpack_from('<I', data, 12)[0]
        doc = json.loads(data[20:20 + length])
        buffers = [data[28 + length:]]
    else:
        doc = json.loads(path.read_text(encoding='utf-8'))
        buffers = [(path.parent / b['uri']).read_bytes() for b in doc['buffers']]
    return doc, buffers


def accessor(doc, buffers, index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
    width = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    offset = v.get('byteOffset',0) + a.get('byteOffset',0)
    return np.ndarray((a['count'],width), dtype=dtype, buffer=buffers[v.get('buffer',0)], offset=offset,
                      strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize))


def transform(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape(4,4).T
    x,y,z,w = node.get('rotation',[0,0,0,1])
    r = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m = np.eye(4)
    m[:3,:3] = r @ np.diag(node.get('scale',[1,1,1]))
    m[:3,3] = node.get('translation',[0,0,0])
    return m


def primitives(path, parent=None):
    doc,buffers = read(path)
    def walk(index, matrix):
        node = doc['nodes'][index]
        matrix = matrix @ transform(node)
        if 'mesh' in node:
            for p in doc['meshes'][node['mesh']]['primitives']:
                if p.get('mode',4) != 4:
                    continue
                points = accessor(doc,buffers,p['attributes']['POSITION']).astype('f4')
                points = points @ matrix[:3,:3].T + matrix[:3,3]
                indices = accessor(doc,buffers,p['indices']).ravel() if 'indices' in p else np.arange(len(points))
                mat = doc.get('materials',[{}])[p.get('material',0)].get('name','')
                yield node.get('name',''), mat, points.astype('f4'), indices.reshape(-1,3)
        for child in node.get('children',[]):
            yield from walk(child,matrix)
    for root in doc['scenes'][doc.get('scene',0)]['nodes']:
        yield from walk(root,np.eye(4) if parent is None else parent)
