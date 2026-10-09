# -*- coding: utf-8 -*-
"""生成 HFSP 项目全流程图（模块结构 + 端到端数据流 + 算法 + 产物）。

用法：
    python3 docs/make_project_flowchart.py

输出（写在 docs/ 下，同时生成 png 与 svg）：
    项目全流程图.png / .svg

依赖：matplotlib；中文字体使用 macOS 自带的 Hiragino Sans GB。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

DOCS = Path(__file__).resolve().parent
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FP = FontProperties(fname=FONT)
FPB = FontProperties(fname=FONT, weight="bold")

INK = "#152238"
LABEL = "#5b6b80"
PALETTE = {
    "main": ("#eef4ff", "#3b6fd4"),
    "pso": ("#f4efff", "#7a5cd6"),
    "ig": ("#fff6e8", "#dd8a1c"),
    "data": ("#ecfaf3", "#2e9e6b"),
    "out": ("#fdeff3", "#c0392b"),
    "gray": ("#f5f7fa", "#94a3b8"),
}

LINE_STEP = 4.9
FIRST_LINE = 11.0
PAD_BOTTOM = 3.8


class Canvas:
    def __init__(self, width, height, figsize):
        self.width = width
        self.height = height
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.axis("off")
        self.ax.invert_yaxis()

    # ---------------------------------------------------------------- 基本元素
    def text(self, x, y, text, fs=8.6, color=None, ha="center", bold=False, box=False):
        self.ax.text(
            x, y, text, ha=ha, va="center",
            fontproperties=(FPB if bold else FP), fontsize=fs,
            color=color or INK, zorder=5,
            bbox=({"facecolor": "white", "edgecolor": "none", "pad": 0.6} if box else None),
        )

    def title(self, text, y=5.4, fs=15.5):
        self.text(self.width / 2, y, text, fs=fs, color=INK, bold=True)

    def box(self, x, y, w, title, lines=(), kind="gray", fs=8.6, tfs=10.2, h=None):
        h = h if h is not None else (FIRST_LINE + LINE_STEP * max(0, len(lines) - 1) + PAD_BOTTOM)
        fc, ec = PALETTE[kind]
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.8,rounding_size=2.0",
            linewidth=1.5, facecolor=fc, edgecolor=ec, zorder=2))
        if lines:
            self.ax.text(x + w / 2, y + 5.0, title, ha="center", va="center",
                         fontproperties=FPB, fontsize=tfs, color=ec, zorder=4)
            for i, line in enumerate(lines):
                self.ax.text(x + 3.2, y + FIRST_LINE + i * LINE_STEP, line,
                             ha="left", va="center", fontproperties=FP,
                             fontsize=fs, color=INK, zorder=4)
        else:
            self.ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                         fontproperties=FPB, fontsize=tfs, color=ec, zorder=4)
        return h

    def frame(self, x, y, w, h, label, edge="#dbe3ee", fill="#fbfcfe"):
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=1.2,rounding_size=3.0",
            linewidth=1.3, facecolor=fill, edgecolor=edge,
            linestyle=(0, (6, 4)), zorder=1))
        self.text(x + 3.5, y + 5.0, label, fs=9.8, color="#334155", ha="left", bold=True)

    def dashed_region(self, x, y, w, h, label, edge="#c4b5fd", label_right=False):
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2.4",
            linewidth=1.2, facecolor="none", edgecolor=edge,
            linestyle=(0, (5, 3)), zorder=1))
        if label_right:
            self.text(x + w - 3.0, y - 3.4, label, fs=7.8, color=edge, ha="right")
        else:
            self.text(x + 3.0, y + h - 4.6, label, fs=7.8, color=edge, ha="left")

    def diamond(self, cx, cy, w, h, text, kind="gray", fs=8.2, edge=None):
        fc, ec = PALETTE[kind]
        ec = edge or ec
        pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
        self.ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec,
                                  linewidth=1.5, zorder=2))
        self.ax.text(cx, cy, text, ha="center", va="center",
                     fontproperties=FPB, fontsize=fs, color=ec, zorder=4)

    def arrow(self, start, end, color=None, lw=1.5):
        self.ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=13,
            linewidth=lw, color=color or LABEL, zorder=3))

    def poly(self, points, color=None, lw=1.5):
        color = color or LABEL
        for a, b in zip(points[:-2], points[1:-1]):
            self.ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, zorder=3)
        self.ax.add_patch(FancyArrowPatch(
            points[-2], points[-1], arrowstyle="-|>", mutation_scale=13,
            linewidth=lw, color=color, zorder=3))

    def save(self, name):
        for suffix in ("png", "svg"):
            path = DOCS / f"{name}.{suffix}"
            self.fig.savefig(path, dpi=160, bbox_inches="tight",
                             facecolor="white")
            print("已生成", path)
        plt.close(self.fig)


def project_flowchart():
    W, H = 212, 290
    canvas = Canvas(W, H, (13.8, 18.9))
    canvas.title("HFSP 项目全流程图（模块结构 · 端到端数据流 · 算法与产物）", y=5.6)
    canvas.text(W / 2, 11.6,
                "src/ 下 4 个文件：main.py 建模与编排 → pso.py 粒子群搜索 → ig.py 迭代贪婪局部搜索，另加 gantt.py 甘特图模块；"
                "统一以自适应时间（Time_Limit = 0.01 × μ^3 × σ 毫秒）为终止条件",
                fs=8.8, color=LABEL)

    # 图例
    legend = [("main.py", "main"), ("pso.py", "pso"), ("ig.py", "ig"), ("gantt.py", "out"),
              ("数据/建模", "data"), ("产物", "out"), ("输入资源", "gray")]
    lx = 12.0
    for name, kind in legend:
        fc, ec = PALETTE[kind]
        canvas.ax.add_patch(FancyBboxPatch((lx, 15.4), 3.0, 3.0,
                                           boxstyle="round,pad=0.2,rounding_size=0.8",
                                           facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3))
        canvas.text(lx + 4.4, 16.9, name, fs=8.2, color=LABEL, ha="left")
        lx += 4.4 + len(name) * 2.55 + 5.0

    # ================================================================== ① 输入与建模
    y1 = 26.0
    canvas.frame(5, y1, 202, 52, "① 输入与建模 ｜ main.py · HFSPEnvironment（所有算法唯一的评价入口）")

    cy = y1 + 21.0
    a1 = canvas.box(8, cy - 9.85, 37, "5benchmark/ 算例库",
                    ["Carlier 96 · Small 240", "Small-Big 480 · Big 240"], "gray", fs=8.0, tfs=9.4)
    a2 = canvas.box(50, cy - 9.85, 47, "HFSPEnvironment.from_file()",
                    [".txt → from_txt()（Carlier 文本）", ".json → from_dict()（JSON 结构）"],
                    "main", fs=8.0, tfs=9.4)
    a3 = canvas.box(102, cy - 9.85, 33, "维度校验",
                    ["工件 / 阶段 / 机器数", "加工时间张量形状"], "main", fs=8.0, tfs=9.4)
    a4 = canvas.box(140, cy - 14.7, 62, "env：HFSPEnvironment",
                    ["n_jobs · n_stages · machines_per_stage",
                     "decode_and_evaluate() 解码 + LRU 评价缓存",
                     "metadata() 输出算例规模；上限 20 万条评价"], "data", fs=8.0, tfs=9.4)
    canvas.arrow((45, cy), (50, cy))
    canvas.arrow((97, cy), (102, cy))
    canvas.arrow((135, cy), (140, cy))

    canvas.text(9, y1 + 35.0, "解码：decode_and_evaluate() 支持正向(Forward)、反向(Backward)与混合解码(Hybrid，正反向各算一次取较小 makespan)；"
                              "evaluate() 是只取 makespan 的轻量接口",
                fs=8.2, ha="left")
    canvas.text(9, y1 + 41.0, "启发式：neh_spt_heuristic() 平均加工时间升序 + 最优插入　｜　neh_lpt_heuristic() 降序 + 最优插入　｜　"
                              "best_insertion() 穷举插入位取 makespan 最小（NEH 与 IG 重构共用）",
                fs=8.2, ha="left")
    canvas.text(9, y1 + 47.0, "数据结构：Operation（单道工序：工件/阶段/机器/起止时间）　｜　"
                              "ScheduleEvaluation（排列 + makespan + 完工时间 + 机器分配 + 工序表）",
                fs=8.2, ha="left")

    # ================================================================== ② 搜索
    y2 = 82.0
    canvas.frame(5, y2, 202, 102, "② 搜索 ｜ pso.py · pso()（以自适应时间为终止条件，每 12 代调用一次 ig()）")

    loop_y, loop_h = y2 + 10.0, 44.0
    canvas.dashed_region(78, loop_y, 124, loop_h, "自适应时间循环：while (耗时 < Time_Limit)", label_right=True)

    ccy = y2 + 26.0            # 主链中心线
    bh = 22.0
    canvas.box(8, ccy - bh / 2, 32, "① 配置与计时",
               ["SolverConfig(t=0.01)", "启动高精度秒表 start_time"], "main", fs=7.8, tfs=9.4, h=bh)
    canvas.box(44, ccy - bh / 2, 31, "② 初始种群",
               ["NEH+SPT / NEH+LPT", "其余随机填至 N=40"], "pso", fs=8.0, tfs=9.6, h=bh)
    canvas.box(79, ccy - bh / 2, 34, "③ 速度更新",
               ["惯性 w 随耗时比例衰减", "⊕ 认知 c1 ⊕ 社会 c2"], "pso", fs=7.8, tfs=9.6, h=bh)
    canvas.box(117, ccy - bh / 2, 32, "④ 位置更新",
               ["施加交换序列", "+ 变异 pm=0.1"], "pso", fs=8.0, tfs=9.6, h=bh)
    canvas.box(153, ccy - bh / 2, 49, "⑤ 解码评估 / 更新最优",
               ["正向/反向/混合解码", "更新 pbest 与 gbest"], "pso", fs=8.0, tfs=9.6, h=bh)
    for x in (40, 75, 113, 149):
        canvas.arrow((x, ccy), (x + 4, ccy))

    canvas.poly([(180, ccy + bh / 2), (180, loop_y + loop_h - 2),
                 (96, loop_y + loop_h - 2), (96, ccy + bh / 2)])
    canvas.text(138, loop_y + loop_h - 2, "耗时未超（耗时 < Time_Limit）→ 下一代进化", fs=7.6, color="#7a5cd6", box=True)

    # IG 分支
    ig_y = y2 + 62.0
    canvas.box(8, ig_y, 134, "ig(gbest)：破坏 → 最优重构 → 模拟退火（ig.py）",
               ["① 破坏：随机摘除 d = round(destruction_ratio 0.3 × n_jobs) 个工件",
                "② 重构：逐个调用 env.best_insertion() 放回 makespan 最小的插入位",
                "③ 退火：Δ > 0 时以 exp(-Δ / T) 接受劣解，T ← 0.95 T，共 ig_iterations = 20 轮"],
               "ig", fs=8.0, tfs=9.6)
    canvas.poly([(166, ccy + bh / 2), (166, ig_y - 5), (140, ig_y - 5), (140, ig_y)])
    canvas.text(163, ig_y - 19, "每 12 代触发 IG", fs=7.6, color="#dd8a1c", ha="right")
    canvas.poly([(142, ig_y + 12), (176, ig_y + 12), (176, loop_y + loop_h)])
    canvas.text(179, ig_y + 10, "refined 更优：", fs=7.6, color="#dd8a1c", ha="left")
    canvas.text(179, ig_y + 4, "gbest ← refined，", fs=7.6, color="#dd8a1c", ha="left")
    canvas.text(179, ig_y - 2, "替换最差粒子", fs=7.6, color="#dd8a1c", ha="left")

    canvas.text(9, y2 + 94.0,
                "终止条件：严格以自适应时间为上限（Time_Limit = 0.01 × μ^3 × σ 毫秒，按工件数 μ 与阶段数 σ 动态自适应确定）；"
                "惯性权重 w 随耗时比例动态自适应衰减；速度为交换序列，融合认知/社会分量与 IG 局部搜索",
                fs=8.2, ha="left")

    # ================================================================== ③ 归档
    y3 = 188.0
    canvas.frame(5, y3, 202, 50, "③ 多模态档案 ｜ main.py · MultimodalArchive + gantt.py（以甘特图识别模态：同图只留一条）")

    acy = y3 + 22.0
    canvas.box(8, acy - 11, 30, "候选解集合", (), "gray", h=22, tfs=9.4)
    canvas.diamond(100, acy, 56, 28, "甘特图是否相同？", "data", fs=8.4)
    canvas.box(160, acy - 11, 32, "入档", (), "out", h=22, tfs=9.4)
    canvas.arrow((38, acy), (72, acy))
    canvas.arrow((128, acy), (160, acy))
    canvas.poly([(100, acy + 14), (100, acy + 19)])
    canvas.text(102.5, acy + 19.5, "是 × 同一张甘特图，去重丢弃", fs=7.6, color="#c0392b", ha="left")
    canvas.text(9, y3 + 45.0,
                "甘特图识别：仅保留 makespan 为全局最优的解；gantt_signature() 抽取机器工序块序列，排布相同判为同模态；"
                "gantt_similarity() 给出块级相似度（0~1）",
                fs=8.2, ha="left")

    # ================================================================== ④ 产物与运行
    y4 = 242.0
    canvas.frame(5, y4, 202, 44, "④ 产物与运行")

    canvas.box(8, y4 + 9.0, 96, "产物（output/ + results/）",
               ["output/multimodal_archive_<算例>.json：最优多模态解完整档案",
                "output/<算例>_summary.json：最优 makespan、模态数、甘特图清单、求解耗时",
                "results/<算例>_optimal_mode<k>_makespan<M>.png：各模态独立甘特图"],
               "out", fs=7.9, tfs=9.4)
    canvas.box(110, y4 + 9.0, 92, "运行与关键参数",
               ["python3 src/main.py --benchmark <算例>（其余参数均有默认值）",
                "--population-size 40 --time-factor 0.01（按算例规模自适应确定时间上限）",
                "终止条件：自适应时间 Time_Limit = 0.01 × μ^3 × σ (毫秒)",
                "PSO：w 0.9 → 0.4（随耗时比例线性衰减） ｜ IG：每 12 代触发 20 轮精修"],
               "main", fs=7.9, tfs=9.4)

    canvas.save("项目全流程图")


if __name__ == "__main__":
    project_flowchart()
