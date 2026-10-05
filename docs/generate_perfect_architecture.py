# -*- coding: utf-8 -*-
"""完整版：HFSP 全项目架构与求解流程图生成脚本。
五大支柱高度均衡、全程无空白、涵盖 16 个源文件、所有数学公式与三种求解模式。
"""
from pathlib import Path

def generate_perfect_architecture():
    # 画布尺寸
    W, H = 2260, 1480

    BG_CANVAS = "#FBF9F1"
    PANEL_BG = "rgba(255, 255, 255, 0.92)"

    C_BLUE_BG = "#EBF3FC"
    C_BLUE_BORDER = "#3A82E4"
    C_BLUE_TXT = "#1A365D"

    C_ORANGE_BG = "#FDF2E4"
    C_ORANGE_BORDER = "#E67A1E"
    C_ORANGE_TXT = "#7C2D12"

    C_PURPLE_BG = "#F5EEF8"
    C_PURPLE_BORDER = "#9C56B8"
    C_PURPLE_TXT = "#4A154B"

    C_RED_BG = "#FDEDEC"
    C_RED_BORDER = "#E74C3C"
    C_RED_TXT = "#78281F"

    C_GREEN_BG = "#EAF7EE"
    C_GREEN_BORDER = "#27AE60"
    C_GREEN_TXT = "#145A32"

    C_TEAL_BG = "#E6FFFA"
    C_TEAL_BORDER = "#0D9488"
    C_TEAL_TXT = "#115E59"

    C_LINE = "#475569"
    C_DASH = "#94A3B8"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('<defs>')
    svg.append('''
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#475569" />
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#3A82E4" />
        </marker>
        <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#E67A1E" />
        </marker>
        <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#9C56B8" />
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#27AE60" />
        </marker>
        <filter id="shadow" x="-2%" y="-2%" width="104%" height="106%" filterUnits="userSpaceOnUse">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06"/>
        </filter>
        <style>
            .title-main { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 800; font-size: 27px; fill: #0F172A; }
            .title-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 500; font-size: 13.5px; fill: #475569; }
            .col-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 800; font-size: 15.5px; }
            .sec-tag { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 700; font-size: 11px; }
            .box-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 700; font-size: 12.5px; }
            .box-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 400; font-size: 11.2px; line-height: 1.45; }
            .lbl-branch { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-size: 11px; font-weight: 600; fill: #334155; }
        </style>
    ''')
    svg.append('</defs>')

    svg.append(f'<rect width="{W}" height="{H}" fill="{BG_CANVAS}" />')

    # 顶部标题
    svg.append(f'''
    <g transform="translate(0, 36)">
        <text x="{W/2}" y="0" text-anchor="middle" class="title-main">HFSP 混合流水车间调度求解系统 · 全项目完整架构与求解全流程图</text>
        <text x="{W/2}" y="27" text-anchor="middle" class="title-sub">涵盖系统 5 层架构、16 个源文件、商集空间 Π/~ 理论、小生境离散 PSO、退火 IG、三种求解模式 (basic / multi_agent / compare)、档案四步准入与工业弹性切换</text>
    </g>
    ''')

    # 顶部系统分层与依赖导航
    layers = [
        ("L0 基础设施与评测核", "hfsp_environment.py · schedule_distance.py", C_BLUE_BG, C_BLUE_BORDER, C_BLUE_TXT),
        ("L1 基础优化算子", "iterated_greedy.py · niching_mechanism.py", C_ORANGE_BG, C_ORANGE_BORDER, C_ORANGE_TXT),
        ("L2 混合搜索器", "niching_pso.py · archive_guided_search.py", C_PURPLE_BG, C_PURPLE_BORDER, C_PURPLE_TXT),
        ("L3 主求解器与编排", "multimodal_hfsp_solver.py (三种求解模式)", C_TEAL_BG, C_TEAL_BORDER, C_TEAL_TXT),
        ("L4 学术指标与工业落地", "multimodal_evaluation.py · demo_fault_switching.py", C_GREEN_BG, C_GREEN_BORDER, C_GREEN_TXT),
        ("批量实验与对比评测", "run_carlier_multimodal_benchmark.py · report_*.py", C_BLUE_BG, C_BLUE_BORDER, C_BLUE_TXT),
    ]
    ly_w, ly_h, ly_gap, ly_x0, ly_y0 = 335, 46, 26, 45, 80
    for i, (l_top, l_sub, bg, border, txt) in enumerate(layers):
        lx = ly_x0 + i * (ly_w + ly_gap)
        svg.append(f'''
        <g transform="translate({lx}, {ly_y0})">
            <rect width="{ly_w}" height="{ly_h}" rx="6" fill="{bg}" stroke="{border}" stroke-width="1.3" filter="url(#shadow)"/>
            <text x="{ly_w/2}" y="19" text-anchor="middle" class="box-title" fill="{txt}">{l_top}</text>
            <text x="{ly_w/2}" y="34" text-anchor="middle" class="box-body" fill="{txt}" opacity="0.85">{l_sub}</text>
        </g>
        ''')
        if i < len(layers) - 1:
            arr_x1 = lx + ly_w
            arr_x2 = arr_x1 + ly_gap
            svg.append(f'<line x1="{arr_x1}" y1="{ly_y0 + ly_h/2}" x2="{arr_x2}" y2="{ly_y0 + ly_h/2}" stroke="{C_LINE}" stroke-width="1.4" marker-end="url(#arrow)"/>')

    def xesc(s):
        if not isinstance(s, str):
            return "" if s is None else str(s)
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    # 辅助绘图函数
    def draw_node(x, y, w, h, title, lines, bg=C_BLUE_BG, border=C_BLUE_BORDER, txt=C_BLUE_TXT, tag=None):
        out = [f'<g transform="translate({x}, {y})">']
        out.append(f'<rect width="{w}" height="{h}" rx="7" fill="{bg}" stroke="{border}" stroke-width="1.3" filter="url(#shadow)"/>')
        if tag:
            out.append(f'<rect x="8" y="7" width="{len(tag)*8+10}" height="17" rx="3.5" fill="{border}" fill-opacity="0.15"/>')
            out.append(f'<text x="{13+len(tag)*4}" y="19" text-anchor="middle" class="sec-tag" fill="{border}">{xesc(tag)}</text>')
            out.append(f'<text x="{26+len(tag)*8}" y="20" class="box-title" fill="{txt}">{xesc(title)}</text>')
        else:
            out.append(f'<text x="12" y="20" class="box-title" fill="{txt}">{xesc(title)}</text>')
        
        cur_y = 38
        for l in lines:
            esc_l = xesc(l)
            if l.startswith("•"):
                out.append(f'<text x="12" y="{cur_y}" class="box-body" fill="{txt}" font-weight="700">{esc_l}</text>')
            elif l.startswith("  -"):
                out.append(f'<text x="18" y="{cur_y}" class="box-body" fill="{txt}">{esc_l}</text>')
            elif l.startswith("  "):
                out.append(f'<text x="24" y="{cur_y}" class="box-body" fill="{txt}" opacity="0.9">{esc_l}</text>')
            else:
                out.append(f'<text x="12" y="{cur_y}" class="box-body" fill="{txt}">{esc_l}</text>')
            cur_y += 15.5
        out.append('</g>')
        return "\n".join(out)

    def draw_diamond(cx, cy, rx, ry, title, subtitle="", bg=C_RED_BG, border=C_RED_BORDER, txt=C_RED_TXT):
        pts = f"{cx},{cy-ry} {cx+rx},{cy} {cx},{cy+ry} {cx-rx},{cy}"
        out = [
            f'<polygon points="{pts}" fill="{bg}" stroke="{border}" stroke-width="1.4" filter="url(#shadow)"/>',
            f'<text x="{cx}" y="{cy - (3.5 if subtitle else -4)}" text-anchor="middle" class="box-title" font-size="11.5" fill="{txt}">{xesc(title)}</text>'
        ]
        if subtitle:
            out.append(f'<text x="{cx}" y="{cy+13}" text-anchor="middle" class="box-body" font-size="10" fill="{txt}" opacity="0.9">{xesc(subtitle)}</text>')
        return "\n".join(out)

    # 布局参数：五大支柱
    COL_Y = 145
    COL_H = 1240

    C1_X, C1_W = 35, 415     # ① 建模、ECT 解码与商集距离 (L0)
    C2_X, C2_W = 475, 475    # ② 小生境 PSO 与 IG 深度搜索 (L1/L2)
    C3_X, C3_W = 975, 400    # ③ 求解器编排与三种求解模式 (L3)
    C4_X, C4_W = 1400, 405   # ④ 多模态档案准入与双向引导 (L2/L3)
    C5_X, C5_W = 1830, 395   # ⑤ 制造分析、学术指标与工业落地 (L4)

    col_headers = [
        (C1_X, C1_W, "① 建模、ECT 解码与商集距离 (L0)", "#1E40AF"),
        (C2_X, C2_W, "② 小生境 PSO 与 IG 深度优化 (L1/L2)", "#C2410C"),
        (C3_X, C3_W, "③ 求解模式分派与多智能体协同 (L3)", "#0F766E"),
        (C4_X, C4_W, "④ 多模态档案准入与引导闭环 (L2/L3)", "#7E22CE"),
        (C5_X, C5_W, "⑤ 结果分析、学术指标与工业落地 (L4)", "#15803D"),
    ]

    for cx, cw, title, tcolor in col_headers:
        svg.append(f'''
        <g transform="translate({cx}, {COL_Y})">
            <rect width="{cw}" height="{COL_H}" rx="10" fill="{PANEL_BG}" stroke="#CBD5E1" stroke-width="1.4" stroke-dasharray="5,4"/>
            <text x="16" y="25" class="col-title" fill="{tcolor}">{title}</text>
        </g>
        ''')

    # =========================================================================
    # 栏目 1: 算例建模、ECT 解码内核与商集距离 (C1)
    # =========================================================================
    b1x = C1_X + 14
    b1w = C1_W - 28

    svg.append(draw_node(b1x, 190, b1w, 120, "算例输入与环境建模 (5benchmark/)", [
        "• 支持 Carlier 96 例 / Small / Big TXT 基准算例",
        "• 工件数 n, 阶段数 s, 各阶段机器数 m_s",
        "• 三维加工时间矩阵: P[job][stage][machine]",
        "• 统一校验工件唯一性、无等待/拓扑有效性",
        "• 封装为不可变对象 HFSPEnvironment"
    ], tag="1.1 输入"))

    svg.append(draw_node(b1x, 335, b1w, 175, "确定性唯一解码映射核 D: Π → S (ECT 规则)", [
        "• 阶段拓扑推进: stage = 0 → s-1",
        "• 阶段内严格按工件排列 π 的先后顺序派工",
        "• Earliest Completion Time (最早完工机器选择):",
        "  C[j,s,m] = max(MachineReady, JobDone) + p[j,s,m]",
        "• 内置 LRU 评估缓存，消除相同排列重复计算",
        "• 输出不可变 ScheduleEvaluation: 包含 makespan、完工时间、",
        "  各阶段机器分配阵列与逐工序明细 operations"
    ], bg="#F0FDF4", border="#16A34A", txt="#145A32", tag="1.2 解码"))

    svg.append(draw_node(b1x, 535, b1w, 150, "启发式基准计算 (NEH / SPT 基线)", [
        "• NEH 启发式 (高水准基准与初始全局下界):",
        "  - 各工件在各阶段平均加工工时降序排序",
        "  - 逐个工件在当前序列中穷举贪心最优插入",
        "• SPT 启发式 (短工时优先，经典工程基线):",
        "  - 按工件平均加工时间升序直接调用 D(π) 解码",
        "• 产出高质量探索种子与对照基底"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="1.3 基线"))

    svg.append(draw_node(b1x, 710, b1w, 235, "商集理论 Π/~ 与正交结构距离 (schedule_distance.py)", [
        "• 核心公理: 排列空间与调度空间是多对一映射",
        "  不同排列解码后在机器上的顺序完全相同 (等价类)",
        "  结构等价关系: π₁ ~ π₂ ⟺ D(π₁) = D(π₂)",
        "• 结构签名 Sig(π)={ (阶段, 机器): 工件加工顺序 }",
        "• 两大正交归一化结构距离 (∈ [0, 1]):",
        "  - 机器分配距离 D_assign: 分配到不同机器的对占比",
        "  - 加工顺序距离 D_seq: 相同机器上先后颠倒的 Kendall-τ 比例",
        "• 向量化矩阵加速: ScheduleFeatures 批量广播，",
        "  将 O(m²) 距离调用耗时从 20 分钟骤降至 16 秒！"
    ], bg=C_TEAL_BG, border=C_TEAL_BORDER, txt=C_TEAL_TXT, tag="1.4 商集"))

    svg.append(draw_node(b1x, 970, b1w, 150, "商集空间映射图示 (为什么排列 ≠ 调度)", [
        "• 排列空间 Π: [π₁, π₂, π₃] 具有不同位置海明距离",
        "• 经过 ECT 解码核映射到商集 Π/~:",
        "  D(π₁) = D(π₂) = D(π₃) ⟹ 归入同一【调度 A】",
        "• 档案库判定原则: 同一调度只保留一个代表元！",
        "• 结构不同且完工期均最优的调度 ⟹ 真正的等优解！"
    ], bg=C_BLUE_BG, border=C_BLUE_BORDER, txt=C_BLUE_TXT, tag="1.5 机理"))

    # C1 内部箭头
    svg.append(f'<line x1="{b1x+b1w/2}" y1="310" x2="{b1x+b1w/2}" y2="335" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b1x+b1w/2}" y1="510" x2="{b1x+b1w/2}" y2="535" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b1x+b1w/2}" y1="685" x2="{b1x+b1w/2}" y2="710" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b1x+b1w/2}" y1="945" x2="{b1x+b1w/2}" y2="970" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # =========================================================================
    # 栏目 2: 小生境 PSO 全局搜索与 IG 深度优化 (C2)
    # =========================================================================
    b2x = C2_X + 14
    b2w = C2_W - 28

    svg.append(draw_node(b2x, 190, b2w, 160, "初始化多梯队种群 (N=40) 与进入候选缓冲", [
        "• 种群规模 N=40，逐个评估后进入候选缓冲池:",
        "  - 梯队1: 1 个 NEH 确定性解 (高质量全局锚点)",
        "  - 梯队2: 1 个 SPT 确定性解 (异构工程启发基线)",
        "  - 梯队3: 4 个 NEH 邻域扰动解 (小强度交换对, 扩至 6 个)",
        "  - 梯队4: 4 个 SPT 邻域扰动解 (适度扰动对, 扩至 10 个)",
        "  - 梯队5: (若引导重启) 注入档案库精英解 pool (quota ≤ 30%)",
        "  - 梯队6: 约 30 个全随机排列补齐 N=40，保障全空间分散度",
        "• 候选缓冲: seen_positions 查重，未见新排列写入缓冲池"
    ], tag="2.1 建群"))

    svg.append(draw_node(b2x, 375, b2w, 135, "自适应惯性权重、环形邻域与变异率控制", [
        "• 惯性权重线性递减: w(t) = 0.9 - 0.5 × (t / (T-1))",
        "  - 前期 w ≈ 0.9 保持动量全局探索; 后期 w ≈ 0.4 局部聚焦收敛",
        "• 环形拓扑 (Ring): 粒子仅与左右 k=3 个邻居通信",
        "• 小生境聚类 (Niching): 排列距离 ≤ 3 划入同生境，获取局部最优 lbest",
        "• 自适应变异率: P_mut = min(0.45, 0.08 + 多样性增益 + 停滞增益)",
        "  - 种群拥挤 (Diversity < 0.25) 或停滞时，变异率自动补偿放大"
    ], tag="2.2 控制"))

    svg.append(draw_node(b2x, 535, b2w, 140, "局部引导交换序、速度与位置更新 (防单峰塌陷)", [
        "• 构造认知 / 社会离散速度 (交换序列 SwapSeq):",
        "  - 认知分量: 抽取变至个体历史最优的交换对 SwapSeq(x, pbest)",
        "  - 社会分量: 抽取变至同生境局部最优的 SwapSeq(x, lbest)",
        "  - 用意: 追随局部最优 lbest 促成多峰并行开采，避免全群陷入单一伪极值",
        "• 速度公式: V = w⊙V ⊕ c₁⊙Sample(pbest) ⊕ c₂⊙Sample(lbest)",
        "• 施加位置交换: 依次实施交换对; 依 P_mut 施加随机换位变异"
    ], tag="2.3 推进"))

    svg.append(draw_node(b2x, 700, b2w, 125, "解码评价新粒子、更新最优与候选缓冲 (步步留痕)", [
        "• 统一调用 D(x) 解码，计算当前 makespan 与工序机器分配",
        "• 更新粒子个体历史最优 pbest 与当前代全局最优 gbest",
        "• 候选缓冲深层用意 (步步留痕):",
        "  - 粒子飞行中只要踩到未见过的排列即记录入池，升序维护前 200 名",
        "  - 截断丢弃 200 名之后劣解; 保证粒子飞行轨迹中沿途发现的",
        "    大量优质多模态方案被实时留存，为最终档案库留足种子"
    ], tag="2.4 缓冲"))

    svg.append(draw_node(b2x, 850, b2w, 150, "周期执行 IG 精修与停滞多样性重初始化", [
        "• 周期性 IG 嵌入 (每隔 T/5 = 12 代固定触发):",
        "  - 对当前 gbest 运行破坏重建退火；若挖出更优解，直接覆盖替换",
        "    种群中最差粒子 (worst_fitness)，强力拉升全群进化重心；解入缓冲",
        "• 停滞检测与多样性重初始化:",
        "  - 连续 10 代无全局最优改进 → 触发停滞响应",
        "  - 保护 gbest，淘汰最差 20% 粒子: 50% 从档案库注入精英，",
        "    50% 纯随机重启，兼顾深度利用与广度探索"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="2.5 精修"))

    # D1 循环判断
    d1_cx, d1_cy = b2x + b2w/2, 1045
    svg.append(draw_diamond(d1_cx, d1_cy, 125, 24, "代数 gen + 1 < max_gen ?", "默认迭代 60 代"))

    # 阶段 2.6：PSO 结束后最终 IG 强化与多模态采样
    svg.append(draw_node(b2x, 1095, b2w, 125, "最终 IG 两阶段深度强化与多模态采样 (iterated_greedy.py)", [
        "• 以 PSO 的 gbest 为起点执行最终 IG 强化优化 (Ruiz 初始温度)",
        "• 破坏 (Destruction: 随机抽离 30% 工件) + 重建 (贪心最优插入放回)",
        "• 模拟退火接受准则: 劣解以 exp(-Δ/T) 概率接受跳出极值陷阱",
        "• 多模态并发采样 find_multimodal_solutions: 扰动+IG 采 5 条候选解",
        "• 产出最终精修解与局域多模态解，直接注入主求解器档案中枢"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="2.6 采样"))

    # C2 内部连接
    svg.append(f'<line x1="{b2x+b2w/2}" y1="350" x2="{b2x+b2w/2}" y2="375" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="510" x2="{b2x+b2w/2}" y2="535" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="675" x2="{b2x+b2w/2}" y2="700" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="825" x2="{b2x+b2w/2}" y2="850" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="1000" x2="{b2x+b2w/2}" y2="{d1_cy-24}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D1 回环
    pso_loop_x = b2x - 8
    svg.append(f'''
    <path d="M {d1_cx - 125} {d1_cy} L {pso_loop_x} {d1_cy} L {pso_loop_x} 440 L {b2x} 440" fill="none" stroke="{C_BLUE_BORDER}" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
    <text x="{pso_loop_x + 8}" y="{d1_cy - 8}" class="lbl-branch" fill="{C_BLUE_BORDER}">是: 下一代</text>
    ''')

    # D1 (否) -> 2.6
    svg.append(f'<line x1="{d1_cx}" y1="{d1_cy+24}" x2="{d1_cx}" y2="1095" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{d1_cx + 8}" y="{d1_cy+18}" class="lbl-branch">否: 结束</text>')

    # C1 -> C2 基线注入
    svg.append(f'''
    <path d="M {b1x+b1w} 600 L {C2_X - 10} 600 L {C2_X - 10} 270 L {b2x} 270" fill="none" stroke="{C_LINE}" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)"/>
    <text x="{C2_X - 45}" y="262" class="lbl-branch">基线注入</text>
    ''')

    # =========================================================================
    # 栏目 3: 求解器主编排与三种求解模式 (C3)
    # =========================================================================
    b3x = C3_X + 14
    b3w = C3_W - 28

    svg.append(draw_node(b3x, 190, b3w, 130, "主求解器调度中枢 (solve_environment)", [
        "• 统一参数管理 SolverConfig: 种群、代数、公差等",
        "• 先行计算 NEH / SPT 两大基线备用",
        "• 核心模式分派分流 (mode 参数):",
        "  - basic_pso_ig: 经典两阶段混合求解",
        "  - multi_agent: 四智能体协同协同求解",
        "  - compare: 双模式对照择优求解"
    ], tag="3.1 分派"))

    svg.append(draw_node(b3x, 345, b3w, 155, "模式一 · 经典两阶段 basic_pso_ig (推荐主线)", [
        "• 架构流水线: NEH/SPT → Niching PSO → IG 最终强化 → 档案引导",
        "• 优势: 阶段边界清晰、搜索力度强劲、多模态解集丰富",
        "• 候选汇聚: 将 PSO 缓冲池 200 解 + IG 精修解 + 多模态采样解",
        "  一次性统一送入 _build_archive 构建初始档案库",
        "• 可选衔接: 触发档案库引导搜索与 PSO Elite Restart 闭环"
    ], bg=C_BLUE_BG, border=C_BLUE_BORDER, txt=C_BLUE_TXT, tag="3.2 基础模式"))

    svg.append(draw_node(b3x, 525, b3w, 310, "模式二 · 四智能体协同 multi_agent (专业分工)", [
        "• 四类异构搜索智能体协同运作:",
        "  1. Seed Agent (种子智能体):",
        "     - NEH / SPT 策略快速构建高质量起点",
        "  2. Local Refiner Agent (局部精修智能体):",
        "     - 基于 Ruiz 温度的 IG 针对性攻坚强化",
        "  3. Exploration Agent (扩展探索智能体):",
        "     - 高变异率 (1.8x) 短跑 PSO 大面积勘探解空间",
        "  4. Intensification Agent (重点强化智能体):",
        "     - 小步距集中算力深度 PSO+IG 强化深井",
        "• 协同枢纽机制 (Coordinator Archive):",
        "  - 各智能体统一向共享 MultimodalArchive 提交候选",
        "  - 动态统计各 Agent 提报解数、贡献度与胜出率",
        "  - 记录详细协同报告 agent_reports 用于学术机制分析"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="3.3 多智能体"))

    svg.append(draw_node(b3x, 860, b3w, 180, "模式三 · 对照竞争决策 compare (消融首选)", [
        "• 并行独立执行 basic_pso_ig 与 multi_agent 求解",
        "• 自动生成综合对比字典 comparison:",
        "  - 完工期对比 (best_makespan 对比)",
        "  - 求解耗时对比 (elapsed_seconds 对比)",
        "  - 档案库规模对比 (archive_size 对比)",
        "• 胜出者裁定: 完工期更小者胜出; 平手时取耗时更短者",
        "• 专为论文消融实验、算法优劣对比定制的决策出口"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="3.4 对照模式"))

    svg.append(draw_node(b3x, 1065, b3w, 155, "候选解池全量汇聚 (_build_archive)", [
        "• 汇集来源:",
        "  ① PSO 产生的 200 个高质量候选解缓冲",
        "  ② IG 局部深度精修产出的全局最优解",
        "  ③ IG 多模态扰动采样的 5 条近优局部解",
        "• 一并输入第四栏多模态档案库进行四步严格质检"
    ], bg=C_TEAL_BG, border=C_TEAL_BORDER, txt=C_TEAL_TXT, tag="3.5 汇聚"))

    # C3 内部连接
    svg.append(f'<line x1="{b3x+b3w/2}" y1="320" x2="{b3x+b3w/2}" y2="345" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="500" x2="{b3x+b3w/2}" y2="525" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="835" x2="{b3x+b3w/2}" y2="860" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="1040" x2="{b3x+b3w/2}" y2="1065" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # C2 -> C3 候选解注入
    svg.append(f'''
    <path d="M {b2x+b2w} 1150 L {C3_X - 10} 1150 L {C3_X - 10} 420 L {b3x} 420" fill="none" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="{C3_X - 55}" y="412" class="lbl-branch">候选解流转</text>
    ''')

    # =========================================================================
    # 栏目 4: 多模态档案库准入引擎与双向引导闭环 (C4)
    # =========================================================================
    b4x = C4_X + 14
    b4w = C4_W - 28

    svg.append(draw_node(b4x, 190, b4w, 310, "多模态档案库严格四步准入机制 (MultimodalArchive)", [
        "• 核心宗旨: 存调度不存排列，每个结构等价类只留唯一代表元",
        "",
        "【步骤 ① 质量门限筛选 (Quality Cutoff)】",
        "  判断 makespan ≤ (1 + ρ) · best (默认 ρ = 1%)，超标即拒收",
        "",
        "【步骤 ② 结构签名等价类去重 (Equivalence Deduplication)】",
        "  计算结构签名 Sig(π)；若签名相同，仅在候选更优时原地替换，",
        "  否则视作同调度冗余拒绝 (rejected_same_class)",
        "",
        "【步骤 ③ 析取式三维新颖性判定 (Disjunctive Novelty)】",
        "  二分窗口比对相近解: 仅当「质量相近 且 D_m ≤ 0.05",
        "  且 D_s ≤ 0.10」同时满足时才拒收；有一项新颖即接纳入档",
        "",
        "【步骤 ④ 质量动态剪枝与最远点优先容量裁剪】",
        "  - 剪枝: 最优刷新后，自动剔除超出新门限的陈旧解",
        "  - 裁剪: 超过容量(200)时，按最远点优先法则贪心挑选最分散子集",
        "• 完善的审计字典 stats: 记录 rejected_quality / same_class / trimmed"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="4.1 档案准入"))

    # D3 是否启用引导
    d3_cx, d3_cy = b4x + b4w/2, 545
    svg.append(draw_diamond(d3_cx, d3_cy, 120, 22, "启用档案引导？", "archive_guided_rounds > 0"))

    svg.append(draw_node(b4x, 600, b4w, 100, "档案引导闭环 Ⅰ · 精英注入重启 PSO", [
        "• 将档案库等优排列整体赋给 pso.diversity_pool",
        "• 重置停滞计数，执行 archive_pso_restart_generations 代短跑",
        "• 初始建群与停滞时高比例注入精英种子，产出新解全量冲刷档案库",
        "• 形成由高质量多模态解集反向赋能全局探索的强力闭环"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="4.2 重启闭环"))

    svg.append(draw_node(b4x, 725, b4w, 170, "档案引导闭环 Ⅱ · 定向多样化游走 (AGS)", [
        "• 轮次交替种子选择 (Alternating Seed Strategy):",
        "  - 偶数轮(强化 Intensify): 从等优解集中随机挑，小扰动 15%",
        "  - 奇数轮(探索 Explore): 挑最孤立解 argmax(Crowding)，大扰动 35%",
        "• 多样化游走与新颖性接受准则 (Diversity Acceptance Walk):",
        "  - 种子扰动后执行 IG 重优化",
        "  - 核心突破: makespan 更好 或 (不同等价类 且 离起点更远) 均接受，",
        "    允许在等优平原横向平移而不塌陷；每个候选调用 add_solution 入档"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="4.3 引导游走"))

    # D4 循环判断
    d4_cx, d4_cy = b4x + b4w/2, 940
    svg.append(draw_diamond(d4_cx, d4_cy, 125, 22, "未停滞且未达最大轮数？", "stagnation < 15 且 rounds < Max"))

    svg.append(draw_node(b4x, 1000, b4w, 80, "比较档案库首解，更优则更新最终 best", [
        "• 若引导搜索挖掘出比原先全局最优更低的 makespan，",
        "  将档案库第 1 名刷新为最终全局最优解 best_evaluation",
        "• 实现档案库不仅存解、更反哺单解最优的双重价值"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="4.4 最终更新"))

    svg.append(draw_node(b4x, 1105, b4w, 115, "工序明细数据补充 (_enrich_with_schedule_data)", [
        "• 遍历档案库所有保留解，调用统一解码器补充:",
        "  - completion_times: 每个工件的最终完工时刻",
        "  - operations: 每道工序的 (开始时刻, 完工时刻, 机器号)",
        "• 保证档案库保存的 JSON 解集可直接用于甘特图渲染"
    ], bg=C_TEAL_BG, border=C_TEAL_BORDER, txt=C_TEAL_TXT, tag="4.5 数据补全"))

    # C4 内部连接
    svg.append(f'<line x1="{b4x+b4w/2}" y1="500" x2="{b4x+b4w/2}" y2="{d3_cy-22}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{d3_cx}" y1="{d3_cy+22}" x2="{d3_cx}" y2="600" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{d3_cx + 8}" y="{d3_cy+18}" class="lbl-branch">是</text>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="700" x2="{b4x+b4w/2}" y2="725" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="895" x2="{b4x+b4w/2}" y2="{d4_cy-22}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D4 回环
    ags_loop_x = b4x - 8
    svg.append(f'''
    <path d="M {d4_cx - 125} {d4_cy} L {ags_loop_x} {d4_cy} L {ags_loop_x} 775 L {b4x} 775" fill="none" stroke="{C_ORANGE_BORDER}" stroke-width="1.4" marker-end="url(#arrow-orange)"/>
    <text x="{ags_loop_x + 6}" y="{d4_cy - 6}" class="lbl-branch" fill="{C_ORANGE_BORDER}">是: 继续开采</text>
    ''')

    # D4 (否) -> 4.4 -> 4.5
    svg.append(f'<line x1="{d4_cx}" y1="{d4_cy+22}" x2="{d4_cx}" y2="1000" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{d4_cx + 8}" y="{d4_cy+18}" class="lbl-branch">否: 结束</text>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="1080" x2="{b4x+b4w/2}" y2="1105" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # C3 -> C4 解写入
    svg.append(f'''
    <path d="M {b3x+b3w} 1130 L {C4_X - 10} 1130 L {C4_X - 10} 245 L {b4x} 245" fill="none" stroke="{C_PURPLE_BORDER}" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
    <text x="{C4_X - 55}" y="237" class="lbl-branch">候选入档</text>
    ''')

    # =========================================================================
    # 栏目 5: 结果分析、学术指标、工业落地与批量评测 (C5)
    # =========================================================================
    b5x = C5_X + 14
    b5w = C5_W - 28

    svg.append(draw_node(b5x, 190, b5w, 145, "标准化求解结果组装 (_build_solver_result)", [
        "• best_solution: 档案库第 1 名最优调度方案",
        "• archive: 结构互异的多模态解集 (含逐工序甘特图数据)",
        "• baselines: NEH / SPT 对照值与加速比",
        "• metadata: 记录消融统计 stats 与各阶段精确耗时",
        "• 保存为 summary.json 与 multimodal_archive.json"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="5.1 结果组装"))

    svg.append(draw_node(b5x, 360, b5w, 160, "制造工程深度分析 (solver_analysis.py)", [
        "• 阶段负荷分析: 各阶段总加工工时与瓶颈定位",
        "• 机器利用率分析: 每台机器有效利用率与空闲占比",
        "• 工件排队分析: 各工件在各阶段之间的平均排队等待时间",
        "• 静态甘特图导出 (gantt_chart_generator.py):",
        "  基于 matplotlib 自动生成工序级多色彩分配甘特图"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="5.2 工程分析"))

    svg.append(draw_node(b5x, 545, b5w, 170, "学术多模态科学评价体系 (multimodal_evaluation.py)", [
        "• 等优解数量 N_ρ: makespan ≤ (1+ρ)·best 的",
        "  结构互异解数目 (ρ = 0, 1%, 2%, 5%)",
        "• 解集结构多样性 Diversity_pair:",
        "  库内等优解两两平均机器分配距离与加工顺序距离",
        "• 空间覆盖度与稀疏采样均衡性分析",
        "• 消融证实: 档案引导在解集质量与多样性上显著超越单解算法"
    ], bg=C_BLUE_BG, border=C_BLUE_BORDER, txt=C_BLUE_TXT, tag="5.3 学术指标"))

    svg.append(draw_node(b5x, 740, b5w, 185, "工业落地: 机器故障免重算秒级弹性切换", [
        "• 工业痛点: 机器突然停机，传统单解需停线耗费数十分钟重算",
        "• 本系统解决方案 (demo_fault_switching.py):",
        "  1. 预先持有多模态档案库中互异等优的 k 个结构候选",
        "  2. 突发故障时，将 k 条解并行代入故障场景进行损伤评估",
        "  3. 遴选因故障完工期恶化最小的备选解瞬间顶上",
        "• 零重算响应: 算法复杂度仅 O(k)，实现毫秒级快速切换！"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="5.4 工业落地"))

    svg.append(draw_node(b5x, 950, b5w, 175, "批量基准对比与实验总控 (run_carlier_multimodal_benchmark.py)", [
        "• 批量流水线: Carlier 96 算例 / Small_Size / Big_Size 批量比对",
        "• 三方对照: 基线(只存不用) vs 档案引导 vs 老师MOAIG",
        "• 输出 csv 实验总表与 report_multimodal_results 报表",
        "• 一键复现论文完整消融实验数据与科研结论",
        "• 单元测试验证: bulk_distance 向量化与标量版本 100% 等价"
    ], bg=C_TEAL_BG, border=C_TEAL_BORDER, txt=C_TEAL_TXT, tag="5.5 批量评测"))

    svg.append(draw_node(b5x, 1150, b5w, 75, "交付物与报告产出 (output/)", [
        "• multimodal_archive_<算例>.json (完整多模态方案集)",
        "• <算例>_summary.json (算例求解与消融指标摘要)",
        "• carlier_multimodal_compare.csv (全量批量实验总表)"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="5.6 交付"))

    # C5 内部连接
    svg.append(f'<line x1="{b5x+b5w/2}" y1="335" x2="{b5x+b5w/2}" y2="360" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b5x+b5w/2}" y1="520" x2="{b5x+b5w/2}" y2="545" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b5x+b5w/2}" y1="715" x2="{b5x+b5w/2}" y2="740" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b5x+b5w/2}" y1="925" x2="{b5x+b5w/2}" y2="950" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b5x+b5w/2}" y1="1125" x2="{b5x+b5w/2}" y2="1150" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # C4 -> C5 结果交接
    # D3 (否) -> 5.1
    svg.append(f'''
    <path d="M {d3_cx + 120} {d3_cy} L {C5_X - 10} {d3_cy} L {C5_X - 10} 255 L {b5x} 255" fill="none" stroke="{C_LINE}" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)"/>
    <text x="{C5_X - 60}" y="{d3_cy - 8}" class="lbl-branch">否: 直接输出</text>
    ''')

    # 4.5 -> 5.1
    svg.append(f'''
    <path d="M {b4x+b4w} 1162 L {C5_X - 10} 1162 L {C5_X - 10} 270 L {b5x} 270" fill="none" stroke="{C_GREEN_BORDER}" stroke-width="1.5" marker-end="url(#arrow-green)"/>
    <text x="{C5_X - 60}" y="1154" class="lbl-branch" fill="{C_GREEN_BORDER}">数据补齐交接</text>
    ''')

    # ================= 底部图例栏 (Legend) =================
    leg_y = 1410
    svg.append(f'''
    <g transform="translate(45, {leg_y})">
        <!-- 常规计算 -->
        <rect x="0" y="0" width="22" height="15" rx="3" fill="{C_BLUE_BG}" stroke="{C_BLUE_BORDER}" stroke-width="1.2"/>
        <text x="30" y="12" class="box-body" fill="#334155">L0/L2 常规计算与解码</text>

        <!-- 启发式 / 局部搜索 -->
        <rect x="190" y="0" width="22" height="15" rx="3" fill="{C_ORANGE_BG}" stroke="{C_ORANGE_BORDER}" stroke-width="1.2"/>
        <text x="220" y="12" class="box-body" fill="#334155">L1 启发式与 IG 局部深挖</text>

        <!-- 档案操作 -->
        <rect x="400" y="0" width="22" height="15" rx="3" fill="{C_PURPLE_BG}" stroke="{C_PURPLE_BORDER}" stroke-width="1.2"/>
        <text x="430" y="12" class="box-body" fill="#334155">L3 多模态档案准入与引导</text>

        <!-- 协同与调度 -->
        <rect x="620" y="0" width="22" height="15" rx="3" fill="{C_TEAL_BG}" stroke="{C_TEAL_BORDER}" stroke-width="1.2"/>
        <text x="650" y="12" class="box-body" fill="#334155">L0 商集理论 / L3 模式分派</text>

        <!-- 判断节点 -->
        <polygon points="850,0 865,7.5 850,15 835,7.5" fill="{C_RED_BG}" stroke="{C_RED_BORDER}" stroke-width="1.2"/>
        <text x="875" y="12" class="box-body" fill="#334155">判定与分支</text>

        <!-- 结果输出 -->
        <rect x="980" y="0" width="22" height="15" rx="3" fill="{C_GREEN_BG}" stroke="{C_GREEN_BORDER}" stroke-width="1.2"/>
        <text x="1010" y="12" class="box-body" fill="#334155">L4 评价分析与工业落地</text>

        <text x="1420" y="12" class="box-body" fill="#64748B" font-weight="700">HFSP 求解器完整 5 层架构 · 16 个源文件 · 全要素无死角完整工程图</text>
    </g>
    ''')

    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    out_svg = "docs/HFSP全项目完整架构与求解流程图.svg"
    content = generate_perfect_architecture()
    Path(out_svg).write_text(content, encoding="utf-8")
    print("Perfect full system SVG generated successfully.")
