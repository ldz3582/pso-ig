"""档案库引导搜索（Archive-Guided Search）。

原实现中 MultimodalArchive 只「存」不「用」：候选解跑完才入档，档案库既不参与
变异、也不参与重启，容量还被硬截断，导致多模态解集只是搜索的副产品。

本模块让档案库反过来成为**搜索的状态变量**，在每个轮次里同时做两件事：

  1. 选择种子（archive → search）：
     - 探索 explore：挑「最孤立」成员（到其他成员的最小结构距离最大），
       代表当前采样最稀疏的区域；
     - 强化 intensify：挑「接近最优」成员，在同一盆地内继续采等优解。
     孤立度用商集 Π/~ 上的结构距离度量，而不是排列的位置海明距离。

  2. 多样化游走（search → archive）：
     以种子为起点做多步「扰动 + IG」。接受准则除了 makespan 之外还看结构：
     若候选与当前游走点的等价类不同、且离起点的结构距离更大，则接受为新的
     游走点。这样可以在**等优解之间走**，而不是每次都塌回同一个局部最优。
     这一步正是把多样性写进接受准则，而不是只在事后统计。
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from hfsp_environment import HFSPEnvironment
from iterated_greedy import IteratedGreedy
from schedule_distance import ScheduleDistance, build_features, bulk_distance, schedule_signature


@dataclass
class ArchiveGuidedConfig:
    rounds: int = 40                 # 最大轮数
    ig_iterations: int = 12          # 每步 IG 迭代次数
    destruction_ratio: float = 0.35  # IG 破坏比例
    explore_ratio: float = 0.35      # 探索型扰动的工件比例
    intensify_ratio: float = 0.15    # 强化型扰动的工件比例
    stagnation_limit: int = 15       # 连续多少轮没有新增等优解就停
    walk_length: int = 3             # 每个种子最多游走几步
    diversity_acceptance: bool = True  # 接受准则是否纳入结构多样性


class ArchiveGuidedSearch:
    """把被动档案库升级为主动搜索算子。"""

    def __init__(
        self,
        env: HFSPEnvironment,
        archive: Any,
        config: ArchiveGuidedConfig | None = None,
        seed: int | None = None,
    ) -> None:
        self.env = env
        self.archive = archive
        self.config = config or ArchiveGuidedConfig()
        self.rng = random.Random(seed)
        self.ig = IteratedGreedy(
            destruction_ratio=self.config.destruction_ratio,
            max_iterations=self.config.ig_iterations,
        )

    # ------------------------------------------------------------ 结构距离
    @staticmethod
    def _structure_distance(left: dict[str, Any], right_permutation: Sequence[int],
                            right_assignments: Sequence[Sequence[int]]) -> float:
        """归一化结构距离 = 机器分配距离 + 加工顺序距离。"""
        machine_distance, sequence_distance = ScheduleDistance.distance(
            left["permutation"],
            left["machine_assignments"],
            right_permutation,
            right_assignments,
        )
        return machine_distance + sequence_distance

    def _min_distance_to_archive(self, permutation: Sequence[int],
                                 assignments: Sequence[Sequence[int]]) -> float:
        if not self.archive.solutions:
            return 1.0
        machine_stack, key_stack, sign_stack = self.archive._feature_stacks()
        machine_row, sequence_row = bulk_distance(
            build_features(permutation, assignments), machine_stack, key_stack, sign_stack
        )
        return float((machine_row + sequence_row).min())

    # ------------------------------------------------------------ 选择策略
    def _crowding(self, solution: dict[str, Any]) -> float:
        """孤立度：到其他成员的最小结构距离。越大表示周围越空旷。"""
        crowding = self.archive.crowding()
        for index, item in enumerate(self.archive.solutions):
            if item is solution:
                return float(crowding[index])
        return 1.0

    def _crowding_all(self) -> np.ndarray:
        """全部成员的孤立度（一次算完，避免 O(m²) 次标量距离调用）。"""
        return self.archive.crowding()

    def _pick_explore_seed(self) -> dict[str, Any]:
        crowding = self._crowding_all()
        if crowding.size == 0:
            return self.archive.solutions[0]
        return self.archive.solutions[int(np.argmax(crowding))]

    def _pick_intensify_seed(self) -> dict[str, Any]:
        return self.rng.choice(self.archive.equivalent_subset())

    # ------------------------------------------------------------ 扰动算子
    def _perturb(self, permutation: Sequence[int], ratio: float) -> list[int]:
        candidate = list(permutation)
        count = max(1, int(round(len(candidate) * ratio)))
        positions = sorted(self.rng.sample(range(len(candidate)), count))
        picked = [candidate[index] for index in positions]
        self.rng.shuffle(picked)
        for index, job_id in zip(positions, picked):
            candidate[index] = job_id
        if len(candidate) > 2:
            source = self.rng.randrange(len(candidate))
            job_id = candidate.pop(source)
            target = self.rng.randrange(len(candidate) + 1)
            candidate.insert(target, job_id)
        return candidate

    # ------------------------------------------------------------ 主循环
    def _walk(self, seed_item: dict[str, Any], ratio: float) -> int:
        """从一个种子出发游走若干步，把接纳的解写入档案库，返回接纳次数。"""
        origin_permutation = list(seed_item["permutation"])
        origin_assignments = [list(row) for row in seed_item["machine_assignments"]]

        current = self.ig.optimize(origin_permutation, self.env, seed=self.rng.randint(0, 10**9))
        accepted = 0
        if self.archive.add_solution(
            list(current.permutation), current.makespan,
            [list(row) for row in current.machine_assignments],
        ):
            accepted += 1

        origin_distance = self._min_distance_to_archive(origin_permutation, origin_assignments)
        for _ in range(max(0, self.config.walk_length - 1)):
            perturbed = self._perturb(current.permutation, ratio)
            candidate = self.ig.optimize(perturbed, self.env, seed=self.rng.randint(0, 10**9))

            take = candidate.makespan < current.makespan
            if not take and self.config.diversity_acceptance:
                # 结构不同的解，且离起点更远 → 接受为新的游走点，允许等质量平移
                different_class = schedule_signature(
                    candidate.permutation, candidate.machine_assignments
                ) != schedule_signature(current.permutation, current.machine_assignments)
                if different_class:
                    candidate_distance = self._min_distance_to_archive(
                        candidate.permutation, candidate.machine_assignments
                    )
                    if candidate_distance > origin_distance:
                        take = True
            if take:
                current = candidate

            if self.archive.add_solution(
                list(candidate.permutation), candidate.makespan,
                [list(row) for row in candidate.machine_assignments],
            ):
                accepted += 1
        return accepted

    def run(self) -> dict[str, float]:
        if not self.archive.solutions:
            return {"rounds": 0.0, "archive_size": 0.0}

        entry_best = self.archive.solutions[0]["makespan"]
        start_best = entry_best
        start_optimal = self._optimal_count()
        stale = 0
        rounds = 0
        improved_best_rounds = 0
        admitted_total = 0

        for round_index in range(self.config.rounds):
            if stale >= self.config.stagnation_limit:
                break
            rounds = round_index + 1
            if round_index % 2 == 0:
                seed_item = self._pick_intensify_seed()
                ratio = self.config.intensify_ratio
            else:
                seed_item = self._pick_explore_seed()
                ratio = self.config.explore_ratio

            before_optimal = self._optimal_count()
            admitted = self._walk(seed_item, ratio)
            admitted_total += admitted

            current_best = self.archive.solutions[0]["makespan"]
            if current_best < start_best:
                start_best = current_best
                improved_best_rounds += 1
                stale = 0
            elif self._optimal_count() > before_optimal:
                stale = 0
            else:
                stale += 1

        final_best = self.archive.solutions[0]["makespan"]
        final_optimal = self._optimal_count()
        return {
            "rounds": float(rounds),
            "archive_size": float(len(self.archive.solutions)),
            "best_gain": float(entry_best - final_best),
            "final_best": float(final_best),
            "optimal_count_entry": float(start_optimal),
            "optimal_count_final": float(final_optimal),
            "new_optimal_solutions": float(final_optimal - start_optimal),
            "improved_best_rounds": float(improved_best_rounds),
            "admitted_total": float(admitted_total),
        }

    def _optimal_count(self) -> int:
        if not self.archive.solutions:
            return 0
        best = self.archive.solutions[0]["makespan"]
        return sum(1 for item in self.archive.solutions if item["makespan"] <= best)

    def seed_pool(self) -> list[list[int]]:
        """供 PSO 停滞时注入多样性使用的档案排列池。"""
        return [list(item["permutation"]) for item in self.archive.solutions]
