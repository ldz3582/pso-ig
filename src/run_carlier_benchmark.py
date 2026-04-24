from __future__ import annotations

import argparse
import json
from pathlib import Path

from multimodal_hfsp_solver import SolverConfig, run_multimodal_hfsp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量运行 Carlier benchmark")
    parser.add_argument("--benchmarks-dir", default="benchmarks")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--population-size", type=int, default=35)
    parser.add_argument("--max-generations", type=int, default=50)
    parser.add_argument("--ig-iterations", type=int, default=18)
    parser.add_argument("--seed", type=int, default=20260326)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    benchmark_paths = sorted(Path(args.benchmarks_dir).glob("benchmark_carlier_[0-9][0-9].json"))
    benchmark_paths = benchmark_paths[: args.limit]

    summaries = []
    for index, benchmark_path in enumerate(benchmark_paths):
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
            generate_chart=False,
        )
        summaries.append(summary)
        print(
            f"{benchmark_path.name}: best_makespan={summary['best_makespan']}, "
            f"archive_size={summary['archive_size']}, elapsed={summary['elapsed_seconds']}s"
        )

    destination = Path(args.output_dir) / "carlier_benchmark_summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(summaries, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
