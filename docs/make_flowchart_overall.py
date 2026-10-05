# -*- coding: utf-8 -*-
"""生成 HFSP 总体求解流程图。

内容：输入与建模 → 三阶段混合搜索（小生境 PSO / IG / 档案库引导）
      → 入档判定四步 → 商集 Π/~ 示意 → 输出等优解集与用途。

用法：
    python3 docs/make_flowchart_overall.py docs/总体求解流程图.png

依赖：matplotlib；中文字体使用 macOS 自带的 Hiragino Sans GB。
画布高度按内容自适应（每英寸 10.3 个坐标单位），保证字号与框高匹配。
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
from matplotlib.font_manager import FontProperties

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
fp  = FontProperties(fname=FONT); fpb = FontProperties(fname=FONT, weight="bold")

XMAX, YMAX = 132.0, 300.0   # 实际范围在脚本末尾按内容自适应重设
fig, ax = plt.subplots(figsize=(12.6, 13.0))
ax.set_xlim(0, XMAX); ax.set_ylim(0, YMAX); ax.axis("off"); ax.invert_yaxis()

C = {"proc":("#eef4ff","#3b6fd4"), "heur":("#fff6e8","#dd8a1c"),
     "dec":("#ecfaf3","#2e9e6b"), "term":("#f4efff","#7a5cd6"),
     "diam":("#fff6f6","#c0392b")}
TXT, ARR, LBL = "#152238", "#5b6b80", "#7a8798"
FS = 10.8

def hof(t, kind, extra=0.0):
    if kind == "diam": return 12.0
    return 6.0 + 3.0*(t.count("\n")) + extra

def node(x, y, text, kind="proc", w=50.0, fs=FS, bold=False):
    h = hof(text, kind); fc, ec = C[kind]
    if kind == "diam":
        ax.add_patch(Polygon([[x,y-h/2],[x+w/2,y],[x,y+h/2],[x-w/2,y]], closed=True,
            fc=fc, ec=ec, lw=1.5, zorder=4))
        ax.text(x, y, text, ha="center", va="center", zorder=5, fontproperties=fp,
                fontsize=fs-1.2, color="#7a1c12", linespacing=1.5)
    else:
        ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
            boxstyle="round,pad=0.3,rounding_size=1.4", fc=fc, ec=ec, lw=1.5, zorder=4))
        ax.text(x, y, text, ha="center", va="center", zorder=5,
                fontproperties=(fpb if bold else fp), fontsize=fs, color=TXT, linespacing=1.62)
    return h

def line(pts, head=True):
    for a, b in zip(pts, pts[1:]):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-", lw=1.5, color=ARR, zorder=2))
    if head:
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=14,
            lw=1.5, color=ARR, zorder=2))

def varrow(y1, y2, x, head=True):
    ax.add_patch(FancyArrowPatch((x,y1), (x,y2), arrowstyle=("-|>" if head else "-"),
        mutation_scale=15, lw=1.5, color=ARR, zorder=2, shrinkA=0.5, shrinkB=0.5))

def vlabel(x, y, t):
    ax.text(x, y, t, fontproperties=fp, fontsize=9.6, color=LBL, rotation=90,
            va="center", ha="center")

def panel(x0, y0, x1, y1, title):
    ax.add_patch(FancyBboxPatch((x0, y0), x1-x0, y1-y0,
        boxstyle="round,pad=0.6,rounding_size=2.0", fc="#f8fafd", ec="#9fb3cc",
        lw=1.4, ls=(0,(5,3)), zorder=0))
    ax.text(x0+3.2, y0+4.4, title, fontproperties=fpb, fontsize=11.6,
            color="#2b4a72", zorder=1)

UNITS_PER_INCH = 10.3   # 与原版流程图一致：保证字号与框高匹配
GAP = 2.6

def stack(nodes, cx, w, top):
    ys, hs = [], []
    cur = top
    for t, k in nodes:
        h = hof(t, k)
        yc = cur + h / 2
        node(cx, yc, t, k, w=w)
        ys.append(yc); hs.append(h)
        cur += h + GAP
    return ys, hs, cur - GAP

# ================= ① 顶部：输入与建模 =================
TOP = 9.0
top_boxes = [
    ("输入 HFSP 算例\nn 工件 × s 阶段 × 每阶段机器数", "term", 40.0, 22.0),
    ("解码器 D：排列 π → 调度 S\n逐阶段列表调度 + ECT 机器分配", "dec", 40.0, 66.0),
    ("初始解：NEH / SPT / 随机排列", "heur", 40.0, 110.0),
]
for text, kind, width, cx in top_boxes:
    node(cx, TOP + 4.5, text, kind, w=width, fs=9.6)
for left, right in [(42.0, 46.0), (86.0, 90.0)]:
    ax.add_patch(FancyArrowPatch((left, TOP + 4.5), (right, TOP + 4.5), arrowstyle="-|>",
        mutation_scale=13, lw=1.5, color=ARR, zorder=2))

M0 = TOP + 17.0

# ================= ② 左：主流程 =================
L_nodes = [
    ("阶段一 · 小生境 PSO（广度）\n交换序速度 + 环形邻域 + 小生境分组", "proc"),
    ("停滞时：从档案库排列池注入精英重启", "heur"),
    ("阶段二 · IG 深度强化（深度）\n破坏 d = 0.3n → 贪心最优插入重建 → SA 接受", "heur"),
    ("阶段三 · 档案库引导（核心）\n候选解 → 入档四步（见右栏）", "proc"),
    ("种子选择：探索 = 最孤立 / 强化 = 接近最优", "proc"),
    ("多样化游走：扰动 + IG 重优化\n接受准则同时看 makespan 与结构距离", "proc"),
    ("又新增等优解？", "diam"),
]
lcx, lw_ = 33.0, 52.0
l_ys, l_hs, l_bottom = stack(L_nodes, lcx, lw_, M0 + 11.0)
LPANEL1 = l_bottom + 6.0
panel(2.0, M0, 65.0, LPANEL1, "主流程 · 三阶段混合搜索")
for i in range(len(L_nodes) - 1):
    varrow(l_ys[i] + l_hs[i] / 2, l_ys[i + 1] - l_hs[i + 1] / 2, lcx)
line([(lcx - lw_ / 2, l_ys[6]), (4.4, l_ys[6]), (4.4, l_ys[4]), (lcx - lw_ / 2, l_ys[4])])
ax.text(6.1, (l_ys[6] + l_ys[4]) / 2, "是：继续开采", fontproperties=fp, fontsize=9.0,
        color=LBL, rotation=90, va="center", ha="center")
varrow(l_ys[6] + l_hs[6] / 2, LPANEL1 - 2.0, lcx)
ax.text(lcx + 2.5, l_ys[6] + l_hs[6] / 2 + 3.4, "否：停滞达上限", fontproperties=fp,
        fontsize=9.0, color=LBL, va="center")

# ================= ③ 右：入档四步 =================
rcx, rw = 98.0, 60.0
R_nodes = [
    ("入档① 质量门限：makespan ≤ (1 + ρ) · best", "proc"),
    ("入档② 结构签名去重\n同一个调度只保留一个代表元", "dec"),
    ("入档③ 析取式新颖性判定\n与某已存解在「质量 + 机器分配 + 加工顺序」\n三个维度同时接近时才判为重复", "proc"),
    ("入档④ 容量裁剪\n超出 capacity → 最远点优先，保留最分散子集", "proc"),
]
r_ys, r_hs, r_bottom = stack(R_nodes, rcx, rw, M0 + 11.0)
for i in range(len(R_nodes) - 1):
    varrow(r_ys[i] + r_hs[i] / 2, r_ys[i + 1] - r_hs[i + 1] / 2, rcx)
# 右栏下方补充说明
extra_y = r_bottom + 9.0
ax.text(70.0, extra_y, "档案库的语义（存的是调度，不是排列）", fontproperties=fpb,
        fontsize=10.4, color="#2b4a72", va="center")
ax.text(70.0, extra_y + 8.0,
        "· 每个结构等价类只留一个代表元，库内解两两结构互异\n"
        "· 只收 (1+ρ)·best 以内的解；最优值改进后自动剪掉超限旧解\n"
        "· 门槛默认 ρ = 1%，δ_m = 0.05，δ_s = 0.10，容量 200\n"
        "· stats 记录 rejected_quality / same_class / too_close / trimmed",
        fontproperties=fp, fontsize=9.0, color="#245c42", linespacing=1.75, va="top")
panel(67.0, M0, 130.0, LPANEL1, "阶段三展开 · 入档判定四步")

# ================= ④ 底部：商集示意 =================
Q0 = LPANEL1 + 5.0
q_top = Q0 + 12.0
ax.text(6.0, q_top, "为什么要在商集 Π/~ 上搜索：排列 ≠ 调度", fontproperties=fpb,
        fontsize=11.0, color="#2b4a72", va="center")

chips = ["π1", "π2", "π3", "π4", "π5", "π6"]
chip_x, chip_w, chip_h = 16.0, 15.0, 5.2
chip_ys = [q_top + 9.0 + i * 6.2 for i in range(6)]
for label, yc in zip(chips, chip_ys):
    ax.add_patch(FancyBboxPatch((chip_x - chip_w / 2, yc - chip_h / 2), chip_w, chip_h,
        boxstyle="round,pad=0.2,rounding_size=0.9", fc="#eef4ff", ec="#3b6fd4",
        lw=1.1, zorder=4))
    ax.text(chip_x, yc, label, fontproperties=fp, fontsize=9.0, color=TXT,
            ha="center", va="center", zorder=5)

classes = [("调度 A   makespan = 139", "#ecfaf3", "#2e9e6b"),
           ("调度 B   makespan = 139", "#ecfaf3", "#2e9e6b"),
           ("调度 C   makespan = 141（超出 ρ，不入档）", "#f2f4f7", "#9aa4b0")]
class_x, class_w, class_h = 62.0, 46.0, 6.4
class_ys = [chip_ys[1], chip_ys[3], chip_ys[4] + 3.1]
for (label, fc, ec), yc in zip(classes, class_ys):
    ax.add_patch(FancyBboxPatch((class_x - class_w / 2, yc - class_h / 2), class_w, class_h,
        boxstyle="round,pad=0.25,rounding_size=1.0", fc=fc, ec=ec, lw=1.2, zorder=4))
    ax.text(class_x, yc, label, fontproperties=fp, fontsize=8.8, color=TXT,
            ha="center", va="center", zorder=5)
for chip_index, class_index in [(0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 2)]:
    ax.add_patch(FancyArrowPatch(
        (chip_x + chip_w / 2, chip_ys[chip_index]),
        (class_x - class_w / 2, class_ys[class_index]),
        arrowstyle="-|>", mutation_scale=9, lw=1.0, color="#8fa3ba", zorder=3,
        shrinkA=0.5, shrinkB=0.5))

note_x = 90.0
ax.text(note_x, class_ys[0] - 7.0,
        "π1、π2、π3 是三个不同排列，解码后却是同一个调度\n"
        "→ 只算 1 个解（位置海明距离会误算成 3 个）\n"
        "调度 A 与 B 结构不同、makespan 相同 → 这才是 2 个等优解",
        fontproperties=fp, fontsize=9.0, color="#245c42", linespacing=1.75, va="top")
ax.text(note_x, class_ys[2] + 9.0,
        "结构距离（两个归一化分量）：\n"
        "· 机器分配距离 = 分配到不同机器的 (工件, 阶段) 对占比\n"
        "· 加工顺序距离 = 同一机器上工件对先后顺序翻转的比例",
        fontproperties=fp, fontsize=9.0, color="#8a5a1c", linespacing=1.75, va="top")

Q1 = max(chip_ys[-1] + 6.0, class_ys[2] + 22.0)
panel(2.0, Q0, 130.0, Q1, "")

# ================= ⑤ 输出 =================
ny = Q1 + 5.0
ax.add_patch(FancyBboxPatch((2.0, ny), 128.0, 19.0, boxstyle="round,pad=0.6,rounding_size=2.0",
    fc="#f4fbf7", ec="#2e9e6b", lw=1.4, ls=":", zorder=1))
ax.text(6.0, ny + 4.8, "输出：等优解集 {π1, π2, …, πk}——结构互异，各带机器分配与甘特图",
        fontproperties=fpb, fontsize=10.6, color="#1d6b48", zorder=2)
ax.text(6.0, ny + 12.0,
        "多模态指标：等优解数（ρ = 0/1%/2%/5%）、解集多样性（两个结构距离分量）、故障鲁棒性\n"
        "下游用途：机器故障时把 k 条解逐条代入停机情景，选恶化最小的那条立即顶上——免重算，O(k) 响应",
        fontproperties=fp, fontsize=9.4, color="#245c42", linespacing=1.75, va="center", zorder=2)

BOTTOM = ny + 21.5
ax.set_ylim(BOTTOM, 0)
fig.set_size_inches(12.6, BOTTOM / UNITS_PER_INCH)
import sys
out_png = sys.argv[1]
fig.savefig(out_png, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.25)
import sys
out_png = sys.argv[1]
fig.savefig(out_png.replace(".png", ".svg"), bbox_inches="tight", facecolor="white", pad_inches=0.25)
print("ok BOTTOM", round(BOTTOM, 1), "figheight", round(BOTTOM / UNITS_PER_INCH, 1))
