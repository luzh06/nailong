"""把渲染图和参考图并排 + 50% 叠加, 用来核对构图。
用法: python compare.py <渲染图> <参考图> <输出图>
"""
import sys

from PIL import Image, ImageDraw


def main(render, ref, out):
    a = Image.open(render).convert("RGB")
    b = Image.open(ref).convert("RGB").resize(a.size, Image.LANCZOS)
    blend = Image.blend(a, b, 0.5)
    w, h = a.size
    sheet = Image.new("RGB", (w * 3 + 40, h + 30), "white")
    for i, (im, label) in enumerate(((b, "reference"), (a, "render"), (blend, "overlay 50%"))):
        sheet.paste(im, (i * (w + 20), 30))
        ImageDraw.Draw(sheet).text((i * (w + 20) + 6, 8), label, fill="black")
    sheet.save(out, quality=90)


if __name__ == "__main__":
    main(*sys.argv[1:4])
