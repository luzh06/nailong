"""生成 asset-register.csv 和 japanese-text-list.csv。Excel 可直接打开 (UTF-8 BOM)。"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_atlas as K
import kit_props
import kit_shops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sources = json.load(open(os.path.join(ROOT, "textures", "sources.json"), encoding="utf-8"))
TOOL = "Claude 编写的 Blender Python 程序化建模"
TOOL_TEX = "Claude 编写的 Pillow 脚本, 字体 Zen Antique"
OWN = "项目自有"

ROLE_NOTE = {
    "roof": "yn_mat_roof, 已压暗调色",
    "paint_wood": "yn_mat_vermilion_a/b/c, 已染朱红",
    "cedar": "yn_mat_cedar, 已压暗调色",
    "shutter": "yn_mat_shutter, 已调色并降到 1K",
    "plaster": "yn_mat_plaster, 降到 1K",
    "corrugated": "yn_mat_corrugated, 降到 1K",
    "paving": "yn_mat_paving, 已调色",
}

rows = [["资产名", "作者或工具", "来源网址", "许可证", "是否AI生成", "备注"]]
for key, w, front, upper, _ in kit_shops.BODIES:
    rows.append([f"YN_shop_{key}_01", TOOL, "scripts/kit_shops.py", OWN, "是", f"宽 {w} 米, {front}/{upper}; 门脸结构没有平视例图, 属推断"])
rows.append(["YN_sign_NN_wNN (16 家招牌)", TOOL, "scripts/kit_shops.py", OWN, "是", "虚构店名, 文字待人工核实"])
rows.append(["YN_awning_corrugated/cloth/tile", TOOL, "scripts/kit_shops.py", OWN, "是", "每种 3.6 和 5.4 两个宽度"])
rows.append(["YN_shop_end_01/02", TOOL, "scripts/kit_shops.py", OWN, "是", "段尾山墙, 形状按 191 目测"])
rows.append(["YN_shop_lod_NN", TOOL, "scripts/kit_shops.py", OWN, "是", "只用于主机位远景"])
for name in kit_props.PROPS:
    rows.append([name, TOOL, "scripts/kit_props.py", OWN, "是", "无品牌"])
rows.append(["YN_prop_wires_01", TOOL, "scripts/kit_props.py", OWN, "是", "按电杆位置生成"])
rows.append(["YN_ground_street_01, YN_ground_base_01", TOOL, "scripts/build_scene.py", OWN, "是", ""])
rows.append(["YN_bg_hozomon_standin", TOOL, "scripts/build_scene.py", OWN, "是", "宝藏门替身, 只为构图, 不是复原; 能否呈现待人工确认"])
rows.append(["YN_bg_pagoda_standin", TOOL, "scripts/build_scene.py", OWN, "是", "五重塔替身, 只为构图, 位置不是测绘; 能否呈现待人工确认"])
rows.append(["YN_bg_city_NN", TOOL, "scripts/kit_city.py", OWN, "是", "背景杂居楼, 按材质合并; 位置按 191 的感觉排, 不是测绘; 只有部分有 UV1"])
rows.append(["YN_person_NN (12 种)", TOOL, "scripts/kit_city.py", OWN, "是", "低模行人, 只适合远看; 单独导出, 无 UV1"])
for tex, note in (("yn_signs_basecolor_2k", "招牌和货品图集"), ("yn_noren_basecolor_2k", "暖帘图集"),
                  ("yn_props_basecolor_1k", "贩卖机, 看板, 条纹, 旗幡"), ("yn_lantern_basecolor_512", "灯笼")):
    rows.append([tex, TOOL_TEX, "scripts/02b_prepare_kit_textures.py", OWN + ", 字体见下", "是", note + ", 文字待人工核实"])
rows.append(["yn_citysigns_1k", TOOL_TEX, "scripts/02c_prepare_city_textures.py", OWN + ", 字体见下", "是", "背景楼招牌和远景店面, 文字待人工核实"])
rows.append(["yn_roof_red_basecolor_2k", "Claude 编写的 NumPy 脚本, 由 grey_roof_tiles_02 染色", "scripts/02c_prepare_city_textures.py", "CC0 衍生", "是", "红瓦"])
for tex, note in (("yn_facade_plaster/tile/concrete/brick, basecolor + emissive", "背景楼立面"), ("yn_people_palette", "行人调色板"),
                  ("yn_grime_1k, yn_ground_stain_1k", "污渍")):
    rows.append([tex, "Claude 编写的 Pillow/NumPy 脚本", "scripts/02b_prepare_kit_textures.py, 02c_prepare_city_textures.py", OWN, "是", note])
for role, s in sources.items():
    rows.append([s["asset"], "、".join(s["authors"]), s["url"], "CC0", "否", ROLE_NOTE[role]])
for tex, note in (("yn_kawara_basecolor/normal/orm_2k", "本瓦屋面, 由高度场计算"), ("yn_roof_red_basecolor_2k", "本瓦染红"),
                  ("yn_trim_basecolor/normal/orm_2k, emissive_1k", "屋檐 Trim Sheet, 结构对照 201 和 188"),
                  ("yn_shutter_art_2k", "卷帘画, 自己构图, 不是真实的浅草绘巻"), ("yn_plaque_1k", "吊牌, 写的是街名")):
    rows.append([tex, "Claude 编写的 NumPy/Pillow 脚本", "scripts/02d_prepare_reference_textures.py", OWN, "是", note])
rows.append(["YN_noren_NN, YN_shutter_*, YN_prop_plum_branch_*", TOOL, "scripts/kit_shops.py", OWN, "是", "暖帘, 关店卷帘, 季节花枝"])
rows.append(["YN_awning_nakamise_w36/w54", TOOL, "scripts/kit_shops.py", OWN, "是", "统一的仲见世店头, 对照平视照片"])
for name, url in (("参考: 早晨的仲见世 (只看不下载)", "https://www.pakutaso.com/20210109015post-32890.html"),
                  ("参考: 雨夜的仲见世 (只看不下载)", "https://www.pakutaso.com/en/20200730195post-27999.html")):
    rows.append([name, "PAKUTASO 摄影师", url, "站点免费素材条款, 未下载使用", "否", "只用来看结构, 没有任何像素进贴图"])
for name, asset in (("hdri/morning.hdr", "kloppenheim_06_puresky"), ("hdri/sunset.hdr", "belfast_sunset_puresky"), ("hdri/dusk.hdr", "qwantani_dusk_2_puresky"),
                    ("wall_plaster", "white_plaster_rough_01"), ("wall_concrete", "concrete_wall_006"), ("wall_tile", "rectangular_facade_tiles"),
                    ("wall_brick", "red_brick_03"), ("wall_paint (已下载, 未使用)", "painted_concrete")):
    rows.append([name, "Poly Haven", f"https://polyhaven.com/a/{asset}", "CC0", "否", "离线渲染的天空或墙面"])
rows.append(["yn_skyline_morning/sunset/dusk_2k, YN_bg_skyline_far/near", "reference/web/web_01.jpg 抠图调色 (Marco Almbauer)", "https://commons.wikimedia.org/wiki/File:Sens%C5%8D-ji_Tempel_mit_Nakamise-dor.jpg", "CC0", "否", "远景背景; 照片里可能有真实招牌文字"])
rows.append(["yn_goods_photo_2k", "reference/shops 的货架实拍", "见 reference/shops/sources.json", "CC BY-SA 4.0 等", "否", "店内货品贴图, 自用; 公开发布前要处理授权"])
rows.append(["yn_shutter_art_2k", "reference/web 的 web_06, web_07, web_12 照片校正而成", "见 reference/web/sources.json", "CC BY 2.0 / CC BY-SA 4.0", "否",
             "自用可以; 公开发布前要署名, 且 CC BY-SA 有相同方式共享要求; 照片上可能有真实商号"])
web_sources = os.path.join(ROOT, "reference", "web", "sources.json")
if os.path.exists(web_sources):
    for s in json.load(open(web_sources, encoding="utf-8")):
        rows.append([f"reference/web/{s['local']}", s["author"], s["page"], s["license"], "否",
                     f"只作建模参考, 不进 GLB; 原名 {s['title']}; 本地 {s['saved_size']}, 原图 {s['original_size']}"])
rows.append(["Zen Antique 字体", "The Zen Antique Project Authors", "https://github.com/googlefonts/zen-antique",
             "SIL OFL 1.1", "否", "只用于生成招牌贴图"])
rows.append(["reference/ref_191_dusk.jpg, ref_189_day.jpg", "原作者未知 (F:\\东京 的手机截图)", "未知", "未知, 只作参考", "未知",
             "只用来核对构图, 不进任何 GLB, 不要外传"])
with open(os.path.join(ROOT, "asset-register.csv"), "w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(rows)

texts = [["日文", "类别", "用在哪里", "是否虚构", "人工核实"]]
seen = set()


def add(text, kind, where, fictional):
    if (text, kind) not in seen:
        seen.add((text, kind))
        texts.append([text, kind, where, fictional, "待核实"])


for name, mark, board, noren, _ in K.SHOPS:
    add(name, "店名", "吊牌", "是, 未查重名")
    add(mark, "店徽字", "吊牌、暖帘", "是")
    add(board, "商品词", "店头横板", "通用词, 待确认用法")
    add(noren, "商品词", "暖帘, 从右往左读", "通用词, 待确认用法")
add("朝凪", "灯笼字", "所有灯笼", "是")
add("あられ", "商品词", "第 3 步旧贴图, 现已不用", "通用词")
for text, meaning, where in K.PROP_TEXTS:
    add(text, f"道具 ({meaning})", where, "通用词")
with open(os.path.join(ROOT, "japanese-text-list.csv"), "w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(texts)
print("assets", len(rows) - 1, "texts", len(texts) - 1)
