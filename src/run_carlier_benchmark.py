"""批量运行一个基准集，输出最优解 / 多模态解档案与汇总文档。

用法（在项目根目录执行，默认算例集为 Carlier benchmark）：
    .venv/bin/python src/run_carlier_benchmark.py

产物（<标签> 默认由算例目录名推导，Carlier_benchmark → carlier）：
    output/multimodal_archive_<算例>.json                  每个算例的多模态解完整档案
    output/<算例>_summary.json                             每个算例的运行摘要
    output/<标签>_multimodal_summary.json                  汇总数据（含每条模态解）
    output/<标签>_multimodal_summary.csv                   汇总表
    output/<标签>_multimodal_summary.md                    汇总文档（最优解 + 多模态解）
    results/<标签>/<算例>_optimal_mode<k>_makespan<M>.png   多模态解甘特图
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量运行基准集并汇总最优解 / 多模态解")
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="项目根目录（默认取本脚本所在 src/ 的上级目录）",
    )
    parser.add_argument("--benchmark-dir", default="5benchmark/Carlier_benchmark", help="算例目录（相对项目根或绝对路径）")
    parser.add_argument("--label", default=None, help="算例集标签，决定汇总文件名与甘特图子目录（默认由算例目录名推导）")
    parser.add_argument("--output-dir", default="output", help="档案与汇总输出目录")
    parser.add_argument("--results-dir", default=None, help="甘特图输出目录（默认为 results/<标签>）")
    parser.add_argument("--population-size", type=int, default=40)
    parser.add_argument("--time-factor", type=float, default=0.01, help="论文时间系数（Carlier 96 标准 0.01）")
    parser.add_argument("--time-limit-sec", type=float, default=None)
    parser.add_argument("--ig-iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260326)
    parser.add_argument("--similarity-threshold", type=float, default=1.0)
    parser.add_argument("--max-charts", type=int, default=5, help="每个算例最多绘制的最优多模态甘特图张数")
    parser.add_argument(
        "--decode-mode",
        choices=["forward", "backward", "hybrid"],
        default="hybrid",
        help="解码方向：forward 仅正向 / backward 仅反向 / hybrid 正反取较小 makespan（默认）",
    )
    parser.add_argument("--limit", type=int, default=None, help="仅求解前 N 个算例（调试用）")
    return parser.parse_args()


def derive_label(benchmark_dir: Path) -> str:
    """由算例目录名推导标签：Carlier_benchmark → carlier。"""
    name = benchmark_dir.name.lower()
    for suffix in ("_benchmark", "_instances", "benchmark", "instances"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    slug = "".join(char if char.isalnum() else "_" for char in name).strip("_")
    return slug or "instances"


def format_permutation(permutation: list[int] | tuple[int, ...]) -> str:
    return "-".join(str(job) for job in permutation)


def clean_stale_charts(results_dir: Path, instance_names: set[str]) -> int:
    """删除旧一轮生成、且文件名以本次算例名开头的甘特图，避免新旧结果混淆。"""
    removed = 0
    if not results_dir.exists():
        return removed
    for path in results_dir.iterdir():
        if path.is_file() and path.suffix.lower() == ".png":
            for name in instance_names:
                if path.name.startswith(f"{name}_"):
                    path.unlink()
                    removed += 1
                    break
    return removed


def run_one(
    env_module,
    pso_module,
    gantt_module,
    benchmark: Path,
    output_root: Path,
    results_root: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    env = env_module.HFSPEnvironment.from_file(benchmark)
    env.decode_mode = args.decode_mode
    config = pso_module.SolverConfig(
        time_factor=args.time_factor,
        time_limit_sec=args.time_limit_sec,
        population_size=args.population_size,
        ig_iterations=args.ig_iterations,
        seed=args.seed,
    )
    rng = random.Random(config.seed)

    started = time.perf_counter()
    best, candidates = pso_module.pso(env, config, rng)
    elapsed = time.perf_counter() - started

    archive = env_module.MultimodalArchive(
        only_optimal=True, similarity_threshold=args.similarity_threshold
    )
    for evaluation in candidates:
        if evaluation.makespan == best.makespan:
            archive.add(evaluation)

    archive_path = archive.save(output_root / f"multimodal_archive_{env.name}.json")

    chart_paths: list[str] = []
    for rank, solution in enumerate(archive.solutions[: args.max_charts], start=1):
        evaluation = env.decode_and_evaluate(solution["permutation"])
        chart_paths.append(
            str(
                gantt_module.draw_gantt(
                    env,
                    evaluation,
                    results_root / f"{env.name}_optimal_mode{rank}_makespan{evaluation.makespan}.png",
                    title=f"{env.name} | 最优多模态解 Mode {rank} | makespan={evaluation.makespan}",
                )
            )
        )

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
    with (output_root / f"{env.name}_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    return {
        "instance": env.name,
        "n_jobs": env.n_jobs,
        "n_stages": env.n_stages,
        "total_machines": env.total_machines,
        "best_makespan": best.makespan,
        "multimodal_count": len(archive.solutions),
        "charts_drawn": len(chart_paths),
        "best_permutation": format_permutation(best.permutation),
        "solve_time_sec": round(elapsed, 2),
        "modes": [
            {
                "rank": rank,
                "makespan": solution["makespan"],
                "permutation": format_permutation(solution["permutation"]),
                "chart": Path(chart_paths[rank - 1]).name if rank <= len(chart_paths) else "",
            }
            for rank, solution in enumerate(archive.solutions, start=1)
        ],
    }


def write_json(
    records: list[dict[str, Any]],
    path: Path,
    args: argparse.Namespace,
    elapsed: float,
    label: str,
    benchmark_rel: str,
) -> None:
    payload = {
        "benchmark": benchmark_rel,
        "label": label,
        "instance_count": len(records),
        "algorithm": "discrete PSO + IG",
        "modality_rule": "全局最优 makespan + 甘特图块级严格去重",
        "similarity_threshold": args.similarity_threshold,
        "decode_mode": args.decode_mode,
        "seed": args.seed,
        "population_size": args.population_size,
        "ig_iterations": args.ig_iterations,
        "time_factor": args.time_factor,
        "max_charts_per_instance": args.max_charts,
        "total_seconds": round(elapsed, 2),
        "results": [
            {
                "index": index,
                "instance": record["instance"],
                "n_jobs": record["n_jobs"],
                "n_stages": record["n_stages"],
                "total_machines": record["total_machines"],
                "best_makespan": record["best_makespan"],
                "multimodal_count": record["multimodal_count"],
                "charts_drawn": record["charts_drawn"],
                "best_permutation": record["best_permutation"],
                "solve_time_sec": record["solve_time_sec"],
                "gantt_chart_sample": record["modes"][0]["chart"] if record["modes"] else "",
                "modes": record["modes"],
            }
            for index, record in enumerate(records, start=1)
        ],
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "序号", "算例名称", "工件数", "阶段数", "机器总数",
                "最优Makespan", "多模态解数", "出图数", "求解耗时(s)", "最优工件排列",
            ]
        )
        for index, record in enumerate(records, start=1):
            writer.writerow(
                [
                    index, record["instance"], record["n_jobs"], record["n_stages"],
                    record["total_machines"], record["best_makespan"], record["multimodal_count"],
                    record["charts_drawn"], record["solve_time_sec"], record["best_permutation"],
                ]
            )


def write_markdown(
    records: list[dict[str, Any]],
    path: Path,
    results_root: Path,
    args: argparse.Namespace,
    elapsed: float,
    stale_removed: int,
    label: str,
    benchmark_rel: str,
) -> None:
    label_title = label.replace("_", " ").title()
    charts_rel = os.path.relpath(results_root, path.parent).replace(os.sep, "/")
    total_modes = sum(record["multimodal_count"] for record in records)
    unique_optimal = len({record["best_makespan"] for record in records})
    multimodal_instances = sum(1 for record in records if record["multimodal_count"] > 1)
    best_single = min(record["multimodal_count"] for record in records)
    worst_single = max(record["multimodal_count"] for record in records)
    chart_total = sum(record["charts_drawn"] for record in records)
    slowest = max(records, key=lambda record: record["solve_time_sec"])
    fastest = min(records, key=lambda record: record["solve_time_sec"])

    size_groups: dict[tuple[int, int], int] = {}
    for record in records:
        key = (record["n_jobs"], record["n_stages"])
        size_groups[key] = size_groups.get(key, 0) + 1
    size_desc = "、".join(
        f"{count} 个 {jobs} 工件×{stages} 阶段"
        for (jobs, stages), count in sorted(size_groups.items())
    )

    import matplotlib

    lines: list[str] = []
    add = lines.append

    add(f"# {label_title} 基准集：最优解与多模态解汇总文档")
    add("")
    add(f"> 本文件由批量求解脚本自动生成，覆盖 {label_title} 基准集全部 **{len(records)} 个算例** 的")
    add("> 最优解（optimal solution）与多模态解（multimodal solutions）。")
    add("")
    add("## 1. 实验设置")
    add("")
    add("| 项目 | 取值 |")
    add("|:---|:---|")
    add(f"| 算例集 | `{benchmark_rel}` |")
    add(f"| 算例总数 | {len(records)}（{size_desc}） |")
    add("| 求解算法 | 离散粒子群（PSO）+ 迭代贪婪（IG）局部搜索 |")
    add(f"| 解码方向 | {args.decode_mode}（forward 仅正向 / backward 仅反向 / hybrid 正反取较小 makespan） |")
    add("| 粒子规模 | 40 |")
    add(f"| IG 迭代次数 | {args.ig_iterations}（每 12 代触发一次） |")
    add(f"| 时间系数 t | {args.time_factor}（终止时间 = t·μ³·σ，单位毫秒） |")
    add(f"| 随机种子 | {args.seed} |")
    add(f"| 模态识别 | 仅保留全局最优 makespan；甘特图块级相似度阈值 = {args.similarity_threshold}（1.0 为严格去重） |")
    add(f"| 每算例出图上限 | {args.max_charts} 张 |")
    add(f"| 运行环境 | Python {sys.version.split()[0]} / matplotlib {matplotlib.__version__} |")
    add(f"| 全部算例总耗时 | **{elapsed:.1f} 秒** |")
    add("")
    add("**名词说明**")
    add("")
    add("- **最优解**：算法在给定时间预算内找到的最小 makespan（最大完工时间）及其对应工件加工排列。")
    add("- **多模态解**：在 makespan 全局最优的前提下，**甘特图排布各不相同**的调度方案。")
    add("  若两条解的所有机器上工序块序列完全一致，则视为同一模态，只保留一条；")
    add("  模态数越多，说明该算例越存在「同工期、不同排产」的等价最优方案。")
    add("")
    add("**产物路径**")
    add("")
    add("- 多模态解完整档案（含机器分配与每道工序起止时间）：`output/multimodal_archive_<算例>.json`")
    add("- 单算例运行摘要：`output/<算例>_summary.json`")
    add(f"- 多模态解甘特图：`{charts_rel}/<算例>_optimal_mode<k>_makespan<值>.png`")
    add(f"- 汇总数据：`output/{label}_multimodal_summary.{{json,csv,md}}`")
    add("")
    if stale_removed:
        add(f"> 本次运行前清理了 `{charts_rel}/` 下 {stale_removed} 张上一轮生成的甘特图。")
        add("")

    add("## 2. 结果总览")
    add("")
    add("| 指标 | 数值 |")
    add("|:---|:---|")
    add(f"| 算例数 | {len(records)} |")
    add(f"| 多模态解总数（所有算例累加） | {total_modes} |")
    add(f"| 存在多模态的最优解算例数（模态数 > 1） | {multimodal_instances} / {len(records)} |")
    add(f"| 单算例模态数范围 | {best_single} ~ {worst_single} |")
    add(f"| 不同最优 makespan 取值个数 | {unique_optimal} |")
    add(f"| 绘制甘特图总数 | {chart_total} |")
    add(f"| 单算例最快 / 最慢求解 | {fastest['instance']} {fastest['solve_time_sec']}s / {slowest['instance']} {slowest['solve_time_sec']}s |")
    add("")
    add("## 3. 各算例汇总表")
    add("")
    add("「最优多模态解数」为该算例在最优 makespan 下互不相同的甘特图模态总数；")
    add("「出图数」为实际导出的甘特图张数（不超过每算例上限）。")
    add("")
    add("| 序号 | 算例名称 | 工件数 | 阶段数 | 机器总数 | 最优 Makespan | 最优多模态解数 | 出图数 | 求解耗时(s) | 最优工件排列 |")
    add("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    for index, record in enumerate(records, start=1):
        add(
            f"| {index} | `{record['instance']}` | {record['n_jobs']} | {record['n_stages']} | "
            f"{record['total_machines']} | **{record['best_makespan']}** | {record['multimodal_count']} | "
            f"{record['charts_drawn']} | {record['solve_time_sec']} | `{record['best_permutation']}` |"
        )
    add("")

    add("## 4. 最优解与多模态解明细")
    add("")
    add(f"以下逐个算例列出全部多模态最优解（工件排列编号为 0 基）。共 {len(records)} 个算例、{total_modes} 条模态解。")
    add("")
    for index, record in enumerate(records, start=1):
        add(f"### 4.{index} `{record['instance']}`")
        add("")
        add(
            f"- 规模：{record['n_jobs']} 工件 × {record['n_stages']} 阶段，共 {record['total_machines']} 台机器"
        )
        add(f"- **最优 Makespan：{record['best_makespan']}**")
        add(f"- 最优多模态解数：**{record['multimodal_count']}**（出图 {record['charts_drawn']} 张）")
        add(f"- 求解耗时：{record['solve_time_sec']} s")
        add(f"- 最优排列（档案首条）：`{record['best_permutation']}`")
        if record["charts_drawn"]:
            links = "、".join(
                f"[Mode {mode['rank']}]({charts_rel}/{mode['chart']})"
                for mode in record["modes"][: record["charts_drawn"]]
            )
            add(f"- 甘特图：{links}")
        add("")
        add("| 模态 | Makespan | 工件加工排列（0 基） | 甘特图 |")
        add("|:---:|:---:|:---|:---:|")
        for mode in record["modes"]:
            chart_cell = (
                f"[查看]({charts_rel}/{mode['chart']})" if mode["chart"] else "—"
            )
            add(f"| Mode {mode['rank']} | {mode['makespan']} | `{mode['permutation']}` | {chart_cell} |")
        add("")

    add("## 5. 多模态解分布")
    add("")
    add("| 模态数区间 | 算例数 |")
    add("|:---|:---:|")
    buckets = [(1, 1), (2, 5), (6, 20), (21, 50), (51, 10**9)]
    for low, high in buckets:
        count = sum(1 for record in records if low <= record["multimodal_count"] <= high)
        label = f"{low}" if low == high else (f"{low}+" if high >= 10**9 else f"{low} ~ {high}")
        add(f"| {label} | {count} |")
    add("")
    top = sorted(records, key=lambda record: record["multimodal_count"], reverse=True)[:10]
    add("多模态解数最多的 10 个算例：")
    add("")
    add("| 排名 | 算例 | 多模态解数 | 最优 Makespan |")
    add("|:---:|:---|:---:|:---:|")
    for rank, record in enumerate(top, start=1):
        add(f"| {rank} | `{record['instance']}` | {record['multimodal_count']} | {record['best_makespan']} |")
    add("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    sys.path.insert(0, str(project_root / "src"))

    import main as env_module  # noqa: E402  (HFSPEnvironment / MultimodalArchive)
    import gantt as gantt_module  # noqa: E402
    import pso as pso_module  # noqa: E402

    benchmark_dir = project_root / args.benchmark_dir
    label = args.label or derive_label(benchmark_dir)
    output_root = project_root / args.output_dir
    results_root = project_root / (args.results_dir or f"results/{label}")
    output_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    try:
        benchmark_rel = benchmark_dir.relative_to(project_root).as_posix()
    except ValueError:
        benchmark_rel = benchmark_dir.as_posix()

    benchmarks = sorted(benchmark_dir.glob("*.txt"))
    if args.limit is not None:
        benchmarks = benchmarks[: args.limit]
    if not benchmarks:
        raise SystemExit(f"未在 {benchmark_dir} 找到任何 .txt 算例")

    instance_names = {path.stem for path in benchmarks}
    stale_removed = clean_stale_charts(results_root, instance_names)

    print(f"算例集：{benchmark_rel}（标签 {label}）；共 {len(benchmarks)} 个算例；清理旧甘特图 {stale_removed} 张")
    records: list[dict[str, Any]] = []
    started = time.perf_counter()
    for index, benchmark in enumerate(benchmarks, start=1):
        record = run_one(
            env_module, pso_module, gantt_module,
            benchmark, output_root, results_root, args,
        )
        records.append(record)
        print(
            f"[{index:>3}/{len(benchmarks)}] {record['instance']:<12} "
            f"最优={record['best_makespan']:<5} 模态数={record['multimodal_count']:<5} "
            f"耗时={record['solve_time_sec']}s",
            flush=True,
        )
    elapsed = time.perf_counter() - started

    summary_json = output_root / f"{label}_multimodal_summary.json"
    summary_csv = output_root / f"{label}_multimodal_summary.csv"
    summary_md = output_root / f"{label}_multimodal_summary.md"

    write_json(records, summary_json, args, elapsed, label, benchmark_rel)
    write_csv(records, summary_csv)
    write_markdown(
        records,
        summary_md,
        results_root,
        args,
        elapsed,
        stale_removed,
        label,
        benchmark_rel,
    )

    print(f"\n全部完成：{len(records)} 个算例，总耗时 {elapsed:.1f} 秒")
    print(f"文档：{summary_md}")


if __name__ == "__main__":
    main()
