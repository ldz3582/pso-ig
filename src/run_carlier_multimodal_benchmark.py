"""Carlier 基准上的多模态批量实验：基线 vs 档案库引导。

用法：
    python3 run_carlier_multimodal_benchmark.py \
        --txt-dir ../5benchmark/Carlier_benchmark \
        --teacher ../5benchmark/teacher_moaig_result.csv \
        --out ../output/carlier_multimodal_compare.csv

对每个算例各跑一次：
  baseline = 原始 PSO + IG（档案库只存不用）
  guided   = 追加档案库引导搜索 + 档案库重启 PSO
输出逐算例对比（最优 makespan、等优解个数、解集多样性、故障鲁棒性）。
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from hfsp_environment import HFSPEnvironment
from multimodal_evaluation import evaluate_solution_set
from multimodal_hfsp_solver import SolverConfig, solve_environment


def load_carlier_txt(path: Path) -> HFSPEnvironment:
    tokens = path.read_text(encoding="utf-8").split()
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
    return HFSPEnvironment(
        name=path.stem,
        n_jobs=n_jobs,
        n_stages=n_stages,
        machines_per_stage=machines_per_stage,
        processing_times=processing_times,
    )


def load_teacher(path: Path) -> dict[str, int]:
    best: dict[str, int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["Instance_Name"].strip()
            value = int(float(row["MakeSpan"]))
            if name not in best or value < best[name]:
                best[name] = value
    return best


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    default_txt_dir = root_dir / "5benchmark" / "Carlier_benchmark"
    default_teacher = root_dir / "5benchmark" / "teacher_moaig_result.csv"
    default_out = root_dir / "output" / "carlier_multimodal_compare.csv"

    parser = argparse.ArgumentParser(description="Carlier 多模态批量对比实验")
    parser.add_argument("--txt-dir", default=str(default_txt_dir))
    parser.add_argument("--teacher", default=str(default_teacher))
    parser.add_argument("--out", default=str(default_out))
    parser.add_argument("--population-size", type=int, default=40)
    parser.add_argument("--max-generations", type=int, default=60)
    parser.add_argument("--ig-iterations", type=int, default=20)
    parser.add_argument("--guided-rounds", type=int, default=60)
    parser.add_argument("--guided-ig-iterations", type=int, default=12)
    parser.add_argument("--restart-generations", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260326)
    parser.add_argument("--limit", type=int, default=0, help=">0 时只跑前 N 个算例")
    parser.add_argument("--names", default="", help="逗号分隔的算例名，只跑这些")
    args = parser.parse_args()

    txt_dir = Path(args.txt_dir)
    files = sorted(txt_dir.glob("*.txt"))
    if not files:
        # 如果从当前路径也没找到，尝试备选路径
        fallback = Path("5benchmark/Carlier_benchmark")
        if fallback.exists():
            files = sorted(fallback.glob("*.txt"))

    if not files:
        print(f"[错误] 在目录 '{txt_dir}' 下未找到任何 .txt 算例文件，请检查路径。")
        return

    if args.names:
        wanted = {item.strip() for item in args.names.split(",") if item.strip()}
        files = [path for path in files if path.stem in wanted]
    if args.limit > 0:
        files = files[: args.limit]

    teacher = load_teacher(Path(args.teacher)) if Path(args.teacher).exists() else {}
    rows: list[dict[str, object]] = []

    for index, path in enumerate(files):
        env = load_carlier_txt(path)
        seed = args.seed + index

        base_config = SolverConfig(
            population_size=args.population_size,
            max_generations=args.max_generations,
            ig_max_iterations=args.ig_iterations,
            seed=seed,
        )
        started = time.perf_counter()
        base_result = solve_environment(env, config=base_config)
        base_seconds = time.perf_counter() - started

        guided_config = SolverConfig(
            population_size=args.population_size,
            max_generations=args.max_generations,
            ig_max_iterations=args.ig_iterations,
            seed=seed,
            archive_guided_rounds=args.guided_rounds,
            archive_guided_ig_iterations=args.guided_ig_iterations,
            archive_pso_restart_generations=args.restart_generations,
        )
        started = time.perf_counter()
        guided_result = solve_environment(env, config=guided_config)
        guided_seconds = time.perf_counter() - started

        base_metrics = evaluate_solution_set(env, base_result["archive"])
        guided_metrics = evaluate_solution_set(env, guided_result["archive"])
        teacher_best = teacher.get(path.stem, -1)

        row = {
            "instance": path.stem,
            "n_jobs": env.n_jobs,
            "stages": env.n_stages,
            "machines": "/".join(str(count) for count in env.machines_per_stage),
            "teacher_best": teacher_best,
            "base_best": base_result["best_makespan"],
            "guided_best": guided_result["best_makespan"],
            "base_minus_teacher": (base_result["best_makespan"] - teacher_best)
            if teacher_best > 0
            else "",
            "guided_minus_teacher": (guided_result["best_makespan"] - teacher_best)
            if teacher_best > 0
            else "",
            "base_archive": len(base_result["archive"]),
            "guided_archive": len(guided_result["archive"]),
            "base_optimal_count": int(base_metrics.get("optimal_count", 0)),
            "guided_optimal_count": int(guided_metrics.get("optimal_count", 0)),
            "base_rho01_count": int(base_metrics.get("rho01_count", 0)),
            "guided_rho01_count": int(guided_metrics.get("rho01_count", 0)),
            "base_rho05_count": int(base_metrics.get("rho05_count", 0)),
            "guided_rho05_count": int(guided_metrics.get("rho05_count", 0)),
            "base_div_machine": round(base_metrics.get("optimal_machine_diversity", 0.0), 4),
            "base_div_sequence": round(base_metrics.get("optimal_sequence_diversity", 0.0), 4),
            "guided_div_machine": round(guided_metrics.get("optimal_machine_diversity", 0.0), 4),
            "guided_div_sequence": round(guided_metrics.get("optimal_sequence_diversity", 0.0), 4),
            "base_seconds": round(base_seconds, 2),
            "guided_seconds": round(guided_seconds, 2),
        }
        rows.append(row)
        print(
            f"[{index + 1}/{len(files)}] {path.stem}: teacher={teacher_best} "
            f"base={row['base_best']} guided={row['guided_best']} "
            f"opt {row['base_optimal_count']}->{row['guided_optimal_count']} "
            f"({row['base_seconds']}s -> {row['guided_seconds']}s)",
            flush=True,
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    comparable = [row for row in rows if row["teacher_best"] > 0]
    better = sum(1 for row in comparable if row["guided_best"] < row["teacher_best"])
    equal = sum(1 for row in comparable if row["guided_best"] == row["teacher_best"])
    worse = sum(1 for row in comparable if row["guided_best"] > row["teacher_best"])
    base_better = sum(1 for row in comparable if row["base_best"] < row["teacher_best"])
    base_equal = sum(1 for row in comparable if row["base_best"] == row["teacher_best"])
    base_worse = sum(1 for row in comparable if row["base_best"] > row["teacher_best"])
    total_opt_base = sum(int(row["base_optimal_count"]) for row in rows)
    total_opt_guided = sum(int(row["guided_optimal_count"]) for row in rows)
    total_rho01_base = sum(int(row["base_rho01_count"]) for row in rows)
    total_rho01_guided = sum(int(row["guided_rho01_count"]) for row in rows)

    summary = {
        "instances": len(rows),
        "baseline_vs_teacher": {"better": base_better, "equal": base_equal, "worse": base_worse},
        "guided_vs_teacher": {"better": better, "equal": equal, "worse": worse},
        "total_equal_optimal_solutions": {"baseline": total_opt_base, "guided": total_opt_guided},
        "total_rho01_solutions": {"baseline": total_rho01_base, "guided": total_rho01_guided},
        "sum_seconds": round(sum(float(row["base_seconds"]) + float(row["guided_seconds"]) for row in rows), 1),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"结果写入 {out_path}")


if __name__ == "__main__":
    main()
