# make_decals.py - printed graphics for props. All names and marks are invented; fonts are SIL OFL.
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = r'D:\Cijian\assets\decals'
F = r'D:\Cijian\assets\fonts'
os.makedirs(OUT, exist_ok=True)
random.seed(7)
def font(n, s):
    return ImageFont.truetype(os.path.join(F, n + '.ttf'), s)
MIN, YUJI, DOT, GOTH, KAI, REG = 'ShipporiMincho-ExtraBold', 'YujiSyuku-Regular', 'DotGothic16-Regular', 'ZenKakuGothicNew-Bold', 'KaiseiOpti-Bold', 'ReggaeOne-Regular'

def ctext(d, xy, s, f, fill):
    d.text(xy, s, font=f, fill=fill, anchor='mm')

def vtext(d, x, y0, s, f, fill, step=None):
    step = step or int(f.size * 1.08)
    for i, c in enumerate(s):
        d.text((x, y0 + i * step), c, font=f, fill=fill, anchor='ma')

# ---- drink wraps (1024x512, wrap around a can/bottle label)
DRINKS = [
 ('山霧', '緑茶', (30, 92, 56), (232, 236, 214), (168, 190, 120)),
 ('夕凪', '珈琲 微糖', (58, 34, 24), (226, 196, 150), (170, 90, 40)),
 ('澄空', 'サイダー', (20, 92, 170), (240, 246, 250), (120, 196, 232)),
 ('麦の香', '麦茶', (150, 96, 36), (248, 234, 200), (204, 150, 70)),
 ('柑', 'みかん', (226, 112, 18), (255, 244, 214), (250, 176, 40)),
 ('朝霞', 'ミルク紅茶', (196, 160, 118), (120, 40, 44), (244, 232, 214)),
 ('黒潮', 'ブラック', (18, 18, 22), (214, 184, 110), (70, 70, 78)),
 ('白湯', '水', (226, 238, 244), (34, 90, 150), (150, 200, 226)),
]
for i, (nm, kind, bg, fg, ac) in enumerate(DRINKS):
    im = Image.new('RGB', (1024, 512), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 400, 1024, 512), fill=ac)
    for cx in (256, 768):
        d.ellipse((cx - 170, 30, cx + 170, 370), outline=ac, width=6)
        n = len(nm)
        s = 150 if n == 1 else 118 if n == 2 else 86
        f = font(MIN, s)
        vtext(d, cx, 200 - n * s * 1.08 / 2, nm, f, fg)
        ctext(d, (cx, 455), kind, font(GOTH, 46), bg)
    im.save(os.path.join(OUT, 'drink_%02d.png' % i))

# ---- price strip for a row of 10 (2048x128)
def prices(idx, vals):
    im = Image.new('RGB', (2048, 128), (240, 240, 236))
    d = ImageDraw.Draw(im)
    w = 2048 / 10
    for k, v in enumerate(vals):
        ctext(d, ((k + .5) * w, 58), '%d' % v, font(GOTH, 62), (20, 20, 24))
        d.text(((k + .5) * w + 58, 62), '円', font=font(GOTH, 28), fill=(20, 20, 24), anchor='lm')
        d.line(((k + 1) * w, 8, (k + 1) * w, 120), fill=(200, 200, 196), width=2)
    im.save(os.path.join(OUT, 'price_%d.png' % idx))
prices(0, [160, 160, 180, 160, 130, 160, 160, 180, 130, 110])
prices(1, [130, 130, 130, 120, 130, 140, 130, 130, 120, 110])
prices(2, [120, 120, 130, 130, 110, 130, 120, 120, 130, 110])

# ---- vending lower panel 2000x1100 : invented brand on a sky gradient
W, H = 2000, 1100
im = Image.new('RGB', (W, H))
for y in range(H):
    t = y / H
    c = (int(18 + 40 * t), int(92 + 90 * t), int(150 + 70 * t))
    ImageDraw.Draw(im).line((0, y, W, y), fill=c)
d = ImageDraw.Draw(im)
for k in range(5):
    d.ellipse((-200 + k * 460, 640 - k % 2 * 60, 420 + k * 460, 1300), fill=(238, 244, 240))
ctext(d, (760, 260), 'そよかぜ', font(REG, 250), (255, 255, 255))
ctext(d, (760, 450), 'SOYOKAZE DRINK WORKS', font(GOTH, 72), (230, 240, 244))
ctext(d, (760, 560), 'つめたい・あたたかい いつでも一本', font(GOTH, 58), (250, 250, 240))
im.save(os.path.join(OUT, 'vm_panel.png'))

# ---- vending header
im = Image.new('RGB', (2000, 300), (20, 96, 156))
d = ImageDraw.Draw(im)
d.rectangle((0, 0, 2000, 16), fill=(240, 240, 236))
d.rectangle((0, 284, 2000, 300), fill=(240, 240, 236))
ctext(d, (560, 150), 'そよかぜ', font(REG, 170), (255, 255, 255))
ctext(d, (1420, 150), '冷たいお茶あります', font(GOTH, 96), (255, 244, 180))
im.save(os.path.join(OUT, 'vm_header.png'))

# ---- small printed labels atlas pieces
def label(name, size, bg, lines):
    im = Image.new('RGB', size, bg)
    d = ImageDraw.Draw(im)
    for (x, y, s, fn, sz, col) in lines:
        ctext(d, (x, y), s, font(fn, sz), col)
    im.save(os.path.join(OUT, name + '.png'))
label('vm_takeout', (1200, 240), (26, 26, 28), [(600, 120, '取 出 口', GOTH, 120, (235, 235, 230))])
label('vm_coin', (600, 300), (34, 36, 40), [(300, 70, '硬貨投入口', GOTH, 62, (235, 235, 230)), (300, 170, '10・50・100・500円', GOTH, 44, (200, 200, 196)), (300, 245, '千円札', GOTH, 44, (200, 200, 196))])
label('vm_notice', (900, 600), (244, 238, 214), [(450, 90, 'お願い', GOTH, 96, (170, 30, 26)), (450, 220, '空き缶は回収箱へ', GOTH, 72, (30, 30, 30)), (450, 330, 'ゆらさないでください', GOTH, 64, (30, 30, 30)), (450, 450, '故障の連絡先', GOTH, 52, (30, 30, 30)), (450, 530, '0120-000-000', GOTH, 66, (30, 30, 30))])
label('bike_reg', (600, 240), (250, 214, 60), [(300, 70, '自転車登録', GOTH, 70, (20, 20, 20)), (300, 170, '台東-0482', GOTH, 90, (180, 20, 20))])
label('bike_head', (400, 400), (196, 180, 130), [(200, 200, '風', MIN, 280, (70, 40, 20))])

# ---- awning 3600x1350 px = 3.6 x 1.35 m. top of the image = wall end, bottom = valance
W, H = 3600, 1390
BASE = (46, 82, 64)
im = Image.new('RGB', (W, H), BASE)
d = ImageDraw.Draw(im)
for x in range(0, W, 300):
    d.rectangle((x + 150, 0, x + 300, H - 240), fill=(214, 206, 180))
d.rectangle((0, H - 240, W, H), fill=(36, 66, 54))
d.rectangle((0, H - 244, W, H - 232), fill=(214, 206, 180))
ctext(d, (W / 2, H - 120), '三 径 茶 舗', font(MIN, 130), (232, 226, 200))
ctext(d, (560, H - 120), '煎茶・焙じ茶', font(GOTH, 70), (222, 216, 192))
ctext(d, (W - 560, H - 120), 'TEL 03-0000-3412', font(GOTH, 62), (222, 216, 192))
im.save(os.path.join(OUT, 'sf01_awning.png'))

# ---- noren 1800x900: 3 panels of indigo cloth, white dyed character with soft resist edge
W, H = 1800, 900
im = Image.new('RGB', (W, H), (24, 40, 74))
mask = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(mask)
ctext(d, (900, 420), '茶', font(YUJI, 560), 255)
ctext(d, (300, 460), '三', font(YUJI, 300), 255)
ctext(d, (1500, 460), '径', font(YUJI, 300), 255)
mask = mask.filter(ImageFilter.GaussianBlur(2.2))
im.paste(Image.new('RGB', (W, H), (226, 222, 206)), (0, 0), mask)
im.save(os.path.join(OUT, 'sf01_noren.png'))

# ---- side lightbox 700x2000 double sided
W, H = 700, 2000
im = Image.new('RGB', (W, H), (244, 238, 222))
d = ImageDraw.Draw(im)
d.rectangle((0, 0, W, 300), fill=(150, 34, 28))
ctext(d, (W / 2, 150), 'お茶', font(MIN, 190), (250, 244, 228))
vtext(d, W / 2, 380, '三径茶舗', font(YUJI, 340), (28, 28, 30), step=380)
im.save(os.path.join(OUT, 'sf01_side.png'))

# ---- window papers
im = Image.new('RGB', (600, 900), (240, 232, 206))
d = ImageDraw.Draw(im)
vtext(d, 400, 70, '新茶入荷', font(YUJI, 170), (160, 30, 24), step=190)
vtext(d, 170, 120, '量り売り', font(YUJI, 110), (30, 30, 30), step=125)
im.save(os.path.join(OUT, 'sf01_paper1.png'))
im = Image.new('RGB', (500, 700), (230, 216, 170))
d = ImageDraw.Draw(im)
ctext(d, (250, 140), '本日', font(YUJI, 120), (30, 30, 30))
ctext(d, (250, 300), '焙じたて', font(YUJI, 96), (150, 34, 28))
ctext(d, (250, 470), '百g', font(YUJI, 90), (30, 30, 30))
ctext(d, (250, 590), '六百円', font(YUJI, 90), (30, 30, 30))
im.save(os.path.join(OUT, 'sf01_paper2.png'))

# ---- tea tin wraps
for i, (c, s) in enumerate(((150, '煎茶'), (60, '玉露'), (110, '番茶'))):
    bg = [(150, 40, 34), (30, 60, 50), (190, 150, 70)][i]
    im = Image.new('RGB', (1024, 512), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 60, 1024, 76), fill=(220, 190, 110))
    d.rectangle((0, 436, 1024, 452), fill=(220, 190, 110))
    for cx in (256, 768):
        vtext(d, cx, 110, s, font(YUJI, 150), (240, 232, 210), step=155)
    im.save(os.path.join(OUT, 'tin_%d.png' % i))
# ---- vending LED: amber dot digits on near black
im = Image.new('RGB', (600, 160), (10, 6, 4))
d = ImageDraw.Draw(im)
ctext(d, (300, 80), '投入金額  0', font(DOT, 84), (255, 120, 30))
im.save(os.path.join(OUT, 'vm_led.png'))
# ---- shop back wall glow: warm pools under two pendants, falling off into the corners
import math as _m
W, H = 1860, 2100
px = Image.new('RGB', (W // 6, H // 6))
L = px.load()
for y in range(H // 6):
    for x in range(W // 6):
        X, Y = x * 6, y * 6
        v = .10
        for cx in (W * .23, W * .70):
            r = _m.hypot((X - cx) / 620, (Y - 330) / 900)
            v += .62 * _m.exp(-r * r * 1.6)
        L[x, y] = (min(255, int(235 * v)), min(255, int(168 * v)), min(255, int(92 * v)))
px.resize((W // 2, H // 2), Image.BICUBIC).save(os.path.join(OUT, 'sf01_glow.png'))
# ---- vending machine, proportions from photos: green body panel with sticker ghosts, wide takeout label
W, H = 1600, 1000
im = Image.new('RGB', (W, H), (24, 118, 62))
d = ImageDraw.Draw(im)
for k in range(0, 40):
    d.line((0, 330 + k * 3, W, 300 + k * 3), fill=(24 + k, 126 + k // 2, 66), width=3)
d.rectangle((70, 80, 700, 300), fill=(250, 250, 244))
ctext(d, (385, 150), 'そよかぜ', font(REG, 124), (20, 108, 60))
ctext(d, (385, 250), 'SOYOKAZE DRINK WORKS', font(GOTH, 40), (40, 40, 40))
d.rectangle((760, 90, 980, 290), fill=(242, 214, 60))
ctext(d, (870, 150), '100', font(REG, 92), (190, 30, 24))
ctext(d, (870, 240), '円均一', font(GOTH, 46), (30, 30, 30))
im.save(os.path.join(OUT, 'vm2_panel.png'))
im = Image.new('RGB', (1000, 2200), (22, 112, 58))
d = ImageDraw.Draw(im)
d.ellipse((-260, 900, 1260, 2420), fill=(30, 132, 72))
vtext(d, 500, 300, 'そよかぜ', font(REG, 330), (248, 248, 240), step=360)
im.save(os.path.join(OUT, 'vm2_side.png'))
# ---- sf02: glossy PVC tent, faded unevenly. top of image = wall end. 5400 x 1650 px = 5.4 x 1.65 m
W, H = 5400, 1650
im = Image.new('RGB', (W, H), (28, 96, 176))
d = ImageDraw.Draw(im)
for y in range(H - 280):
    k = y / (H - 280)
    d.line((0, y, W, y), fill=(int(70 - 42 * k), int(140 - 44 * k), int(214 - 38 * k)))
d.rectangle((0, H - 280, W, H), fill=(20, 84, 160))
ctext(d, (W / 2, H - 140), '三 径 茶 舗', font(MIN, 150), (246, 246, 240))
ctext(d, (900, H - 140), '煎茶・焙じ茶・海苔', font(GOTH, 74), (240, 240, 234))
ctext(d, (W - 900, H - 140), 'TEL 03-0000-3412', font(GOTH, 74), (240, 240, 234))
im.save(os.path.join(OUT, 'sf02_tent.png'))
# ---- shop interior wall: white paint lit by ceiling tubes
W, H = 800, 700
px = Image.new('RGB', (W, H))
L = px.load()
import math as _m2
for y in range(H):
    for x in range(W):
        v = .16 + .30 * _m2.exp(-((y) / 300) ** 2) * (.72 + .28 * _m2.sin(x / 90))
        L[x, y] = (min(255, int(250 * v)), min(255, int(236 * v)), min(255, int(206 * v)))
px.save(os.path.join(OUT, 'sf02_inwall.png'))
# ---- paper tea packs for the street table
for i, (bg, fg, t) in enumerate((((236, 228, 206), (150, 34, 28), '煎茶'), ((206, 226, 196), (24, 76, 44), '新茶'), ((240, 214, 120), (70, 44, 20), '番茶'), ((226, 90, 66), (250, 244, 224), '玉露'))):
    im = Image.new('RGB', (400, 560), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((30, 30, 370, 530), outline=fg, width=8)
    vtext(d, 200, 90, t, font(YUJI, 170), fg, step=190)
    ctext(d, (200, 490), '百g 六百円', font(GOTH, 40), fg)
    im.save(os.path.join(OUT, 'pack_%d.png' % i))
# ---- A-board and notices
im = Image.new('RGB', (600, 900), (252, 250, 240))
d = ImageDraw.Draw(im)
d.rectangle((20, 20, 580, 150), fill=(170, 34, 28))
ctext(d, (300, 85), '本日のお茶', font(GOTH, 88), (255, 255, 250))
vtext(d, 420, 190, '新茶', font(YUJI, 210), (28, 28, 30), step=235)
vtext(d, 170, 220, '量り売り', font(YUJI, 120), (160, 34, 28), step=135)
im.save(os.path.join(OUT, 'sf02_board.png'))
print('decals ok')
