from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

# ==============================================================================
# 第一部分：基础数据结构（清晰记录工件、机器、工序、以及最终排产报告）
# ==============================================================================

@dataclass(frozen=True)
class Job:
    """单个工件的信息。
    
    通俗理解：流水线上待加工的一个产品（如一辆车）。
    - job_id: 工件编号（从 0 开始）
    - processing_times: 三维元组，表示该工件在 [阶段][机器] 上的加工耗时
    """
    job_id: int
    processing_times: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Machine:
    """单台机器的标识。
    
    通俗理解：车间里的某一台机床。
    - stage_id: 机器所在的工序阶段（如 0 代表冲压，1 代表焊接）
    - machine_id: 该阶段内部的机器编号（0 号机、1 号机...）
    """
    stage_id: int
    machine_id: int


@dataclass(frozen=True)
class Operation:
    """一道具体执行完成的工序记录（可直接用于绘制甘特图）。
    
    - job_id: 哪个工件
    - stage_id: 哪个工序阶段
    - machine_id: 在哪台机器上加工
    - start_time: 开始加工的时间刻度
    - end_time: 加工完成的时间刻度
    - processing_time: 实际耗时
    """
    job_id: int
    stage_id: int
    machine_id: int
    start_time: int
    end_time: int
    processing_time: int


@dataclass(frozen=True)
class ScheduleEvaluation:
    """【核心输出】排程结果综合评估报告。
    
    当算法排好一个工件加工顺序后，解码器会输出这份完整报告：
    - permutation: 输入的工件加工次序，如 (2, 0, 1) 表示先加工工件2，再0，再1
    - makespan: 【最关键优化指标】整个车间彻底做完的最终完工时间（目标：越小越好）
    - completion_times: 每个工件最终出厂时的完成时间
    - machine_assignments: 每个工件在每个阶段分别进了哪台机器
    - operations: 每一道具体工序的时间表清单
    """
    permutation: tuple[int, ...]
    makespan: int
    completion_times: tuple[int, ...]
    machine_assignments: tuple[tuple[int, ...], ...]
    operations: tuple[Operation, ...]

    def to_dict(self) -> dict[str, Any]:
        """转换成标准字典，方便查看或保存为 JSON 文件。"""
        return {
            "permutation": list(self.permutation),
            "makespan": self.makespan,
            "completion_times": list(self.completion_times),
            "machine_assignments": [list(row) for row in self.machine_assignments],
            "operations": [asdict(operation) for operation in self.operations],
        }


# ==============================================================================
# 第二部分：HFSP 车间仿真环境类（包含车间建模、核心解码算法与启发式基准）
# ==============================================================================

class HFSPEnvironment:
    """混合流水车间（HFSP）环境模拟器。
    
    车间物理规则：
    1. 车间由多个连续【阶段】组成（冲压 -> 焊接 -> 喷漆...），工件必须按阶段顺序加工。
    2. 每个阶段有若干台【平行机器】，任选一台空闲的就能加工。
    3. 同一时间，一台机器只能做一个工件，一个工件也只能在一台机器上做。
    """

    def __init__(
        self,
        name: str,
        n_jobs: int,
        n_stages: int,
        machines_per_stage: Sequence[int],
        processing_times: Sequence[Sequence[Sequence[int]]],
    ) -> None:
        """初始化车间参数并校验数据完整性。"""
        self.name = name
        self.n_jobs = int(n_jobs)                     # 工件总数
        self.n_stages = int(n_stages)                 # 阶段总数
        self.machines_per_stage = tuple(int(value) for value in machines_per_stage)  # 每阶段机器数
        
        # 规整化加工时间为元组：[工件][阶段][机器] = 耗时
        self.processing_times = tuple(
            tuple(tuple(int(machine_time) for machine_time in stage) for stage in job)
            for job in processing_times
        )

        # 基础数据安全校验
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
        # 结果缓存字典：算过的排列直接返回，避免重复计算
        self._evaluation_cache: dict[tuple[int, ...], ScheduleEvaluation] = {}

    @property
    def total_machines(self) -> int:
        """车间所有机器总数。"""
        return sum(self.machines_per_stage)

    @property
    def total_operations(self) -> int:
        """所有工序总数（每个工件都要经过每个阶段）。"""
        return self.n_jobs * self.n_stages

    def metadata(self) -> dict[str, Any]:
        """车间概况元数据。"""
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
        """从字典构建环境对象。"""
        return cls(
            name=payload.get("name", "hfsp_instance"),
            n_jobs=payload["n_jobs"],
            n_stages=payload["n_stages"],
            machines_per_stage=payload["machines_per_stage"],
            processing_times=payload["processing_times"],
        )

    @classmethod
    def from_txt(cls, path: str | Path) -> "HFSPEnvironment":
        """从 Carlier 原始文本格式（.txt）解析并构建车间环境。"""
        file_path = Path(path)
        tokens = file_path.read_text(encoding="utf-8").split()
        if not tokens:
            raise ValueError(f"文件 {file_path} 内容为空")
        cursor = 0
        n_jobs = int(tokens[cursor]); cursor += 1
        n_stages = int(tokens[cursor]); cursor += 1
        machines_per_stage = [int(tokens[cursor + i]) for i in range(n_stages)]
        cursor += n_stages
        stage_times: list[list[int]] = []
        for _ in range(n_stages):
            stage_times.append([int(tokens[cursor + j]) for j in range(n_jobs)])
            cursor += n_jobs
        processing_times = [
            [
                [stage_times[stage][job] for _ in range(machines_per_stage[stage])]
                for stage in range(n_stages)
            ]
            for job in range(n_jobs)
        ]
        return cls(
            name=file_path.stem,
            n_jobs=n_jobs,
            n_stages=n_stages,
            machines_per_stage=machines_per_stage,
            processing_times=processing_times,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "HFSPEnvironment":
        """从文件中加载环境。自动识别 .txt 文本算例或 .json 格式算例，杜绝解析崩溃。"""
        file_path = Path(path)
        # 如果文件后缀是 .txt，直接按 txt 格式解析
        if file_path.suffix.lower() == ".txt":
            return cls.from_txt(file_path)
        # 否则尝试 JSON 解析，失败时自动尝试 txt 容错解析
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return cls.from_dict(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return cls.from_txt(file_path)

    def _validate_permutation(self, permutation: Sequence[int]) -> tuple[int, ...]:
        """检查工件排列合法性（无重复、不越界）。"""
        canonical = tuple(int(job_id) for job_id in permutation)
        if len(set(canonical)) != len(canonical):
            raise ValueError("排列中存在重复工件")
        if any(job_id < 0 or job_id >= self.n_jobs for job_id in canonical):
            raise ValueError("排列中的工件编号越界")
        return canonical

    # --------------------------------------------------------------------------
    # 🔥【全文件最核心算法】：工件排列 -> 车间具体调度的解码器（ECT法则）
    # --------------------------------------------------------------------------
    def decode_and_evaluate(self, permutation: Sequence[int]) -> ScheduleEvaluation:
        """核心解码函数：把输入的工件顺序，翻译成车间里每道工序的具体起止时间与机器分配。
        
        工作原理：
        1. 阶段推进：阶段 0 -> 阶段 1 -> ... 顺序流水推进。
        2. 工件入场：在当前阶段，按 permutation 的顺序依次处理每个工件。
        3. 机器分配（ECT 最早完工法则）：
           遍历该阶段的所有可用机器，计算“在哪台机器上能最快做完”，就分给哪台机器。
        4. 开工时间约束（木桶原理）：
           - 工件必须做完了上一阶段才能开始（job_release_time）
           - 机器必须等前一个工件做完空出来（machine_ready_times）
           因此：开工时间 = max(工件可用时间, 机器空闲时间)
        """
        permutation_key = self._validate_permutation(permutation)
        
        # 查缓存：算过了直接返回
        cached = self._evaluation_cache.get(permutation_key)
        if cached is not None:
            return cached

        # machine_ready_times[stage_id][machine_id]: 记录每台机器排到了哪个时间点
        machine_ready_times = [
            [0 for _ in range(machine_count)] for machine_count in self.machines_per_stage
        ]
        # completion_times[job_id]: 每个工件从上一阶段出来的时刻
        completion_times = [0 for _ in range(self.n_jobs)]
        # machine_assignments[job_id][stage_id]: 每个工件在各阶段分配的机器
        machine_assignments = [
            [-1 for _ in range(self.n_stages)] for _ in range(self.n_jobs)
        ]
        operations: list[Operation] = []

        # 逐阶段流水排程
        for stage_id in range(self.n_stages):
            stage_completion_times = completion_times[:]
            
            # 按排列顺序依次安排工件
            for job_id in permutation_key:
                job_release_time = completion_times[job_id]
                
                best_machine = 0
                best_start = 0
                best_finish: int | None = None

                # 遍历当前阶段所有平行机，挑能够“最早做完”的那台
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

        # 包装评估结果
        evaluation = ScheduleEvaluation(
            permutation=permutation_key,
            makespan=max(completion_times) if completion_times else 0, # 总完工时间
            completion_times=tuple(completion_times),
            machine_assignments=tuple(tuple(row) for row in machine_assignments),
            operations=tuple(operations),
        )
        self._evaluation_cache[permutation_key] = evaluation
        return evaluation

    def evaluate(self, permutation: Sequence[int]) -> int:
        """轻量级接口：只返回总完工时间 makespan。"""
        return self.decode_and_evaluate(permutation).makespan

    # --------------------------------------------------------------------------
    # ⭐ 经典启发式算法基准（NEH 与 SPT）
    # --------------------------------------------------------------------------
    def _job_average_processing_time(self, job_id: int) -> float:
        """计算某个工件在所有阶段的平均总加工耗时。"""
        return sum(
            sum(stage_times) / len(stage_times)
            for stage_times in self.processing_times[job_id]
        )

    def _best_insertion_order(self, job_order: Iterable[int]) -> ScheduleEvaluation:
        """NEH 算法核心步骤：贪心最优插入法。
        逐个将工件尝试插入到已有队列的每一个可能位置，保留 makespan 最小的插入方案。
        """
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
        """经典 NEH 启发式算法：
        1. 按总耗时从大到小排序（大活优先）。
        2. 依次用最优插入法加入序列。
        质量极高、速度快，常作为 PSO 种群初始化的高质量种子。
        """
        job_order = sorted(
            range(self.n_jobs),
            key=self._job_average_processing_time,
            reverse=True,
        )
        return self._best_insertion_order(job_order)

    def spt_heuristic(self) -> ScheduleEvaluation:
        """最短加工时间优先（SPT）：按总工时从小到大排序。"""
        job_order = sorted(range(self.n_jobs), key=self._job_average_processing_time)
        return self.decode_and_evaluate(job_order)

    def generate_initial_solution(
        self, method: str = "neh", rng: random.Random | None = None
    ) -> list[int]:
        """生成初始工件排列解。支持 'neh' / 'spt' / 'random'。"""
        generator = rng or random.Random()
        method_name = method.lower()
        if method_name == "neh":
            return list(self.neh_heuristic().permutation)
        if method_name == "spt":
            return list(self.spt_heuristic().permutation)
        if method_name == "random":
            return generator.sample(list(range(self.n_jobs)), self.n_jobs)
        raise ValueError(f"不支持的初始化方法: {method}")
