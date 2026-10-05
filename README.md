# HFSP 混合流水车间调度求解器（算法版）

面向混合流水车间调度问题（HFSP, Hybrid Flow Shop Scheduling Problem）的求解与结果分析程序。

> 说明：本仓库已移除 Web 后端（FastAPI / 登录 / 人员管理）与前端页面，仅保留算法代码、基准数据与求解结果。

## 目录结构

```
.
├── src/                # 算法实现与运行脚本
├── 5benchmark/         # 基准数据（唯一数据目录）
│   ├── Carlier_benchmark/      # Carlier txt 算例 96 个（与老师 MOAIG 结果同一批）
│   ├── Small_Size_Instances/   # instancia_10_* 共 240 个
│   ├── Small_Big_Size_instances/  # 中小规模算例
│   ├── Big_Size_Instances/     # 大规模算例
│   └── teacher_moaig_result.csv  # 老师的 MOAIG 结果（96 算例 × 5 次运行）
├── output/             # 求解结果（summary、多模态档案库、对比实验表）
├── docs/               # 代码结构说明、技术文档、开发文档、流程图与生成脚本
├── requirements.txt
└── LICENSE
```

`src/` 文件说明：

| 文件 | 作用 |
|------|------|
| `hfsp_environment.py` | HFSP 建模、排列解码、makespan 评估、NEH / SPT 基线 |
| `niching_mechanism.py` | 排列距离与机器分配距离、小生境聚类、种群多样性 |
| `niching_pso.py` | 离散 PSO（交换序速度、环形邻域、小生境、停滞重初始化、档案库注入） |
| `iterated_greedy.py` | IG 破坏-重建局部搜索 + 模拟退火接受准则 |
| `multimodal_hfsp_solver.py` | 主求解器：`basic_pso_ig` / `multi_agent` / `compare` + 多模态档案库 |
| `archive_guided_search.py` | **档案库引导搜索**：探索 / 强化两种种子选取 + 扰动 + IG 回写档案库 |
| `multimodal_evaluation.py` | **多模态评价指标**：等优解计数、结构签名去重、解集多样性、故障鲁棒性 |
| `solver_analysis.py` | 结果分析：瓶颈阶段、机器利用率、工件等待时间、档案统计 |
| `gantt_chart_generator.py` | 基于 matplotlib 导出静态甘特图（可选） |
| `hfsp_benchmark_instances.py` | 算例 JSON 读写辅助函数 |
| `run_complete_test.py` | 批量运行内置示例算例 |
| `run_carlier_benchmark.py` | 批量运行 Carlier 系列算例 |
| `run_carlier_multimodal_benchmark.py` | **批量对比实验**：基线 vs 档案库引导 vs 老师结果 |
| `report_multimodal_results.py` | 把逐算例结果合并汇总成总表 |
| `demo_fault_switching.py` | 演示机器故障时用等优解集免重算切换方案 |
| `test_carlier_instances.py` | 运行单个算例并打印结果 |

## 文档

| 文档 | 内容 |
|------|------|
| `docs/代码结构说明.md` | **逐模块代码讲解**：目录分层、数据流、每个文件的关键实现与参数速查、扩展指南 |
| `docs/总体求解流程图.png` | 总体求解流程（三阶段主流程 + 入档四步 + 商集 Π/~ 示意） |
| `docs/算法流程图_多模态.png` | 阶段级细节流程图（PSO / IG 每个节点展开） |
| `docs/技术文档.md` | 技术设计文档 |
| `docs/开发文档.md` | 开发过程文档 |

## 算法流程

1. 环境建模与解码：按工件排列，逐阶段为每个工件选择最早完工的可用机器，得到调度与 makespan。
2. 基线对比：NEH（按平均加工时间降序 + 最优插入）与 SPT。
3. 小生境 PSO：粒子以「交换序列」作为速度，环形邻域内取局部最优；小生境聚类维持多样性，停滞时重初始化最差粒子。
4. IG 局部搜索：随机破坏部分工件后以最优插入重建，模拟退火接受劣解。
5. 多模态档案库：按 makespan 相近度、排列距离、机器分配差异判定解的新颖性，保留多样化解。
6. 档案库引导搜索（多模态增强）：把档案库从「只存不用」变成搜索算子——交替从「最孤立」成员（探索）与「最接近最优」成员（强化）出发做扰动 + IG，结果回写档案库；停滞时用档案库排列重启 PSO。
7. 结果分析：输出阶段/机器利用率、工件等待时间、瓶颈阶段与档案库统计。

求解模式：

- `basic_pso_ig`：NEH 初始化 → 小生境 PSO → IG 精修
- `multi_agent`：种子智能体 → 局部精修 → 扩展探索 → 重点强化 协同产生候选解
- `compare`：同时运行上述两种模式并给出对比结论

## 运行

核心算法依赖 `numpy`（批量结构距离取向量化实现），甘特图另需 `matplotlib`：

```bash
python3 src/run_carlier_multimodal_benchmark.py --limit 10   # 基线 vs 档案库引导 + 老师对比
python3 src/test_schedule_distance_bulk.py                   # 单元测试：批量距离 == 标量距离
python3 src/test_archive_capacity.py                         # 单元测试：容量裁剪不改变语义
```

常用参数（三个脚本通用）：

```
--output-dir        结果输出目录，默认 output
--population-size   种群规模，默认 30~40
--max-generations   迭代代数，默认 40~60
--ig-iterations     IG 迭代次数，默认 15~20
--seed              随机种子
--generate-chart    额外导出甘特图 PNG（需安装 matplotlib）
```

安装可选依赖以导出甘特图：

```bash
pip install -r requirements.txt
```

## 算例数据格式

```json
{
  "name": "Carlier_small",
  "n_jobs": 5,
  "n_stages": 3,
  "machines_per_stage": [2, 2, 2],
  "processing_times": [
    [[11, 8], [15, 12], [9, 11]]
  ]
}
```

`processing_times[job][stage][machine]` 为对应工序的加工时间。

## 结果说明

运行后写入 `output/`：

- `multimodal_archive_<算例>.json`：多模态档案库，每个解包含 `permutation`、`makespan`、`machine_assignments`、`completion_times`、`operations`（逐工序的起止时间与机器）。
- `<算例>_summary.json`：算例摘要（最优 makespan、耗时、参数、档案路径）。
- `carlier_benchmark_summary.json` / `complete_test_summary.json`：批量运行汇总。

`--generate-chart` 时甘特图输出到 `results/`。

## 多模态档案库与评价口径

### 为什么不能在排列空间上谈"多个解"

工件排列 π 与调度方案不是一一对应：多个不同排列经解码后可能得到**完全相同**的调度
（每个阶段、每台机器上的工件加工顺序一致），它们构成一个**结构等价类**。设解码映射
D: Π → S，等价关系为

```
π₁ ~ π₂  ⟺  D(π₁) = D(π₂)
```

真正要搜索、统计、比较的对象是**商集 Π/~**（调度空间 S），而不是 Π。排列空间上的
位置海明距离有两个缺陷：相邻交换（结构几乎没变）距离为 1，会虚报差异；结构差异极大
的两个解也可能只在少数位置不同，会漏报差异。因此本项目的距离一律在商集上定义
（`src/schedule_distance.py`）：

| 分量 | 定义 | 取值 |
|------|------|------|
| `assignment_distance` | 分配到不同机器的 (工件, 阶段) 对占比 | [0, 1] |
| `sequence_distance` | 两解中位于同一台机器的工件对，先后顺序翻转的比例（Kendall tau 型） | [0, 1] |

两个分量都归一化，与算例规模无关，可直接作为阈值使用。

### 档案库的语义（`MultimodalArchive`）

1. **存调度，不存排列**：每个结构等价类只保留一个代表元（makespan 最优者），
   因此库中解两两结构互异。
2. **质量门限 ρ**：只接纳 `makespan ≤ (1+ρ)·当前最优` 的解，即「备择最优 / 近优
   调度」集合；最优值改进后，超出新门限的旧解会被剪掉。
3. **析取式新颖性判定**：候选解与某个已存解在「质量、机器分配、加工顺序」三个维度
   上**同时**足够接近时才判为重复而拒收；只要有一个维度差异足够大即接纳——质量维度
   与结构维度因此都得到保证。
4. **容量 + 最远点裁剪**：超出 `capacity` 时保留最优解，其余按「到已保留集合的最小
   结构距离最大」逐个挑选，使解集在结构上尽量分散。

`MultimodalArchive.stats` 会记录 `rejected_quality` / `rejected_same_class` /
`rejected_too_close` / `pruned_by_quality` / `trimmed`，可直接用于论文的消融分析。

### 档案库是搜索的状态变量，不是结果容器

`src/archive_guided_search.py` 让档案库反向驱动搜索：

- **选择种子**：探索（explore）挑「最孤立」成员——到其他成员的最小结构距离最大，
  代表采样最稀疏的区域；强化（intensify）挑「接近最优」成员，在同一盆地内继续采
  等优解。
- **多样化游走**：以种子为起点做多步「扰动 + IG」。接受准则除 makespan 外还看结构——
  若候选与当前游走点属于不同等价类、且离起点更远，则接受为新的游走点，从而可以
  **在等优解之间走**，而不是每次塌回同一个局部最优。

PSO 侧同样反向连接：`NichingPSO.diversity_pool` 指向档案库排列池，停滞重初始化时
从库中注入精英而不是纯随机重启。

### 评价指标（`src/multimodal_evaluation.py`）

| 指标 | 定义 |
|------|------|
| 等优解数 (ρ) | makespan ≤ (1+ρ)·best 的**结构互异**解的条数，ρ = 0 / 1% / 2% / 5% |
| 解集多样性 | 等优解之间的平均成对结构距离（机器分配 / 加工顺序两个分量） |
| 故障鲁棒性 | 机器停机时按原方案冻结执行的 makespan 恶化，以及「切换到恶化最小的备选解」的挽回量 |

## 实验复现

```bash
cd src
# 基线（档案库只存不用） vs 档案库引导，逐算例对比老师结果
python3 run_carlier_multimodal_benchmark.py \
    --txt-dir ../5benchmark/Carlier_benchmark \
    --teacher ../5benchmark/teacher_moaig_result.csv \
    --guided-rounds 60 --restart-generations 30 \
    --out ../output/carlier_multimodal_compare.csv

# 汇总成总表
python3 report_multimodal_results.py \
    --inputs ../output/carlier_multimodal_compare.csv \
    --out ../output/multimodal_vs_teacher_combined.csv

# 故障切换演示
python3 demo_fault_switching.py --instance ../5benchmark/Carlier_benchmark/j10c5d1.txt --downtime 12
```

流程图：

```bash
python3 docs/make_flowchart_overall.py docs/总体求解流程图.png   # 总体求解流程（含商集示意）
python3 docs/make_flowchart.py docs/算法流程图_多模态.png          # 含档案库引导的细节版
python3 docs/make_flowchart.py docs/算法流程图.png --base          # 只画 PSO + IG 基础流程
```

- `docs/总体求解流程图.png` —— 总体求解过程：三阶段主流程 + 入档判定四步 + 商集 Π/~ 示意 + 输出与用途
- `docs/算法流程图_多模态.png` —— 阶段级细节：PSO / IG 每个节点的展开
- `docs/算法流程图.png` —— 只含基础 PSO + IG 的版本

### 已跑结果（新档案库语义，6 个算例抽测）

| 算例 | 老师 | 基线 | 引导版 | 等优解 基线→引导 |
|------|-----|------|--------|-----------------|
| `j10c10a1` | 139 | 139 | 139 | 32 → **108** |
| `j10c5d1` | 66 | 68 | 68 | 4 → **20** |
| `j10c5d2` | 74 | 75 | **74** | 12 → 5 |
| `j10c10d3` | 116 | 119 | 119 | 5 → **25** |
| `j15c10c1` | 134 | 142 | 142 | 3 → **13** |
| `j15c5c1` | 85 | 87 | **86** | 1 → 1 |

- 等优解总数 **57 → 172**（约 3.0 倍），ρ=1% 近优解 **67 → 226**；
- 与老师对比：基线 1 平 / 5 负 → 引导版 **2 平 / 4 负**；
- `j10c5d2` 是典型的**目标冲突**样本：最优值 75→74 追平老师，但等优解从 12 条降到 5 条；
- 结论：档案库引导能稳定放大解集规模并小幅改进最优值，但单解最优值仍未追平 MOAIG。

历史数据：`output/multimodal_vs_teacher_combined.csv`（46 算例）是在**旧档案库语义**
（位置海明距离、无质量门限）下测得的，与当前实现不可直接比较，需要重跑。

## 许可证

本项目采用 [MIT License](./LICENSE)。
