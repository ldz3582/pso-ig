# HFSP 混合流水车间调度求解器（PSO + IG）

面向混合流水车间调度问题（HFSP, Hybrid Flow Shop Scheduling Problem）的多模态求解程序。
算法核心只有 4 个文件：`main.py`、`pso.py`、`ig.py`、`gantt.py`；
另有批量运行脚本 `run_carlier_benchmark.py`，把一个基准集整体跑完并汇总成文档。

## 文件结构

每个算法文件只有一个与文件名同名的顶层函数作为主体：

```
src/
├── main.py                     # 主体 main()（主函数）：读算例 → 跑 pso() → 建多模态档案 → 出甘特图
├── pso.py                      # 主体 pso()：初始化 → 速度更新 → 位置更新；每 12 代调用一次 ig()
├── ig.py                       # 主体 ig()：破坏-重构 + 模拟退火
├── gantt.py                    # 甘特图模块：画图 + 以甘特图块识别多模态解
└── run_carlier_benchmark.py    # 批量运行脚本：遍历基准集所有算例 → 汇总最优解与多模态解文档
```

| 文件 | 主体函数 | 支撑定义（同文件内，供主体使用） |
|------|----------|----------------------------------|
| `main.py` | `main()` 主函数 | `HFSPEnvironment` 车间建模与解码、`MultimodalArchive` 档案 |
| `pso.py` | `pso()` 粒子群 | `Particle` 粒子、`SolverConfig` 参数 |
| `ig.py` | `ig()` 迭代贪婪 | 无 |
| `gantt.py` | `draw_gantt()` 画甘特图 | `gantt_blocks()` / `gantt_signature()` / `gantt_similarity()` |
| `run_carlier_benchmark.py` | `main()` 批量入口（脚本，非算法模块） | `run_one()` 单算例求解、`write_markdown()` / `write_json()` / `write_csv()` 汇总 |

依赖方向：`main.py` → `pso.py` → `ig.py`，`main.py` → `gantt.py`，无循环依赖；
`run_carlier_benchmark.py` → `main.py` / `pso.py` / `gantt.py`（只调用，不被调用）。
（问题模型/档案这类公共支撑放在主程序 `main.py` 中；`pso()`、`ig()` 通过参数接收环境对象。）

## 算法流程

1. **环境与解码**（`main.py`）：给定工件加工顺序，支持三种解码方向
   （`--decode-mode`）：
   - `forward`：正向解码，逐阶段按 ECT（最早完工）法则分配平行机；
   - `backward`：反向解码，工件逆序、阶段从后往前排（镜像实例正向解码后做时间反演）；
   - `hybrid`（默认）：正、反向各算一次，取 makespan 较小者。
   得到调度与 makespan；NEH+SPT / NEH+LPT 用于 PSO 初始化。
2. **PSO**（`pso.py`）：
   - 初始化：1 个 NEH+SPT、1 个 NEH+LPT，其余随机排列；
   - 速度更新：惯性 + 认知（个体最优）+ 社会（全局最优），速度是交换序列；
   - 位置更新：对当前排列施加交换序列，再按小概率随机变异；
   - **每 12 代**对全局最优执行一次 IG，改进后替换最差粒子。
3. **IG**（`ig.py`）：随机破坏部分工件 → 最优插入重构 → 模拟退火接受劣解。
4. **多模态档案**（`main.py` + `gantt.py`）：以甘特图识别模态——把每条解拆成
   「机器 → 工序块序列」，甘特图完全相同的解只留一条，其余全部保留，不限数量。
5. **多模态解识别/输出**（`gantt.py`）：块级比较给出相似度，每条模态解各画一张甘特图。

## 运行

先准备环境（已内置 `.venv`，如缺失可重建）：

```bash
# 在项目根目录
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # 网络慢可用 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

在 IDE 里把解释器选为 `./.venv/bin/python`（`.vscode/settings.json` 已默认指向它）。
命令行运行（先激活虚拟环境）：

```bash
source .venv/bin/activate
cd src
# 默认算例 j10c5a2
python3 main.py

# 指定算例与规模
python3 main.py \
    --benchmark ../5benchmark/Carlier_benchmark/j10c10a1.txt \
    --population-size 40 --ig-iterations 20

# 仅正向 / 仅反向 / 混合解码（默认 hybrid）
python3 main.py --benchmark ../5benchmark/Carlier_benchmark/j10c5a2.txt --decode-mode forward
python3 main.py --benchmark ../5benchmark/Carlier_benchmark/j10c5a2.txt --decode-mode backward
python3 main.py --benchmark ../5benchmark/Carlier_benchmark/j10c5a2.txt --decode-mode hybrid
```

输出：

- `output/multimodal_archive_<算例>.json` —— 多模态解档案（排列、makespan、机器分配、工序）
- `output/<算例>_summary.json` —— 最优 makespan、多模态解数量、耗时等
- `results/<算例>_optimal_mode<k>_makespan<M>.png` —— 每条多模态解的甘特图

### 批量跑一个基准集

`run_carlier_benchmark.py` 遍历算例目录下所有 `.txt` 算例，逐个求解并汇总成
一份**含最优解与全部多模态解**的 Markdown 文档（同时输出 json / csv）：

```bash
source .venv/bin/activate
# 默认：Carlier 基准集全部 96 个算例
python3 src/run_carlier_benchmark.py

# 换算例集 / 调参 / 小样本调试
python3 src/run_carlier_benchmark.py \
    --benchmark-dir 5benchmark/Small_Size_Instances \
    --population-size 40 --ig-iterations 20 --time-factor 0.01 \
    --max-charts 5 --limit 10
```

主要参数：`--benchmark-dir`（算例目录）、`--label`（汇总文件与甘特图子目录的标签，
默认由目录名推导，`Carlier_benchmark → carlier`）、`--results-dir`、`--max-charts`
（每个算例最多出图张数）、`--limit`（只跑前 N 个，调试用）。算法参数与 `main.py` 一致。

批量运行输出（以 Carlier 为例，`<标签>` = `carlier`）：

- `output/<标签>_multimodal_summary.md` —— **汇总文档**：实验设置 + 汇总表 + 逐算例的
  最优解与全部多模态解明细（排列、makespan、甘特图链接）+ 多模态分布统计
- `output/<标签>_multimodal_summary.json` —— 同样内容的机器可读版（含每条模态解）
- `output/<标签>_multimodal_summary.csv` —— 逐算例汇总表
- `output/multimodal_archive_<算例>.json`、`output/<算例>_summary.json` —— 单算例产物（同上）
- `results/<标签>/<算例>_optimal_mode<k>_makespan<M>.png` —— 多模态解甘特图
  （脚本运行前会清理该目录下同批算例的旧甘特图，避免新旧结果混杂）

## 文档与图

| 文件 | 内容 |
|------|------|
| [output/carlier_multimodal_summary.md](./output/carlier_multimodal_summary.md) | Carlier 96 算例的最优解与多模态解汇总文档（由 `src/run_carlier_benchmark.py` 生成） |
| [docs/代码结构说明.md](./docs/代码结构说明.md) | 逐文件、按行号讲解四个算法源文件（改代码后需同步） |
| [docs/技术文档.md](./docs/技术文档.md) | 问题数学模型、算法设计、复杂度、参数与实测结果 |
| [docs/开发文档.md](./docs/开发文档.md) | 项目概览、架构、实现效果与扩展方向 |
| [docs/HFSP开发文档.docx](./docs/HFSP开发文档.docx) | 开发文档的 Word 版（由 `docs/make_dev_doc_docx.py` 从 Markdown 生成） |
| [docs/项目全流程图.png](./docs/项目全流程图.png) | 一页总览：模块结构 + 端到端数据流 + 算法 + 产物 |
| [docs/项目结构与依赖图.png](./docs/项目结构与依赖图.png) | 四文件结构与依赖关系 |
| [docs/求解总流程图.png](./docs/求解总流程图.png) | 从读算例到出甘特图的完整流程 |
| [docs/初始解生成流程图.png](./docs/初始解生成流程图.png) | NEH+SPT / NEH+LPT / 随机 三种初始解的生成细节 |
| [docs/算法流程图_横向.png](./docs/算法流程图_横向.png) | PSO + IG + 档案库横向流程 |
| [docs/算法流程图_横向_详细.png](./docs/算法流程图_横向_详细.png) | 同上，展开各子步骤与关键参数 |

全流程总图由 `python3 docs/make_project_flowchart.py` 生成；两张总图由
`python3 docs/make_hfsp_diagrams.py` 生成；横向流程图由
`docs/make_flowchart_horizontal.py` 与 `docs/make_flowchart_detail.py` 生成。

## 许可证

本项目采用 [MIT License](./LICENSE)。
