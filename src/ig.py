"""ig.py —— 迭代贪婪局部搜索（IG）。

主体是 ig()：破坏 → 重构 → 模拟退火接受准则。
"""
from __future__ import annotations

import math
import random
from typing import Any, Sequence


def ig(
    permutation: Sequence[int],
    env: Any,
    config: Any,
    rng: random.Random,
) -> Any:
    """迭代贪婪局部搜索。

    每一轮：
    1. 破坏：随机摘除一定比例的工件；
    2. 重构：逐个把被摘工件按最优插入位置放回（复用 env.best_insertion）；
    3. 模拟退火：劣解以 exp(-Δ/T) 的概率接受，温度按冷却率下降。
    """
    current = env.decode_and_evaluate(permutation)
    best = current
    temperature = max(1.0, current.makespan * 0.1)
    destroy_count = max(1, int(round(env.n_jobs * config.destruction_ratio)))

    for _ in range(config.ig_iterations):
        # 破坏
        removed_indices = set(rng.sample(range(env.n_jobs), destroy_count))
        destroyed = [
            job for index, job in enumerate(current.permutation) if index in removed_indices
        ]
        remaining = [
            job for index, job in enumerate(current.permutation) if index not in removed_indices
        ]

        # 重构：最优插入（与 NEH 共用 env.best_insertion）
        for job in destroyed:
            remaining = env.best_insertion(remaining, job)

        candidate = env.decode_and_evaluate(remaining)

        # 模拟退火接受准则
        if candidate.makespan <= current.makespan:
            current = candidate
        else:
            delta = candidate.makespan - current.makespan
            if rng.random() < math.exp(-delta / max(temperature, 1e-6)):
                current = candidate

        if candidate.makespan < best.makespan:
            best = candidate
        temperature *= config.cooling_rate

    return best
