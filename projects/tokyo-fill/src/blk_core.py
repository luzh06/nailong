# Block generator core: mesh accumulator, primitives, materials, scene, export
import bpy, math, random, json, os, sys, time
from math import sin, cos, pi, sqrt, floor, ceil, exp
from mathutils import Vector as V, noise, geometry

ROOT = r"D:\project\cijian\work"
TEX = ROOT + r"\assets\tex2k_lite"
GEN = ROOT + r"\assets\gen"

# ENU metres (x=east,y=north, origin real stair top) -> qs_h1 world: +x south, +y east
ALIGN_E = 32.5   # model_y = E + 32.5  (model stair bottom y=1.4 sits on real stair bottom E=-31.1)
ALIGN_N = 1.8    # model_x = 1.8 - N   (real street centre N=1.8 sits on model x=0)
def to_model(p):
    return (ALIGN_N - p[1], p[0] + ALIGN_E, p[2])


class M:
    """Per-object mesh accumulator; flushes to one Blender mesh with material slots."""
    def __init__(s, name):
        s.name = name; s.v = []; s.uv = []; s.c = []; s.f = []; s.fm = []; s.fs = []; s.mi = {}

    def mid(s, m):
        if m not in s.mi: s.mi[m] = len(s.mi)
        return s.mi[m]

    def poly(s, mat, pts, uvs=None, col=(1, 1, 1), smooth=False):
        i = len(s.v); n = len(pts)
        s.v.extend(tuple(p) for p in pts)
        s.uv.extend(uvs if uvs else [(0, 0)] * n)
        s.c.extend(col if isinstance(col, list) else [col] * n)
        s.f.append(tuple(range(i, i + n))); s.fm.append(s.mid(mat)); s.fs.append(smooth)

    def grid(s, mat, P, UV=None, C=None, smooth=True, close_u=False, skip=None):
        """P[i][j]: i along u, j along v. close_u wraps i."""
        nu = len(P); nv = len(P[0]); b = len(s.v); m = s.mid(mat)
        for i in range(nu):
            for j in range(nv):
                s.v.append(tuple(P[i][j]))
                s.uv.append(UV[i][j] if UV else (0, 0))
                s.c.append(C[i][j] if C else (1, 1, 1))
        lim = nu if close_u else nu - 1
        for i in range(lim):
            i2 = (i + 1) % nu
            for j in range(nv - 1):
                if skip and skip(i, j): continue
                s.f.append((b + i * nv + j, b + i2 * nv + j, b + i2 * nv + j + 1, b + i * nv + j + 1))
                s.fm.append(m); s.fs.append(smooth)

    def tris(s): return sum(len(f) - 2 for f in s.f)


def tint(c, k): return (c[0] * k, c[1] * k, c[2] * k)


class Frame:
    """Local frame: a along u, b along v, c along outward n."""
    def __init__(s, o, u, v, n=None):
        s.o = V(o); s.u = V(u).normalized(); s.v = V(v).normalized()
        s.n = V(n).normalized() if n is not None else s.u.cross(s.v).normalized()

    def p(s, a, b=0, c=0): return s.o + s.u * a + s.v * b + s.n * c

    def uvframe(s, a, b): return (a, b)


def box(m, mat, f, a0, a1, b0, b1, c0, c1, ch=0.0, sc=1.0, col=(1, 1, 1), off=(0, 0)):
    """Oriented box in frame f; ch>0 gives flat chamfers that catch highlights."""
    P = lambda a, b, c: f.p(a, b, c)
    def q(pts, ua, va):
        uvs = [((ua(x) + off[0]) / sc, (va(x) + off[1]) / sc) for x in pts]
        m.poly(mat, [P(*x) for x in pts], uvs, col)
    A0, A1, B0, B1, C0, C1 = a0 + ch, a1 - ch, b0 + ch, b1 - ch, c0 + ch, c1 - ch
    ga = lambda x: x[0]; gb = lambda x: x[1]; gc = lambda x: x[2]
    q([(A0, B0, c1), (A1, B0, c1), (A1, B1, c1), (A0, B1, c1)], ga, gb)      # +c
    q([(A1, B0, c0), (A0, B0, c0), (A0, B1, c0), (A1, B1, c0)], ga, gb)      # -c
    q([(a1, B0, C1), (a1, B0, C0), (a1, B1, C0), (a1, B1, C1)], gc, gb)      # +a
    q([(a0, B0, C0), (a0, B0, C1), (a0, B1, C1), (a0, B1, C0)], gc, gb)      # -a
    q([(A0, b1, C1), (A1, b1, C1), (A1, b1, C0), (A0, b1, C0)], ga, gc)      # +b
    q([(A0, b0, C0), (A1, b0, C0), (A1, b0, C1), (A0, b0, C1)], ga, gc)      # -b
    if ch <= 0: return
    # edge chamfers
    q([(A0, b1, C1), (A0, B1, c1), (A1, B1, c1), (A1, b1, C1)], ga, gb)
    q([(A0, b0, C1), (A1, b0, C1), (A1, B0, c1), (A0, B0, c1)], ga, gb)
    q([(A0, B1, c0), (A0, b1, C0), (A1, b1, C0), (A1, B1, c0)], ga, gb)
    q([(A0, B0, c0), (A1, B0, c0), (A1, b0, C0), (A0, b0, C0)], ga, gb)
    q([(a1, B0, C1), (A1, B0, c1), (A1, B1, c1), (a1, B1, C1)], gc, gb)
    q([(A0, B0, c1), (a0, B0, C1), (a0, B1, C1), (A0, B1, c1)], gc, gb)
    q([(A1, B0, c0), (a1, B0, C0), (a1, B1, C0), (A1, B1, c0)], gc, gb)
    q([(a0, B0, C0), (A0, B0, c0), (A0, B1, c0), (a0, B1, C0)], gc, gb)
    q([(A1, b1, C1), (a1, B1, C1), (a1, B1, C0), (A1, b1, C0)], ga, gb)
    q([(a0, B1, C1), (A0, b1, C1), (A0, b1, C0), (a0, B1, C0)], ga, gb)
    q([(A1, b0, C0), (a1, B0, C0), (a1, B0, C1), (A1, b0, C1)], ga, gb)
    q([(a0, B0, C0), (A0, b0, C0), (A0, b0, C1), (a0, B0, C1)], ga, gb)


def tube(m, mat, pts, r, n=8, col=(1, 1, 1), sc=.5):
    """Round pipe through pts with mitred elbows; smooth normals."""
    pts = [V(p) for p in pts]; L = len(pts)
    up = V((0, 0, 1))
    t0 = (pts[1] - pts[0]).normalized()
    if abs(t0.dot(up)) > .9: up = V((1, 0, 0))
    P = []; UV = []; d = 0
    for k in range(n + 1):
        P.append([]); UV.append([])
    for j, p in enumerate(pts):
        a = (pts[j] - pts[j - 1]).normalized() if j else (pts[1] - pts[0]).normalized()
        b = (pts[j + 1] - pts[j]).normalized() if j < L - 1 else a
        t = (a + b).normalized()
        s = t.cross(up).normalized(); w = s.cross(t).normalized()
        if j: d += (pts[j] - pts[j - 1]).length
        for k in range(n + 1):
            th = 2 * pi * k / n
            P[k].append(p + s * (cos(th) * r) + w * (sin(th) * r))
            UV[k].append((k / n * 2 * pi * r / sc, d / sc))
    C = [[col] * L for _ in range(n + 1)]
    m.grid(mat, P, UV, C, smooth=True)


def lerp(a, b, t): return a + (b - a) * t


def nz(p, f=1.0):
    return noise.noise(V((p[0] * f, p[1] * f, p[2] * f)))


def wall_col(p, base, top, tc, amt=1.0):
    """Macro weathering carried in vertex colour: ground splash, eave staining, large mottling."""
    z = p[2] - base
    k = 1.0
    k -= amt * .30 * exp(-max(z, 0) / .55)
    k -= amt * .13 * exp(-max(top - z, 0) / .6)
    k += amt * (.11 * nz(p, .55) + .06 * nz(p, 1.9))
    k = max(.3, k)
    w = amt * .03 * nz(p, .3)   # hue drift
    return (tc[0] * k * (1 + w), tc[1] * k, tc[2] * k * (1 - w))


def wall(m, mat, f, w, h, holes=(), a0=0, seg=.3, tc=(1, 1, 1), off=(0, 0), sc=3.0, top=None, base_z=None,
         bump=.005, amt=1.0, rough_edge=False):
    """Rectilinear wall grid with rectangular holes (a0,b0,a1,b1 in wall coords)."""
    us = {a0, a0 + w}; vs = {0.0, h}
    nu = max(1, int(w / seg)); nv = max(1, int(h / seg))
    for i in range(nu): us.add(a0 + w * i / nu)
    for j in range(nv): vs.add(h * j / nv)
    for H in holes:
        us.update((H[0], H[2])); vs.update((H[1], H[3]))
    us = sorted(x for x in us if a0 - 1e-6 <= x <= a0 + w + 1e-6); vs = sorted(x for x in vs if -1e-6 <= x <= h + 1e-6)
    # merge near-duplicates that make sliver quads
    def clean(L):
        o = [L[0]]
        for x in L[1:]:
            if x - o[-1] > .012: o.append(x)
        return o
    us = clean(us); vs = clean(vs)
    bz = f.o.z if base_z is None else base_z
    tp = (h if top is None else top)
    P = []; UV = []; C = []
    for u in us:
        pc = []; uc = []; cc = []
        for t in vs:
            p = f.p(u, t, 0)
            d = bump * (nz(p, .9) + .4 * nz(p, 2.7)) if bump else 0
            edge = min(u - a0, a0 + w - u)
            d *= min(1, edge / .25)
            p = f.p(u, t, d)
            pc.append(p); uc.append(((u + off[0]) / sc, (t + off[1]) / sc))
            cc.append(wall_col(p, bz, tp, tc, amt))
        P.append(pc); UV.append(uc); C.append(cc)
    def skip(i, j):
        cu = (us[i] + us[i + 1]) / 2; cv = (vs[j] + vs[j + 1]) / 2
        return any(H[0] < cu < H[2] and H[1] < cv < H[3] for H in holes)
    m.grid(mat, P, UV, C, smooth=True, skip=skip)


def corner_strip(m, mat, p0, n0, n1, c, h, sc, tc, base, top, seg=.4, off=0):
    """Rounded plaster/siding corner between two walls, c = setback from the corner."""
    t = [p0 + n0 * 0 - (-n1) * 0]  # keep local names short
    a = V(p0) - n1 * c  # on wall with normal n0
    b = V(p0) - n0 * c  # on wall with normal n1
    mid = V(p0) - (n0 + n1) * (c * .29)
    nv = max(1, int(h / seg))
    P = [[], [], []]; UV = [[], [], []]; C = [[], [], []]
    for j in range(nv + 1):
        z = h * j / nv
        for i, q in enumerate((a, mid, b)):
            pp = q + V((0, 0, z)); P[i].append(pp); UV[i].append(((off + i * c) / sc, z / sc)); C[i].append(wall_col(pp, base, top, tc))
    m.grid(mat, P, UV, C, smooth=True)


DEC_N = 4
def decal(m, f, a, b, w, h, cell, off=.004, flip=False, k=1.0, mat="decal"):
    """Alpha decal quad from the 4x4 atlas, offset in front of the surface."""
    cx = cell % DEC_N; cy = cell // DEC_N
    u0 = cx / DEC_N; u1 = (cx + 1) / DEC_N; v1 = 1 - cy / DEC_N; v0 = 1 - (cy + 1) / DEC_N
    if flip: u0, u1 = u1, u0
    # atlas top edge sits at the wall-side start of a streak
    pts = [f.p(a, b, off), f.p(a + w, b, off), f.p(a + w, b + h, off), f.p(a, b + h, off)]
    m.poly(mat, pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], (k, k, k))


# ---------- roofs ----------
TW, TR = .30, .245   # tile width / row pitch

def tile_slope(m, A, B, C, D, rng, palette=((.105, .11, .12), (.08, .085, .095), (.14, .145, .155)), mat="kawara", wav=.042, rows_skip=0):
    """J-tile field on the plane A-B (eave) to D-C (ridge). Each tile is its own patch so colour steps per tile."""
    A, B, C, D = V(A), V(B), V(C), V(D)
    ux = (B - A).normalized()
    slope = ((C + D) / 2 - (A + B) / 2)
    nn = ux.cross(slope).normalized()
    if nn.z < 0: nn = -nn
    up = nn.cross(ux).normalized()
    if up.dot(slope) < 0: up = -up
    S = slope.dot(up); rows = max(1, int(round(S / TR)))
    # slab under tiles
    m.poly("roofbase", [A - nn * .03, B - nn * .03, C - nn * .03, D - nn * .03], None, (.5, .5, .5))
    lL = lambda t: (A + (D - A) * t - A).dot(ux)
    lR = lambda t: (B + (C - B) * t - A).dot(ux)
    prof = [(u / 8, .5 - .5 * cos(2 * pi * (u / 8) ** .85)) for u in range(9)]
    for r in range(rows):
        t0 = r / rows; t1 = (r + 1) / rows; tc = (t0 + t1) / 2
        L = lL(tc); R = lR(tc)
        i0 = int(floor(L / TW)); i1 = int(ceil(R / TW))
        s0 = S * t0 - .012; s1 = S * t1 + .03
        org = A + up * 0
        for i in range(i0, i1):
            x0 = max(i * TW, L); x1 = min((i + 1) * TW, R)
            if x1 - x0 < .03: continue
            base = palette[0] if rng.random() < .72 else palette[rng.randrange(len(palette))]
            k = 1 + (rng.random() - .5) * .1
            if rng.random() < .03: k *= .82
            col = tint(base, k)
            P = []; UV = []
            lift = lambda s: .032 * (1 - (s - s0) / (s1 - s0))
            for u_, w_ in prof:
                x = i * TW + u_ * TW
                x = min(max(x, x0), x1)
                row = []; uvr = []
                for s in (s0, s1):
                    row.append(org + ux * x + up * s + nn * (wav * w_ + lift(s)))
                    uvr.append(((x) / 1.2 + r * .37, s / 1.2))
                P.append(row); UV.append(uvr)
            CC = [[col, col] for _ in P]
            m.grid(mat, P, UV, CC, smooth=True)
            # butt lip closes the gap under the row above
            pts = [p[0] for p in P]
            lipP = [[q, q - nn * .03] for q in pts]
            m.grid(mat, lipP, [[(0, 0), (0, .02)] for _ in pts], [[tint(col, .75)] * 2 for _ in pts], smooth=True)


def ridge(m, P0, P1, rng, mat="kawara", layers=3, cap=.082, col=(.09, .095, .105)):
    """Noshi stack and round cap along ridge or hip."""
    P0, P1 = V(P0), V(P1); d = P1 - P0; L = d.length
    if L < .05: return
    u = d.normalized(); up = V((0, 0, 1)); s = up.cross(u)
    if s.length < .1: s = V((1, 0, 0))
    s.normalize(); v = u.cross(s).normalized()
    if v.z < 0: v = -v; s = -s
    f = Frame(P0, u, v, s)
    n = max(1, int(L / .31)); seg = L / n
    for k in range(layers):
        hh = .04 + k * .036
        w = .15 - k * .018
        for i in range(n):
            j = (rng.random() - .5) * .006
            box(m, mat, f, i * seg + (k % 2) * .07, min(L, (i + 1) * seg + (k % 2) * .07), hh - .02 + j, hh + .018 + j, -w, w, ch=.004,
                sc=.8, col=tint(col, 1 + (rng.random() - .5) * .16))
    b = .04 + layers * .036 + .03
    tube(m, mat, [f.p(0, b, 0), f.p(L, b, 0)], cap, 10, col, sc=1.)
    for i in range(n + 1):  # cap collars
        tube(m, mat, [f.p(i * seg - .012, b, 0), f.p(i * seg + .012, b, 0)], cap + .007, 10, tint(col, .85), sc=1.)


def seam_slope(m, A, B, C, D, mat, rib, tc, pitch=.455, sc=2.0, rib_h=.035):
    """Flat metal sheet plane with ribs running up the slope."""
    A, B, C, D = V(A), V(B), V(C), V(D)
    ux = (B - A).normalized(); W = (B - A).length
    sl = ((C + D) / 2 - (A + B) / 2); Ls = sl.length; ws = sl.normalized()
    nn = ux.cross(ws).normalized()
    if nn.z < 0: nn = -nn
    nu = max(2, int(W / .6)); nv = max(2, int(Ls / .6))
    P = []; UV = []; Cc = []
    for i in range(nu + 1):
        r = []; q = []; c = []
        for j in range(nv + 1):
            a = i / nu; b = j / nv
            p = lerp(lerp(A, B, a), lerp(D, C, a), b)
            r.append(p); q.append((a * W / sc, b * Ls / sc))
            c.append(wall_col(p, -3, 99, tc, .8))
        P.append(r); UV.append(q); Cc.append(c)
    m.grid(mat, P, UV, Cc, smooth=False)
    n = int(W / pitch)
    fr = Frame(A, ux, ws, nn)
    for i in range(1, n):
        a = i * pitch
        t = a / W
        pa = lerp(A, B, t); pb = lerp(D, C, t)
        L = (pb - pa).length
        fi = Frame(pa, ux, (pb - pa).normalized(), nn)
        box(m, rib, fi, -.016, .016, 0, L, 0, rib_h, ch=.006, col=tc, sc=sc)


# ---------- materials ----------
MATS = {
    # name: (tex dir, metres per tile handled at UV time, base tint, overrides)
}

def _img(path, cs):
    im = bpy.data.images.get(os.path.basename(os.path.dirname(path)) + "_" + os.path.basename(path))
    if im is None:
        im = bpy.data.images.load(path)
        im.name = os.path.basename(os.path.dirname(path)) + "_" + os.path.basename(path)
    im.colorspace_settings.name = cs
    return im


def pbr(name, texid=None, rough=None, metal=None, solid=None, alpha=None, nor_k=1.0, rough_k=None, spec=.5, backface=False):
    """glTF-friendly Principled material: base image x vertex colour, normal map, ARM packed roughness/metal."""
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    nt = mt.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Specular IOR Level"].default_value = spec
    va = nt.nodes.new("ShaderNodeVertexColor"); va.layer_name = "Col"
    if texid and not all(os.path.exists(os.path.join(TEX, texid, x)) for x in ("diff.jpg", "nor.jpg")):
        print("MISSING TEX", texid, flush=True); texid = None; solid = solid or (.6, .6, .6)
    if texid:
        d = os.path.join(TEX, texid)
        tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = _img(os.path.join(d, "diff.jpg"), "sRGB")
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(tb.outputs["Color"], mx.inputs["A"]); nt.links.new(va.outputs["Color"], mx.inputs["B"])
        nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = _img(os.path.join(d, "nor.jpg"), "Non-Color")
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = nor_k
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
        arm = os.path.join(d, "arm1k.jpg")
        if os.path.exists(arm) and rough is None:
            ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = _img(arm, "Non-Color")
            sp = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(ta.outputs["Color"], sp.inputs["Color"])
            nt.links.new(sp.outputs["Green"], bs.inputs["Roughness"])
            nt.links.new(sp.outputs["Blue"], bs.inputs["Metallic"])
        else:
            bs.inputs["Roughness"].default_value = rough if rough is not None else .7
            bs.inputs["Metallic"].default_value = metal or 0
    else:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        mx.inputs["A"].default_value = (*(solid or (.8, .8, .8)), 1)
        nt.links.new(va.outputs["Color"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = rough if rough is not None else .5
        bs.inputs["Metallic"].default_value = metal or 0
    if alpha is not None:
        bs.inputs["Alpha"].default_value = alpha
        mt.surface_render_method = "BLENDED"
    return mt


def decal_mat():
    mt = bpy.data.materials.new("decal"); mt.use_nodes = True
    nt = mt.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = _img(GEN + r"\decals.png", "sRGB")
    nt.links.new(t.outputs["Color"], bs.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], bs.inputs["Alpha"])
    bs.inputs["Roughness"].default_value = .85
    mt.surface_render_method = "BLENDED"
    return mt


def curtain_mat():
    mt = bpy.data.materials.new("curtain"); mt.use_nodes = True
    nt = mt.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = _img(GEN + r"\curtain.jpg", "sRGB")
    va = nt.nodes.new("ShaderNodeVertexColor"); va.layer_name = "Col"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    nt.links.new(t.outputs["Color"], mx.inputs["A"]); nt.links.new(va.outputs["Color"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = .8
    return mt


def build_materials(defs):
    out = {}
    for k, kw in defs.items():
        if k == "decal": out[k] = decal_mat()
        elif k == "curtain": out[k] = curtain_mat()
        else: out[k] = pbr(k, **kw)
    return out


def flush(M_, mats, coll, tag="block"):
    """Create the Blender object from a mesh accumulator, converting ENU to model coordinates."""
    me = bpy.data.meshes.new(M_.name)
    vs = [to_model(p) for p in M_.v]
    me.from_pydata(vs, [], M_.f)
    me.update(calc_edges=True)
    order = sorted(M_.mi, key=lambda k: M_.mi[k])
    for k in order: me.materials.append(mats[k])
    me.polygons.foreach_set("material_index", M_.fm)
    me.polygons.foreach_set("use_smooth", M_.fs)
    uv = me.uv_layers.new(name="UVMap")
    li = [0] * len(me.loops); me.loops.foreach_get("vertex_index", li)
    fl = []
    for i in li: fl.extend(M_.uv[i])
    uv.data.foreach_set("uv", fl)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    cf = []
    for c in M_.c: cf.extend((c[0], c[1], c[2], 1.0))
    ca.data.foreach_set("color", cf)
    me.color_attributes.active_color_index = 0
    me.update()
    ob = bpy.data.objects.new(M_.name, me); coll.objects.link(ob)
    return ob


# ---------- scene ----------
def setup_render(res, spp):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    p = bpy.context.preferences.addons["cycles"].preferences
    p.compute_device_type = "OPTIX"; p.get_devices()
    for d in p.devices: d.use = d.type == "OPTIX"
    c = sc.cycles; c.device = "GPU"; c.samples = spp; c.use_adaptive_sampling = True; c.adaptive_threshold = .02
    c.use_denoising = True; c.denoiser = "OPTIX"; c.max_bounces = 8; c.transparent_max_bounces = 16; c.caustics_reflective = False
    c.caustics_refractive = False
    sc.render.resolution_x = res; sc.render.resolution_y = int(res * 9 / 16); sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = .15
    sc.render.film_transparent = False


def lighting(az=250, el=30, sun=3.2, sky=2.6, warm=(1, .86, .68)):
    """Fixed preview lighting. az is compass degrees in real ENU."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("sky"); w.use_nodes = True; sc.world = w
    nt = w.node_tree; bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(ROOT + r"\assets\sky_2k.hdr")
    nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = sky
    sd = bpy.data.lights.new("sun", "SUN"); sd.energy = sun; sd.color = warm; sd.angle = math.radians(1.2)
    ob = bpy.data.objects.new("sun", sd); bpy.context.scene.collection.objects.link(ob)
    a = math.radians(az); e = math.radians(el)
    # direction toward sun in ENU, then to model axes
    dE, dN, dZ = sin(a) * cos(e), cos(a) * cos(e), sin(e)
    dv = V((-dN, dE, dZ))
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = dv.to_track_quat("Z", "Y")


def add_cam(name, pos, look, lens=26):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = .05; cd.clip_end = 2000
    ob = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(ob)
    p = V(to_model(pos)); l = V(to_model(look))
    ob.location = p; ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = (l - p).to_track_quat("-Z", "Y")
    return ob


def export_glb(coll, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects: o.select_set(True)
    bpy.context.view_layer.objects.active = coll.objects[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=False,
                              export_vertex_color="ACTIVE", export_all_vertex_colors=False, export_tangents=False,
                              export_image_format="JPEG", export_jpeg_quality=74, export_yup=True, export_cameras=False,
                              export_lights=False, export_materials="EXPORT")
