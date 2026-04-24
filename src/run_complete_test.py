from __future__ import annotations

import argparse
import json
from pathlib import Path

from multimodal_hfsp_solver import SolverConfig, run_multimodal_hfsp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行完整 HFSP 示例测试")
    parser.add_argument("--benchmarks-dir", default="benchmarks")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--population-size", type=int, default=30)
    parser.add_argument("--max-generations", type=int, default=40)
    parser.add_argument("--ig-iterations", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20260326)
    parser.add_argument("--generate-chart", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    benchmarks = [
        Path(args.benchmarks_dir) / "benchmark_carlier_small.json",
        Path(args.benchmarks_dir) / "benchmark_carlier_medium.json",
        Path(args.benchmarks_dir) / "benchmark_taillard_small.json",
        Path(args.benchmarks_dir) / "benchmark_uniform_10x5x2.json",
        Path(args.benchmarks_dir) / "benchmark_bottleneck_10jobs_s0.json",
        Path(args.benchmarks_dir) / "benchmark_demo_multimodal_8x4x2.json",
    ]

    summaries = []
    for index, benchmark_path in enumerate(benchmarks):
        config = SolverConfig(
            population_size=args.population_size,
            max_generations=args.max_generations,
            ig_max_iterations=args.ig_iterations,
            seed=args.seed + index,
        )
        summary = run_multimodal_hfsp(
            benchmark_path=benchmark_path,
            output_dir=args.output_dir,
            results_dir=args.results_dir,
            config=config,
            generate_chart=args.generate_chart,
        )
        summaries.append(summary)
        print(
            f"{benchmark_path.name}: best_makespan={summary['best_makespan']}, "
            f"elapsed={summary['elapsed_seconds']}s"
        )

    destination = Path(args.output_dir) / "complete_test_summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(summaries, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
