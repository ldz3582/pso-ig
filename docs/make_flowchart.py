# -*- coding: utf-8 -*-
"""生成 HFSP 算法流程图（含多模态档案库与引导搜索）。

用法：
    python3 docs/make_flowchart.py docs/算法流程图.png

依赖：matplotlib；中文字体使用 macOS 自带的 Hiragino Sans GB。
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
from matplotlib.font_manager import FontProperties

# --base 时只画基础算法流程（PSO + IG），默认画含档案库引导的完整版
WITH_MULTIMODAL = "--base" not in sys.argv

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
fp  = FontProperties(fname=FONT); fpb = FontProperties(fname=FONT, weight="bold")

XMAX, YMAX = 130.0, (250.0 if WITH_MULTIMODAL else 150.0)
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

# ================= 顶部总览 =================
top = ["输入 HFSP 算例", "NEH 初始排列", "PSO 全局搜索", "IG 局部强化", "取两者更优解 π*", "输出调度结果"]
kinds = ["term", "heur", "proc", "heur", "proc", "dec"]
bw, gx, x0, ty = 19.0, 2.4, 2.0, 9.0
tx = []
for i, (t, k) in enumerate(zip(top, kinds)):
    cx = x0 + bw/2 + i*(bw+gx); tx.append(cx)
    node(cx, ty, t, k, w=bw, fs=10.2)
for i in range(len(top)-1):
    ax.add_patch(FancyArrowPatch((tx[i]+bw/2, ty), (tx[i+1]-bw/2, ty), arrowstyle="-|>",
        mutation_scale=14, lw=1.5, color=ARR, zorder=2))

# ================= PSO 面板 =================
p_nodes = [
    ("初始化种群：1 个 NEH 解 + (N - 1) 个随机排列\n评估每个粒子 makespan = decode(π)\npbest ← π；多样化解写入多模态档案库", "proc"),
    ("gbest ← 当前最优的 pbest", "proc"),
    ("自适应惯性权重 w 线性递减（w_max → w_min）", "proc"),
    ("小生境分组：组内 pbest 最优作为局部 gbest\n（孤粒子回退到全局 gbest）", "proc"),
    ("速度更新：v ← 惯性 w·v + 认知分量 + 社会分量\n认知分量指向 pbest，社会分量指向局部 gbest\n位置更新：x ← 对 x 依次施加 v 中的交换序列", "proc"),
    ("评估新位置 → 更新 pbest、档案库、gbest\n本轮无改进则 stagnation += 1", "proc"),
    ("gen < max_generations 且 stagnation < 8 ？", "diam"),
]
PX0, PX1 = 2.0, 64.0
pcx, pw = 35.5, 50.0
gap = 2.6
total = sum(hof(t, k) for t, k in p_nodes) + gap*(len(p_nodes)-1)
PY0 = 24.0
py = PY0 + 11.0 + total
p_ys, p_hs = [], []
cur = PY0 + 11.0
for t, k in p_nodes:
    h = hof(t, k); yc = cur + h/2
    node(pcx, yc, t, k, w=pw); p_ys.append(yc); p_hs.append(h); cur += h + gap
PY1 = cur - gap + 6.0
panel(PX0, PY0, PX1, PY1, "PSO 全局搜索  详细流程")
for i in range(len(p_nodes)-1):
    varrow(p_ys[i]+p_hs[i]/2, p_ys[i+1]-p_hs[i+1]/2, pcx)
# 回环：是 → 回到「自适应权重」
chan = 5.2
line([(pcx-pw/2, p_ys[-1]), (chan, p_ys[-1]), (chan, p_ys[2]), (pcx-pw/2, p_ys[2])])
vlabel(chan+3.0, (p_ys[-1]+p_ys[2])/2, "是：进入下一代")
varrow(p_ys[-1]+p_hs[-1]/2, PY1-1.5, pcx)
ax.text(pcx+2.5, p_ys[-1]+p_hs[-1]/2+3.6, "否：结束 PSO，输出 gbest", fontproperties=fp,
        fontsize=9.6, color=LBL, va="center")

# ================= IG 面板 =================
i_nodes = [
    ("以 PSO 的 gbest 作为起始排列 π\n初始温度 T 由 Ruiz 公式自动计算", "heur"),
    ("破坏 Destroy：随机移除 d = round(0.3n) 个工件", "proc"),
    ("重建 Reconstruct：打乱被移除工件，逐个做\n「贪心最优插入」放回", "proc"),
    ("接受准则：Δ ≤ 0 直接接受，否则以 exp(-Δ / T) 接受\n更新最优解 best；降温 T ← T × 0.95", "proc"),
    ("iter < max_iterations ？", "diam"),
]
IX0, IX1 = 66.0, 128.0
icx, iw = 97.5, 50.0
total_i = sum(hof(t, k) for t, k in i_nodes) + gap*(len(i_nodes)-1)
iy_start = PY0 + 11.0 + (total - total_i)/2.0
cur = iy_start
i_ys, i_hs = [], []
for t, k in i_nodes:
    h = hof(t, k); yc = cur + h/2
    node(icx, yc, t, k, w=iw); i_ys.append(yc); i_hs.append(h); cur += h + gap
panel(IX0, PY0, IX1, PY1, "IG 局部强化  详细流程")
for i in range(len(i_nodes)-1):
    varrow(i_ys[i]+i_hs[i]/2, i_ys[i+1]-i_hs[i+1]/2, icx)
chan2 = 68.5
line([(icx-iw/2, i_ys[-1]), (chan2, i_ys[-1]), (chan2, i_ys[1]), (icx-iw/2, i_ys[1])])
vlabel(chan2+3.0, (i_ys[-1]+i_ys[1])/2, "是：进入下一轮")
varrow(i_ys[-1]+i_hs[-1]/2, PY1-1.5, icx)
ax.text(icx+2.5, i_ys[-1]+i_hs[-1]/2+3.6, "否：结束 IG，输出 best", fontproperties=fp,
        fontsize=9.6, color=LBL, va="center")

# 顶部 → 面板 的展开示意（虚线）
for src, dst_x, dst_y in [(tx[2], pcx, PY0-1.0), (tx[3], icx, PY0-1.0)]:
    ax.add_patch(FancyArrowPatch((src, ty+hof("", "proc")/2+1.0), (dst_x, dst_y),
        arrowstyle="-|>", mutation_scale=13, lw=1.3, color="#a9b7c9",
        linestyle=(0,(4,3)), zorder=1))

# ================= 多模态面板 =================
if WITH_MULTIMODAL:
    # ================= 多模态面板 =================
    M0 = PY1 + 5.0
    m_nodes = [
        ("PSO / IG 产出的候选解（含机器分配）", "proc"),
        ("结构签名去重：解码后各阶段各机器的\n工件顺序完全相同 → 视为同一调度，只留一条", "dec"),
        ("入档判定：makespan ≤ (1 + ρ) · best\n（ρ 为等优容差，默认 1%）", "proc"),
        ("选择种子解\n探索：挑「最孤立」成员 → 大扰动\n强化：挑「接近最优」成员 → 小扰动", "heur"),
        ("扰动 + IG 重优化 → 回写档案库\n停滞时用档案库排列重启 PSO", "heur"),
        ("还有新增等优解？", "diam"),
    ]
    MX0, MX1 = 2.0, 74.0
    mcx, mw = 41.0, 58.0
    mgap = 2.6
    cur = M0 + 11.0
    m_ys, m_hs = [], []
    for t, k in m_nodes:
        h = hof(t, k); yc = cur + h/2
        node(mcx, yc, t, k, w=mw); m_ys.append(yc); m_hs.append(h); cur += h + mgap
    M1 = cur - mgap + 6.0
    panel(MX0, M0, MX1, M1, "多模态档案库与引导搜索（新增）")
    for i in range(len(m_nodes) - 1):
        varrow(m_ys[i] + m_hs[i]/2, m_ys[i+1] - m_hs[i+1]/2, mcx)
    mch = 5.8
    line([(mcx-mw/2, m_ys[-1]), (mch, m_ys[-1]), (mch, m_ys[3]), (mcx-mw/2, m_ys[3])])
    vlabel(mch+3.4, (m_ys[-1]+m_ys[3])/2, "是：继续开采")
    varrow(m_ys[-1]+m_hs[-1]/2, M1-1.5, mcx)
    ax.text(mcx+2.5, m_ys[-1]+m_hs[-1]/2+3.6, "否：停滞达上限，输出解集", fontproperties=fp,
            fontsize=9.6, color=LBL, va="center")

    # ---- 右侧：多模态输出与用途 ----
    OX0 = 76.0
    ax.add_patch(FancyBboxPatch((OX0, M0+11.0), 52.0, M1-M0-17.0,
        boxstyle="round,pad=0.5,rounding_size=1.6", fc="#f4fbf7", ec="#2e9e6b",
        lw=1.4, ls=":", zorder=1))
    ax.text(OX0+2.6, M0+16.4, "输出：等优解集 {π1, π2, …, πk}", fontproperties=fpb,
            fontsize=10.6, color="#1d6b48", zorder=2)
    ax.text(OX0+2.6, M0+25.0,
            "每个解都自带：makespan、机器分配、甘特图\n"
            "解集按「调度结构」互不相同，可直接择优下发。",
            fontproperties=fp, fontsize=9.4, color="#245c42", linespacing=1.65, va="top", zorder=2)
    ax.text(OX0+2.6, M0+38.0, "下游用途：机器故障时免重算切换", fontproperties=fpb,
            fontsize=10.6, color="#1d6b48", zorder=2)
    ax.text(OX0+2.6, M0+46.0,
            "把同一算例的 k 条等优解逐条代入「该机器停机」的\n"
            "情景，选恶化最小的那条立即顶上，无需重新迭代。",
            fontproperties=fp, fontsize=9.4, color="#245c42", linespacing=1.65, va="top", zorder=2)
    ax.text(OX0+2.6, M0+60.0, "对照：单解算法（如 MOAIG）每次运行只交出 1 条方案。",
            fontproperties=fp, fontsize=9.2, color="#8a5a1c", zorder=2)

# ================= 底部说明 =================
ny = (M1 if WITH_MULTIMODAL else PY1) + 5.0
ax.add_patch(FancyBboxPatch((2.0, ny), 126.0, 15.5, boxstyle="round,pad=0.6,rounding_size=2.0",
    fc="#f4fbf7", ec="#2e9e6b", lw=1.4, ls=":", zorder=1))
ax.text(6.0, ny+4.6, "公共内核 decode_permutation（列表调度 + ECT 机器分配）",
        fontproperties=fpb, fontsize=11.2, color="#1d6b48", zorder=2)
ax.text(6.0, ny+9.6,
        "① 按阶段推进，阶段内按工件排列 π 的顺序依次派工　② 每道工序选「最早完工」的机器（Earliest Completion Time）\n"
        "③ 同时满足两个约束：工件已完成上一阶段、机器已空闲　④ PSO 与 IG 的每一次评价都由它给出 makespan",
        fontproperties=fp, fontsize=9.8, color="#245c42", linespacing=1.7, va="center", zorder=2)

import sys
out_png = sys.argv[1]
fig.savefig(out_png, dpi=170, bbox_inches="tight", facecolor="white", pad_inches=0.2)
fig.savefig(out_png.replace(".png", ".svg"), bbox_inches="tight", facecolor="white", pad_inches=0.2)
print("ok", "base+multimodal" if WITH_MULTIMODAL else "base", PY0, PY1, ny)
