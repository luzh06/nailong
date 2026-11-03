# make_decals2.py: printed art for the batch shops. Every name is invented; fonts SIL OFL.
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = r'D:\Cijian\assets\decals'
F = r'D:\Cijian\assets\fonts'
def font(n, s): return ImageFont.truetype(os.path.join(F, n + '.ttf'), s)
MIN, YUJI, DOT, GOTH, KAI, REG = 'ShipporiMincho-ExtraBold', 'YujiSyuku-Regular', 'DotGothic16-Regular', 'ZenKakuGothicNew-Bold', 'KaiseiOpti-Bold', 'ReggaeOne-Regular'
def ctext(d, xy, s, f, fill): d.text(xy, s, font=f, fill=fill, anchor='mm')
def vtext(d, x, y0, s, f, fill, step=None):
    step = step or int(f.size * 1.08)
    for i, c in enumerate(s): d.text((x, y0 + i * step), c, font=f, fill=fill, anchor='ma')
def tin(name, w_m, h_m, bg, fg, big, small, phone):
    W, H = int(w_m * 400), int(h_m * 400)
    im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 26), fill=tuple(int(c * .7) for c in bg)); d.rectangle((0, H - 26, W, H), fill=tuple(int(c * .7) for c in bg))
    n = len(big)
    for i, c in enumerate(big):
        ctext(d, (W * (i + .5) / n, H * .40), c, font(MIN, int(H * .33)), fg)
    ctext(d, (W * .5, H * .70), small, font(GOTH, int(H * .1)), fg)
    ctext(d, (W * .5, H * .86), phone, font(GOTH, int(H * .07)), fg)
    im.save(os.path.join(OUT, name + '.png'))
tin('sf03_tin', 5.0, 2.0, (34, 92, 168), (246, 246, 240), '鮮魚 魚辰', '活魚・干物・刺身', '☎ 0000-2817')
tin('sf08_tin', 6.0, 2.0, (34, 120, 72), (248, 246, 232), '青果 八百政', '朝採り野菜・果物', '☎ 0000-8031')
def tent(name, w_m, l_m, top, top2, val, fg, text, side, stripes=0, big=(MIN, 150), small=(GOTH, 70), stroke=0):
    W, H = int(w_m * 1000), int(l_m * 1000); vh = 270
    im = Image.new('RGB', (W, H), top); d = ImageDraw.Draw(im)
    if stripes:
        for x in range(0, W, stripes * 2): d.rectangle((x + stripes, 0, x + 2 * stripes, H - vh), fill=top2)
    else:
        for y in range(H - vh):
            k = y / (H - vh); d.line((0, y, W, y), fill=tuple(int(a + (b - a) * k) for a, b in zip(top, top2)))
    d.rectangle((0, H - vh, W, H), fill=val)
    sc = tuple(int(c * .45) for c in val)
    d.text((W / 2, H - vh / 2), text, font=font(*big), fill=fg, anchor='mm', stroke_width=stroke, stroke_fill=sc)
    for xx in (W * .16, W * .84):
        d.text((xx, H - vh / 2), side, font=font(*small), fill=fg, anchor='mm', stroke_width=max(0, stroke - 2), stroke_fill=sc)
    im.save(os.path.join(OUT, name + '.png'))
tent('sf03_tent', 5.0, 1.65, (214, 76, 120), (176, 52, 92), (160, 40, 80), (250, 240, 244), '魚 辰', '鮮魚')
tent('sf05_tent', 5.8, 1.65, (150, 30, 30), (120, 22, 22), (120, 22, 22), (250, 236, 210), '喫茶 ひより', 'COFFEE')
tent('sf08_tent', 6.0, 1.65, (232, 232, 222), (40, 120, 70), (34, 100, 58), (250, 250, 240), '八 百 政', '青果', stripes=220)
# vertical lightbox for the cafe
im = Image.new('RGB', (600, 2000), (246, 236, 210)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, 600, 360), fill=(120, 24, 24)); ctext(d, (300, 180), '喫茶', font(MIN, 200), (250, 240, 220))
vtext(d, 300, 430, 'ひより', font(YUJI, 380), (40, 30, 24), step=420)
im.save(os.path.join(OUT, 'sf05_box.png'))
# red paper lantern wrap (u around, v up)
im = Image.new('RGB', (1024, 512), (196, 36, 26)); d = ImageDraw.Draw(im)
for y in range(0, 512, 34): d.line((0, y, 1024, y), fill=(160, 26, 18), width=3)
for cx in (256, 768): vtext(d, cx, 40, 'やきとり', font(YUJI, 100), (24, 16, 12), step=108)
im.save(os.path.join(OUT, 'sf07_lantern.png'))
im = Image.new('RGB', (1500, 800), (150, 28, 24)); m = Image.new('L', (1500, 800), 0); d = ImageDraw.Draw(m)
ctext(d, (750, 380), 'と り 源', font(YUJI, 300), 255); m = m.filter(ImageFilter.GaussianBlur(2))
im.paste(Image.new('RGB', (1500, 800), (240, 232, 214)), (0, 0), m); im.save(os.path.join(OUT, 'sf07_noren.png'))
# notices for the closed shop
im = Image.new('RGB', (700, 1000), (246, 244, 236)); d = ImageDraw.Draw(im)
ctext(d, (350, 230), '貸店舗', font(GOTH, 170), (180, 30, 26)); ctext(d, (350, 520), '1F 約18㎡', font(GOTH, 80), (30, 30, 30))
ctext(d, (350, 700), '問合せ 三径不動産', font(GOTH, 56), (30, 30, 30)); ctext(d, (350, 820), '0000-1192', font(GOTH, 70), (30, 30, 30))
im.save(os.path.join(OUT, 'sf06_notice.png'))
im = Image.new('RGB', (600, 420), (250, 248, 232)); d = ImageDraw.Draw(im)
ctext(d, (300, 140), '本日休業', font(YUJI, 120), (30, 30, 30)); ctext(d, (300, 300), '店主', font(YUJI, 70), (30, 30, 30))
im.save(os.path.join(OUT, 'sf06_closed.png'))
# laundry prints
for i, (bg, st) in enumerate((((236, 236, 228), (90, 120, 170)), ((214, 84, 70), (240, 220, 200)), ((70, 110, 160), (236, 236, 228)), ((240, 214, 120), (200, 120, 60)))):
    im = Image.new('RGB', (512, 512), bg); d = ImageDraw.Draw(im)
    for y in range(0, 512, 64): d.rectangle((0, y, 512, y + 18), fill=st)
    im.save(os.path.join(OUT, 'cloth_%d.png' % i))
# cafe menu board
im = Image.new('RGB', (600, 900), (30, 36, 32)); d = ImageDraw.Draw(im)
ctext(d, (300, 110), 'MENU', font(GOTH, 100), (236, 230, 210))
for k, t in enumerate(('ブレンド 450', '珈琲ゼリー 500', 'ナポリタン 800', 'ホットケーキ 650')): ctext(d, (300, 270 + k * 140), t, font(KAI, 62), (236, 230, 210))
im.save(os.path.join(OUT, 'sf05_menu.png'))
# barrier stripes
im = Image.new('RGB', (1024, 256), (240, 240, 236)); d = ImageDraw.Draw(im)
for x in range(-256, 1024, 128): d.polygon([(x, 256), (x + 64, 256), (x + 320, 0), (x + 256, 0)], fill=(210, 40, 30))
im.save(os.path.join(OUT, 'barrier.png'))
print('decals2 ok')
