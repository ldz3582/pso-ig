from __future__ import annotations

from pathlib import Path

from hfsp_environment import HFSPEnvironment, ScheduleEvaluation


def generate_gantt_chart(
    env: HFSPEnvironment,
    evaluation: ScheduleEvaluation,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("生成甘特图需要安装 matplotlib") from exc

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, max(4, env.n_stages * 1.4)))
    colors = plt.cm.tab20.colors

    for operation in evaluation.operations:
        y = sum(env.machines_per_stage[: operation.stage_id]) + operation.machine_id
        ax.barh(
            y=y,
            width=operation.processing_time,
            left=operation.start_time,
            color=colors[operation.job_id % len(colors)],
            edgecolor="black",
        )
        ax.text(
            operation.start_time + operation.processing_time / 2,
            y,
            f"J{operation.job_id}",
            ha="center",
            va="center",
            fontsize=8,
        )

    labels = []
    for stage_id, machine_count in enumerate(env.machines_per_stage):
        for machine_id in range(machine_count):
            labels.append(f"S{stage_id + 1}-M{machine_id + 1}")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Time")
    ax.set_ylabel("Machines")
    ax.set_title(title or f"{env.name} Gantt Chart")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(destination, dpi=160)
    plt.close(fig)
    return destination
