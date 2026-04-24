# HFSP 智能求解与可视化工作台

这是一个面向混合流水车间调度问题（HFSP, Hybrid Flow Shop Scheduling Problem）的求解与可视化系统。

项目集成了：

- HFSP 环境建模与调度解码
- NEH、SPT 基线启发式
- 带小生境机制的 PSO + IG 求解算法
- 多智能体协同求解模式
- 多模态解档案库
- Web 前端算例编辑、求解、分析、甘特图回放与仿真演示
- Docker 部署文件

## 目录结构

- `src/`：核心算法、分析逻辑与 FastAPI 服务
- `web/`：前端页面、样式与交互脚本
- `benchmarks/`：基准算例
- `output/`：导出的摘要与档案结果
- `results/`：生成的图表与结果文件

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动 Web 服务：

```bash
python src/web_app.py
```

浏览器访问：

- `http://127.0.0.1:8000`

Windows 下也可以直接双击：

- `start_hfsp_web.bat`

## Docker 运行

构建并启动：

```bash
docker compose up --build -d
```

停止：

```bash
docker compose down
```

Windows 下提供一键脚本：

- `start_hfsp_docker.bat`
- `stop_hfsp_docker.bat`

Docker 详细说明见：

- `README_Docker.md`

## 主要功能

### 1. 算例工作台

- 加载内置 benchmark 算例
- 导入自定义 JSON 算例
- 生成模板算例
- 在线编辑并校验算例数据

### 2. 求解模式

- `PSO + IG` 基础求解
- `Multi-Agent` 多智能体协同求解
- `Compare` 双模式对比求解

### 3. 结果分析

- 最优 `makespan` 摘要
- 相对 NEH / SPT 的改进情况
- 瓶颈阶段分析
- 机器利用率与工件等待时间分析
- 多解档案浏览

### 4. 动态可视化

- 动态甘特图回放
- 多解档案中每个解对应的甘特图查看
- 独立的仿真演示页面
- 机器与工件状态实时显示

## API 接口

- `GET /api/health`
- `GET /api/benchmarks`
- `GET /api/benchmarks/{file_name}`
- `POST /api/solve`

## 内置算例

仓库中包含多类测试算例，例如：

- Carlier 系列算例
- 瓶颈型 benchmark 算例

## 说明

- 前端资源由 FastAPI 直接从 `web/` 目录提供
- 求解结果会返回调度 `operations`，供甘特图和仿真动画共同使用
- 如果需要导出静态甘特图，需安装 `matplotlib`

## 许可证

本项目采用 [MIT License](./LICENSE)。
