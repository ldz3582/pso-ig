from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Sequence

from hfsp_environment import HFSPEnvironment, ScheduleEvaluation
from iterated_greedy import IteratedGreedy
from niching_mechanism import DiversityMaintainer, DistanceCalculator, NichingMechanism


@dataclass
class Particle:
    position: list[int]
    velocity: list[tuple[int, int]] = field(default_factory=list)
    evaluation: ScheduleEvaluation | None = None
    personal_best_position: list[int] = field(default_factory=list)
    personal_best_evaluation: ScheduleEvaluation | None = None

    @property
    def fitness(self) -> int:
        if self.evaluation is None:
            raise RuntimeError("粒子尚未评估")
        return self.evaluation.makespan

    @property
    def personal_best_fitness(self) -> int:
        if self.personal_best_evaluation is None:
            raise RuntimeError("粒子尚未初始化个体最优")
        return self.personal_best_evaluation.makespan

    @classmethod
    def from_evaluation(cls, evaluation: ScheduleEvaluation) -> "Particle":
        position = list(evaluation.permutation)
        return cls(
            position=position[:],
            evaluation=evaluation,
            personal_best_position=position[:],
            personal_best_evaluation=evaluation,
        )


@dataclass
class StagnationDetector:
    threshold: int
    no_improvement_count: int = 0

    def update(self, improved: bool) -> bool:
        if improved:
            self.no_improvement_count = 0
            return False
        self.no_improvement_count += 1
        return self.no_improvement_count >= self.threshold

    def reset(self) -> None:
        self.no_improvement_count = 0


class NichingPSO:
    def __init__(
        self,
        env: HFSPEnvironment,
        population_size: int = 100,
        max_generations: int = 200,
        w_max: float = 0.9,
        w_min: float = 0.4,
        c1: float = 1.5,
        c2: float = 1.5,
        k_neighbors: int = 3,
        stagnation_threshold: int = 10,
        mutation_probability: float = 0.12,
        niche_distance_threshold: int = 3,
        seed: int | None = None,
    ) -> None:
        self.env = env
        self.population_size = population_size
        self.max_generations = max_generations
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.k_neighbors = k_neighbors
        self.base_mutation_probability = mutation_probability
        self.rng = random.Random(seed)
        self.distance_calculator = DistanceCalculator()
        self.niching_mechanism = NichingMechanism(
            k_neighbors=k_neighbors,
            distance_threshold=niche_distance_threshold,
        )
        self.diversity_maintainer = DiversityMaintainer(self.distance_calculator)
        self.stagnation_detector = StagnationDetector(stagnation_threshold)
        self.ig_algorithm: IteratedGreedy | None = None
        self.multimodal_solutions: list[dict[str, object]] = []
        # 档案库引导（archive-guided）开关：pool 为档案库排列的实时引用，
        # 停滞重初始化 / 初期建群时可从中直接注入精英方案，避免纯随机重启。
        self.diversity_pool: list[list[int]] | None = None
        self.pool_seed_fraction: float = 0.3
        self.injection_probability: float = 0.5
        # 候选解缓冲：只做「排列精确去重 + 容量裁剪」，真正的结构去重与质量门限
        # 交给 MultimodalArchive 判定，避免在这里用位置距离误杀结构不同的解。
        self.multimodal_capacity: int = 200
        self._seen_positions: set[tuple[int, ...]] = set()

    def set_ig_algorithm(self, algorithm: IteratedGreedy) -> None:
        self.ig_algorithm = algorithm

    def _evaluate(self, permutation: Sequence[int]) -> ScheduleEvaluation:
        return self.env.decode_and_evaluate(permutation)

    def _compute_swap_sequence(
        self, source: Sequence[int], target: Sequence[int]
    ) -> list[tuple[int, int]]:
        working = list(source)
        index_of = {job_id: index for index, job_id in enumerate(working)}
        swaps: list[tuple[int, int]] = []

        for index, job_id in enumerate(target):
            if working[index] == job_id:
                continue
            swap_index = index_of[job_id]
            swaps.append((index, swap_index))
            other_job = working[index]
            working[index], working[swap_index] = working[swap_index], working[index]
            index_of[job_id] = index
            index_of[other_job] = swap_index

        return swaps

    def _sample_swaps(
        self, swaps: Sequence[tuple[int, int]], coefficient: float
    ) -> list[tuple[int, int]]:
        if not swaps:
            return []
        count = max(
            1,
            min(len(swaps), math.ceil(self.rng.random() * coefficient * len(swaps) / 2.0)),
        )
        if count >= len(swaps):
            return list(swaps)
        return self.rng.sample(list(swaps), count)

    def update_velocity_adaptive(
        self,
        current_position: Sequence[int],
        current_velocity: Sequence[tuple[int, int]],
        personal_best: Sequence[int],
        local_best: Sequence[int],
        weight: float,
    ) -> list[tuple[int, int]]:
        velocity: list[tuple[int, int]] = []

        for swap in current_velocity:
            if self.rng.random() < weight:
                velocity.append(swap)

        cognitive_swaps = self._compute_swap_sequence(current_position, personal_best)
        social_swaps = self._compute_swap_sequence(current_position, local_best)

        velocity.extend(self._sample_swaps(cognitive_swaps, self.c1))
        velocity.extend(self._sample_swaps(social_swaps, self.c2))

        deduplicated: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()
        for swap in velocity:
            if swap not in seen and swap[0] != swap[1]:
                seen.add(swap)
                deduplicated.append(swap)

        return deduplicated[: len(current_position)]

    def _apply_velocity(
        self, position: Sequence[int], velocity: Sequence[tuple[int, int]]
    ) -> list[int]:
        candidate = list(position)
        for left, right in velocity:
            candidate[left], candidate[right] = candidate[right], candidate[left]
        return candidate

    def _mutate(self, permutation: Sequence[int], strength: int = 1) -> list[int]:
        candidate = list(permutation)
        for _ in range(strength):
            left, right = self.rng.sample(range(len(candidate)), 2)
            candidate[left], candidate[right] = candidate[right], candidate[left]
        return candidate

    def _record_solution(self, evaluation: ScheduleEvaluation) -> None:
        """把候选解放进缓冲池（结构去重与质量门限由 MultimodalArchive 负责）。"""
        key = tuple(evaluation.permutation)
        if key in self._seen_positions:
            return
        self._seen_positions.add(key)
        self.multimodal_solutions.append(
            {
                "permutation": list(evaluation.permutation),
                "makespan": evaluation.makespan,
                "machine_assignments": [list(row) for row in evaluation.machine_assignments],
            }
        )
        self.multimodal_solutions.sort(key=lambda item: item["makespan"])
        if len(self.multimodal_solutions) > self.multimodal_capacity:
            self.multimodal_solutions = self.multimodal_solutions[: self.multimodal_capacity]

    def _initialize_population(self) -> list[Particle]:
        population: list[Particle] = []

        neh = self.env.neh_heuristic()
        population.append(Particle.from_evaluation(neh))
        self._record_solution(neh)

        spt = self.env.spt_heuristic()
        if len(population) < self.population_size:
            population.append(Particle.from_evaluation(spt))
            self._record_solution(spt)

        while len(population) < min(self.population_size, 6):
            seeded = self._mutate(neh.permutation, strength=max(1, self.env.n_jobs // 6))
            evaluation = self._evaluate(seeded)
            population.append(Particle.from_evaluation(evaluation))
            self._record_solution(evaluation)

        while len(population) < min(self.population_size, 10):
            seeded = self._mutate(spt.permutation, strength=max(1, self.env.n_jobs // 5))
            evaluation = self._evaluate(seeded)
            population.append(Particle.from_evaluation(evaluation))
            self._record_solution(evaluation)

        pool = self.diversity_pool or []
        pool_quota = min(len(pool), int(self.population_size * self.pool_seed_fraction))
        for offset in range(pool_quota):
            if len(population) >= self.population_size:
                break
            evaluation = self._evaluate(list(pool[offset]))
            population.append(Particle.from_evaluation(evaluation))
            self._record_solution(evaluation)

        while len(population) < self.population_size:
            permutation = self.env.generate_initial_solution("random", rng=self.rng)
            evaluation = self._evaluate(permutation)
            population.append(Particle.from_evaluation(evaluation))
            self._record_solution(evaluation)

        return population

    def _get_local_best(
        self,
        particle_index: int,
        population: Sequence[Particle],
        neighbors: dict[int, list[int]],
        niche_for_particle: dict[int, int],
    ) -> list[int]:
        niche_id = niche_for_particle[particle_index]
        candidate_indices = [
            index
            for index in neighbors[particle_index]
            if niche_for_particle.get(index) == niche_id
        ]
        if not candidate_indices:
            candidate_indices = neighbors[particle_index]

        best_index = min(
            candidate_indices,
            key=lambda index: population[index].personal_best_fitness,
        )
        return population[best_index].personal_best_position[:]

    def _reinitialize_worst_particles(
        self, population: list[Particle], protected_permutation: Sequence[int]
    ) -> None:
        count = max(1, math.ceil(self.population_size * 0.2))
        ranked = sorted(
            range(len(population)),
            key=lambda index: population[index].fitness,
            reverse=True,
        )
        replaced = 0
        for index in ranked:
            if replaced >= count:
                break
            if tuple(population[index].position) == tuple(protected_permutation):
                continue
            pool = self.diversity_pool or []
            if pool and self.rng.random() < self.injection_probability:
                permutation = list(self.rng.choice(pool))
            else:
                permutation = self.env.generate_initial_solution("random", rng=self.rng)
            evaluation = self._evaluate(permutation)
            population[index] = Particle.from_evaluation(evaluation)
            self._record_solution(evaluation)
            replaced += 1

    def run(self) -> tuple[int, list[int], list[dict[str, object]]]:
        population = self._initialize_population()
        global_best_particle = min(
            population, key=lambda particle: particle.personal_best_fitness
        )
        global_best_evaluation = global_best_particle.personal_best_evaluation
        if global_best_evaluation is None:
            raise RuntimeError("全局最优未初始化")

        local_search_interval = max(5, self.max_generations // 5)

        for generation in range(self.max_generations):
            weight = self.w_max - (self.w_max - self.w_min) * (
                generation / max(1, self.max_generations - 1)
            )
            neighbors = self.niching_mechanism.build_ring_neighbors(len(population))
            _, niche_for_particle = self.niching_mechanism.cluster_positions(
                [particle.position for particle in population]
            )
            diversity = self.diversity_maintainer.population_diversity(
                [particle.position for particle in population]
            )
            mutation_probability = max(
                self.base_mutation_probability,
                self.diversity_maintainer.mutation_probability(
                    diversity, self.stagnation_detector.no_improvement_count
                ),
            )

            generation_improved = False

            for index, particle in enumerate(population):
                local_best = self._get_local_best(
                    index, population, neighbors, niche_for_particle
                )
                particle.velocity = self.update_velocity_adaptive(
                    current_position=particle.position,
                    current_velocity=particle.velocity,
                    personal_best=particle.personal_best_position,
                    local_best=local_best,
                    weight=weight,
                )
                candidate_position = self._apply_velocity(particle.position, particle.velocity)

                if self.rng.random() < mutation_probability:
                    candidate_position = self._mutate(
                        candidate_position,
                        strength=max(1, self.env.n_jobs // 8),
                    )

                candidate_evaluation = self._evaluate(candidate_position)
                particle.position = list(candidate_evaluation.permutation)
                particle.evaluation = candidate_evaluation
                self._record_solution(candidate_evaluation)

                if candidate_evaluation.makespan < particle.personal_best_fitness:
                    particle.personal_best_position = list(candidate_evaluation.permutation)
                    particle.personal_best_evaluation = candidate_evaluation

            current_best_particle = min(
                population, key=lambda particle: particle.personal_best_fitness
            )
            current_best_evaluation = current_best_particle.personal_best_evaluation
            if current_best_evaluation is None:
                raise RuntimeError("当前最优未初始化")

            if current_best_evaluation.makespan < global_best_evaluation.makespan:
                global_best_evaluation = current_best_evaluation
                generation_improved = True
                self._record_solution(global_best_evaluation)

            if (
                self.ig_algorithm is not None
                and (generation + 1) % local_search_interval == 0
            ):
                refined = self.ig_algorithm.optimize(
                    global_best_evaluation.permutation,
                    self.env,
                    seed=self.rng.randint(0, 10**9),
                )
                self._record_solution(refined)
                if refined.makespan < global_best_evaluation.makespan:
                    global_best_evaluation = refined
                    generation_improved = True

                    worst_index = max(
                        range(len(population)),
                        key=lambda idx: population[idx].fitness,
                    )
                    population[worst_index] = Particle.from_evaluation(refined)

            if self.stagnation_detector.update(generation_improved):
                self._reinitialize_worst_particles(
                    population, protected_permutation=global_best_evaluation.permutation
                )
                self.stagnation_detector.reset()

        return (
            global_best_evaluation.makespan,
            list(global_best_evaluation.permutation),
            self.multimodal_solutions[:],
        )
