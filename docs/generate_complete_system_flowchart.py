# -*- coding: utf-8 -*-
"""生成 HFSP 求解系统完整、高精度的系统架构与算法流程矢量图 (SVG)。
无外部依赖，使用纯 Python 内置库生成标准 SVG。
"""
from pathlib import Path

def generate_svg(output_path: str):
    W, H = 1480, 2220
    
    # 颜色定义
    BG = "#F8FAFC"
    PANEL_BG = "#FFFFFF"
    BORDER = "#CBD5E1"
    TEXT_MAIN = "#0F172A"
    TEXT_MUTED = "#475569"
    TEXT_LIGHT = "#64748B"
    
    # 主题色
    PRIMARY_BG = "#EFF6FF"
    PRIMARY_BORDER = "#3B82F6"
    PRIMARY_TITLE = "#1E40AF"
    
    ACCENT_BG = "#F0FDF4"
    ACCENT_BORDER = "#22C55E"
    ACCENT_TITLE = "#15803D"
    
    ORANGE_BG = "#FFF7ED"
    ORANGE_BORDER = "#F97316"
    ORANGE_TITLE = "#C2410C"
    
    PURPLE_BG = "#FAF5FF"
    PURPLE_BORDER = "#A855F7"
    PURPLE_TITLE = "#7E22CE"
    
    TEAL_BG = "#F0FDFA"
    TEAL_BORDER = "#14B8A6"
    TEAL_TITLE = "#0F766E"
    
    ROSE_BG = "#FFF1F2"
    ROSE_BORDER = "#F43F5E"
    ROSE_TITLE = "#BE123C"
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('<defs>')
    # 箭头标记
    svg.append('''
        <marker id="arr-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#3B82F6" />
        </marker>
        <marker id="arr-gray" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748B" />
        </marker>
        <marker id="arr-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#16A34A" />
        </marker>
        <marker id="arr-orange" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#EA580C" />
        </marker>
        <marker id="arr-purple" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#9333EA" />
        </marker>
        <filter id="shadow" x="-3%" y="-2%" width="106%" height="108%" filterUnits="userSpaceOnUse">
            <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.06"/>
        </filter>
        <filter id="card-shadow" x="-2%" y="-2%" width="104%" height="106%" filterUnits="userSpaceOnUse">
            <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.04"/>
        </filter>
        <style>
            .font-bold { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 700; }
            .font-medium { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 600; }
            .font-normal { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 400; }
            .font-mono { font-family: "SF Mono", "Fira Code", Menlo, Monaco, Consolas, monospace; }
        </style>
    ''')
    svg.append('</defs>')
    
    # 背景
    svg.append(f'<rect width="{W}" height="{H}" fill="{BG}" />')
    
    # 顶部标题栏
    svg.append(f'''
    <g transform="translate(60, 40)">
        <rect width="1360" height="90" rx="16" fill="#1E293B" filter="url(#shadow)"/>
        <text x="40" y="42" class="font-bold" font-size="26" fill="#FFFFFF">HFSP 混合流水车间调度：多模态智能求解系统完整执行流程图</text>
        <text x="40" y="68" class="font-normal" font-size="14" fill="#94A3B8">覆盖数据结构、商集空间 Π/~ 理论、小生境离散 PSO、退火 IG 强化、多模态档案库准入四步、双向引导闭环及多智能体协同机制</text>
        <rect x="1100" y="24" width="220" height="42" rx="8" fill="#334155" />
        <text x="1210" y="50" text-anchor="middle" class="font-mono font-medium" font-size="13" fill="#38BDF8">Strict Architectural Flow</text>
    </g>
    ''')

    # 辅助绘图函数
    def draw_panel(x, y, w, h, title, subtitle="", color=PRIMARY_BORDER, bg=PANEL_BG):
        return f'''
        <g transform="translate({x}, {y})">
            <rect width="{w}" height="{h}" rx="12" fill="{bg}" stroke="{color}" stroke-width="1.8" filter="url(#shadow)"/>
            <rect x="1.8" y="1.8" width="{w-3.6}" height="38" rx="10" fill="{color}" fill-opacity="0.08"/>
            <text x="20" y="26" class="font-bold" font-size="16" fill="{TEXT_MAIN}">{title}</text>
            <text x="{w-20}" y="25" text-anchor="end" class="font-normal" font-size="12" fill="{TEXT_LIGHT}">{subtitle}</text>
        </g>
        '''

    def draw_box(x, y, w, h, lines, fill="#F8FAFC", stroke=BORDER, bold_idx=0, text_color=TEXT_MAIN, badge=""):
        res = [f'<g transform="translate({x}, {y})">']
        res.append(f'<rect width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.2" filter="url(#card-shadow)"/>')
        if badge:
            res.append(f'<rect x="{w-70}" y="6" width="62" height="18" rx="4" fill="{stroke}" fill-opacity="0.15"/>')
            res.append(f'<text x="{w-39}" y="19" text-anchor="middle" class="font-medium" font-size="10" fill="{stroke}">{badge}</text>')
        start_y = 20 if len(lines) > 1 else h // 2 + 5
        line_gap = 18
        for i, line in enumerate(lines):
            weight_class = "font-bold" if i == bold_idx else "font-normal"
            fsize = 13 if i == bold_idx else 11.5
            fcolor = text_color if i == bold_idx else TEXT_MUTED
            res.append(f'<text x="14" y="{start_y + i * line_gap}" class="{weight_class}" font-size="{fsize}" fill="{fcolor}">{line}</text>')
        res.append('</g>')
        return "\n".join(res)

    def draw_arrow(x1, y1, x2, y2, color="#64748B", marker="arr-gray", text="", text_anchor="middle", text_offset=(0,-6), dash=""):
        dash_str = f'stroke-dasharray="{dash}"' if dash else ""
        res = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8" marker-end="url(#{marker})" {dash_str}/>']
        if text:
            mx, my = (x1 + x2) / 2 + text_offset[0], (y1 + y2) / 2 + text_offset[1]
            res.append(f'<rect x="{mx-len(text)*4-6}" y="{my-11}" width="{len(text)*8+12}" height="18" rx="4" fill="#FFFFFF" fill-opacity="0.92" stroke="#E2E8F0" stroke-width="0.8"/>')
            res.append(f'<text x="{mx}" y="{my+2}" text-anchor="{text_anchor}" class="font-medium" font-size="11" fill="{color}">{text}</text>')
        return "\n".join(res)

    def draw_path(pts, color="#64748B", marker="arr-gray", text="", text_pt=None, dash=""):
        dash_str = f'stroke-dasharray="{dash}"' if dash else ""
        d = f"M {pts[0][0]} {pts[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts[1:])
        res = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{marker})" {dash_str}/>']
        if text and text_pt:
            tx, ty = text_pt
            res.append(f'<rect x="{tx-len(text)*4-6}" y="{ty-11}" width="{len(text)*8+12}" height="18" rx="4" fill="#FFFFFF" fill-opacity="0.92" stroke="#E2E8F0" stroke-width="0.8"/>')
            res.append(f'<text x="{tx}" y="{ty+2}" text-anchor="middle" class="font-medium" font-size="11" fill="{color}">{text}</text>')
        return "\n".join(res)

    # =========================================================================
    # 第一层：输入、环境建模与解码内核 (Y: 150 -> 340)
    # =========================================================================
    svg.append(draw_panel(60, 150, 1360, 200, "1. 算例输入、数学建模与 ECT 解码内核 (hfsp_environment.py)", "L0 基础支撑与统一评测标准", PRIMARY_BORDER))
    
    # 算例输入框
    svg.append(draw_box(80, 205, 260, 125, [
        "基准算例输入 (Benchmark Input)",
        "• 工件规模: n jobs",
        "• 阶段结构: s stages",
        "• 机器分布: m_s machines per stage",
        "• 加工矩阵: P[job][stage][machine]",
        "• 数据源: Carlier / Small / Big TXT"
    ], fill=PRIMARY_BG, stroke=PRIMARY_BORDER, badge="Input Data"))

    # 解码器核心框
    svg.append(draw_box(410, 205, 360, 125, [
        "解码器映射核 D: Π → S (ECT 规则)",
        "• 拓扑约束: 阶段推进 stage 0 → s-1",
        "• 阶段内派工: 按工件排列 π 的先后顺序派工",
        "• 机器分配: min Earliest Completion Time",
        "  C[j,s,m] = max(Ready[s,m], Done[j,s-1]) + p[j,s,m]",
        "• 评估缓存: LRU 字典消除同排列重复解码"
    ], fill="#F0FDF4", stroke="#16A34A", badge="Unified Decoder"))

    # ScheduleEvaluation 数据结构框
    svg.append(draw_box(840, 205, 270, 125, [
        "调度评估对象 ScheduleEvaluation",
        "• makespan = max(C_completion[j])",
        "• completion_times: 每个工件最终完工时刻",
        "• machine_assignments[job][stage]: 机器阵列",
        "• operations: 每道工序的 (开始, 结束, 机器)",
        "• 保持商集等价类计算的完整特征"
    ], fill="#FEF3C7", stroke="#D97706", badge="Frozen Dataclass"))

    # 启发式基线生成框
    svg.append(draw_box(1170, 205, 230, 125, [
        "基线启发式 (Baselines)",
        "• NEH 启发式:",
        "  各阶段工件平均工时降序",
        "  逐个执行贪心最优插入",
        "• SPT 启发式: 平均工时升序",
        "• 产生确定性种子与对照基准"
    ], fill="#FDF4FF", stroke="#C084FC", badge="Heuristics"))

    # 第一层内部箭头连接
    svg.append(draw_arrow(340, 267, 410, 267, PRIMARY_BORDER, "arr-blue", "载入算例"))
    svg.append(draw_arrow(770, 267, 840, 267, "#16A34A", "arr-green", "输出调度 S"))
    svg.append(draw_arrow(1170, 245, 770, 245, "#C084FC", "arr-purple", "送入解码评估", dash="4,3"))

    # =========================================================================
    # 第二层：离散小生境粒子群搜索 (NichingPSO) 与 迭代贪婪 (IG) (Y: 380 -> 980)
    # =========================================================================
    # 左栏：离散小生境粒子群 (Width: 840)
    svg.append(draw_panel(60, 380, 840, 580, "2. 离散小生境粒子群全局搜索 (niching_pso.py)", "L2 全局搜索器 · 交换序代数 · 多样性聚类", PRIMARY_BORDER))

    # PSO 步骤 1：种群初始化
    svg.append(draw_box(80, 435, 380, 95, [
        "2.1 混合种群初始化 (Initialize Population)",
        "• 种群规模 N (默认 40), 评估粒子初始 makespan",
        "• 精英种子注入: 1 个 NEH 解 + 1 个 SPT 解",
        "• 种子扰动变异: 生成若干基于 NEH/SPT 变异个体",
        "• 档案库池注入: 停滞/重启时注入精英解 (pool_quota)",
        "• 随机排列: 补齐剩余粒子，初始化 pbest = x"
    ], fill=PRIMARY_BG, stroke=PRIMARY_BORDER, badge="Init Swarm"))

    # PSO 步骤 2：小生境与环境感知
    svg.append(draw_box(500, 435, 380, 95, [
        "2.2 小生境聚类与自适应控制 (Niching & Adapt)",
        "• 惯性权重动态递减: w(t) = w_max - (w_max-w_min)*(t/T)",
        "• 环形邻域拓扑 (Ring): 仅与左右 k 个粒子交互",
        "• 小生境聚类 (Niche Clustering): 位置距离 ≤ 阈值归类",
        "• 种群多样性检测 → 自适应放大变异率 P_mutation",
        "• 局部导引 local_best: 取环形邻域+同生境内最优 pbest"
    ], fill="#F8FAFC", stroke="#64748B", badge="Niching & Comm"))

    # PSO 步骤 3：离散速度与位置更新
    svg.append(draw_box(80, 560, 800, 110, [
        "2.3 离散交换序速度更新与位置推进 (Discrete Velocity & Position Update)",
        "• 交换序抽取: SwapSeq(X, Y) 得到由 X 变换到 Y 的最小对换对序列 [(i₁, j₁), (i₂, j₂), ...]",
        "• 速度更新公式: V_{t+1} = w ⊙ V_t ⊕ c₁ ⊙ Sample(SwapSeq(x, pbest)) ⊕ c₂ ⊙ Sample(SwapSeq(x, lbest))",
        "• 速度应用: 依次在当前排列执行交换对，并依概率 P_mut 执行局部随机换位变异",
        "• 统一解码: 调用 env.decode_and_evaluate(x) 获得 makespan，更新个人最优 pbest"
    ], fill="#EFF6FF", stroke="#2563EB", badge="Algebraic PSO"))

    # PSO 步骤 4：候选解缓冲池
    svg.append(draw_box(80, 700, 380, 85, [
        "2.4 候选解缓冲池 (_record_solution)",
        "• 精确排列查重: seen_positions 集合过滤",
        "• 按 makespan 升序维护前 200 优选解",
        "• 仅作缓冲，不作粗暴距离去重",
        "• 完整保留结构多样性以备入档"
    ], fill="#F0FDF4", stroke="#16A34A", badge="Candidate Buffer"))

    # PSO 步骤 5：停滞检测与多样性重启
    svg.append(draw_box(500, 700, 380, 85, [
        "2.5 停滞检测与档案库注入 (Stagnation & Injection)",
        "• 连续 10 代无全局最优改进 → 触发停滞响应",
        "• 淘汰种群中最差的 20% 劣质粒子",
        "• 50% 概率从多模态档案库中随机抽取精英注入",
        "• 50% 概率生成全新随机解，保留全局最优 gbest"
    ], fill="#FFF7ED", stroke="#EA580C", badge="Restart"))

    # PSO 步骤 6：周期性 IG 局部精修
    svg.append(draw_box(80, 815, 800, 75, [
        "2.6 阶段内混合强化：周期性调用 IG 精修 (Periodic Local Search)",
        "• 每隔 T/5 代 (约 12 代)，对当前全局最优 gbest 执行 Iterated Greedy 强化搜索",
        "• 若精修解优于 gbest，则更新 gbest 并直接替换种群中最差粒子，强化开采深井"
    ], fill="#FAF5FF", stroke="#9333EA", badge="Hybrid LS"))

    # PSO 循环判断
    svg.append(draw_box(80, 915, 380, 36, [
        "判断: 代数 gen < max_gen ?"
    ], fill="#F1F5F9", stroke="#475569", bold_idx=0))

    svg.append(draw_box(500, 915, 380, 36, [
        "输出: (gbest_makespan, gbest_perm, 候选解集)"
    ], fill="#DCFCE7", stroke="#16A34A", bold_idx=0))

    # PSO 内部连接
    svg.append(draw_arrow(270, 530, 270, 560, PRIMARY_BORDER, "arr-blue"))
    svg.append(draw_arrow(690, 530, 690, 560, "#64748B", "arr-gray"))
    svg.append(draw_arrow(270, 670, 270, 700, "#16A34A", "arr-green", "产生新解"))
    svg.append(draw_arrow(460, 742, 500, 742, "#EA580C", "arr-orange", "无改进计数++"))
    svg.append(draw_arrow(270, 785, 270, 815, "#9333EA", "arr-purple", "达到周期"))
    svg.append(draw_arrow(270, 890, 270, 915, "#475569", "arr-gray"))
    svg.append(draw_arrow(460, 933, 500, 933, "#16A34A", "arr-green", "否 (结束)"))
    # 循环回环
    svg.append(draw_path([(80, 933), (70, 933), (70, 480), (80, 480)], PRIMARY_BORDER, "arr-blue", "是: 下一代", (70, 700)))

    # 右栏：局部搜索算子 Iterated Greedy (Width: 500)
    svg.append(draw_panel(920, 380, 500, 580, "3. 迭代贪婪局部强化算子 (iterated_greedy.py)", "L1 基础算子 · 破坏-重建 · 模拟退火", ORANGE_BORDER))

    svg.append(draw_box(940, 435, 460, 85, [
        "3.1 初始配置与自适应温度 (IG Setup)",
        "• 起始排列: 接收 PSO gbest / 档案库种子排列",
        "• 初始退火温度: T_0 = max(1.0, current_makespan * 0.1)",
        "• 破坏比例: d = round(n_jobs * destruction_ratio) (默认 0.3n)",
        "• 最大迭代轮数: 15 ~ 20 轮"
    ], fill=ORANGE_BG, stroke=ORANGE_BORDER, badge="Setup"))

    svg.append(draw_box(940, 545, 460, 105, [
        "3.2 破坏阶段 (Destruction: 随机抽离工件)",
        "• 随机选取 d 个不同索引位置",
        "• 将被选工件从排列中抽离，保存为 destroyed_jobs",
        "• 剩余 (n - d) 个工件严格保持原有的相对先后次序",
        "  构成 partial sequence remaining_jobs"
    ], fill="#FFFBEB", stroke="#D97706", badge="Destruction"))

    svg.append(draw_box(940, 675, 460, 125, [
        "3.3 重建阶段 (Reconstruction: 贪心最优插入)",
        "• 遍历 destroyed_jobs 中的每个被抽离工件:",
        "  - 穷举探测当前部分序列的全部 (k + 1) 个插入位置",
        "  - 每次试探调用 env.evaluate(candidate_permutation)",
        "  - 选拔 makespan 最小的最佳位置完成放回插入",
        "• 重建出具有极强局部竞争力的完整新排列"
    ], fill="#FEF3C7", stroke="#B45309", badge="Reconstruction"))

    svg.append(draw_box(940, 825, 460, 125, [
        "3.4 退火接受准则与多模态扩展 (Acceptance & Multimodal)",
        "• 接受准则: 若 Δ = C_new - C_cur ≤ 0，必定接受",
        "  若 Δ > 0，则以概率 exp(-Δ / T) 接受劣解跳出局部极小",
        "• 几何降温: T ← T * cooling_rate (默认 0.95)",
        "• 多模态采样 (find_multimodal_solutions):",
        "  对基准解执行多次随机扰动 + IG，并发采集优质局域解"
    ], fill="#FFF1F2", stroke="#E11D48", badge="Annealing Acceptance"))

    # IG 内部连接
    svg.append(draw_arrow(1170, 520, 1170, 545, ORANGE_BORDER, "arr-orange"))
    svg.append(draw_arrow(1170, 650, 1170, 675, "#D97706", "arr-orange"))
    svg.append(draw_arrow(1170, 800, 1170, 825, "#B45309", "arr-orange"))

    # 从第一层到第二层的跨层数据流
    svg.append(draw_path([(975, 330), (975, 360), (270, 360), (270, 435)], PRIMARY_BORDER, "arr-blue", "启发式解作为种子注入", (600, 355)))

    # =========================================================================
    # 第三层：商集多模态档案库核心机制 (MultimodalArchive & schedule_distance.py) (Y: 990 -> 1460)
    # =========================================================================
    svg.append(draw_panel(60, 990, 1360, 470, "4. 调度商集空间 Π/~ 映射与多模态档案库核心准入机制 (multimodal_hfsp_solver.py & schedule_distance.py)", "L0 理论基石 + L3 多模态准入引擎 · 存调度不存排列", TEAL_BORDER))

    # 理论阐释：商集空间
    svg.append(draw_box(80, 1045, 1320, 75, [
        "核心公理：排列空间与调度空间的多对一映射 (Quotient Space: Π/~)",
        "• 结构等价关系: π₁ ~ π₂ ⟺ D(π₁) = D(π₂)，即两排列解码后在各阶段每台机器上的工件加工顺序完全相同。等价类中的多个排列仅属同一调度 S 的冗余表达。",
        "• 结构签名: Sig(π) = { (阶段 s, 机器 m): [工件在排列中的自然顺序] }。两解签名相同 ⟺ 属于同一结构等价类。必须在商集 Π/~ 上进行搜索与去重，严禁使用位置海明距离！"
    ], fill=TEAL_BG, stroke=TEAL_BORDER, badge="Mathematical Axiom"))

    # 结构距离两正交分量
    svg.append(draw_box(80, 1135, 360, 135, [
        "商集归一化结构距离 (Schedule Distance)",
        "• 机器分配距离 D_assign ∈ [0, 1]:",
        "  分配到不同机器的 (工件, 阶段) 对占比",
        "  D_assign = Σ I(M_A(j,s) ≠ M_B(j,s)) / (n · s)",
        "• 加工顺序距离 D_seq ∈ [0, 1]:",
        "  在同阶段同机器上的可比工件对中，",
        "  先后加工顺序发生颠倒的 Kendall-τ 比例",
        "• 向量化加速: ScheduleFeatures 整块广播"
    ], fill="#F0FDFA", stroke="#0D9488", badge="Metric Definition"))

    # 准入四步流程图
    svg.append(draw_box(470, 1135, 430, 310, [
        "多模态档案库入档严格四步准入机制 (add_solution)",
        "",
        "【步骤 ① 质量门限筛选 (Quality Cutoff)】",
        "  判断: candidate_makespan ≤ (1 + ρ) · best_makespan ？ (默认 ρ = 1%)",
        "  - 否: 记 rejected_quality，立即丢弃劣质候选",
        "",
        "【步骤 ② 结构签名等价类去重 (Equivalence Class Deduplication)】",
        "  计算结构签名 Sig(candidate)，遍历现有档案库解:",
        "  - 若签名完全相同: 仅当候选 makespan 更优时替换原解 (replaced)，否则拒收 (rejected_same_class)",
        "",
        "【步骤 ③ 析取式新颖性判定 (Disjunctive Novelty Check)】",
        "  二分查找锁定质量临界窗口，针对相近解比对正交结构距离:",
        "  - 仅当 「质量相近(≤ρ) 且 D_assign ≤ δ_m 且 D_seq ≤ δ_s」 三者同时满足时，才判定为冗余解拒收！",
        "  - 只要有一个维度展现出足够新颖性，即予以接纳入库 (admitted)！(默认 δ_m=0.05, δ_s=0.10)",
        "",
        "【步骤 ④ 质量剪枝与最远点容量裁剪 (Prune & Farthest-Point Trimming)】",
        "  - 质量剪枝: 若新解刷新全局 best，立即剪除超出新 (1+ρ)·best 的旧解",
        "  - 容量裁剪: 超过 capacity (200) 时，保留最优解，其余按「到已保集合的最小结构距离最大」贪心挑选"
    ], fill="#FFFFFF", stroke=TEAL_BORDER, bold_idx=0, badge="4-Step Admission"))

    # 档案库的自生状态与统计
    svg.append(draw_box(930, 1135, 470, 310, [
        "档案库核心语义与消融统计指标 (Archive State & Stats)",
        "",
        "• 状态属性与接口:",
        "  - solutions: 内部已排序的备选最优/近优调度集合",
        "  - equivalent_subset(): 提取 makespan = best 的绝对等优解集",
        "  - crowding(): 基于矩阵批量计算全库成员的结构孤立度向量",
        "  - _enrich_with_schedule_data(): 注入每道工序详细开始/结束时间",
        "",
        "• 完备的消融实验审计字典 (self.stats):",
        "  1. offered: 累计提审解数量",
        "  2. rejected_quality: 因超标 (1+ρ) 被阻拦解数",
        "  3. rejected_same_class: 结构相同且不占优势被阻拦解数",
        "  4. replaced_in_class: 结构相同但更优发生的原地替换数",
        "  5. rejected_too_close: 距离过近缺乏新颖性被阻拦解数",
        "  6. admitted: 成功入库解数",
        "  7. pruned_by_quality: 因全局最优刷新被动态剔除解数",
        "  8. trimmed: 超出容量上限被最远点法则裁剪解数"
    ], fill="#F8FAFC", stroke="#64748B", bold_idx=0, badge="Archive State"))

    # 第二层向第四层的入档汇聚线
    svg.append(draw_path([(500, 785), (500, 1010), (680, 1010), (680, 1135)], TEAL_BORDER, "arr-green", "PSO 候选解缓冲池批量灌入", (590, 1000)))
    svg.append(draw_path([(1170, 950), (1170, 1010), (720, 1010), (720, 1135)], TEAL_BORDER, "arr-green", "IG 精修与多模态解灌入", (945, 1000)))

    # =========================================================================
    # 第四层：档案库引导双向闭环搜索 (Archive-Guided Search) (Y: 1490 -> 1830)
    # =========================================================================
    svg.append(draw_panel(60, 1490, 1360, 340, "5. 档案库反向引导搜索：双向闭环与多智能体协同 (archive_guided_search.py)", "L2 核心突破 · 将静态容器转变为主动驱动状态机", PURPLE_BORDER))

    # 双向闭环交互示意
    svg.append(draw_box(80, 1545, 380, 265, [
        "5.1 档案库反馈闭环 Ⅰ：PSO 精英重启",
        "• 传统模式缺陷: 档案库只存不用，仅为搜索副产品",
        "• 闭环机制 (archive_pso_restart_generations):",
        "  1. 将档案库中的解排列绑定至 pso.diversity_pool",
        "  2. 重置停滞检测器与候选解池",
        "  3. 启动次级 PSO: 建群与停滞重初始化时，",
        "     大比例直接抽取档案库中保留的高质量等优解作为种子",
        "  4. 产出全新解集再次反哺冲刷档案库",
        "• 实现由多模态解向全局探索的强力能量注入"
    ], fill=PURPLE_BG, stroke=PURPLE_BORDER, badge="Closed-Loop I"))

    svg.append(draw_box(490, 1545, 460, 265, [
        "5.2 档案库引导闭环 Ⅱ：多样化定向游走 (Archive Guided Walk)",
        "• 轮次交替种子选择策略 (Alternating Seed Strategy):",
        "  - 奇数轮(强化 Intensify): 随机选取等优解 (best)，施加小扰动(15%)",
        "  - 偶数轮(探索 Explore): 选取全库孤立度最高者(argmax Crowding)，施加粗粒度大扰动(35%)",
        "",
        "• 多样化游走与新颖性接受 (Diversity Acceptance Walk):",
        "  - 种子经过扰动后执行 IG 重优化",
        "  - 接受判定不仅看 makespan，更纳入结构多样性:",
        "    【条件 A】candidate.makespan < current.makespan",
        "    【条件 B】不同等价类 (Sig_cand ≠ Sig_cur) 且 离起点结构距离更大",
        "  - 满足任一条件即被接受为新游走点！",
        "• 允许算法在等优平原上自由横向穿梭，避免局部塌陷"
    ], fill="#FAF5FF", stroke="#9333EA", badge="Guided Search"))

    # 多智能体协同求解机制
    svg.append(draw_box(980, 1545, 420, 265, [
        "5.3 协同求解分支：多智能体模式 (multi_agent)",
        "• 四类专业化搜索智能体 (Specialized Agents):",
        "  1. Seed Agent: NEH/SPT 初始启发式快速构建",
        "  2. Local Refiner: 基于 Ruiz 温度的 IG 针对性攻坚",
        "  3. Exploration Agent: 高变异率(1.8x)短跑 PSO 大面积勘探",
        "  4. Intensification Agent: 集中算力的小步距深度 PSO+IG 强化",
        "",
        "• 协同枢纽: 统一向 coordinator MultimodalArchive 提交候选",
        "• 动态效能评估: 统计各智能体的成功率与贡献度",
        "• 求解模式: basic_pso_ig / multi_agent / compare 对比"
    ], fill="#FFF7ED", stroke="#EA580C", badge="Multi-Agent Mode"))

    # 第四层内部闭环箭头
    svg.append(draw_path([(720, 1545), (720, 1460)], PURPLE_BORDER, "arr-purple", "采种引导", (690, 1500)))
    svg.append(draw_path([(750, 1460), (750, 1545)], TEAL_BORDER, "arr-green", "回写入库", (780, 1500)))

    # =========================================================================
    # 第五层：求解结果输出、多模态科学评价与下游工业应用 (Y: 1860 -> 2170)
    # =========================================================================
    svg.append(draw_panel(60, 1860, 1360, 310, "6. 求解结果、多模态科学评价指标与工业场景应用 (solver_analysis.py & multimodal_evaluation.py)", "L4 交付输出 · 理论评价 · 工业抗扰鲁棒性落地", ROSE_BORDER))

    svg.append(draw_box(80, 1915, 400, 235, [
        "6.1 最终结果组装与分析报告 (Solver Result)",
        "• 最优解确定: 取档案库第一名首选方案 (best_solution)",
        "• 算例统计摘要 (summary.json):",
        "  最优 makespan、计算耗时、全量求解配置",
        "• 制造瓶颈深度分析 (solver_analysis.py):",
        "  - 阶段负荷与瓶颈阶段定位",
        "  - 各机器有效工时与平均利用率利用分析",
        "  - 工件各阶段平均排队等待时间与空闲分析",
        "• 可视化甘特图: 自动生成工序级多色彩分配图"
    ], fill="#FFF1F2", stroke=ROSE_BORDER, badge="Output Data"))

    svg.append(draw_box(510, 1915, 430, 235, [
        "6.2 多模态学术评价四维指标体系 (Multimodal Evaluation)",
        "• 指标 1 · 等优解数量 N_ρ (Equivalent Solution Count):",
        "  统计 makespan ≤ (1+ρ)·best 的结构互异解数目 (ρ=0, 1%, 2%, 5%)",
        "• 指标 2 · 解集结构多样性 Diversity_pair:",
        "  库内等优解两两之间的平均机器分配距离与加工顺序距离",
        "• 指标 3 · 空间覆盖度与稀疏采样均衡性:",
        "  衡量解在解空间 Pareto 结构前沿上的分散均匀度",
        "• 消融对比: 科学证实档案库引导显著优于盲目存解与单解算法"
    ], fill="#EFF6FF", stroke="#3B82F6", badge="Academic Metrics"))

    svg.append(draw_box(970, 1915, 430, 235, [
        "6.3 工业现场应用：机器故障免重算秒级动态切换",
        "• 工业痛点: 传统算法只给单解，机器突然停机必须暂停产线重新耗费数十分钟计算",
        "• 本系统解决方案 (demo_fault_switching.py):",
        "  1. 预先持有多模态档案库中互异但性能等优的 k 个结构候选",
        "  2. 突发故障时，将 k 条解并行代入故障场景进行损伤评估",
        "  3. 遴选因故障受阻最小、完工时间恶化度最低的备选解瞬间顶上",
        "• 零重算响应: 算法复杂度 O(k)，实现毫秒级快速弹性切换！"
    ], fill="#F0FDF4", stroke="#16A34A", badge="Zero-Recalculation"))

    # 从第四层到第五层的最终汇聚箭头
    svg.append(draw_arrow(270, 1830, 270, 1915, ROSE_BORDER, "arr-purple", "最终解集输出"))
    svg.append(draw_arrow(720, 1830, 720, 1915, "#3B82F6", "arr-blue", "多模态指标评估"))
    svg.append(draw_arrow(1180, 1830, 1180, 1915, "#16A34A", "arr-green", "下发工业应用"))

    svg.append('</svg>')
    
    Path(output_path).write_text("\n".join(svg), encoding="utf-8")
    print(f"成功生成 SVG 流程图: {output_path}")

if __name__ == "__main__":
    generate_svg("docs/系统完整架构流程图.svg")
