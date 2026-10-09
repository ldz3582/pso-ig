"""main.py —— 主函数（main）。

主体是 main()：读算例 → 跑 pso()（内部每 12 代调用一次 ig()）
→ 建多模态档案（以甘特图识别模态）→ 为每条多模态解输出一张甘特图。
同文件的 HFSPEnvironment / ScheduleEvaluation / MultimodalArchive 是支撑定义，
甘特图的绘制与识别在 gantt.py。
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from gantt import (
    draw_gantt,
    draw_gantt_similarity_comparison,
    gantt_signature,
    gantt_similarity,
)
from pso import SolverConfig, pso


# --------------------------------------------------------------------------- #
# HFSP 模型与解码
# --------------------------------------------------------------------------- #

# 评价缓存容量上限：超限后按最久未使用淘汰，避免长跑大规模算例时内存持续增长。
EVALUATION_CACHE_CAPACITY = 200_000


# =========================================================================== #
# 主体：main()（主函数）
# =========================================================================== #
def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    default_benchmark = project_root / "5benchmark" / "Carlier_benchmark" / "j10c5a2.txt"
    parser = argparse.ArgumentParser(description="HFSP：PSO + IG + 多模态档案")
    parser.add_argument("--benchmark", default=str(default_benchmark), help="算例路径（.txt/.json）")
    parser.add_argument("--output-dir", default=str(project_root / "output"), help="档案与摘要输出目录")
    parser.add_argument("--results-dir", default=str(project_root / "results"), help="甘特图输出目录")
    parser.add_argument("--population-size", type=int, default=40)
    parser.add_argument("--time-factor", type=float, default=0.01, help="老师论文时间系数 t（Carlier 96 默认 0.01）")
    parser.add_argument("--time-limit-sec", type=float, default=None, help="手动指定运行时间（秒），若未指定则按论文公式计算")
    parser.add_argument("--ig-iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260326)
    parser.add_argument("--similarity-threshold", type=float, default=1.0, help="甘特图相似度阈值（1.0为严格甘特图去重，<1.0如0.85为模态聚类）")
    parser.add_argument("--max-charts", type=int, default=20, help="最多绘制的最优多模态甘特图张数")
    parser.add_argument(
        "--decode-mode",
        choices=["forward", "backward", "hybrid"],
        default="hybrid",
        help="解码方向：forward 仅正向 / backward 仅反向 / hybrid 正反取较小 makespan（默认）",
    )
    args = parser.parse_args()

    env = HFSPEnvironment.from_file(args.benchmark)
    env.decode_mode = args.decode_mode
    config = SolverConfig(
        time_factor=args.time_factor,
        time_limit_sec=args.time_limit_sec,
        population_size=args.population_size,
        ig_iterations=args.ig_iterations,
        seed=args.seed,
    )
    rng = random.Random(config.seed)

    started = time.perf_counter()
    best, candidates = pso(env, config, rng)
    elapsed = time.perf_counter() - started

    # 多模态档案：只保留最优解的不同多模态，以甘特图识别模态并去重
    archive = MultimodalArchive(only_optimal=True, similarity_threshold=args.similarity_threshold)
    optimal_candidates = [item for item in candidates if item.makespan == best.makespan]
    for evaluation in optimal_candidates:
        archive.add(evaluation)

    output_root = Path(args.output_dir)
    results_root = Path(args.results_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)
    archive_path = archive.save(output_root / f"multimodal_archive_{env.name}.json")

    # 多模态解的识别：只为最优解的不同多模态输出甘特图（最多 max_charts 张）
    chart_paths: list[str] = []
    for rank, solution in enumerate(archive.solutions[: args.max_charts], start=1):
        evaluation = env.decode_and_evaluate(solution["permutation"])
        chart_path = draw_gantt(
            env,
            evaluation,
            results_root / f"{env.name}_optimal_mode{rank}_makespan{evaluation.makespan}.png",
            title=f"{env.name} | 最优多模态解 Mode {rank} | makespan={evaluation.makespan}",
        )
        chart_paths.append(str(chart_path))

    summary = {
        "instance": env.metadata(),
        "best_makespan": best.makespan,
        "best_permutation": list(best.permutation),
        "multimodal_optimal_count": len(archive.solutions),
        "archive_path": str(archive_path),
        "gantt_charts": chart_paths,
        "elapsed_seconds": round(elapsed, 2),
        "decode_mode": env.decode_mode,
        "config": dict(config.__dict__),
    }
    summary_path = output_root / f"{env.name}_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


# =========================================================================== #
# 支撑定义：HFSP 模型与解码 / 多模态档案
# =========================================================================== #
@dataclass(frozen=True)
class Operation:
    """一道已排定的工序，可直接用于绘制甘特图。"""

    job_id: int
    stage_id: int
    machine_id: int
    start_time: int
    end_time: int
    processing_time: int


@dataclass(frozen=True)
class ScheduleEvaluation:
    """一次排产的完整结果。"""

    permutation: tuple[int, ...]
    makespan: int
    completion_times: tuple[int, ...]
    machine_assignments: tuple[tuple[int, ...], ...]
    operations: tuple[Operation, ...]
    direction: str = "forward"  # 该调度由哪种解码方式得到：forward / backward

    def to_dict(self) -> dict[str, Any]:
        return {
            "permutation": list(self.permutation),
            "makespan": self.makespan,
            "completion_times": list(self.completion_times),
            "machine_assignments": [list(row) for row in self.machine_assignments],
            "operations": [asdict(operation) for operation in self.operations],
            "direction": self.direction,
        }


class HFSPEnvironment:
    """混合流水车间：多阶段、每阶段多台平行机、工件按阶段顺序加工。"""

    def __init__(
        self,
        name: str,
        n_jobs: int,
        n_stages: int,
        machines_per_stage: Sequence[int],
        processing_times: Sequence[Sequence[Sequence[int]]],
        decode_mode: str = "hybrid",
    ) -> None:
        self.name = name
        self.n_jobs = int(n_jobs)
        self.n_stages = int(n_stages)
        self.machines_per_stage = tuple(int(value) for value in machines_per_stage)
        self.processing_times = tuple(
            tuple(tuple(int(time) for time in stage) for stage in job)
            for job in processing_times
        )

        if len(self.processing_times) != self.n_jobs:
            raise ValueError("processing_times 与 n_jobs 不匹配")
        if len(self.machines_per_stage) != self.n_stages:
            raise ValueError("machines_per_stage 与 n_stages 不匹配")
        for job_index, job in enumerate(self.processing_times):
            if len(job) != self.n_stages:
                raise ValueError(f"工件 {job_index} 的阶段数与 n_stages 不匹配")
            for stage_index, stage_times in enumerate(job):
                expected = self.machines_per_stage[stage_index]
                if len(stage_times) != expected:
                    raise ValueError(
                        f"工件 {job_index} 在阶段 {stage_index} 的机器数应为 {expected}"
                    )

        mode = str(decode_mode).lower()
        if mode not in {"forward", "backward", "hybrid"}:
            raise ValueError(f"不支持的解码方向: {decode_mode}")
        # 默认解码方向：hybrid = 正/反向各算一次取较小 makespan
        self.decode_mode = mode

        # 有上限的 LRU 缓存：解码结果只依赖（排列, 方向），可安全复用。
        self._evaluation_cache: OrderedDict[
            tuple[tuple[int, ...], str], ScheduleEvaluation
        ] = OrderedDict()

    @property
    def total_machines(self) -> int:
        return sum(self.machines_per_stage)

    @property
    def total_operations(self) -> int:
        return self.n_jobs * self.n_stages

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_jobs": self.n_jobs,
            "n_stages": self.n_stages,
            "machines_per_stage": list(self.machines_per_stage),
            "total_machines": self.total_machines,
            "total_operations": self.total_operations,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HFSPEnvironment":
        return cls(
            name=payload.get("name", "hfsp_instance"),
            n_jobs=payload["n_jobs"],
            n_stages=payload["n_stages"],
            machines_per_stage=payload["machines_per_stage"],
            processing_times=payload["processing_times"],
        )

    @classmethod
    def from_txt(cls, path: str | Path) -> "HFSPEnvironment":
        """解析 Carlier 文本格式算例。"""
        file_path = Path(path)
        tokens = file_path.read_text(encoding="utf-8").split()
        if not tokens:
            raise ValueError(f"文件 {file_path} 内容为空")
        cursor = 0
        n_jobs = int(tokens[cursor]); cursor += 1
        n_stages = int(tokens[cursor]); cursor += 1
        machines_per_stage = [int(tokens[cursor + i]) for i in range(n_stages)]
        cursor += n_stages
        stage_times: list[list[int]] = []
        for _ in range(n_stages):
            stage_times.append([int(tokens[cursor + j]) for j in range(n_jobs)])
            cursor += n_jobs
        processing_times = [
            [
                [stage_times[stage][job] for _ in range(machines_per_stage[stage])]
                for stage in range(n_stages)
            ]
            for job in range(n_jobs)
        ]
        return cls(
            name=file_path.stem,
            n_jobs=n_jobs,
            n_stages=n_stages,
            machines_per_stage=machines_per_stage,
            processing_times=processing_times,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "HFSPEnvironment":
        """自动识别 .txt / .json 算例。"""
        file_path = Path(path)
        if file_path.suffix.lower() == ".txt":
            return cls.from_txt(file_path)
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return cls.from_dict(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return cls.from_txt(file_path)

    def _validate_permutation(self, permutation: Sequence[int]) -> tuple[int, ...]:
        canonical = tuple(int(job_id) for job_id in permutation)
        if len(set(canonical)) != len(canonical):
            raise ValueError("排列中存在重复工件")
        if any(job_id < 0 or job_id >= self.n_jobs for job_id in canonical):
            raise ValueError("排列中的工件编号越界")
        return canonical

    # ------------------------------------------------------------------ #
    # 解码：正向 / 反向 / 混合
    # ------------------------------------------------------------------ #
    @staticmethod
    def _schedule_forward(
        permutation_key: tuple[int, ...],
        n_jobs: int,
        n_stages: int,
        machines_per_stage: Sequence[int],
        processing_times: Sequence[Sequence[Sequence[int]]],
        direction: str = "forward",
    ) -> ScheduleEvaluation:
        """在给定问题数据上执行正向解码（逐阶段推进，每阶段按 ECT 选最早完工的机器）。

        `permutation_key` 可以是部分排列（NEH 插入阶段），因此数组长度用 `n_jobs`
        而非排列长度。抽成静态方法是为了让反向解码复用：反向解码 = 在"镜像实例"上
        正向解码后再对时间轴做反演。
        """
        machine_ready_times = [
            [0] * machine_count for machine_count in machines_per_stage
        ]
        completion_times = [0] * n_jobs
        machine_assignments = [[-1] * n_stages for _ in range(n_jobs)]
        operations: list[Operation] = []

        for stage_id in range(n_stages):
            stage_completion_times = completion_times[:]
            for job_id in permutation_key:
                job_release_time = completion_times[job_id]
                best_machine = 0
                best_start = 0
                best_finish: int | None = None

                for machine_id in range(machines_per_stage[stage_id]):
                    processing_time = processing_times[job_id][stage_id][machine_id]
                    start_time = max(
                        job_release_time, machine_ready_times[stage_id][machine_id]
                    )
                    finish_time = start_time + processing_time
                    if (
                        best_finish is None
                        or finish_time < best_finish
                        or (
                            finish_time == best_finish
                            and machine_ready_times[stage_id][machine_id]
                            < machine_ready_times[stage_id][best_machine]
                        )
                    ):
                        best_machine = machine_id
                        best_start = start_time
                        best_finish = finish_time

                if best_finish is None:
                    raise RuntimeError("无法为工件分配机器")

                processing_time = processing_times[job_id][stage_id][best_machine]
                machine_ready_times[stage_id][best_machine] = best_finish
                stage_completion_times[job_id] = best_finish
                machine_assignments[job_id][stage_id] = best_machine
                operations.append(
                    Operation(
                        job_id=job_id,
                        stage_id=stage_id,
                        machine_id=best_machine,
                        start_time=best_start,
                        end_time=best_finish,
                        processing_time=processing_time,
                    )
                )
            completion_times = stage_completion_times

        return ScheduleEvaluation(
            permutation=permutation_key,
            makespan=max(completion_times) if completion_times else 0,
            completion_times=tuple(completion_times),
            machine_assignments=tuple(tuple(row) for row in machine_assignments),
            operations=tuple(operations),
            direction=direction,
        )

    def _decode_forward(self, permutation_key: tuple[int, ...]) -> ScheduleEvaluation:
        """正向解码：按排列顺序、阶段 1→S，每阶段安排到最早可用的机器。"""
        return self._schedule_forward(
            permutation_key,
            self.n_jobs,
            self.n_stages,
            self.machines_per_stage,
            self.processing_times,
            direction="forward",
        )

    def _decode_backward(self, permutation_key: tuple[int, ...]) -> ScheduleEvaluation:
        """反向解码：工件逆序、阶段从 S→1（先排最后一个工件、从最后阶段往前排）。

        实现上把"阶段顺序"与"工件顺序"都倒置得到镜像实例，在镜像实例上做正向解码，
        再把时间轴反演（start' = Cmax - end）。由于各阶段存在并行机，HFSP 不可逆，
        因此同一排列的正向与反向解码可能得到不同的 makespan。
        """
        reversed_machines = tuple(reversed(self.machines_per_stage))
        reversed_times = tuple(
            tuple(
                tuple(self.processing_times[job_id][self.n_stages - 1 - stage_id])
                for stage_id in range(self.n_stages)
            )
            for job_id in range(self.n_jobs)
        )
        mirrored = self._schedule_forward(
            tuple(reversed(permutation_key)),
            self.n_jobs,
            self.n_stages,
            reversed_machines,
            reversed_times,
            direction="backward",
        )
        horizon = mirrored.makespan

        completion_times = [0] * self.n_jobs
        machine_assignments = [[-1] * self.n_stages for _ in range(self.n_jobs)]
        operations: list[Operation] = []
        for operation in mirrored.operations:
            stage_id = self.n_stages - 1 - operation.stage_id
            start_time = horizon - operation.end_time
            end_time = horizon - operation.start_time
            operations.append(
                Operation(
                    job_id=operation.job_id,
                    stage_id=stage_id,
                    machine_id=operation.machine_id,
                    start_time=start_time,
                    end_time=end_time,
                    processing_time=operation.processing_time,
                )
            )
            machine_assignments[operation.job_id][stage_id] = operation.machine_id
            if end_time > completion_times[operation.job_id]:
                completion_times[operation.job_id] = end_time

        return ScheduleEvaluation(
            permutation=permutation_key,
            makespan=horizon,
            completion_times=tuple(completion_times),
            machine_assignments=tuple(tuple(row) for row in machine_assignments),
            operations=tuple(operations),
            direction="backward",
        )

    def _decode_cached(
        self, permutation_key: tuple[int, ...], direction: str
    ) -> ScheduleEvaluation:
        """按（排列, 方向）缓存解码结果。"""
        cache_key = (permutation_key, direction)
        cached = self._evaluation_cache.get(cache_key)
        if cached is not None:
            self._evaluation_cache.move_to_end(cache_key)
            return cached

        if direction == "forward":
            evaluation = self._decode_forward(permutation_key)
        elif direction == "backward":
            evaluation = self._decode_backward(permutation_key)
        else:
            raise ValueError(f"不支持的解码方向: {direction}")

        self._evaluation_cache[cache_key] = evaluation
        if len(self._evaluation_cache) > EVALUATION_CACHE_CAPACITY:
            self._evaluation_cache.popitem(last=False)
        return evaluation

    def decode_and_evaluate(
        self, permutation: Sequence[int], direction: str | None = None
    ) -> ScheduleEvaluation:
        """对排列解码并求 makespan。

        direction 取 "forward" / "backward" / "hybrid"：
        - forward：正向解码（ECT，最早完工）；
        - backward：反向解码；
        - hybrid：正、反各算一次后取 makespan 较小者。
        省略时使用实例的 self.decode_mode（默认 hybrid）。
        """
        permutation_key = self._validate_permutation(permutation)
        mode = (direction or self.decode_mode).lower()
        if mode == "hybrid":
            forward = self._decode_cached(permutation_key, "forward")
            backward = self._decode_cached(permutation_key, "backward")
            return forward if forward.makespan <= backward.makespan else backward
        return self._decode_cached(permutation_key, mode)

    def decode_forward(self, permutation: Sequence[int]) -> ScheduleEvaluation:
        """正向解码的公开接口。"""
        return self.decode_and_evaluate(permutation, direction="forward")

    def decode_backward(self, permutation: Sequence[int]) -> ScheduleEvaluation:
        """反向解码的公开接口。"""
        return self.decode_and_evaluate(permutation, direction="backward")

    def evaluate(self, permutation: Sequence[int]) -> int:
        """只取 makespan 的轻量接口（遵循 self.decode_mode）。"""
        return self.decode_and_evaluate(permutation).makespan

    def _job_average_processing_time(self, job_id: int) -> float:
        return sum(
            sum(stage_times) / len(stage_times)
            for stage_times in self.processing_times[job_id]
        )

    def best_insertion(self, permutation: Sequence[int], job_id: int) -> list[int]:
        """把 job_id 插到使 makespan 最小的位置（NEH 与 IG 重构共用）。"""
        current = list(permutation)
        best_permutation: list[int] | None = None
        best_makespan: int | None = None
        for position in range(len(current) + 1):
            candidate = current[:position] + [job_id] + current[position:]
            makespan = self.evaluate(candidate)
            if best_makespan is None or makespan < best_makespan:
                best_makespan = makespan
                best_permutation = candidate
        if best_permutation is None:
            raise RuntimeError("最优插入失败")
        return best_permutation

    def _best_insertion_order(self, job_order: Iterable[int]) -> ScheduleEvaluation:
        """NEH 的贪心最优插入。"""
        current: list[int] = []
        for job_id in job_order:
            current = self.best_insertion(current, job_id)
        return self.decode_and_evaluate(current)

    def sorted_job_order(self, rule: str = "lpt") -> list[int]:
        """按平均加工时间排序工件：`spt` 升序，`lpt` 降序。"""
        rule_name = rule.lower()
        if rule_name not in {"spt", "lpt"}:
            raise ValueError(f"不支持的排序规则: {rule}")
        return sorted(
            range(self.n_jobs),
            key=self._job_average_processing_time,
            reverse=(rule_name == "lpt"),
        )

    def neh_heuristic(self, rule: str = "lpt") -> ScheduleEvaluation:
        """NEH：先按 `rule` 排序，再逐个做最优插入，作为高质量初始解。

        - `rule="spt"`：平均加工时间升序 → NEH+SPT；
        - `rule="lpt"`：平均加工时间降序 → NEH+LPT（原 NEH 行为）。
        """
        return self._best_insertion_order(self.sorted_job_order(rule))

    def neh_spt_heuristic(self) -> ScheduleEvaluation:
        """NEH+SPT：按平均加工时间升序排序后做最优插入。"""
        return self.neh_heuristic("spt")

    def neh_lpt_heuristic(self) -> ScheduleEvaluation:
        """NEH+LPT：按平均加工时间降序排序后做最优插入。"""
        return self.neh_heuristic("lpt")

    def generate_initial_solution(
        self, method: str = "random", rng: random.Random | None = None
    ) -> list[int]:
        generator = rng or random.Random()
        method_name = method.lower().replace("+", "_").replace("-", "_")
        if method_name in {"neh_spt", "spt"}:
            return list(self.neh_spt_heuristic().permutation)
        if method_name in {"neh_lpt", "neh", "lpt"}:
            return list(self.neh_lpt_heuristic().permutation)
        if method_name == "random":
            return generator.sample(list(range(self.n_jobs)), self.n_jobs)
        raise ValueError(f"不支持的初始化方法: {method}")


# --------------------------------------------------------------------------- #
# 多模态档案
# --------------------------------------------------------------------------- #
class MultimodalArchive:
    """多模态档案库：以甘特图识别模态 —— 仅保留全局最优解的不同多模态，甘特图相同的解去重。"""

    def __init__(self, only_optimal: bool = True, similarity_threshold: float = 1.0) -> None:
        self.only_optimal = only_optimal
        self.similarity_threshold = similarity_threshold
        self.best_makespan: int | None = None
        self.solutions: list[dict[str, Any]] = []
        self._seen_gantt: set[tuple[Any, ...]] = set()
        self._evaluations: list[ScheduleEvaluation] = []

    def add(self, candidate: ScheduleEvaluation) -> bool:
        """甘特图去重与模态识别：
        - 若开启 only_optimal，只保留达到全局最优 makespan 的解，劣解直接舍弃；
        - 若出现更优 makespan，自动清空旧解并更新基准；
        - 甘特图完全相同（或相似度超过阈值）的解只保留一次。
        """
        if self.only_optimal:
            if self.best_makespan is None or candidate.makespan < self.best_makespan:
                self.best_makespan = candidate.makespan
                self.solutions.clear()
                self._seen_gantt.clear()
                self._evaluations.clear()
            elif candidate.makespan > self.best_makespan:
                # 劣于当前全局最优解，不予入档
                return False

        signature = gantt_signature(candidate)
        if signature in self._seen_gantt:
            return False

        if self.similarity_threshold < 1.0:
            for existing_eval in self._evaluations:
                if gantt_similarity(candidate, existing_eval) > self.similarity_threshold:
                    return False

        self._seen_gantt.add(signature)
        self._evaluations.append(candidate)
        self.solutions.append(
            {
                "permutation": list(candidate.permutation),
                "makespan": candidate.makespan,
                "machine_assignments": [list(row) for row in candidate.machine_assignments],
                "operations": [dict(operation.__dict__) for operation in candidate.operations],
            }
        )
        self.solutions.sort(key=lambda item: item["makespan"])
        return True

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "count": len(self.solutions),
                    "solutions": self.solutions,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )
        return destination


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    main()
