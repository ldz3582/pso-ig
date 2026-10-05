"""多模态解集评价指标（Multimodal Solution-Set Metrics）。

本模块把评价口径从"单次运行的最优 makespan"扩展为"解集质量 + 解集多样性 +
扰动鲁棒性"，用于衡量多模态求解器一次运行能交出多少条**结构不同**的可用方案。

核心概念：
  - 等优解（equivalent optimum）：makespan ≤ (1+ρ)·best 的解，ρ 为容差；
  - 结构同一性：两个排列若解码后各阶段各机器上的工件顺序完全一致，则视为
    同一个调度方案（排列不同但调度相同 = 假多样性）；
  - 冻结方案鲁棒性：机器在 [t0, t1) 故障时，按原方案继续执行造成的 makespan
    恶化；多模态解集的价值在于"可直接切换到恶化最小的那条备选方案"。
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable, Sequence

import numpy as np

from hfsp_environment import HFSPEnvironment, ScheduleEvaluation
from schedule_distance import (
    ScheduleDistance,
    build_features,
    pairwise_matrices,
    schedule_signature,
)

DEFAULT_TOLERANCES: tuple[float, ...] = (0.0, 0.01, 0.02, 0.05)


def _get(solution: Any, key: str) -> Any:
    if isinstance(solution, dict):
        return solution[key]
    return getattr(solution, key)


def solution_signature(evaluation: ScheduleEvaluation) -> tuple[Any, ...]:
    """调度结构签名：各 (阶段, 机器) 上按加工顺序排列的工件表。

    两个解签名相同 ⇔ 属于同一个结构等价类 ⇔ 是同一个调度方案（只是排列写法
    不同），不应计为两个多模态解。实现见 schedule_distance.schedule_signature。
    """
    return schedule_signature(evaluation.permutation, evaluation.machine_assignments)


def equivalent_subset(
    solutions: Sequence[Any],
    tolerance: float = 0.0,
    deduplicate: bool = True,
) -> list[Any]:
    """挑出 makespan 落在最优值 (1+tolerance) 之内的解，并按调度结构去重。"""
    if not solutions:
        return []
    ranked = sorted(solutions, key=lambda item: _get(item, "makespan"))
    best = _get(ranked[0], "makespan")
    cutoff = best * (1.0 + tolerance)
    selected = [item for item in ranked if _get(item, "makespan") <= cutoff + 1e-9]
    if not deduplicate:
        return selected

    seen: set[Any] = set()
    unique: list[Any] = []
    for item in selected:
        signature = _get(item, "signature")
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(item)
    return unique


def pairwise_diversity(solutions: Sequence[Any]) -> dict[str, float]:
    """解集多样性（商集口径）：机器分配距离与加工顺序距离的成对均值。

    与档案库的新颖性判定使用**同一个** ScheduleDistance，因此这里的数值可以和
    档案库内部的 `_distance` 直接对比，不会出现"两处多样性口径不一致"的问题。
    两个分量都归一化到 [0, 1]：
      - machine  分到不同机器的 (工件, 阶段) 对占比；
      - sequence 同一台机器上相对先后顺序发生翻转的工件对占比。
    """
    if len(solutions) < 2:
        return {"machine": 0.0, "sequence": 0.0, "pairs": 0.0}
    if any(_get(item, "machine_assignments") is None for item in solutions):
        raise ValueError("pairwise_diversity 需要带 machine_assignments 的解，请先用 with_signatures 补齐")
    features = [build_features(_get(item, "permutation"), _get(item, "machine_assignments"))
                for item in solutions]
    machine_matrix, sequence_matrix = pairwise_matrices(features)
    upper = np.triu_indices(len(features), 1)
    return {
        "machine": float(machine_matrix[upper].mean()),
        "sequence": float(sequence_matrix[upper].mean()),
        "pairs": float(len(upper[0])),
    }


def replay_with_downtime(
    env: HFSPEnvironment,
    permutation: Sequence[int],
    machine_assignments: Sequence[Sequence[int]],
    downtime: tuple[int, int, int] | None,
) -> int:
    """按"已下发的方案"（固定工件顺序 + 固定机器分配）重放，返回新的 makespan。

    downtime = (stage_id, machine_id, repair_time)：该机器在 `repair_time` 之前不可用，
    受影响的工序顺延到修复完成之后（可理解为故障停机窗口 [0, repair_time)）。
    """
    repair_stage, repair_machine, repair_time = (
        downtime if downtime is not None else (-1, -1, 0)
    )
    machine_ready = [[0] * count for count in env.machines_per_stage]
    completion = [0] * env.n_jobs

    for stage_id in range(env.n_stages):
        for job_id in permutation:
            machine_id = machine_assignments[job_id][stage_id]
            start = max(completion[job_id], machine_ready[stage_id][machine_id])
            if (
                downtime is not None
                and stage_id == repair_stage
                and machine_id == repair_machine
                and start < repair_time
            ):
                start = repair_time
            finish = start + env.processing_times[job_id][stage_id][machine_id]
            machine_ready[stage_id][machine_id] = finish
            completion[job_id] = finish
    return max(completion) if completion else 0


def fault_robustness(
    env: HFSPEnvironment,
    solutions: Sequence[Any],
    downtime: tuple[int, int, int] | None = None,
) -> dict[str, float]:
    """冻结方案在故障下的鲁棒性：恶化幅度，以及"切换备选方案"能挽回多少。

    - mean_relative_worsening: 解集内平均相对恶化率；
    - best_after_fault: 故障后解集内最好的 makespan（= 立刻切到该条备选方案即可用）；
    - switch_gain_vs_worst: 相对解集内最差方案的挽回量；
    - switch_gain_vs_mean: 相对平均方案的挽回量。
    """
    if not solutions:
        return {}
    if downtime is None:
        downtime = (env.n_stages // 2, 0, 0)

    nominal: list[int] = []
    degraded: list[int] = []
    for item in solutions:
        base = replay_with_downtime(env, _get(item, "permutation"), _get(item, "machine_assignments"), None)
        after = replay_with_downtime(
            env, _get(item, "permutation"), _get(item, "machine_assignments"), downtime
        )
        nominal.append(base)
        degraded.append(after)

    relative = [
        (after - base) / max(1, base) for base, after in zip(nominal, degraded)
    ]
    mean_degraded = sum(degraded) / len(degraded)
    return {
        "downtime_stage": float(downtime[0]),
        "downtime_machine": float(downtime[1]),
        "downtime_repair_time": float(downtime[2]),
        "best_after_fault": float(min(degraded)),
        "worst_after_fault": float(max(degraded)),
        "mean_after_fault": float(mean_degraded),
        "mean_relative_worsening": float(sum(relative) / len(relative)),
        "max_relative_worsening": float(max(relative)),
        "switch_gain_vs_worst": float(max(degraded) - min(degraded)),
        "switch_gain_vs_mean": float(mean_degraded - min(degraded)),
    }


def evaluate_solution_set(
    env: HFSPEnvironment,
    solutions: Sequence[Any],
    tolerances: Iterable[float] = DEFAULT_TOLERANCES,
    fault: tuple[int, int, int] | None = None,
) -> dict[str, float]:
    """一次性算出解集的多模态指标。solutions 需含 permutation / makespan /
    machine_assignments（可用 `with_signatures` 补齐 signature）。"""
    if not solutions:
        return {"size": 0.0, "best_makespan": 0.0}

    prepared = with_signatures(env, solutions)
    best = min(_get(item, "makespan") for item in prepared)
    metrics: dict[str, float] = {
        "size": float(len(prepared)),
        "best_makespan": float(best),
        "worst_makespan": float(max(_get(item, "makespan") for item in prepared)),
    }

    for tolerance in tolerances:
        subset = equivalent_subset(prepared, tolerance)
        label = f"rho{int(round(tolerance * 100)):02d}"
        metrics[f"{label}_count"] = float(len(subset))
        diversity = pairwise_diversity(subset)
        metrics[f"{label}_machine_diversity"] = diversity["machine"]
        metrics[f"{label}_sequence_diversity"] = diversity["sequence"]

    optimal = pairwise_diversity(equivalent_subset(prepared, 0.0))
    metrics["optimal_count"] = float(len(equivalent_subset(prepared, 0.0)))
    metrics["optimal_machine_diversity"] = optimal["machine"]
    metrics["optimal_sequence_diversity"] = optimal["sequence"]

    metrics.update(fault_robustness(env, prepared, fault))
    return metrics


def with_signatures(env: HFSPEnvironment, solutions: Sequence[Any]) -> list[dict[str, Any]]:
    """把外部解（dict / ScheduleEvaluation）统一成带 signature 的 dict 列表。"""
    prepared: list[dict[str, Any]] = []
    for item in solutions:
        permutation = list(_get(item, "permutation"))
        machine_assignments = [
            list(row) for row in _get(item, "machine_assignments")
        ] if _has_machine_assignments(item) else None
        evaluation = env.decode_and_evaluate(permutation)
        if machine_assignments is None:
            machine_assignments = [list(row) for row in evaluation.machine_assignments]
        prepared.append(
            {
                "permutation": permutation,
                "makespan": int(_get(item, "makespan")),
                "machine_assignments": machine_assignments,
                "signature": solution_signature(evaluation),
            }
        )
    return prepared


def _has_machine_assignments(item: Any) -> bool:
    value = item.get("machine_assignments") if isinstance(item, dict) else getattr(
        item, "machine_assignments", None
    )
    return value is not None
