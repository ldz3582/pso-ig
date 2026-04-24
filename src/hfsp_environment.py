from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class Job:
    job_id: int
    processing_times: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Machine:
    stage_id: int
    machine_id: int


@dataclass(frozen=True)
class Operation:
    job_id: int
    stage_id: int
    machine_id: int
    start_time: int
    end_time: int
    processing_time: int


@dataclass(frozen=True)
class ScheduleEvaluation:
    permutation: tuple[int, ...]
    makespan: int
    completion_times: tuple[int, ...]
    machine_assignments: tuple[tuple[int, ...], ...]
    operations: tuple[Operation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "permutation": list(self.permutation),
            "makespan": self.makespan,
            "completion_times": list(self.completion_times),
            "machine_assignments": [list(row) for row in self.machine_assignments],
            "operations": [asdict(operation) for operation in self.operations],
        }


class HFSPEnvironment:
    def __init__(
        self,
        name: str,
        n_jobs: int,
        n_stages: int,
        machines_per_stage: Sequence[int],
        processing_times: Sequence[Sequence[Sequence[int]]],
    ) -> None:
        self.name = name
        self.n_jobs = int(n_jobs)
        self.n_stages = int(n_stages)
        self.machines_per_stage = tuple(int(value) for value in machines_per_stage)
        self.processing_times = tuple(
            tuple(tuple(int(machine_time) for machine_time in stage) for stage in job)
            for job in processing_times
        )

        if len(self.processing_times) != self.n_jobs:
            raise ValueError("processing_times 与 n_jobs 不匹配")
        if len(self.machines_per_stage) != self.n_stages:
            raise ValueError("machines_per_stage 与 n_stages 不匹配")

        for job_index, job in enumerate(self.processing_times):
            if len(job) != self.n_stages:
                raise ValueError(f"工件 {job_index} 的阶段数量与 n_stages 不匹配")
            for stage_index, stage_times in enumerate(job):
                expected_machine_count = self.machines_per_stage[stage_index]
                if len(stage_times) != expected_machine_count:
                    raise ValueError(
                        f"工件 {job_index} 在阶段 {stage_index} 的机器数应为 {expected_machine_count}"
                    )

        self.jobs = tuple(
            Job(job_id=job_id, processing_times=self.processing_times[job_id])
            for job_id in range(self.n_jobs)
        )
        self.machines = tuple(
            Machine(stage_id=stage_id, machine_id=machine_id)
            for stage_id, machine_count in enumerate(self.machines_per_stage)
            for machine_id in range(machine_count)
        )
        self._evaluation_cache: dict[tuple[int, ...], ScheduleEvaluation] = {}

    @property
    def total_machines(self) -> int:
        return sum(self.machines_per_stage)

    @property
    def total_operations(self) -> int:
        return self.n_jobs * self.n_stages

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_jobs": self.n_jobs,
            "n_stages": self.n_stages,
            "machines_per_stage": list(self.machines_per_stage),
            "total_machines": self.total_machines,
            "total_operations": self.total_operations,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HFSPEnvironment":
        return cls(
            name=payload.get("name", "hfsp_instance"),
            n_jobs=payload["n_jobs"],
            n_stages=payload["n_stages"],
            machines_per_stage=payload["machines_per_stage"],
            processing_times=payload["processing_times"],
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "HFSPEnvironment":
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls.from_dict(payload)

    def _validate_permutation(self, permutation: Sequence[int]) -> tuple[int, ...]:
        canonical = tuple(int(job_id) for job_id in permutation)
        if len(set(canonical)) != len(canonical):
            raise ValueError("排列中存在重复工件")
        if any(job_id < 0 or job_id >= self.n_jobs for job_id in canonical):
            raise ValueError("排列中的工件编号越界")
        return canonical

    def decode_and_evaluate(self, permutation: Sequence[int]) -> ScheduleEvaluation:
        permutation_key = self._validate_permutation(permutation)
        cached = self._evaluation_cache.get(permutation_key)
        if cached is not None:
            return cached

        machine_ready_times = [
            [0 for _ in range(machine_count)] for machine_count in self.machines_per_stage
        ]
        completion_times = [0 for _ in range(self.n_jobs)]
        machine_assignments = [
            [-1 for _ in range(self.n_stages)] for _ in range(self.n_jobs)
        ]
        operations: list[Operation] = []

        for stage_id in range(self.n_stages):
            stage_completion_times = completion_times[:]
            for job_id in permutation_key:
                job_release_time = completion_times[job_id]
                best_machine = 0
                best_start = 0
                best_finish: int | None = None

                for machine_id in range(self.machines_per_stage[stage_id]):
                    processing_time = self.processing_times[job_id][stage_id][machine_id]
                    start_time = max(
                        job_release_time, machine_ready_times[stage_id][machine_id]
                    )
                    finish_time = start_time + processing_time
                    if (
                        best_finish is None
                        or finish_time < best_finish
                        or (
                            finish_time == best_finish
                            and machine_ready_times[stage_id][machine_id]
                            < machine_ready_times[stage_id][best_machine]
                        )
                    ):
                        best_machine = machine_id
                        best_start = start_time
                        best_finish = finish_time

                if best_finish is None:
                    raise RuntimeError("无法为工件分配机器")

                processing_time = self.processing_times[job_id][stage_id][best_machine]
                machine_ready_times[stage_id][best_machine] = best_finish
                stage_completion_times[job_id] = best_finish
                machine_assignments[job_id][stage_id] = best_machine
                operations.append(
                    Operation(
                        job_id=job_id,
                        stage_id=stage_id,
                        machine_id=best_machine,
                        start_time=best_start,
                        end_time=best_finish,
                        processing_time=processing_time,
                    )
                )

            completion_times = stage_completion_times

        evaluation = ScheduleEvaluation(
            permutation=permutation_key,
            makespan=max(completion_times) if completion_times else 0,
            completion_times=tuple(completion_times),
            machine_assignments=tuple(tuple(row) for row in machine_assignments),
            operations=tuple(operations),
        )
        self._evaluation_cache[permutation_key] = evaluation
        return evaluation

    def evaluate(self, permutation: Sequence[int]) -> int:
        return self.decode_and_evaluate(permutation).makespan

    def _job_average_processing_time(self, job_id: int) -> float:
        return sum(
            sum(stage_times) / len(stage_times)
            for stage_times in self.processing_times[job_id]
        )

    def _best_insertion_order(self, job_order: Iterable[int]) -> ScheduleEvaluation:
        current: list[int] = []
        for job_id in job_order:
            best_permutation: list[int] | None = None
            best_makespan: int | None = None
            for position in range(len(current) + 1):
                candidate = current[:position] + [job_id] + current[position:]
                makespan = self.evaluate(candidate)
                if best_makespan is None or makespan < best_makespan:
                    best_makespan = makespan
                    best_permutation = candidate
            if best_permutation is None:
                raise RuntimeError("NEH 插入失败")
            current = best_permutation
        return self.decode_and_evaluate(current)

    def neh_heuristic(self) -> ScheduleEvaluation:
        job_order = sorted(
            range(self.n_jobs),
            key=self._job_average_processing_time,
            reverse=True,
        )
        return self._best_insertion_order(job_order)

    def spt_heuristic(self) -> ScheduleEvaluation:
        job_order = sorted(range(self.n_jobs), key=self._job_average_processing_time)
        return self.decode_and_evaluate(job_order)

    def generate_initial_solution(
        self, method: str = "neh", rng: random.Random | None = None
    ) -> list[int]:
        generator = rng or random.Random()
        method_name = method.lower()
        if method_name == "neh":
            return list(self.neh_heuristic().permutation)
        if method_name == "spt":
            return list(self.spt_heuristic().permutation)
        if method_name == "random":
            return generator.sample(list(range(self.n_jobs)), self.n_jobs)
        raise ValueError(f"不支持的初始化方法: {method}")
