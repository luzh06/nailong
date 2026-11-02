"""白模: 真实比例的仲见世前段 60 米和构图所需的远景体量。

坐标: 街道中线是 X=0, 朝北 (朝宝藏门) 是 +Y。Y=0..60 是可步行的 60 米。
已核实: 全长约 250 米, 宝藏门 22.7x21x8 米, 五重塔约 53 米。
推算 (例图目测, 未核实): 街宽 6 米, 店铺剖面高度, 屋顶分段长度。
远景的宝藏门和五重塔位置按 191 的构图摆放, 不是测绘。
"""
import bpy

from cijian_common import clay, collection, mesh_object, wb_box, wb_gable

STREET_HALF = 2.6        # 推算: 由 191 量得步行面约 5.2 米
SEG_LEN = 29.4           # 推算: 由 191 山墙间距反推
SEG_GAP = 1.6            # 推算: 段与段之间的小巷
TERRACE_Y = 2.0          # 推算: 前部低屋面进深
MAIN_DEPTH = 5.0         # 推算: 主屋进深
Z_TERRACE = 3.2
Z_EAVE = 4.6
Z_RIDGE = 7.3
LANE_W = 2.4             # 推算: 屋后背巷宽度
GATE_Y = 244.0
PLAY_LEN = 60.0
SHOP_A_Y = 14.0          # YN_shop_A_01 在西侧的中心位置
STREET_END_Y = GATE_Y - 12.0


def shop_block(side, y0, y1, mats, col, tag, over0=0.5, over1=0.5):
    """side=-1 西侧, +1 东侧。前部低屋面 + 主屋两坡顶。over0/over1 是两端山墙出挑。"""
    x_front = side * STREET_HALF
    x_mid = side * (STREET_HALF + TERRACE_Y)
    x_back = side * (STREET_HALF + TERRACE_Y + MAIN_DEPTH)
    a, b = sorted((x_front, x_mid))
    wb_box(f"wb_terrace_{tag}", (a, y0, 0), (b, y1, Z_TERRACE), mats["block"], col)
    a, b = sorted((x_mid, x_back))
    # 两侧山墙略出挑, 贴近例图的端部轮廓
    wb_gable(f"wb_main_{tag}", a - 0.35, b + 0.35, y0 - over0, y1 + over1, 0, Z_EAVE, Z_RIDGE, mats["roof"], col)


def build(context_col_name="wb_whitebox"):
    col = collection(context_col_name)
    play = collection("wb_play_60m", col)
    far = collection("wb_context", col)
    mats = {
        "ground": clay("wb_mat_ground", (0.42, 0.42, 0.42)),
        "street": clay("wb_mat_street", (0.60, 0.60, 0.58)),
        "block": clay("wb_mat_block", (0.62, 0.62, 0.60)),
        "roof": clay("wb_mat_roof", (0.26, 0.26, 0.27)),
        "city": clay("wb_mat_city", (0.50, 0.50, 0.50)),
        "gate": clay("wb_mat_gate", (0.45, 0.25, 0.20)),
    }

    mesh_object("wb_ground", [(-500, -160, -0.02), (500, -160, -0.02), (500, 1300, -0.02), (-500, 1300, -0.02)],
                [(0, 1, 2, 3)], mats["ground"], col)
    mesh_object("wb_street", [(-STREET_HALF, -30, 0), (STREET_HALF, -30, 0),
                              (STREET_HALF, STREET_END_Y, 0), (-STREET_HALF, STREET_END_Y, 0)],
                [(0, 1, 2, 3)], mats["street"], play)

    # 店铺块: 从 Y=-30 排到宝藏门前。Y 在 0..60 内的归入可步行集合
    n = 0
    y = -31.0
    while y < STREET_END_Y - 10:
        y1 = min(y + SEG_LEN, STREET_END_Y)
        target = play if y < PLAY_LEN else far
        if y <= SHOP_A_Y - 1.8 and SHOP_A_Y + 1.8 <= y1:
            # 给精做店面留出空位, 只出一个, 不量产
            shop_block(-1, y, SHOP_A_Y - 1.8, mats, target, f"w{n:02d}a", over1=0.0)
            shop_block(-1, SHOP_A_Y + 1.8, y1, mats, target, f"w{n:02d}b", over0=0.0)
        else:
            shop_block(-1, y, y1, mats, target, f"w{n:02d}")
        shop_block(1, y, y1, mats, target, f"e{n:02d}")
        y = y1 + SEG_GAP
        n += 1

    # 背巷外侧的建筑 (x0, x1, y0, y1, 高), 位置和高度按 191 反投影目测
    west = [(-12, -21, -31, -6, 11), (-12, -20, -6, 14, 12), (-12, -19, 14, 32, 7), (-12, -21, 32, 50, 11),
            (-12, -21, 50, 78, 14), (-21, -36, 40, 92, 13), (-12, -22, 78, 104, 8), (-12, -22, 104, 136, 12),
            (-12, -24, 136, 168, 9), (-12, -24, 168, 200, 11), (-12, -24, 200, 232, 8)]
    east = [(12, 21, -31, 6, 9), (12, 20, 6, 28, 12), (12, 21, 28, 50, 8), (12, 22, 50, 74, 13),
            (12, 22, 74, 100, 10), (12, 22, 100, 130, 13), (13, 23, 130, 165, 11),
            (13, 25, 165, 200, 14), (13, 25, 200, 232, 12)]
    for i, (x0, x1, y0, y1, h) in enumerate(west + east):
        a, b = sorted((x0, x1))
        wb_box(f"wb_city_{i:02d}", (a, y0, 0), (b, y1, h), mats["city"], far)

    # 远处高楼, 只为天际线 (cx, cy, 半宽, 高), 由 191 的像素位置反算
    far_blocks = [(-138, 1033, 8, 74), (0, 1033, 8, 71), (-18, 453, 10, 39), (22, 453, 13, 34),
                  (-106, 453, 8, 39), (-66, 453, 6, 33), (-34, 340, 22, 25), (46, 340, 16, 26),
                  (-98, 330, 20, 21), (-30, 290, 14, 19), (60, 280, 20, 22), (-120, 270, 30, 17)]
    for i, (cx, cy, hw, h) in enumerate(far_blocks):
        wb_box(f"wb_far_{i:02d}", (cx - hw, cy - hw, 0), (cx + hw, cy + hw, h), mats["city"], far)

    # 宝藏门: 22.7 x 21 x 8 米, 两重檐简化体量
    def gate():
        hw, hd = 10.5, 4.0
        wb_box("wb_gate_body", (-hw, GATE_Y - hd, 0), (hw, GATE_Y + hd, 7.0), mats["gate"], far)
        wb_gable("wb_gate_roof_low", -hw - 3.2, hw + 3.2, GATE_Y - hd - 2.6, GATE_Y + hd + 2.6, 6.4, 6.4, 9.2,
                 mats["roof"], far)
        wb_box("wb_gate_upper", (-hw + 1.5, GATE_Y - hd + 1, 9), (hw - 1.5, GATE_Y + hd - 1, 15), mats["gate"], far)
        # 屋脊沿门宽方向
        v = [(-hw - 2.8, GATE_Y - hd - 2.2, 14.6), (hw + 2.8, GATE_Y - hd - 2.2, 14.6),
             (hw + 2.8, GATE_Y + hd + 2.2, 14.6), (-hw - 2.8, GATE_Y + hd + 2.2, 14.6),
             (-hw + 1, GATE_Y, 22.7), (hw - 1, GATE_Y, 22.7)]
        f = [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4), (3, 2, 1, 0)]
        mesh_object("wb_gate_roof_up", v, f, mats["roof"], far)
    gate()

    # 五重塔: 约 53 米, 位置按构图摆放
    px, py = -62.0, 344.0
    tier_z = [9.0, 15.2, 21.0, 26.4, 31.4]
    widths = [10.9, 10.0, 9.2, 8.4, 7.6]
    wb_box("wb_pagoda_core", (px - 3.5, py - 3.5, 0), (px + 3.5, py + 3.5, 34.0), mats["gate"], far)
    for i, (z, w) in enumerate(zip(tier_z, widths)):
        v = [(px - w, py - w, z), (px + w, py - w, z), (px + w, py + w, z), (px - w, py + w, z),
             (px - w * 0.35, py - w * 0.35, z + 2.6), (px + w * 0.35, py - w * 0.35, z + 2.6),
             (px + w * 0.35, py + w * 0.35, z + 2.6), (px - w * 0.35, py + w * 0.35, z + 2.6)]
        f = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
        mesh_object(f"wb_pagoda_tier_{i}", v, f, mats["roof"], far)
    wb_box("wb_pagoda_spire", (px - 0.5, py - 0.5, 34), (px + 0.5, py + 0.5, 53), mats["gate"], far)
    return col
