from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gantt_chart_generator import generate_gantt_chart
from hfsp_environment import HFSPEnvironment, ScheduleEvaluation
from iterated_greedy import IteratedGreedy
from niching_mechanism import DistanceCalculator
from niching_pso import NichingPSO
from solver_analysis import build_solution_analytics


@dataclass
class SolverConfig:
    population_size: int = 40
    max_generations: int = 60
    w_max: float = 0.9
    w_min: float = 0.4
    c1: float = 1.5
    c2: float = 1.5
    k_neighbors: int = 3
    stagnation_threshold: int = 10
    mutation_probability: float = 0.12
    niche_distance_threshold: int = 3
    destruction_ratio: float = 0.3
    ig_max_iterations: int = 20
    cooling_rate: float = 0.95
    makespan_tolerance: float = 0.01
    permutation_distance_threshold: int = 3
    machine_assignment_threshold: int = 1
    seed: int | None = 20260326


class MultimodalArchive:
    def __init__(
        self,
        makespan_tolerance: float = 0.01,
        permutation_distance_threshold: int = 3,
        machine_assignment_threshold: int = 1,
    ) -> None:
        self.makespan_tolerance = makespan_tolerance
        self.permutation_distance_threshold = permutation_distance_threshold
        self.machine_assignment_threshold = machine_assignment_threshold
        self.distance_calculator = DistanceCalculator()
        self.solutions: list[dict[str, Any]] = []

    def _is_novel_solution(
        self,
        permutation: list[int],
        makespan: int,
        machine_assignments: list[list[int]],
    ) -> bool:
        for solution in self.solutions:
            relative_gap = abs(solution["makespan"] - makespan) / max(1, solution["makespan"])
            permutation_distance = self.distance_calculator.permutation_distance(
                solution["permutation"], permutation
            )
            machine_distance = self.distance_calculator.machine_assignment_distance(
                solution["machine_assignments"], machine_assignments
            )
            if (
                relative_gap <= self.makespan_tolerance
                and permutation_distance <= self.permutation_distance_threshold
                and machine_distance <= self.machine_assignment_threshold
            ):
                return False
        return True

    def add_solution(
        self, permutation: list[int], makespan: int, machine_assignments: list[list[int]]
    ) -> bool:
        if not self._is_novel_solution(permutation, makespan, machine_assignments):
            return False
        self.solutions.append(
            {
                "permutation": permutation,
                "makespan": makespan,
                "machine_assignments": machine_assignments,
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
                    "makespan_tolerance": self.makespan_tolerance,
                    "permutation_distance_threshold": self.permutation_distance_threshold,
                    "machine_assignment_threshold": self.machine_assignment_threshold,
                    "solutions": self.solutions,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "MultimodalArchive":
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        archive = cls(
            makespan_tolerance=payload["makespan_tolerance"],
            permutation_distance_threshold=payload["permutation_distance_threshold"],
            machine_assignment_threshold=payload["machine_assignment_threshold"],
        )
        archive.solutions = payload["solutions"]
        return archive


def _build_solver_result(
    env: HFSPEnvironment,
    config: SolverConfig,
    solver_key: str,
    solver_label: str,
    best_evaluation: ScheduleEvaluation,
    archive: MultimodalArchive,
    neh_evaluation: ScheduleEvaluation,
    spt_evaluation: ScheduleEvaluation,
    elapsed_seconds: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    analytics = build_solution_analytics(
        env=env,
        best_evaluation=best_evaluation,
        archive_solutions=archive.solutions,
        neh_evaluation=neh_evaluation,
        spt_evaluation=spt_evaluation,
    )
    return {
        "solver_key": solver_key,
        "solver_label": solver_label,
        "instance": env.metadata(),
        "config": dict(config.__dict__),
        "elapsed_seconds": round(elapsed_seconds, 4),
        "best_makespan": best_evaluation.makespan,
        "best_solution": best_evaluation.to_dict(),
        "baselines": {
            "neh": neh_evaluation.to_dict(),
            "spt": spt_evaluation.to_dict(),
        },
        "archive": archive.solutions,
        "analytics": analytics,
        "metadata": metadata or {},
    }


def _build_archive(
    env: HFSPEnvironment,
    config: SolverConfig,
    best_evaluation: ScheduleEvaluation,
    multimodal_solutions: list[dict[str, Any]],
    ig_solutions: list[dict[str, Any]],
) -> MultimodalArchive:
    archive = MultimodalArchive(
        makespan_tolerance=config.makespan_tolerance,
        permutation_distance_threshold=config.permutation_distance_threshold,
        machine_assignment_threshold=config.machine_assignment_threshold,
    )
    for solution in multimodal_solutions:
        archive.add_solution(
            permutation=solution["permutation"],
            makespan=solution["makespan"],
            machine_assignments=solution["machine_assignments"],
        )
    archive.add_solution(
        permutation=list(best_evaluation.permutation),
        makespan=best_evaluation.makespan,
        machine_assignments=[list(row) for row in best_evaluation.machine_assignments],
    )
    for solution in ig_solutions:
        archive.add_solution(
            permutation=solution["permutation"],
            makespan=solution["makespan"],
            machine_assignments=solution["machine_assignments"],
        )
    _enrich_archive_with_schedule_data(env, archive)
    return archive


def _enrich_archive_with_schedule_data(
    env: HFSPEnvironment,
    archive: MultimodalArchive,
) -> None:
    for solution in archive.solutions:
        evaluation = env.decode_and_evaluate(solution["permutation"])
        solution["machine_assignments"] = [list(row) for row in evaluation.machine_assignments]
        solution["completion_times"] = list(evaluation.completion_times)
        solution["operations"] = evaluation.operations


def _run_basic_pso_ig(
    env: HFSPEnvironment,
    config: SolverConfig,
    neh_evaluation: ScheduleEvaluation,
    spt_evaluation: ScheduleEvaluation,
) -> dict[str, Any]:
    start_time = time.perf_counter()
    ig = IteratedGreedy(
        destruction_ratio=config.destruction_ratio,
        max_iterations=config.ig_max_iterations,
        cooling_rate=config.cooling_rate,
    )
    pso = NichingPSO(
        env=env,
        population_size=config.population_size,
        max_generations=config.max_generations,
        w_max=config.w_max,
        w_min=config.w_min,
        c1=config.c1,
        c2=config.c2,
        k_neighbors=config.k_neighbors,
        stagnation_threshold=config.stagnation_threshold,
        mutation_probability=config.mutation_probability,
        niche_distance_threshold=config.niche_distance_threshold,
        seed=config.seed,
    )
    pso.set_ig_algorithm(ig)

    _, best_position, multimodal_solutions = pso.run()
    best_evaluation = env.decode_and_evaluate(best_position)
    refined_evaluation = ig.optimize(
        best_position,
        env,
        seed=None if config.seed is None else config.seed + 1,
    )
    if refined_evaluation.makespan < best_evaluation.makespan:
        best_evaluation = refined_evaluation
        best_position = list(refined_evaluation.permutation)

    ig_solutions = ig.find_multimodal_solutions(
        best_position,
        env,
        n_solutions=5,
        seed=None if config.seed is None else config.seed + 2,
    )
    archive = _build_archive(env, config, best_evaluation, multimodal_solutions, ig_solutions)
    return _build_solver_result(
        env=env,
        config=config,
        solver_key="basic_pso_ig",
        solver_label="PSO + IG 基础算法",
        best_evaluation=best_evaluation,
        archive=archive,
        neh_evaluation=neh_evaluation,
        spt_evaluation=spt_evaluation,
        elapsed_seconds=time.perf_counter() - start_time,
        metadata={
            "algorithm_family": "basic",
            "pipeline": ["NEH", "Niching PSO", "Iterated Greedy"],
        },
    )


def _run_multi_agent_solver(
    env: HFSPEnvironment,
    config: SolverConfig,
    neh_evaluation: ScheduleEvaluation,
    spt_evaluation: ScheduleEvaluation,
) -> dict[str, Any]:
    start_time = time.perf_counter()
    seed_base = config.seed or 20260326
    candidate_records: list[dict[str, Any]] = []
    archive = MultimodalArchive(
        makespan_tolerance=config.makespan_tolerance,
        permutation_distance_threshold=config.permutation_distance_threshold,
        machine_assignment_threshold=config.machine_assignment_threshold,
    )

    def add_candidate(evaluation: ScheduleEvaluation, agent_name: str, source: str) -> None:
        archive.add_solution(
            permutation=list(evaluation.permutation),
            makespan=evaluation.makespan,
            machine_assignments=[list(row) for row in evaluation.machine_assignments],
        )
        candidate_records.append(
            {
                "agent_name": agent_name,
                "source": source,
                "makespan": evaluation.makespan,
                "permutation": list(evaluation.permutation),
            }
        )

    coordinator_ig = IteratedGreedy(
        destruction_ratio=config.destruction_ratio,
        max_iterations=config.ig_max_iterations,
        cooling_rate=config.cooling_rate,
    )

    add_candidate(neh_evaluation, "seed_agent", "neh_seed")
    add_candidate(spt_evaluation, "seed_agent", "spt_seed")
    add_candidate(
        coordinator_ig.optimize(
            neh_evaluation.permutation,
            env,
            seed=seed_base + 11,
        ),
        "local_refiner_agent",
        "ig_on_neh",
    )
    add_candidate(
        coordinator_ig.optimize(
            spt_evaluation.permutation,
            env,
            seed=seed_base + 12,
        ),
        "local_refiner_agent",
        "ig_on_spt",
    )

    exploration_config = SolverConfig(**config.__dict__)
    exploration_config.population_size = max(12, config.population_size // 2)
    exploration_config.max_generations = max(12, config.max_generations // 2)
    exploration_config.mutation_probability = min(0.35, config.mutation_probability * 1.8)
    exploration_config.seed = seed_base + 101

    exploration_pso = NichingPSO(
        env=env,
        population_size=exploration_config.population_size,
        max_generations=exploration_config.max_generations,
        w_max=exploration_config.w_max,
        w_min=exploration_config.w_min,
        c1=exploration_config.c1,
        c2=exploration_config.c2,
        k_neighbors=exploration_config.k_neighbors,
        stagnation_threshold=max(4, exploration_config.stagnation_threshold // 2),
        mutation_probability=exploration_config.mutation_probability,
        niche_distance_threshold=exploration_config.niche_distance_threshold,
        seed=exploration_config.seed,
    )
    exploration_pso.set_ig_algorithm(
        IteratedGreedy(
            destruction_ratio=min(0.45, config.destruction_ratio + 0.05),
            max_iterations=max(8, config.ig_max_iterations // 2),
            cooling_rate=config.cooling_rate,
        )
    )
    _, exploration_best_position, exploration_solutions = exploration_pso.run()
    add_candidate(
        env.decode_and_evaluate(exploration_best_position),
        "exploration_agent",
        "diversified_pso",
    )
    for solution in exploration_solutions:
        archive.add_solution(
            permutation=solution["permutation"],
            makespan=solution["makespan"],
            machine_assignments=solution["machine_assignments"],
        )

    intensification_config = SolverConfig(**config.__dict__)
    intensification_config.population_size = max(10, config.population_size // 3)
    intensification_config.max_generations = max(10, config.max_generations // 3)
    intensification_config.seed = seed_base + 202

    intensification_pso = NichingPSO(
        env=env,
        population_size=intensification_config.population_size,
        max_generations=intensification_config.max_generations,
        w_max=intensification_config.w_max,
        w_min=intensification_config.w_min,
        c1=intensification_config.c1,
        c2=intensification_config.c2,
        k_neighbors=intensification_config.k_neighbors,
        stagnation_threshold=max(4, intensification_config.stagnation_threshold // 2),
        mutation_probability=max(0.05, config.mutation_probability * 0.75),
        niche_distance_threshold=intensification_config.niche_distance_threshold,
        seed=intensification_config.seed,
    )
    intensification_pso.set_ig_algorithm(
        IteratedGreedy(
            destruction_ratio=max(0.15, config.destruction_ratio - 0.1),
            max_iterations=max(config.ig_max_iterations, 24),
            cooling_rate=config.cooling_rate,
        )
    )
    _, intensification_best_position, intensification_solutions = intensification_pso.run()
    intensified_evaluation = coordinator_ig.optimize(
        intensification_best_position,
        env,
        seed=seed_base + 203,
    )
    add_candidate(
        intensified_evaluation,
        "intensification_agent",
        "focused_pso_plus_ig",
    )
    for solution in intensification_solutions:
        archive.add_solution(
            permutation=solution["permutation"],
            makespan=solution["makespan"],
            machine_assignments=solution["machine_assignments"],
        )

    _enrich_archive_with_schedule_data(env, archive)

    best_record = min(candidate_records, key=lambda item: item["makespan"])
    best_evaluation = env.decode_and_evaluate(best_record["permutation"])

    agent_reports: dict[str, dict[str, Any]] = {}
    for record in candidate_records:
        report = agent_reports.setdefault(
            record["agent_name"],
            {"agent_name": record["agent_name"], "trials": [], "best_makespan": None},
        )
        report["trials"].append(
            {"source": record["source"], "makespan": record["makespan"]}
        )
        if report["best_makespan"] is None or record["makespan"] < report["best_makespan"]:
            report["best_makespan"] = record["makespan"]

    return _build_solver_result(
        env=env,
        config=config,
        solver_key="multi_agent",
        solver_label="多智能体协同求解",
        best_evaluation=best_evaluation,
        archive=archive,
        neh_evaluation=neh_evaluation,
        spt_evaluation=spt_evaluation,
        elapsed_seconds=time.perf_counter() - start_time,
        metadata={
            "algorithm_family": "multi_agent",
            "agent_reports": list(agent_reports.values()),
            "pipeline": [
                "Seed Agent",
                "Local Refiner Agent",
                "Exploration Agent",
                "Intensification Agent",
            ],
        },
    )


def solve_environment(
    env: HFSPEnvironment,
    config: SolverConfig | None = None,
    mode: str = "basic_pso_ig",
) -> dict[str, Any]:
    config = config or SolverConfig()
    neh_evaluation = env.neh_heuristic()
    spt_evaluation = env.spt_heuristic()
    if mode == "basic_pso_ig":
        return _run_basic_pso_ig(env, config, neh_evaluation, spt_evaluation)
    if mode == "multi_agent":
        return _run_multi_agent_solver(env, config, neh_evaluation, spt_evaluation)
    if mode == "compare":
        basic_result = _run_basic_pso_ig(env, config, neh_evaluation, spt_evaluation)
        multi_agent_result = _run_multi_agent_solver(env, config, neh_evaluation, spt_evaluation)
        preferred = (
            multi_agent_result
            if multi_agent_result["best_makespan"] < basic_result["best_makespan"]
            else basic_result
        )
        comparison = {
            "basic_pso_ig": {
                "best_makespan": basic_result["best_makespan"],
                "elapsed_seconds": basic_result["elapsed_seconds"],
                "archive_size": len(basic_result["archive"]),
            },
            "multi_agent": {
                "best_makespan": multi_agent_result["best_makespan"],
                "elapsed_seconds": multi_agent_result["elapsed_seconds"],
                "archive_size": len(multi_agent_result["archive"]),
            },
            "winner": preferred["solver_key"],
            "winner_label": preferred["solver_label"],
            "makespan_gap": basic_result["best_makespan"] - multi_agent_result["best_makespan"],
        }
        preferred = dict(preferred)
        preferred["mode_results"] = {
            "basic_pso_ig": basic_result,
            "multi_agent": multi_agent_result,
        }
        preferred["comparison"] = comparison
        preferred["request_mode"] = "compare"
        return preferred
    raise ValueError(f"不支持的求解模式: {mode}")


def solve_instance(
    payload: dict[str, Any],
    config: SolverConfig | None = None,
    mode: str = "basic_pso_ig",
) -> dict[str, Any]:
    env = HFSPEnvironment.from_dict(payload)
    return solve_environment(env, config=config, mode=mode)


def run_multimodal_hfsp(
    benchmark_path: str | Path,
    output_dir: str | Path = "output",
    results_dir: str | Path = "results",
    config: SolverConfig | None = None,
    generate_chart: bool = False,
) -> dict[str, Any]:
    benchmark = Path(benchmark_path)
    output_root = Path(output_dir)
    results_root = Path(results_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    env = HFSPEnvironment.from_file(benchmark)
    result = solve_environment(env, config=config)
    archive = MultimodalArchive(
        makespan_tolerance=result["config"]["makespan_tolerance"],
        permutation_distance_threshold=result["config"]["permutation_distance_threshold"],
        machine_assignment_threshold=result["config"]["machine_assignment_threshold"],
    )
    archive.solutions = result["archive"]

    archive_name = f"multimodal_archive_{benchmark.stem}.json"
    archive_path = archive.save(output_root / archive_name)

    chart_path = None
    if generate_chart:
        best_evaluation = env.decode_and_evaluate(result["best_solution"]["permutation"])
        chart_path = generate_gantt_chart(
            env,
            best_evaluation,
            results_root / f"{benchmark.stem}_gantt.png",
            title=f"{env.name} | Makespan={best_evaluation.makespan}",
        )

    summary = {
        "benchmark": benchmark.name,
        "instance_name": result["instance"]["name"],
        "best_makespan": result["best_makespan"],
        "best_permutation": result["best_solution"]["permutation"],
        "archive_size": len(result["archive"]),
        "archive_path": str(archive_path),
        "gantt_chart_path": None if chart_path is None else str(chart_path),
        "elapsed_seconds": result["elapsed_seconds"],
        "config": result["config"],
        "summary_path": str(output_root / f"{benchmark.stem}_summary.json"),
    }

    with Path(summary["summary_path"]).open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HFSP 多模态求解器")
    parser.add_argument("--benchmark", required=True, help="基准文件路径")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--results-dir", default="results", help="图表目录")
    parser.add_argument("--population-size", type=int, default=40)
    parser.add_argument("--max-generations", type=int, default=60)
    parser.add_argument("--ig-iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260326)
    parser.add_argument("--generate-chart", action="store_true")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    config = SolverConfig(
        population_size=args.population_size,
        max_generations=args.max_generations,
        ig_max_iterations=args.ig_iterations,
        seed=args.seed,
    )
    summary = run_multimodal_hfsp(
        benchmark_path=args.benchmark,
        output_dir=args.output_dir,
        results_dir=args.results_dir,
        config=config,
        generate_chart=args.generate_chart,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
