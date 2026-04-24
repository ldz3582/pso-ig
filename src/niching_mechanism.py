from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence


class DistanceCalculator:
    @staticmethod
    def permutation_distance(
        left: Sequence[int] | tuple[int, ...], right: Sequence[int] | tuple[int, ...]
    ) -> int:
        if len(left) != len(right):
            raise ValueError("排列长度不一致")
        return sum(1 for lhs, rhs in zip(left, right) if lhs != rhs)

    @staticmethod
    def machine_assignment_distance(
        left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]
    ) -> int:
        if len(left) != len(right):
            raise ValueError("机器分配长度不一致")
        distance = 0
        for left_row, right_row in zip(left, right):
            if len(left_row) != len(right_row):
                raise ValueError("机器分配阶段长度不一致")
            distance += sum(1 for lhs, rhs in zip(left_row, right_row) if lhs != rhs)
        return distance


@dataclass
class NichingMechanism:
    k_neighbors: int
    distance_threshold: int

    def build_ring_neighbors(self, population_size: int) -> dict[int, list[int]]:
        if population_size <= 0:
            return {}
        neighbors: dict[int, list[int]] = {}
        for index in range(population_size):
            ring = []
            for offset in range(-self.k_neighbors, self.k_neighbors + 1):
                ring.append((index + offset) % population_size)
            neighbors[index] = sorted(set(ring))
        return neighbors

    def cluster_positions(
        self, positions: Iterable[Sequence[int]]
    ) -> tuple[dict[int, list[int]], dict[int, int]]:
        niches: dict[int, list[int]] = {}
        niche_for_particle: dict[int, int] = {}
        seeds: dict[int, Sequence[int]] = {}

        for particle_index, position in enumerate(positions):
            niche_id = None
            for existing_niche_id, seed in seeds.items():
                distance = DistanceCalculator.permutation_distance(position, seed)
                if distance <= self.distance_threshold:
                    niche_id = existing_niche_id
                    break
            if niche_id is None:
                niche_id = len(niches)
                niches[niche_id] = []
                seeds[niche_id] = tuple(position)
            niches[niche_id].append(particle_index)
            niche_for_particle[particle_index] = niche_id

        return niches, niche_for_particle


class DiversityMaintainer:
    def __init__(self, distance_calculator: DistanceCalculator | None = None) -> None:
        self.distance_calculator = distance_calculator or DistanceCalculator()

    def population_diversity(self, positions: Sequence[Sequence[int]]) -> float:
        if len(positions) < 2:
            return 1.0
        distances = [
            self.distance_calculator.permutation_distance(left, right) / len(left)
            for left, right in combinations(positions, 2)
        ]
        return sum(distances) / len(distances)

    def mutation_probability(self, diversity: float, stagnation_level: int) -> float:
        base = 0.08
        diversity_boost = max(0.0, 0.25 - diversity) * 0.8
        stagnation_boost = min(0.2, stagnation_level * 0.02)
        return min(0.45, base + diversity_boost + stagnation_boost)
