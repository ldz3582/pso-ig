"""pso.py —— 粒子群算法（PSO）。

主体是 pso()：初始化 → 速度更新 → 位置更新，每 12 代调用一次 ig()。
文件末尾的 Particle / SolverConfig 是 pso() 自己的支撑定义。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Sequence

from ig import ig

# IG 触发间隔：PSO 每进化 12 代执行一次 IG
IG_INTERVAL = 12

# =========================================================================== #
# 主体：pso()
# =========================================================================== #
@dataclass
class SolverConfig:
    """PSO / IG 的全部参数（以固定时间作为终止条件，对齐老师论文标准）。"""

    time_factor: float = 0.01  # 论文时间系数 t（Carlier 96算例标准为 0.01，短时间为 0.006）
    time_limit_sec: float | None = None  # 可手动指定秒数，若为 None 则按公式自动计算
    population_size: int = 40
    w_max: float = 0.9
    w_min: float = 0.4
    c1: float = 1.5
    c2: float = 1.5
    mutation_probability: float = 0.1
    ig_interval: int = IG_INTERVAL
    ig_iterations: int = 20
    destruction_ratio: float = 0.3
    cooling_rate: float = 0.95
    seed: int | None = 20260326

    def get_time_limit_sec(self, n_jobs: int, n_stages: int) -> float:
        """根据老师论文公式计算固定运行时间上限（秒）：
        Time Limit = t * (mu^3) * sigma (毫秒)
        """
        if self.time_limit_sec is not None and self.time_limit_sec > 0:
            return self.time_limit_sec
        return (self.time_factor * (n_jobs ** 3) * n_stages) / 1000.0


@dataclass
class Particle:
    """粒子：位置（工件排列）+ 速度（交换序列）+ 个体最优。"""

    position: list[int]
    velocity: list[tuple[int, int]] = field(default_factory=list)
    evaluation: Any = None
    best_position: list[int] = field(default_factory=list)
    best_evaluation: Any = None

    @classmethod
    def create(cls, evaluation: Any) -> "Particle":
        position = list(evaluation.permutation)
        return cls(
            position=position[:],
            evaluation=evaluation,
            best_position=position[:],
            best_evaluation=evaluation,
        )

    @property
    def makespan(self) -> int:
        return self.evaluation.makespan

    @property
    def best_makespan(self) -> int:
        return self.best_evaluation.makespan


# =========================================================================== #
# 主体：pso()
# =========================================================================== #
def pso(
    env: Any,
    config: SolverConfig,
    rng: random.Random,
) -> tuple[Any, list[Any]]:
    """离散粒子群 + IG 局部搜索（以固定 CPU 运行时间作为终止条件）。

    终止条件严格参考老师论文公式：t * (mu^3) * sigma (毫秒)。
    """
    import time

    time_limit_sec = config.get_time_limit_sec(env.n_jobs, env.n_stages)
    start_time = time.perf_counter()

    def swap_sequence(source: Sequence[int], target: Sequence[int]) -> list[tuple[int, int]]:
        """把 source 变成 target 所需的交换序列。"""
        working = list(source)
        index_of = {job: index for index, job in enumerate(working)}
        swaps: list[tuple[int, int]] = []
        for index, job in enumerate(target):
            if working[index] == job:
                continue
            swap_index = index_of[job]
            swaps.append((index, swap_index))
            other = working[index]
            working[index], working[swap_index] = working[swap_index], working[index]
            index_of[job] = index
            index_of[other] = swap_index
        return swaps

    def sample(swaps: Sequence[tuple[int, int]], coefficient: float) -> list[tuple[int, int]]:
        """按学习因子随机抽取一部分交换，体现认知/社会分量的随机性。"""
        if not swaps:
            return []
        count = max(
            1,
            min(len(swaps), math.ceil(rng.random() * coefficient * len(swaps) / 2.0)),
        )
        if count >= len(swaps):
            return list(swaps)
        return rng.sample(list(swaps), count)

    def apply_swaps(position: Sequence[int], swaps: Sequence[tuple[int, int]]) -> list[int]:
        candidate = list(position)
        for left, right in swaps:
            candidate[left], candidate[right] = candidate[right], candidate[left]
        return candidate

    def mutate(position: Sequence[int]) -> list[int]:
        candidate = list(position)
        left, right = rng.sample(range(len(candidate)), 2)
        candidate[left], candidate[right] = candidate[right], candidate[left]
        return candidate

    # ---- 初始化：NEH+SPT、NEH+LPT 各 1 个，其余随机 ----
    candidates: dict[tuple[int, ...], Any] = {}

    def evaluate(permutation: Sequence[int]) -> Any:
        evaluation = env.decode_and_evaluate(permutation)
        candidates[evaluation.permutation] = evaluation
        return evaluation

    population: list[Particle] = [
        Particle.create(evaluate(env.neh_spt_heuristic().permutation))
    ]
    if config.population_size > 1:
        population.append(
            Particle.create(evaluate(env.neh_lpt_heuristic().permutation))
        )
    while len(population) < config.population_size:
        population.append(
            Particle.create(evaluate(env.generate_initial_solution("random", rng=rng)))
        )

    global_best = min(population, key=lambda particle: particle.best_makespan).best_evaluation

    # ---- 进化：基于固定运行时间的 while 循环 ----
    generation = 0
    while (time.perf_counter() - start_time) < time_limit_sec:
        generation += 1
        elapsed = time.perf_counter() - start_time
        time_ratio = min(1.0, elapsed / max(1e-6, time_limit_sec))
        weight = config.w_max - (config.w_max - config.w_min) * time_ratio

        for particle in population:
            # 速度更新：惯性 + 认知 + 社会
            velocity = [swap for swap in particle.velocity if rng.random() < weight]
            velocity += sample(swap_sequence(particle.position, particle.best_position), config.c1)
            velocity += sample(swap_sequence(particle.position, global_best.permutation), config.c2)
            deduplicated: list[tuple[int, int]] = []
            seen: set[tuple[int, int]] = set()
            for swap in velocity:
                if swap[0] != swap[1] and swap not in seen:
                    seen.add(swap)
                    deduplicated.append(swap)
            particle.velocity = deduplicated[: len(particle.position)]

            # 位置更新：施加速度 + 随机变异
            candidate_position = apply_swaps(particle.position, particle.velocity)
            if rng.random() < config.mutation_probability:
                candidate_position = mutate(candidate_position)

            evaluation = evaluate(candidate_position)
            particle.position = list(evaluation.permutation)
            particle.evaluation = evaluation
            if evaluation.makespan < particle.best_makespan:
                particle.best_position = list(evaluation.permutation)
                particle.best_evaluation = evaluation

        # 更新全局最优
        generation_best = min(
            population, key=lambda particle: particle.best_makespan
        ).best_evaluation
        if generation_best.makespan < global_best.makespan:
            global_best = generation_best
            candidates[global_best.permutation] = global_best

        # ---- 每 ig_interval 代执行一次 IG ----
        if generation % config.ig_interval == 0:
            refined = ig(global_best.permutation, env, config, rng)
            candidates[refined.permutation] = refined
            if refined.makespan < global_best.makespan:
                global_best = refined
                worst = max(population, key=lambda particle: particle.makespan)
                worst.position = list(refined.permutation)
                worst.evaluation = refined
                worst.best_position = list(refined.permutation)
                worst.best_evaluation = refined

    return global_best, list(candidates.values())
