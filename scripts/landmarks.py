"""Landmark towers visible from the Kirribilli viewpoint, modelled with their real massing.

OSM gives most towers as plain extrusions, which is why the skyline looked uniform. These
replace the OSM parts at each site with parametric shapes: setbacks, crowns, twists, fins.
Positions come from the OSM features (scene metres); sizes are approximate and should be
calibrated against reference photos like the Opera House was.

All geometry goes into the Buildings mesh, so it shares the façade shader; each face carries the
same colour attribute as other buildings (seed, style, height).
"""
import math

from mathutils import Vector

from meshkit import add_beam, add_face, add_prism

# Extra façade styles (the shader reads style = int(attribute.y * STYLE_SLOTS))
STYLE_SLOTS = 16
STYLE_GLASS_TOWER, STYLE_OFFICE = 0, 1
STYLE_UTILITY = 6
STYLE_GOLD = 8         # Sydney Tower turret
STYLE_RIBBED = 9       # Australia Square: off-white concrete, deep vertical fins
STYLE_FINNED = 10      # Quay Quarter Tower: glass behind vertical aluminium fins


def style_color(style, seed, height):
    return (seed, (style + 0.5) / STYLE_SLOTS, min(height / 300.0, 1.0), 1.0)


def paint_new_faces(bm, first_face_index, color):
    """Give every face created since `first_face_index` the building colour attribute."""
    layer = bm.loops.layers.float_color.verify()
    bm.faces.ensure_lookup_table()
    for face in bm.faces[first_face_index:]:
        for loop in face.loops:
            loop[layer] = color


def circle(cx, cy, radius, segments, phase=0.0):
    return [(cx + radius * math.cos(phase + 2 * math.pi * i / segments),
             cy + radius * math.sin(phase + 2 * math.pi * i / segments)) for i in range(segments)]


def add_loft(bm, sections, cap=True):
    """Skin a list of (z, ring) sections with equal vertex counts. U = arc length, V = z."""
    rings = []
    for z, ring in sections:
        rings.append([bm.verts.new((x, y, z)) for x, y in ring])
    n = len(sections[0][1])
    for k in range(len(sections) - 1):
        z0, z1 = sections[k][0], sections[k + 1][0]
        run = 0.0
        for i in range(n):
            j = (i + 1) % n
            a, b = rings[k][i].co, rings[k][j].co
            length = (Vector((b.x, b.y)) - Vector((a.x, a.y))).length
            add_face(bm, (rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]), 0,
                     ((run, z0), (run + length, z0), (run + length, z1), (run, z1)))
            run += length
    if cap:
        top = rings[-1]
        centre = bm.verts.new(sum((v.co for v in top), Vector()) / len(top))
        for i in range(n):
            verts = (top[i], top[(i + 1) % n], centre)
            add_face(bm, verts, 0, [(v.co.x, v.co.y) for v in verts])


def sydney_tower(bm, cx, cy, ground):
    """309 m to the spire tip: slim shaft, gold nine-level turret at ~230-262 m, stay cables."""
    start = len(bm.faces)
    shaft = [(ground + z, circle(cx, cy, 4.2, 24)) for z in (0, 228)]
    add_loft(bm, shaft, cap=False)
    paint_new_faces(bm, start, style_color(STYLE_RIBBED, 0.31, 230))

    start = len(bm.faces)
    turret = [(ground + z, circle(cx, cy, r, 40)) for z, r in
              ((226, 5.0), (230, 12.5), (234, 16.0), (240, 16.6), (254, 16.6), (259, 14.5), (263, 9.0))]
    add_loft(bm, turret)
    paint_new_faces(bm, start, style_color(STYLE_GOLD, 0.5, 263))

    start = len(bm.faces)
    spire = [(ground + z, circle(cx, cy, r, 8)) for z, r in ((263, 1.6), (290, 0.9), (309, 0.25))]
    add_loft(bm, spire)
    # 56 stay cables from the podium roof ring up to the underside of the turret
    for i in range(56):
        a = 2 * math.pi * i / 56
        foot = Vector((cx + 24 * math.cos(a), cy + 24 * math.sin(a), ground + 40))
        head = Vector((cx + 5.2 * math.cos(a + 0.35), cy + 5.2 * math.sin(a + 0.35), ground + 226))
        add_beam(bm, foot, head, 0.35, 0.35)
    paint_new_faces(bm, start, style_color(STYLE_UTILITY, 0.62, 300))


def crown_sydney(bm, cx, cy, ground, height=271.0):
    """Three-petal plan that twists and tapers as it rises (Barangaroo)."""
    start = len(bm.faces)
    sections = []
    for k in range(0, 31):
        t = k / 30
        z = ground + t * height
        radius = 24.0 - 6.0 * t - (8.0 * (t - 0.92) / 0.08 if t > 0.92 else 0.0)
        twist = math.radians(55.0 * t)
        ring = []
        for i in range(72):
            a = 2 * math.pi * i / 72
            r = radius * (0.74 + 0.26 * math.cos(3 * a))
            ring.append((cx + r * math.cos(a + twist), cy + r * math.sin(a + twist)))
        sections.append((z, ring))
    add_loft(bm, sections)
    paint_new_faces(bm, start, style_color(STYLE_GLASS_TOWER, 0.08, height))


def quay_quarter_tower(bm, cx, cy, ground):
    """Five stacked, shifted and slightly rotated volumes, 216 m (50 Bridge Street)."""
    start = len(bm.faces)
    stacks = ((0, 52, 0, 0, 0), (52, 96, 5, -3, 4), (96, 140, -4, 4, -3), (140, 180, 6, 2, 5), (180, 216, -2, -5, -2))
    for z0, z1, dx, dy, rot in stacks:
        a = math.radians(rot + 8.0)
        hw, hd = 24.0, 17.0
        ring = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = sx * hw, sy * hd
            ring.append((cx + dx + x * math.cos(a) - y * math.sin(a), cy + dy + x * math.sin(a) + y * math.cos(a)))
        add_prism(bm, [ring], ground + z0, ground + z1)
    paint_new_faces(bm, start, style_color(STYLE_FINNED, 0.44, 216))


def australia_square(bm, cx, cy, ground):
    """Harry Seidler's 170 m concrete cylinder with 48 deep vertical fins."""
    start = len(bm.faces)
    add_prism(bm, [circle(cx, cy, 20.0, 64)], ground, ground + 170)
    for i in range(48):
        a = 2 * math.pi * i / 48
        foot = Vector((cx + 20.9 * math.cos(a), cy + 20.9 * math.sin(a), ground))
        add_beam(bm, foot, foot + Vector((0, 0, 171)), 1.8, 0.7)
    paint_new_faces(bm, start, style_color(STYLE_RIBBED, 0.12, 170))


def tower_crown(bm, footprint, top, crown_height, mast_height, cx, cy):
    """Open crown of vertical blades round the roof edge plus a central mast (Governor Phillip
    Tower's "toast rack", Chifley Tower's mast)."""
    start = len(bm.faces)
    ring = footprint
    for i in range(len(ring)):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % len(ring)]
        length = math.hypot(x1 - x0, y1 - y0)
        for k in range(max(1, int(length / 3.0))):
            t = (k + 0.5) / max(1, int(length / 3.0))
            p = Vector((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, top))
            if crown_height > 0:
                add_beam(bm, p, p + Vector((0, 0, crown_height)), 0.5, 1.6)
    if mast_height > 0:
        add_beam(bm, Vector((cx, cy, top)), Vector((cx, cy, top + mast_height)), 1.4, 1.4)
    paint_new_faces(bm, start, style_color(STYLE_UTILITY, 0.7, top))


# name -> (OSM site centre in scene metres, radius of OSM parts to replace, builder)
LANDMARKS = {
    "Sydney Tower": ((-573.0, -1523.0), 20.0, "sydney_tower"),
    "Crown Sydney": ((-1306.0, -584.0), 35.0, "crown"),
    "Quay Quarter Tower": ((-340.0, -696.0), 32.0, "qqt"),
    "Australia Square": ((-678.0, -904.0), 26.0, "australia_square"),
}
# Towers kept from OSM that get a crown: name -> (site, crown blade height, mast height)
CROWNS = {
    "Governor Phillip Tower": ((-342.0, -806.0), 18.0, 27.0),
    "Chifley Tower": ((-314.0, -970.0), 0.0, 27.0),
    "Salesforce Tower": ((-605.0, -615.0), 8.0, 0.0),
}
REPLACE_MIN_HEIGHT = 40.0   # podiums and low neighbours inside a site radius are kept


def build_landmark(bm, kind, cx, cy, ground):
    {"sydney_tower": sydney_tower, "crown": crown_sydney, "qqt": quay_quarter_tower,
     "australia_square": australia_square}[kind](bm, cx, cy, ground)
