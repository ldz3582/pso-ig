from __future__ import annotations

import argparse
import json
from pathlib import Path

from multimodal_hfsp_solver import SolverConfig, run_multimodal_hfsp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行单个 HFSP 算例")
    parser.add_argument(
        "--benchmark",
        default=str(Path("benchmarks") / "benchmark_carlier_small.json"),
        help="benchmark JSON 路径",
    )
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
