"""调度空间（商集）上的结构距离。

问题：工件排列 π 与调度方案不是一一对应。多个不同排列经解码后可能得到
完全相同的调度（每个阶段、每台机器上的工件加工顺序一致），这类排列构成
一个**结构等价类**。设解码映射 D: Π → S，则等价关系为

    π₁ ~ π₂  ⟺  D(π₁) = D(π₂)

真正要搜索、要统计、要比较的对象是**商集 Π/~**（即调度空间 S），而不是 Π。

排列空间上的位置海明距离（逐位比较）有两个已知缺陷：
  1. 相邻交换（结构几乎没变）会得到距离 1，误导为"差异很大"；
  2. 结构差异极大的两个解，也可能只在少数几个位置不同。

因此本模块在商集上定义距离，分两个正交分量：

  assignment_distance  机器分配差异：分配到不同机器的 (工件, 阶段) 对占比；
  sequence_distance    加工顺序差异：在两解中位于同一台机器上的工件对，
                       其相对先后顺序发生翻转的比例（Kendall tau 型）。

两者都归一化到 [0, 1]，与算例规模无关，可直接作为阈值使用。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

Signature = tuple[tuple[tuple[int, int], tuple[int, ...]], ...]


def schedule_signature(
    permutation: Sequence[int],
    machine_assignments: Sequence[Sequence[int]],
) -> Signature:
    """返回调度方案的结构签名 = 各 (阶段, 机器) 上按加工顺序排列的工件表。

    解码器在每个阶段按排列顺序派工，因此同一台机器上的工件必然保持排列中的
    相对顺序。于是签名可以直接由「排列 + 机器分配」重建，无需重新解码：

        signature = { (stage, machine): [jobs in permutation order] }

    两个解签名相同 ⟺ 它们属于同一个结构等价类 ⟺ 是同一个调度方案。
    """
    n_jobs = len(permutation)
    if n_jobs == 0:
        return ()
    n_stages = len(machine_assignments[0])
    buckets: dict[tuple[int, int], list[int]] = {}
    for job in permutation:
        for stage in range(n_stages):
            buckets.setdefault((stage, int(machine_assignments[job][stage])), []).append(job)
    return tuple(sorted((key, tuple(jobs)) for key, jobs in buckets.items()))


class ScheduleDistance:
    """商集 Π/~（调度空间）上的归一化距离。"""

    @staticmethod
    def assignment_distance(
        permutation_a: Sequence[int],
        assignments_a: Sequence[Sequence[int]],
        permutation_b: Sequence[int],
        assignments_b: Sequence[Sequence[int]],
    ) -> float:
        """机器分配差异：分配到不同机器的 (工件, 阶段) 对占全部的比例。"""
        n_stages = len(assignments_a[0]) if len(assignments_a) else 0
        if len(permutation_a) == 0 or n_stages == 0:
            return 0.0
        different = 0
        for job in permutation_a:
            row_a, row_b = assignments_a[job], assignments_b[job]
            for stage in range(n_stages):
                if row_a[stage] != row_b[stage]:
                    different += 1
        return different / (len(permutation_a) * n_stages)

    @staticmethod
    def sequence_distance(
        permutation_a: Sequence[int],
        assignments_a: Sequence[Sequence[int]],
        permutation_b: Sequence[int],
        assignments_b: Sequence[Sequence[int]],
    ) -> float:
        """加工顺序差异：可比工件对中，先后顺序发生翻转的比例。

        只统计在两解中「同一阶段被分到同一台机器」的工件对——不同机器上的
        工件之间不存在先后关系，把它们算进差异会虚增距离。
        """
        n_stages = len(assignments_a[0]) if len(assignments_a) else 0
        if len(permutation_a) == 0 or n_stages == 0:
            return 0.0

        position_b = {job: index for index, job in enumerate(permutation_b)}
        discordant = 0
        comparable = 0
        for stage in range(n_stages):
            groups: dict[int, list[int]] = {}
            for job in permutation_a:
                machine = int(assignments_a[job][stage])
                if int(assignments_b[job][stage]) == machine:
                    groups.setdefault(machine, []).append(job)
            for jobs in groups.values():
                if len(jobs) < 2:
                    continue
                for left in range(len(jobs)):
                    for right in range(left + 1, len(jobs)):
                        comparable += 1
                        if position_b[jobs[left]] > position_b[jobs[right]]:
                            discordant += 1
        return discordant / comparable if comparable else 0.0

    @classmethod
    def distance(
        cls,
        permutation_a: Sequence[int],
        assignments_a: Sequence[Sequence[int]],
        permutation_b: Sequence[int],
        assignments_b: Sequence[Sequence[int]],
    ) -> tuple[float, float]:
        """返回 (机器分配距离, 加工顺序距离)，两者均已归一化。"""
        return (
            cls.assignment_distance(permutation_a, assignments_a, permutation_b, assignments_b),
            cls.sequence_distance(permutation_a, assignments_a, permutation_b, assignments_b),
        )


# --------------------------------------------------------------------------- #
# 批量（向量化）距离计算
#
# 上面 scalar 版本的复杂度瓶颈在 sequence_distance：它是 O(n_stages · n_jobs²)
# 的纯 Python 三重循环。当引导搜索需要「一个解 vs 档案库全部成员」或「成员两两
# 之间」的距离时，调用次数本身就是 O(m) / O(m²)，两层相乘会把单个算例拖到几十分钟。
#
# 这里把调度编译成紧凑数组，用 numpy 一次算完整行/整块矩阵。数学定义与 scalar
# 版本完全一致（见 test_schedule_distance_bulk.py 的等价性断言）。
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ScheduleFeatures:
    """调度的紧凑表示，供批量距离使用。

    machines  (n_jobs, n_stages) 各工件各阶段所在机器号；
    pair_key  (P, n_stages)      工件对 (a<b) 在同一机器则为该机器号，否则 -1；
    pair_sign (P, n_stages)      该工件对在排列中的先后（+1: a 在 b 之前）。
    """

    machines: "np.ndarray"
    pair_key: "np.ndarray"
    pair_sign: "np.ndarray"
    n_jobs: int
    n_stages: int


def build_features(
    permutation: Sequence[int],
    machine_assignments: Sequence[Sequence[int]],
) -> ScheduleFeatures:
    """把 (排列, 机器分配) 编译成 ScheduleFeatures。"""
    machines = np.asarray(machine_assignments, dtype=np.int32)
    n_jobs = int(machines.shape[0])
    n_stages = int(machines.shape[1]) if machines.ndim == 2 else 0
    if n_jobs < 2 or n_stages == 0:
        empty_pairs = np.zeros((0, max(n_stages, 0)), dtype=np.int32)
        return ScheduleFeatures(machines, empty_pairs, np.zeros((0, max(n_stages, 0)), dtype=np.int8),
                                n_jobs, n_stages)

    position = np.empty(n_jobs, dtype=np.int64)
    position[np.asarray(permutation, dtype=np.int64)] = np.arange(n_jobs)

    left, right = np.triu_indices(n_jobs, 1)
    same_machine = machines[left] == machines[right]
    pair_key = np.where(same_machine, machines[left], np.int32(-1)).astype(np.int32)
    order = (position[left] < position[right]).astype(np.int8) * 2 - 1
    pair_sign = np.repeat(order[:, None], n_stages, axis=1).astype(np.int8)
    return ScheduleFeatures(machines, pair_key, pair_sign, n_jobs, n_stages)


def stack_features(features_list: Sequence[ScheduleFeatures]):
    """把若干 ScheduleFeatures 堆成 (m, ...) 数组。"""
    if not features_list:
        return (np.zeros((0, 0, 0), dtype=np.int32),
                np.zeros((0, 0, 0), dtype=np.int32),
                np.zeros((0, 0, 0), dtype=np.int8))
    return (
        np.stack([item.machines for item in features_list]),
        np.stack([item.pair_key for item in features_list]),
        np.stack([item.pair_sign for item in features_list]),
    )


def bulk_distance(
    features: ScheduleFeatures,
    machine_stack: "np.ndarray",
    key_stack: "np.ndarray",
    sign_stack: "np.ndarray",
) -> tuple["np.ndarray", "np.ndarray"]:
    """一个调度 vs 一批调度：返回 (机器分配距离数组, 加工顺序距离数组)。"""
    count = int(machine_stack.shape[0])
    if count == 0:
        return np.zeros(0, dtype=np.float64), np.zeros(0, dtype=np.float64)

    cells = features.n_jobs * features.n_stages
    if cells == 0:
        return np.zeros(count, dtype=np.float64), np.zeros(count, dtype=np.float64)

    machine_distance = (machine_stack != features.machines[None, :, :]).sum(axis=(1, 2)) / cells

    if features.pair_key.size == 0:
        return machine_distance.astype(np.float64), np.zeros(count, dtype=np.float64)

    key_self = features.pair_key[None, :, :]
    comparable = (key_stack == key_self) & (key_self >= 0)
    discordant = comparable & (sign_stack != features.pair_sign[None, :, :])
    counts = comparable.sum(axis=(1, 2))
    discord = discordant.sum(axis=(1, 2))
    sequence_distance = np.divide(
        discord, counts, out=np.zeros(count, dtype=np.float64), where=counts > 0
    )
    return machine_distance.astype(np.float64), sequence_distance


def pairwise_matrices(
    features_list: Sequence[ScheduleFeatures], block: int = 32
) -> tuple["np.ndarray", "np.ndarray"]:
    """成员两两之间的完整距离矩阵 (machine_distance, sequence_distance)。"""
    count = len(features_list)
    machine_matrix = np.zeros((count, count), dtype=np.float64)
    sequence_matrix = np.zeros((count, count), dtype=np.float64)
    if count < 2:
        return machine_matrix, sequence_matrix
    machine_stack, key_stack, sign_stack = stack_features(features_list)
    for start in range(0, count, block):
        stop = min(count, start + block)
        machine_matrix[start:stop] = (
            machine_stack[start:stop, None, :, :] != machine_stack[None, :, :, :]
        ).sum(axis=(2, 3)) / max(1, features_list[0].n_jobs * features_list[0].n_stages)
        if features_list[0].pair_key.size:
            key_left = key_stack[start:stop, None, :, :]
            comparable = (key_left == key_stack[None, :, :, :]) & (key_left >= 0)
            discordant = comparable & (sign_stack[start:stop, None, :, :] != sign_stack[None, :, :, :])
            counts = comparable.sum(axis=(2, 3))
            discord = discordant.sum(axis=(2, 3))
            sequence_matrix[start:stop] = np.divide(
                discord, counts, out=np.zeros_like(machine_matrix[start:stop]), where=counts > 0
            )
    return machine_matrix, sequence_matrix


def crowding_vector(features_list: Sequence[ScheduleFeatures]) -> "np.ndarray":
    """每个成员到其余成员的最小结构距离（机器分配 + 加工顺序）。越大越孤立。"""
    count = len(features_list)
    if count < 2:
        return np.ones(count, dtype=np.float64)
    machine_matrix, sequence_matrix = pairwise_matrices(features_list)
    total = machine_matrix + sequence_matrix
    np.fill_diagonal(total, np.inf)
    return total.min(axis=1)
