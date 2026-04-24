from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Sequence

from hfsp_environment import HFSPEnvironment, ScheduleEvaluation


def _group_operations(evaluation: ScheduleEvaluation) -> dict[tuple[int, int], list[dict[str, int]]]:
    grouped: dict[tuple[int, int], list[dict[str, int]]] = defaultdict(list)
    for operation in evaluation.operations:
        grouped[(operation.stage_id, operation.machine_id)].append(
            {
                "job_id": operation.job_id,
                "stage_id": operation.stage_id,
                "machine_id": operation.machine_id,
                "start_time": operation.start_time,
                "end_time": operation.end_time,
                "processing_time": operation.processing_time,
            }
        )
    for operations in grouped.values():
        operations.sort(key=lambda item: (item["start_time"], item["job_id"]))
    return grouped


def _compute_machine_stats(
    env: HFSPEnvironment,
    evaluation: ScheduleEvaluation,
) -> list[dict[str, Any]]:
    makespan = max(1, evaluation.makespan)
    grouped = _group_operations(evaluation)
    machine_stats: list[dict[str, Any]] = []

    for stage_id, machine_count in enumerate(env.machines_per_stage):
        for machine_id in range(machine_count):
            operations = grouped.get((stage_id, machine_id), [])
            busy_time = sum(item["processing_time"] for item in operations)
            active_span = 0
            if operations:
                active_span = operations[-1]["end_time"] - operations[0]["start_time"]
            machine_stats.append(
                {
                    "stage_id": stage_id,
                    "machine_id": machine_id,
                    "label": f"S{stage_id + 1}-M{machine_id + 1}",
                    "busy_time": busy_time,
                    "idle_time": max(0, makespan - busy_time),
                    "utilization": round(busy_time / makespan, 4),
                    "active_span": active_span,
                    "operations_count": len(operations),
                    "operations": operations,
                }
            )

    return machine_stats


def _compute_stage_stats(
    env: HFSPEnvironment,
    evaluation: ScheduleEvaluation,
    machine_stats: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    makespan = max(1, evaluation.makespan)
    stage_stats: list[dict[str, Any]] = []

    for stage_id, machine_count in enumerate(env.machines_per_stage):
        machines = [item for item in machine_stats if item["stage_id"] == stage_id]
        total_busy_time = sum(item["busy_time"] for item in machines)
        utilization = total_busy_time / (makespan * machine_count)
        load_values = [item["busy_time"] for item in machines]
        stage_stats.append(
            {
                "stage_id": stage_id,
                "label": f"Stage {stage_id + 1}",
                "machines": machine_count,
                "total_busy_time": total_busy_time,
                "utilization": round(utilization, 4),
                "avg_machine_load": round(mean(load_values), 2) if load_values else 0,
                "max_machine_load": max(load_values) if load_values else 0,
                "min_machine_load": min(load_values) if load_values else 0,
                "completion_max": max(
                    (
                        operation.end_time
                        for operation in evaluation.operations
                        if operation.stage_id == stage_id
                    ),
                    default=0,
                ),
            }
        )

    return stage_stats


def _compute_job_stats(
    env: HFSPEnvironment,
    evaluation: ScheduleEvaluation,
) -> list[dict[str, Any]]:
    jobs: dict[int, list[dict[str, int]]] = defaultdict(list)
    for operation in evaluation.operations:
        jobs[operation.job_id].append(
            {
                "stage_id": operation.stage_id,
                "machine_id": operation.machine_id,
                "start_time": operation.start_time,
                "end_time": operation.end_time,
                "processing_time": operation.processing_time,
            }
        )

    job_stats: list[dict[str, Any]] = []
    for job_id in range(env.n_jobs):
        operations = sorted(jobs[job_id], key=lambda item: item["stage_id"])
        total_processing_time = sum(item["processing_time"] for item in operations)
        completion_time = operations[-1]["end_time"] if operations else 0
        waiting_time = completion_time - total_processing_time
        job_stats.append(
            {
                "job_id": job_id,
                "completion_time": completion_time,
                "total_processing_time": total_processing_time,
                "waiting_time": waiting_time,
                "assigned_machines": [item["machine_id"] for item in operations],
                "operations": operations,
            }
        )

    return job_stats


def build_solution_analytics(
    env: HFSPEnvironment,
    best_evaluation: ScheduleEvaluation,
    archive_solutions: Sequence[dict[str, Any]],
    neh_evaluation: ScheduleEvaluation,
    spt_evaluation: ScheduleEvaluation,
) -> dict[str, Any]:
    machine_stats = _compute_machine_stats(env, best_evaluation)
    stage_stats = _compute_stage_stats(env, best_evaluation, machine_stats)
    job_stats = _compute_job_stats(env, best_evaluation)

    archive_makespans = [item["makespan"] for item in archive_solutions]
    best_stage = max(stage_stats, key=lambda item: item["utilization"], default=None)

    return {
        "comparison": {
            "neh_makespan": neh_evaluation.makespan,
            "spt_makespan": spt_evaluation.makespan,
            "improvement_vs_neh": round(
                ((neh_evaluation.makespan - best_evaluation.makespan) / max(1, neh_evaluation.makespan))
                * 100,
                2,
            ),
            "improvement_vs_spt": round(
                ((spt_evaluation.makespan - best_evaluation.makespan) / max(1, spt_evaluation.makespan))
                * 100,
                2,
            ),
        },
        "stage_stats": stage_stats,
        "machine_stats": machine_stats,
        "job_stats": job_stats,
        "archive_stats": {
            "count": len(archive_solutions),
            "best_makespan": min(archive_makespans) if archive_makespans else best_evaluation.makespan,
            "worst_makespan": max(archive_makespans) if archive_makespans else best_evaluation.makespan,
            "average_makespan": round(mean(archive_makespans), 2) if archive_makespans else best_evaluation.makespan,
            "spread": (max(archive_makespans) - min(archive_makespans)) if len(archive_makespans) > 1 else 0,
        },
        "bottleneck_stage": best_stage,
    }
