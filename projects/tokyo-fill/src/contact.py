# Tile a QA round's renders into one labelled contact sheet. usage: contact.py TAG cam1,cam2,...
import sys
from PIL import Image, ImageDraw
D = r"D:\project\cijian\work\output\assembly"; tag, cams = sys.argv[1], sys.argv[2].split(",")
ims = [(c, Image.open(rf"{D}\after_{tag}_sunset_{c}.jpg")) for c in cams]
w, h = 640, 360; cols = 4; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for k, (c, im) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * h
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y)); d.rectangle([x, y, x + 150, y + 22], fill=(0, 0, 0)); d.text((x + 6, y + 5), c, fill=(255, 255, 255))
sheet.save(rf"{D}\sheet_{tag}.jpg", quality=88); print("SHEET", rf"{D}\sheet_{tag}.jpg")
