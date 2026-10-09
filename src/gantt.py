"""gantt.py —— 甘特图模块与多模态解识别。

以甘特图进行多模态解识别（Multimodal Solutions Identification via Gantt Chart）：

1. 甘特图块提取与签名：
   - `gantt_blocks()`: 将排产按机器拆解为工序块序列 (工件号, 开始时间, 时长)；
   - `gantt_signature()`: 甘特图完整签名，完全相同的两张甘特图签名一致；

2. 甘特图块级比对与相似度量化（图4核心理论）：
   - `compare_gantt_schedules()`: 精准识别两方案中每台机器上的「相同的甘特图块」与「不相同的甘特图块」；
   - `gantt_similarity()`: 甘特图相似度 Sim(A, B) = 相同块数 / max(方案A块数, 方案B块数)；
   - `gantt_distance()`: 甘特图距离 Dist(A, B) = 1.0 - Sim(A, B)；
   - `gantt_similarity_matrix()`: 多模态解之间的成对甘特图相似度矩阵；

3. 基于甘特图相似度的多模态解识别：
   - `identify_multimodal_modes()`: 按甘特图相似度阈值在高质量解集中聚类/筛选代表性模态；

4. 可视化：
   - `draw_gantt()`: 单个排产解的高清甘特图；
   - `draw_gantt_similarity_comparison()`: 严格复现图4的甘特图相似度对比图（红框相同块、紫框不同块、方案A vs 方案B）。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import matplotlib.patches as patches
import matplotlib.pyplot as plt

# 配置中文字体与负号显示
plt.rcParams["font.sans-serif"] = [
    "PingFang SC",
    "Heiti SC",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

# 一台机器上的一个工序块：(工件号, 开始时间, 加工时长)
GanttBlock = tuple[int, int, int]


# =========================================================================== #
# 数据结构与甘特图块提取
# =========================================================================== #
@dataclass(frozen=True)
class MachineBlockInfo:
    """单台机器上的甘特图块详情（含工序块与空闲时隙）。"""

    job_id: int | str  # 整数工件号或 'I' (空闲 Idle)
    start_time: int
    duration: int
    end_time: int
    is_idle: bool = False
    is_matched: bool = False  # 与对照方案相比是否属于相同的甘特图块


@dataclass
class GanttComparisonResult:
    """两张甘特图的详细对比结果。"""

    matched_blocks_count: int
    total_blocks_left: int
    total_blocks_right: int
    similarity: float
    distance: float
    left_matched_keys: set[tuple[tuple[int, int], GanttBlock]]
    right_matched_keys: set[tuple[tuple[int, int], GanttBlock]]
    left_machine_blocks: dict[tuple[int, int], list[MachineBlockInfo]]
    right_machine_blocks: dict[tuple[int, int], list[MachineBlockInfo]]


def gantt_blocks(evaluation: Any) -> dict[tuple[int, int], tuple[GanttBlock, ...]]:
    """按阶段和机器切出甘特图工序块。

    返回 `{(阶段, 机器): ((工件号, 开始时间, 加工时长), ...)}`，
    每台机器上的块按开始时间升序排列。
    """
    grouped: dict[tuple[int, int], list[GanttBlock]] = {}
    for operation in evaluation.operations:
        grouped.setdefault((operation.stage_id, operation.machine_id), []).append(
            (operation.job_id, operation.start_time, operation.processing_time)
        )
    return {
        machine: tuple(sorted(blocks, key=lambda block: (block[1], block[0])))
        for machine, blocks in sorted(grouped.items())
    }


def gantt_signature(evaluation: Any) -> tuple[Any, ...]:
    """甘特图唯一签名：两张甘特图所有机器上的工序块完全一致时，签名相同。"""
    return tuple(gantt_blocks(evaluation).items())


# =========================================================================== #
# 甘特图块对比与相似度计算（对应论文图4理论）
# =========================================================================== #
def compare_gantt_schedules(left: Any, right: Any) -> GanttComparisonResult:
    """对比两套排产方案的甘特图，精确识别相同甘特图块与不同甘特图块。

    判定规则（图4标准）：
    在同一台机器上，若某工序块的 (工件号, 开始时间, 加工时长) 在两方案中完全一致，
    则判定为「相同的甘特图块」，否则判定为「不相同的甘特图块」。
    """
    left_blocks_dict = gantt_blocks(left)
    right_blocks_dict = gantt_blocks(right)

    all_machines = sorted(set(left_blocks_dict.keys()) | set(right_blocks_dict.keys()))

    matched_count = 0
    total_left = sum(len(b) for b in left_blocks_dict.values())
    total_right = sum(len(b) for b in right_blocks_dict.values())

    left_matched_keys: set[tuple[tuple[int, int], GanttBlock]] = set()
    right_matched_keys: set[tuple[tuple[int, int], GanttBlock]] = set()

    left_machine_blocks: dict[tuple[int, int], list[MachineBlockInfo]] = {}
    right_machine_blocks: dict[tuple[int, int], list[MachineBlockInfo]] = {}

    for machine in all_machines:
        l_blocks = list(left_blocks_dict.get(machine, ()))
        r_blocks = list(right_blocks_dict.get(machine, ()))

        # 统计频次以进行多重集匹配
        r_counter = Counter(r_blocks)
        matched_in_machine: set[GanttBlock] = set()
        for b in l_blocks:
            if r_counter[b] > 0:
                matched_in_machine.add(b)
                r_counter[b] -= 1
                matched_count += 1
                left_matched_keys.add((machine, b))
                right_matched_keys.add((machine, b))

        # 构建左方案机器块（含空闲检测）
        left_machine_blocks[machine] = _build_blocks_with_idle(
            l_blocks, matched_set=matched_in_machine
        )
        # 构建右方案机器块（含空闲检测）
        right_machine_blocks[machine] = _build_blocks_with_idle(
            r_blocks, matched_set=matched_in_machine
        )

    denom = max(total_left, total_right)
    similarity = 1.0 if denom == 0 else matched_count / denom
    distance = 1.0 - similarity

    return GanttComparisonResult(
        matched_blocks_count=matched_count,
        total_blocks_left=total_left,
        total_blocks_right=total_right,
        similarity=similarity,
        distance=distance,
        left_matched_keys=left_matched_keys,
        right_matched_keys=right_matched_keys,
        left_machine_blocks=left_machine_blocks,
        right_machine_blocks=right_machine_blocks,
    )


def _build_blocks_with_idle(
    blocks: list[GanttBlock], matched_set: set[GanttBlock]
) -> list[MachineBlockInfo]:
    """根据工序序列构建包含空闲时隙（'I'）的完整横条列表。"""
    res: list[MachineBlockInfo] = []
    current_time = 0
    for job_id, start_time, duration in blocks:
        if start_time > current_time:
            # 存在空闲时隙
            res.append(
                MachineBlockInfo(
                    job_id="I",
                    start_time=current_time,
                    duration=start_time - current_time,
                    end_time=start_time,
                    is_idle=True,
                    is_matched=False,
                )
            )
        is_same = (job_id, start_time, duration) in matched_set
        end_time = start_time + duration
        res.append(
            MachineBlockInfo(
                job_id=job_id,
                start_time=start_time,
                duration=duration,
                end_time=end_time,
                is_idle=False,
                is_matched=is_same,
            )
        )
        current_time = max(current_time, end_time)
    return res


def gantt_similarity(left: Any, right: Any) -> float:
    """计算两张甘特图的相似度：相同的工序块数 / 较多者的工序块数。

    返回值范围 [0.0, 1.0]，1.0 表示两张甘特图完全相同。
    """
    return compare_gantt_schedules(left, right).similarity


def gantt_distance(left: Any, right: Any) -> float:
    """计算两张甘特图的结构距离：1.0 - 甘特图相似度。"""
    return 1.0 - gantt_similarity(left, right)


def gantt_similarity_matrix(evaluations: Sequence[Any]) -> list[list[float]]:
    """计算一组排产解两两之间的甘特图相似度对称矩阵。"""
    n = len(evaluations)
    matrix = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim = gantt_similarity(evaluations[i], evaluations[j])
            matrix[i][j] = round(sim, 4)
            matrix[j][i] = round(sim, 4)
    return matrix


# =========================================================================== #
# 基于甘特图相似度的多模态解识别
# =========================================================================== #
def identify_multimodal_modes(
    candidates: Sequence[Any],
    similarity_threshold: float = 0.85,
    makespan_tolerance: float = 0.05,
    max_modes: int | None = None,
) -> list[dict[str, Any]]:
    """基于甘特图相似度阈值从候选解中识别出真正的多个模态解。

    识别流程：
    1. 候选解按 makespan 升序排序，确定当前最优 makespan；
    2. 筛选出高质量候选：makespan <= best_makespan * (1 + makespan_tolerance)；
    3. 顺序遍历高质量解，对比其与已识别模态代表解的甘特图相似度：
       - 若与某已有模态代表解的甘特图相似度 > similarity_threshold，则视为该模态的微调变体；
       - 若与所有已有模态代表解的甘特图相似度均 <= similarity_threshold，则识别为一个全新的模态！
    4. 返回各模态代表解及其包含的变体数量。
    """
    if not candidates:
        return []

    sorted_candidates = sorted(candidates, key=lambda item: item.makespan)
    best_makespan = sorted_candidates[0].makespan
    max_acceptable_makespan = int(best_makespan * (1.0 + makespan_tolerance))

    modes: list[dict[str, Any]] = []

    for candidate in sorted_candidates:
        if candidate.makespan > max_acceptable_makespan:
            break

        belongs_to_existing_mode = False
        for mode in modes:
            rep_eval = mode["representative"]
            sim = gantt_similarity(candidate, rep_eval)
            if sim > similarity_threshold:
                belongs_to_existing_mode = True
                mode["cluster_size"] += 1
                break

        if not belongs_to_existing_mode:
            modes.append(
                {
                    "mode_id": len(modes) + 1,
                    "representative": candidate,
                    "makespan": candidate.makespan,
                    "permutation": list(candidate.permutation),
                    "cluster_size": 1,
                }
            )
            if max_modes is not None and len(modes) >= max_modes:
                break

    return modes


# =========================================================================== #
# 图 4 甘特图相似度对比图绘制函数
# =========================================================================== #
def draw_gantt_similarity_comparison(
    env: Any,
    evaluation_a: Any,
    evaluation_b: Any,
    output_path: str | Path,
    label_a: str = "方案\nA",
    label_b: str = "方案\nB",
    title_cn: str = "图 4  甘特图相似度示例说明",
    title_en: str = "Fig. 4 Illustration of Gantt chart similarity",
) -> Path:
    """绘制甘特图相似度对比图（对应论文图4样式）。

    视觉特性：
    - 顶部图例：红框「相同的甘特图块」与紫框「不相同的甘特图块」；
    - 上下两栏对齐：方案 A 与方案 B；
    - 机器坐标轴：M_{阶段, 机器}，顶部带「▲ 机器」箭头标；
    - 时间坐标轴：横向时间对齐，右端带「▶ 时间」箭头标；
    - 工件色块填充马卡龙柔和色，内部居中标注工件号；
    - 外边框：相同块用醒目红框标注，不同块用醒目紫框标注；
    - 底部居中双语题注，标明甘特图相似度定量指标。
    """
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    comparison = compare_gantt_schedules(evaluation_a, evaluation_b)

    # 机器列表与排序（从下到上：S1-M1 -> S2-M2 等）
    # 为还原图4数学风格，格式化为 M_{阶段,机器}
    stage_machines: list[tuple[int, int]] = [
        (stage_id, machine_id)
        for stage_id, count in enumerate(env.machines_per_stage)
        for machine_id in range(count)
    ]
    # 图4中习惯从下往上递增阶段或从上到下，这里按阶段升序排列在 Y 轴上
    y_map = {machine: i for i, machine in enumerate(stage_machines)}
    machine_labels = [f"$M_{{{s + 1},{m + 1}}}$" for s, m in stage_machines]

    # 配色方案（柔和高质感配色，贴合图4）
    soft_palette = [
        "#80DEEA",  # 2: 淡青蓝
        "#C8E6C9",  # 3: 浅果绿
        "#FFE0B2",  # 4: 浅橙黄
        "#D1C4E9",  # 1: 浅淡紫
        "#FFCDD2",  # 浅粉红
        "#B2DFDB",  # 浅薄荷
        "#F0F4C3",  # 浅黄绿
        "#E1BEE7",  # 浅紫罗兰
        "#BBDEFB",  # 浅天蓝
        "#FFECB3",  # 浅琥珀
    ]
    idle_color = "#FFF9C4"  # 空转块淡黄

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    fig.subplots_adjust(top=0.86, bottom=0.15, left=0.14, right=0.88, hspace=0.35)

    bar_height = 0.62
    max_span = max(evaluation_a.makespan, evaluation_b.makespan)
    x_limit = max_span * 1.12

    for ax, blocks_dict, label_text, evaluation in [
        (ax_a, comparison.left_machine_blocks, label_a, evaluation_a),
        (ax_b, comparison.right_machine_blocks, label_b, evaluation_b),
    ]:
        for machine, block_list in blocks_dict.items():
            if machine not in y_map:
                continue
            y_base = y_map[machine] - bar_height / 2

            # 1. 绘制各工序块底色与黑色基础边框
            for block in block_list:
                if block.is_idle:
                    bg_color = idle_color
                    text_str = "$I$"
                    font_style = "italic"
                else:
                    bg_color = soft_palette[block.job_id % len(soft_palette)]
                    text_str = str(block.job_id + 1)  # 1-indexed 展示
                    font_style = "normal"

                rect = patches.Rectangle(
                    (block.start_time, y_base),
                    block.duration,
                    bar_height,
                    facecolor=bg_color,
                    edgecolor="#333333",
                    linewidth=0.8,
                    zorder=2,
                )
                ax.add_patch(rect)

                # 工序文本
                ax.text(
                    block.start_time + block.duration / 2,
                    y_base + bar_height / 2,
                    text_str,
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontstyle=font_style,
                    fontweight="bold" if not block.is_idle else "normal",
                    zorder=3,
                )

            # 2. 绘制图4风格的高亮外包围框（红框：相同甘特图块，紫框：不相同甘特图块）
            # 按连续相同/连续不同划分区间以实现最贴合图4的外框效果
            segments = _group_consecutive_blocks(block_list)
            for is_same, start_t, end_t in segments:
                border_color = "#D32F2F" if is_same else "#7B1FA2"
                outer_rect = patches.Rectangle(
                    (start_t, y_base - 0.03),
                    end_t - start_t,
                    bar_height + 0.06,
                    fill=False,
                    edgecolor=border_color,
                    linewidth=2.4,
                    zorder=4,
                )
                ax.add_patch(outer_rect)

        # 轴刻度与样式
        ax.set_yticks(range(len(stage_machines)))
        ax.set_yticklabels(machine_labels, fontsize=11)
        ax.set_ylim(-0.6, len(stage_machines) - 0.2)
        ax.set_xlim(-0.5, x_limit)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.2)
        ax.spines["bottom"].set_linewidth(1.2)

        # 机器坐标轴箭头与文字
        ax.plot(0, len(stage_machines) - 0.3, "^k", transform=ax.transData, clip_on=False)
        ax.text(
            -0.08 * max_span,
            len(stage_machines) - 0.25,
            "机器",
            fontsize=11,
            va="center",
            ha="center",
        )

        # 右侧方案标识卡片（图4中的浅粉/浅紫色卡片）
        ax.text(
            x_limit * 0.94,
            (len(stage_machines) - 1) / 2,
            label_text,
            ha="center",
            va="center",
            fontsize=11,
            bbox=dict(
                boxstyle="square,pad=0.4",
                facecolor="#FCE4EC",
                edgecolor="#F8BBD0",
                linewidth=1.2,
            ),
        )

        # Makespan 虚线参考线
        ax.axvline(
            x=evaluation.makespan,
            color="#555555",
            linestyle="--",
            linewidth=1.0,
            alpha=0.75,
        )

    # 底部时间轴刻度与箭头
    ax_b.plot(x_limit * 0.98, -0.6, ">k", transform=ax_b.transData, clip_on=False)
    ax_b.text(x_limit * 0.99, -0.6, "时间", fontsize=11, va="center", ha="left")

    # 顶部独立图例（红框与紫框）
    legend_ax = fig.add_axes([0.15, 0.89, 0.7, 0.07])
    legend_ax.axis("off")

    # 红框图例
    rect_red = patches.Rectangle(
        (0.04, 0.25), 0.10, 0.5, linewidth=2.4, edgecolor="#D32F2F", facecolor="none"
    )
    legend_ax.add_patch(rect_red)
    legend_ax.text(0.16, 0.5, "相同的甘特图块", va="center", fontsize=12)

    # 紫框图例
    rect_purple = patches.Rectangle(
        (0.54, 0.25), 0.10, 0.5, linewidth=2.4, edgecolor="#7B1FA2", facecolor="none"
    )
    legend_ax.add_patch(rect_purple)
    legend_ax.text(0.66, 0.5, "不相同的甘特图块", va="center", fontsize=12)

    # 底部题注与相似度统计指标
    similarity_pct = f"{comparison.similarity * 100:.1f}%"
    sub_info = f"甘特图相似度 = {similarity_pct} (相同块数: {comparison.matched_blocks_count}/{denom_text(comparison.total_blocks_left, comparison.total_blocks_right)})"
    fig.text(
        0.5,
        0.055,
        f"{title_cn} ({sub_info})\n{title_en}",
        ha="center",
        va="center",
        fontsize=11.5,
        fontweight="bold",
        linespacing=1.4,
    )

    fig.savefig(destination, dpi=200)
    plt.close(fig)
    return destination


def denom_text(left_count: int, right_count: int) -> str:
    return str(max(left_count, right_count))


def _group_consecutive_blocks(
    blocks: list[MachineBlockInfo],
) -> list[tuple[bool, int, int]]:
    """将机器上的工序块按相同/不相同属性切分成连续区间，用于绘制连贯边框。"""
    if not blocks:
        return []
    segments: list[tuple[bool, int, int]] = []
    current_state = blocks[0].is_matched
    seg_start = blocks[0].start_time
    seg_end = blocks[0].end_time

    for block in blocks[1:]:
        if block.is_matched == current_state:
            seg_end = block.end_time
        else:
            segments.append((current_state, seg_start, seg_end))
            current_state = block.is_matched
            seg_start = block.start_time
            seg_end = block.end_time
    segments.append((current_state, seg_start, seg_end))
    return segments


# =========================================================================== #
# 单解甘特图绘制（保持向后兼容并优化视觉）
# =========================================================================== #
def draw_gantt(
    env: Any,
    evaluation: Any,
    output_path: Path,
    title: str,
) -> Path:
    """把单个多模态解画成高清甘特图。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, max(4.5, env.n_stages * 1.5)))

    soft_palette = [
        "#80DEEA",
        "#C8E6C9",
        "#FFE0B2",
        "#D1C4E9",
        "#FFCDD2",
        "#B2DFDB",
        "#F0F4C3",
        "#E1BEE7",
        "#BBDEFB",
        "#FFECB3",
    ]

    for operation in evaluation.operations:
        row = sum(env.machines_per_stage[: operation.stage_id]) + operation.machine_id
        color = soft_palette[operation.job_id % len(soft_palette)]
        ax.barh(
            y=row,
            width=operation.processing_time,
            left=operation.start_time,
            color=color,
            edgecolor="#222222",
            linewidth=0.9,
        )
        ax.text(
            operation.start_time + operation.processing_time / 2,
            row,
            f"J{operation.job_id + 1}",
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )

    labels = [
        f"$M_{{{stage_id + 1},{machine_id + 1}}}$ (S{stage_id + 1}-M{machine_id + 1})"
        for stage_id, machine_count in enumerate(env.machines_per_stage)
        for machine_id in range(machine_count)
    ]
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Time (时间)", fontsize=11)
    ax.set_ylabel("Machines (机器)", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.45)
    ax.axvline(x=evaluation.makespan, color="#D32F2F", linestyle=":", linewidth=1.5, label=f"Makespan={evaluation.makespan}")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


# =========================================================================== #
# 独立运行与 Demo 示例
# =========================================================================== #
def generate_fig4_demo(output_path: str | Path) -> Path:
    """生成完全复现原论文图4说明的独立示例图。"""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    class DummyOp:
        def __init__(self, job_id: int, stage_id: int, machine_id: int, start: int, dur: int):
            self.job_id = job_id
            self.stage_id = stage_id
            self.machine_id = machine_id
            self.start_time = start
            self.processing_time = dur
            self.end_time = start + dur

    class DummyEval:
        def __init__(self, ops: list[DummyOp], makespan: int):
            self.operations = tuple(ops)
            self.makespan = makespan
            self.permutation = (0, 1, 2, 3)

    class DummyEnv:
        machines_per_stage = (2, 2)
        n_stages = 2

    # 方案A工序
    ops_a = [
        # M_{2,2} (stage 1, machine 1): 2, 3, 2, 3 (完全相同)
        DummyOp(1, 1, 1, 4, 4),
        DummyOp(2, 1, 1, 8, 4),
        DummyOp(1, 1, 1, 12, 4),
        DummyOp(2, 1, 1, 16, 5),
        # M_{2,1} (stage 1, machine 0): 4, 1, 4, 1
        DummyOp(3, 1, 0, 2, 4),
        DummyOp(0, 1, 0, 6, 4),
        DummyOp(3, 1, 0, 10, 5),
        DummyOp(0, 1, 0, 15, 5),
        # M_{1,2} (stage 0, machine 1): 2, 3, 4, 1
        DummyOp(1, 0, 1, 0, 3),
        DummyOp(2, 0, 1, 3, 3),
        DummyOp(3, 0, 1, 6, 5),
        DummyOp(0, 0, 1, 11, 4),
        # M_{1,1} (stage 0, machine 0): 4, 1, [I], 2, 3
        DummyOp(3, 0, 0, 0, 2),
        DummyOp(0, 0, 0, 2, 3),
        DummyOp(1, 0, 0, 7, 4),
        DummyOp(2, 0, 0, 11, 7),
    ]

    # 方案B工序
    ops_b = [
        # M_{2,2} (stage 1, machine 1): 2, 3, 2, 3 (完全相同)
        DummyOp(1, 1, 1, 4, 4),
        DummyOp(2, 1, 1, 8, 4),
        DummyOp(1, 1, 1, 12, 4),
        DummyOp(2, 1, 1, 16, 5),
        # M_{2,1} (stage 1, machine 0): 1, 4, 1, 4
        DummyOp(0, 1, 0, 2, 4),
        DummyOp(3, 1, 0, 6, 4),
        DummyOp(0, 1, 0, 10, 5),
        DummyOp(3, 1, 0, 15, 5),
        # M_{1,2} (stage 0, machine 1): 1, 4, 1, 2, 3
        DummyOp(0, 0, 1, 0, 3),
        DummyOp(3, 0, 1, 3, 4),
        DummyOp(0, 0, 1, 7, 3),
        DummyOp(1, 0, 1, 10, 4),
        DummyOp(2, 0, 1, 14, 4),
        # M_{1,1} (stage 0, machine 0): 2, 3, [I], 4
        DummyOp(1, 0, 0, 0, 3),
        DummyOp(2, 0, 0, 3, 4),
        DummyOp(3, 0, 0, 10, 5),
    ]

    return draw_gantt_similarity_comparison(
        DummyEnv(),
        DummyEval(ops_a, 21),
        DummyEval(ops_b, 20),
        out,
        label_a="方案\nA",
        label_b="方案\nB",
        title_cn="图 4  甘特图相似度示例说明",
        title_en="Fig. 4 Illustration of Gantt chart similarity",
    )


if __name__ == "__main__":
    demo_file = Path(__file__).resolve().parent.parent / "results" / "Fig4_Illustration_of_Gantt_chart_similarity.png"
    saved = generate_fig4_demo(demo_file)
    print(f"[OK] 甘特图相似度图4演示已生成: {saved}")
