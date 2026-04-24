from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

from hfsp_environment import HFSPEnvironment, ScheduleEvaluation


@dataclass
class IteratedGreedy:
    destruction_ratio: float = 0.3
    reconstruction_method: str = "greedy"
    acceptance_criterion: str = "simulated_annealing"
    max_iterations: int = 15
    cooling_rate: float = 0.95

    def _destruction(
        self, permutation: Sequence[int], rng: random.Random
    ) -> tuple[list[int], list[int]]:
        destroy_count = max(1, int(round(len(permutation) * self.destruction_ratio)))
        selected_indices = sorted(rng.sample(range(len(permutation)), destroy_count))
        selected_set = set(selected_indices)
        destroyed_jobs = [permutation[index] for index in selected_indices]
        remaining_jobs = [
            job_id for index, job_id in enumerate(permutation) if index not in selected_set
        ]
        return destroyed_jobs, remaining_jobs

    def _reconstruction(
        self,
        remaining_jobs: Sequence[int],
        destroyed_jobs: Sequence[int],
        env: HFSPEnvironment,
    ) -> list[int]:
        current = list(remaining_jobs)
        for job_id in destroyed_jobs:
            best_permutation: list[int] | None = None
            best_makespan: int | None = None
            for position in range(len(current) + 1):
                candidate = current[:position] + [job_id] + current[position:]
                makespan = env.evaluate(candidate)
                if best_makespan is None or makespan < best_makespan:
                    best_makespan = makespan
                    best_permutation = candidate
            if best_permutation is None:
                raise RuntimeError("IG 重建失败")
            current = best_permutation
        return current

    def _accept(
        self,
        current_makespan: int,
        candidate_makespan: int,
        temperature: float,
        rng: random.Random,
    ) -> bool:
        if candidate_makespan <= current_makespan:
            return True
        if self.acceptance_criterion == "non_deteriorating":
            return False
        delta = candidate_makespan - current_makespan
        return math.exp(-delta / max(temperature, 1e-6)) > rng.random()

    def optimize(
        self,
        initial_permutation: Sequence[int],
        env: HFSPEnvironment,
        seed: int | None = None,
    ) -> ScheduleEvaluation:
        rng = random.Random(seed)
        current = env.decode_and_evaluate(initial_permutation)
        best = current
        temperature = max(1.0, current.makespan * 0.1)

        for _ in range(self.max_iterations):
            destroyed_jobs, remaining_jobs = self._destruction(current.permutation, rng)
            candidate_permutation = self._reconstruction(remaining_jobs, destroyed_jobs, env)
            candidate = env.decode_and_evaluate(candidate_permutation)

            if self._accept(current.makespan, candidate.makespan, temperature, rng):
                current = candidate

            if candidate.makespan < best.makespan:
                best = candidate

            temperature *= self.cooling_rate

        return best

    def find_multimodal_solutions(
        self,
        initial_permutation: Sequence[int],
        env: HFSPEnvironment,
        n_solutions: int = 5,
        seed: int | None = None,
    ) -> list[dict[str, object]]:
        rng = random.Random(seed)
        solutions: dict[tuple[int, ...], ScheduleEvaluation] = {}
        base_permutation = list(initial_permutation)

        for _ in range(max(n_solutions * 3, 6)):
            perturbed = base_permutation[:]
            swap_count = max(1, len(perturbed) // 6)
            for _ in range(swap_count):
                left, right = rng.sample(range(len(perturbed)), 2)
                perturbed[left], perturbed[right] = perturbed[right], perturbed[left]
            optimized = self.optimize(perturbed, env, seed=rng.randint(0, 10**9))
            solutions[optimized.permutation] = optimized
            if len(solutions) >= n_solutions:
                break

        ranked = sorted(solutions.values(), key=lambda item: item.makespan)
        return [
            {
                "permutation": list(solution.permutation),
                "makespan": solution.makespan,
                "machine_assignments": [list(row) for row in solution.machine_assignments],
            }
            for solution in ranked[:n_solutions]
        ]
