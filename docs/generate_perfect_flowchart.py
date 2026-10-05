# -*- coding: utf-8 -*-
"""完整版：HFSP 混合搜索算法求解流程图生成脚本。
严格对照用户原图架构与代码体系，全面补齐所有连线、箭头、判断分支、公式与细节说明。
"""
from pathlib import Path

def generate_complete_flowchart():
    W, H = 1820, 1460

    BG_CANVAS = "#FBF9F1"
    PANEL_BG = "rgba(255, 255, 255, 0.85)"

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

    C_LINE = "#556980"
    C_DASH = "#8FA3BA"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('<defs>')
    svg.append('''
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#556980" />
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
            .title-main { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 800; font-size: 26px; fill: #1E293B; }
            .title-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 500; font-size: 13.5px; fill: #64748B; }
            .col-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 700; font-size: 15.5px; fill: #1E293B; }
            .box-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 700; font-size: 13px; }
            .box-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-weight: 400; font-size: 11.5px; line-height: 1.45; }
            .lbl-branch { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-size: 11px; font-weight: 600; fill: #475569; }
        </style>
    ''')
    svg.append('</defs>')

    # 画布背景
    svg.append(f'<rect width="{W}" height="{H}" fill="{BG_CANVAS}" />')

    # 顶部标题区
    svg.append(f'''
    <g transform="translate(0, 36)">
        <text x="{W/2}" y="0" text-anchor="middle" class="title-main">HFSP 混合搜索算法完整求解流程</text>
        <text x="{W/2}" y="28" text-anchor="middle" class="title-sub">基础必经流程：建模解码 → 小生境 PSO 全局搜索 → IG 局部强化 → 结构多模态档案；档案引导仅在 archive_guided_rounds &gt; 0 时执行</text>
    </g>
    ''')

    # ================= 顶部总览卡片 T1 -> T6 =================
    top_nav = [
        ("T1 输入算例", "解码 + 基线", C_BLUE_BG, C_BLUE_BORDER, C_BLUE_TXT),
        ("T2 小生境 PSO", "全局搜索", C_BLUE_BG, C_BLUE_BORDER, C_BLUE_TXT),
        ("T3 IG 局部强化", "多模态采样", C_ORANGE_BG, C_ORANGE_BORDER, C_ORANGE_TXT),
        ("T4 结构档案", "四步入档", C_PURPLE_BG, C_PURPLE_BORDER, C_PURPLE_TXT),
        ("T5 可选增强", "档案引导搜索", C_ORANGE_BG, C_ORANGE_BORDER, C_ORANGE_TXT),
        ("T6 最优解 + 解集", "结果输出", C_GREEN_BG, C_GREEN_BORDER, C_GREEN_TXT),
    ]
    tn_w, tn_h, tn_gap, tn_x0, tn_y0 = 250, 48, 38, 60, 85
    t_centers = []
    for i, (t_top, t_sub, bg, border, txt) in enumerate(top_nav):
        tx = tn_x0 + i * (tn_w + tn_gap)
        t_centers.append(tx + tn_w/2)
        svg.append(f'''
        <g transform="translate({tx}, {tn_y0})">
            <rect width="{tn_w}" height="{tn_h}" rx="6" fill="{bg}" stroke="{border}" stroke-width="1.4" filter="url(#shadow)"/>
            <text x="{tn_w/2}" y="20" text-anchor="middle" class="box-title" fill="{txt}">{t_top}</text>
            <text x="{tn_w/2}" y="36" text-anchor="middle" class="box-body" fill="{txt}" opacity="0.85">{t_sub}</text>
        </g>
        ''')
        if i < len(top_nav) - 1:
            arr_x1 = tx + tn_w
            arr_x2 = arr_x1 + tn_gap
            svg.append(f'<line x1="{arr_x1}" y1="{tn_y0 + tn_h/2}" x2="{arr_x2}" y2="{tn_y0 + tn_h/2}" stroke="{C_LINE}" stroke-width="1.6" marker-end="url(#arrow)"/>')

    # ================= 辅助函数 =================
    def draw_node(x, y, w, h, title, lines, bg=C_BLUE_BG, border=C_BLUE_BORDER, txt=C_BLUE_TXT, tag=None):
        out = [f'<g transform="translate({x}, {y})">']
        out.append(f'<rect width="{w}" height="{h}" rx="7" fill="{bg}" stroke="{border}" stroke-width="1.3" filter="url(#shadow)"/>')
        if tag:
            out.append(f'<rect x="8" y="7" width="{len(tag)*8+10}" height="18" rx="4" fill="{border}" fill-opacity="0.15"/>')
            out.append(f'<text x="{13+len(tag)*4}" y="20" text-anchor="middle" class="box-title" font-size="11" fill="{border}">{tag}</text>')
            out.append(f'<text x="{26+len(tag)*8}" y="21" class="box-title" fill="{txt}">{title}</text>')
        else:
            out.append(f'<text x="12" y="21" class="box-title" fill="{txt}">{title}</text>')
        
        cur_y = 39
        for l in lines:
            if l.startswith("•"):
                out.append(f'<text x="12" y="{cur_y}" class="box-body" fill="{txt}" font-weight="600">{l}</text>')
            elif l.startswith("  -"):
                out.append(f'<text x="18" y="{cur_y}" class="box-body" fill="{txt}">{l}</text>')
            elif l.startswith("  "):
                out.append(f'<text x="24" y="{cur_y}" class="box-body" fill="{txt}" opacity="0.9">{l}</text>')
            else:
                out.append(f'<text x="12" y="{cur_y}" class="box-body" fill="{txt}">{l}</text>')
            cur_y += 16
        out.append('</g>')
        return "\n".join(out)

    def draw_diamond(cx, cy, rx, ry, title, subtitle="", bg=C_RED_BG, border=C_RED_BORDER, txt=C_RED_TXT):
        pts = f"{cx},{cy-ry} {cx+rx},{cy} {cx},{cy+ry} {cx-rx},{cy}"
        out = [
            f'<polygon points="{pts}" fill="{bg}" stroke="{border}" stroke-width="1.4" filter="url(#shadow)"/>',
            f'<text x="{cx}" y="{cy - (4 if subtitle else -4)}" text-anchor="middle" class="box-title" font-size="12" fill="{txt}">{title}</text>'
        ]
        if subtitle:
            out.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" class="box-body" font-size="10.5" fill="{txt}" opacity="0.9">{subtitle}</text>')
        return "\n".join(out)

    # ================= 四大列面板坐标 =================
    COL_Y = 160
    COL_H = 1190
    C1_X, C1_W = 40, 360    # ① 输入、统一评价与基线
    C2_X, C2_W = 430, 470   # ② 小生境 PSO 全局搜索
    C3_X, C3_W = 930, 420   # ③ IG 强化、多模态采样与入档
    C4_X, C4_W = 1380, 400  # ④ 档案引导 (可选) 与结果输出

    for cx, cw, title in [
        (C1_X, C1_W, "① 输入、统一评价与基线"),
        (C2_X, C2_W, "② 小生境 PSO 全局搜索"),
        (C3_X, C3_W, "③ IG 强化、多模态采样与入档"),
        (C4_X, C4_W, "④ 档案引导 (可选) 与结果输出")
    ]:
        svg.append(f'''
        <g transform="translate({cx}, {COL_Y})">
            <rect width="{cw}" height="{COL_H}" rx="10" fill="{PANEL_BG}" stroke="#CBD5E1" stroke-width="1.4" stroke-dasharray="5,4"/>
            <text x="16" y="26" class="col-title">{title}</text>
        </g>
        ''')

    # 顶部卡片指向下方面板的指示虚线 (T1->①, T2->②, T3->③, T4->③底部, T5->④, T6->④底部)
    svg.append(f'<line x1="{t_centers[0]}" y1="{tn_y0+tn_h}" x2="{C1_X+C1_W/2}" y2="{COL_Y}" stroke="{C_DASH}" stroke-width="1.3" stroke-dasharray="4,3"/>')
    svg.append(f'<line x1="{t_centers[1]}" y1="{tn_y0+tn_h}" x2="{C2_X+C2_W/2}" y2="{COL_Y}" stroke="{C_DASH}" stroke-width="1.3" stroke-dasharray="4,3"/>')
    svg.append(f'<line x1="{t_centers[2]}" y1="{tn_y0+tn_h}" x2="{C3_X+C3_W/2}" y2="{COL_Y}" stroke="{C_DASH}" stroke-width="1.3" stroke-dasharray="4,3"/>')
    svg.append(f'<line x1="{t_centers[4]}" y1="{tn_y0+tn_h}" x2="{C4_X+C4_W/2}" y2="{COL_Y}" stroke="{C_DASH}" stroke-width="1.3" stroke-dasharray="4,3"/>')

    # -------------------------------------------------------------
    # 第一栏：① 输入、统一评价与基线 (S0, S1, S2)
    # -------------------------------------------------------------
    bx = C1_X + 15
    bw = C1_W - 30

    # S0
    svg.append(draw_node(bx, 205, bw, 110, "读取算例，建立 HFSPEnvironment", [
        "• 输入: 工件数 n, 阶段数 s, 机器数 m_s",
        "• 加工时间矩阵: P[job][stage][machine]",
        "• 严格校验工件唯一性、工序连续性与机器分配",
        "• 统一封装算例元数据与环境对象"
    ], tag="S0"))

    # S1
    svg.append(draw_node(bx, 360, bw, 150, "统一解码 D: 按阶段列表调度与 ECT 机器分配", [
        "• 确定性唯一解码映射 D: Π → S",
        "  - 阶段拓扑推进 stage = 0 → s-1",
        "  - 阶段内严格按排列 π 的顺序派工",
        "  - Earliest Completion Time (最早完工机器选择):",
        "    C = max(MachineReady, JobDone) + p",
        "• 内置 LRU 评估缓存，消除相同排列重复计算",
        "• 产出调度 S 与 makespan (不可变 ScheduleEvaluation)"
    ], bg="#F0FDF4", border="#16A34A", txt="#145A32", tag="S1"))

    # S2
    svg.append(draw_node(bx, 555, bw, 140, "生成 NEH 与 SPT 基线 (统一评测)", [
        "• 全部候选解统一调用 decode_and_evaluate 评测",
        "• NEH 启发式基线:",
        "  - 按各阶段平均加工时间降序",
        "  - 逐个工件执行贪心最优插入",
        "• SPT 启发式基线: 按工件平均工时升序",
        "• 产出高水平质量下界与初代探索牵引种子"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S2"))

    # 第一栏内部箭头
    svg.append(f'<line x1="{bx+bw/2}" y1="315" x2="{bx+bw/2}" y2="360" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{bx+bw/2}" y1="510" x2="{bx+bw/2}" y2="555" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # -------------------------------------------------------------
    # 第二栏：② 小生境 PSO 全局搜索 (S3, S4, S5, S6, S7, D1)
    # -------------------------------------------------------------
    b2x = C2_X + 15
    b2w = C2_W - 30

    # S3
    svg.append(draw_node(b2x, 205, b2w, 160, "初始化种群: NEH、SPT、扰动解、随机解与候选缓冲", [
        "• 种群规模 N=40，逐个评估并初始化 pbest = x / 全局 gbest:",
        "  - 梯队1: 1 个 NEH 确定性解 (高质量全局锚点)",
        "  - 梯队2: 1 个 SPT 确定性解 (提供异构工程启发基准)",
        "  - 梯队3: 4 个 NEH 扰动解 (小强度交换对, 扩充至 6 个)",
        "  - 梯队4: 4 个 SPT 扰动解 (适度扰动对, 扩充至 10 个)",
        "  - 梯队5: (若引导重启) 注入档案库精英解 pool (quota ≤ 30%)",
        "  - 梯队6: 约 30 个纯随机排列补齐 N=40，保障全空间分散度",
        "• 候选缓冲: seen_positions 集合查重，新排列写入缓冲池"
    ], tag="S3"))

    # S4
    svg.append(draw_node(b2x, 395, b2w, 135, "自适应惯性权重 w、环形邻域、小生境划分", [
        "• 自适应惯性权重递减: w(t) = 0.9 - 0.5 × (t / (T-1))",
        "  - 前期 w ≈ 0.9 保持动量全局探索; 后期 w ≈ 0.4 局部聚焦收敛",
        "• 环形邻域拓扑 (Ring): 粒子仅与左右 k=3 个邻居通信",
        "• 小生境划分 (Niching): 排列距离 ≤ 3 聚类，获取局部最优 lbest",
        "• 自适应变异率: P_mut = min(0.45, 0.08 + 多样性增益 + 停滞增益)",
        "  - 种群拥挤 (Diversity < 0.25) 或停滞时，变异率自动补偿放大"
    ], tag="S4"))

    # S5
    svg.append(draw_node(b2x, 560, b2w, 145, "由局部 pbest 构造认知/社会交换序 (防单峰塌陷)", [
        "• 离散交换序速度更新机理 (SwapSeq):",
        "  - 认知分量: 抽取变至个体历史最优的对换序列 SwapSeq(x, pbest)",
        "  - 社会分量: 抽取变至同生境局部最优的对换序列 SwapSeq(x, lbest)",
        "  - 用意: 追随局部最优 lbest 促成多峰并行开采，避免全群陷入单一伪极值",
        "• 速度公式: V = w⊙V ⊕ c₁⊙Sample(pbest) ⊕ c₂⊙Sample(lbest)",
        "• 施加位置交换: 依次对当前排列执行交换对; 依 P_mut 施加随机变异"
    ], tag="S5"))

    # S6
    svg.append(draw_node(b2x, 735, b2w, 130, "解码评价新粒子，更新 pbest、gbest 与候选缓冲", [
        "• 统一调用 D(x) 解码，计算当前 makespan 与工序机器分配",
        "• 更新粒子历史最优 pbest 与当前代全局最优 gbest",
        "• 候选缓冲深层用意 (步步留痕):",
        "  - 粒子飞行中只要踩到未见过的排列即记录入池，升序维护前 200 名",
        "  - 截断丢弃 200 名之后劣解; 保证粒子飞行轨迹中沿途发现的",
        "    大量优质多模态方案被实时留存，为最终档案库留足种子"
    ], tag="S6"))

    # S7
    svg.append(draw_node(b2x, 895, b2w, 155, "周期执行 IG 精修；维护停滞计数与档案注入", [
        "• 周期性 IG 嵌入 (每隔 T/5 = 12 代固定触发):",
        "  - 对当前 gbest 运行破坏重建退火；若挖出更优解，直接覆盖替换",
        "    种群中最差粒子 (worst_fitness)，强力拉升全群进化重心；解入缓冲",
        "• 停滞检测与多样性重初始化:",
        "  - 连续 10 代无全局最优改进 → 触发停滞响应",
        "  - 保护 gbest，淘汰最差 20% 粒子: 50% 从档案库注入精英，",
        "    50% 纯随机重启，兼顾深度利用与广度探索"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S7"))

    # D1
    d1_cx, d1_cy = b2x + b2w/2, 1105
    svg.append(draw_diamond(d1_cx, d1_cy, 125, 26, "D1 gen + 1 < max_generations ?", "默认迭代 60 代"))

    # 第二栏内部连接
    svg.append(f'<line x1="{b2x+b2w/2}" y1="365" x2="{b2x+b2w/2}" y2="395" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="530" x2="{b2x+b2w/2}" y2="560" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="705" x2="{b2x+b2w/2}" y2="735" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="865" x2="{b2x+b2w/2}" y2="895" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b2x+b2w/2}" y1="1050" x2="{b2x+b2w/2}" y2="{d1_cy-26}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D1 回环到 S4 (是: 进入下一代)
    loop_x = b2x - 8
    svg.append(f'''
    <path d="M {d1_cx - 125} {d1_cy} L {loop_x} {d1_cy} L {loop_x} 460 L {b2x} 460" fill="none" stroke="{C_BLUE_BORDER}" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
    <text x="{loop_x + 8}" y="{d1_cy - 8}" class="lbl-branch" fill="{C_BLUE_BORDER}">是: 进入下一代</text>
    ''')

    # S2 -> S3 (基线注入)
    svg.append(f'''
    <path d="M {bx+bw} 625 L {C2_X - 10} 625 L {C2_X - 10} 285 L {b2x} 285" fill="none" stroke="{C_LINE}" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)"/>
    <text x="{C2_X - 45}" y="277" class="lbl-branch">基线注入</text>
    ''')

    # -------------------------------------------------------------
    # 第三栏：③ IG 强化、多模态采样与入档 (S8, I1, I2, I3, D2, S9, A1-A4, D3)
    # -------------------------------------------------------------
    b3x = C3_X + 15
    b3w = C3_W - 30

    # S8
    svg.append(draw_node(b3x, 205, b3w, 48, "以 PSO 的 gbest 为起点执行最终 IG 强化", [
        "初始温度 T = max(1.0, current_makespan * 0.1)"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S8"))

    # I1
    svg.append(draw_node(b3x, 280, b3w, 50, "破坏算子 (Destruction)", [
        "随机移除 d = round(0.3n) 个工件，剩余工件保持相对先后次序"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="I1"))

    # I2
    svg.append(draw_node(b3x, 355, b3w, 52, "重建算子 (Reconstruction)", [
        "被抽工件打乱，逐个尝试插入全部可用位置，贪心选 makespan 最小点放回"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="I2"))

    # I3
    svg.append(draw_node(b3x, 432, b3w, 52, "评价与模拟退火接受准则 (SA Acceptance)", [
        "Δ ≤ 0 直接接受; 劣解以 exp(-Δ/T) 概率接受; 几何降温 T ← T * 0.95"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="I3"))

    # D2
    d2_cx, d2_cy = b3x + b3w/2, 520
    svg.append(draw_diamond(d2_cx, d2_cy, 115, 20, "D2 IG iteration < max ?", "默认 15~20 轮"))

    # S9
    svg.append(draw_node(b3x, 570, b3w, 50, "扰动 + IG，并发采样最多 5 条候选解", [
        "对基准解施加轻度换位扰动后各自独立运行 IG，丰富局域多模态样本"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S9"))

    # A1, A2, A3, A4
    svg.append(draw_node(b3x, 645, b3w, 48, "入档① 质量门限筛选", [
        "判断 makespan ≤ (1 + ρ)·best (默认 ρ = 1%)，超标直接丢弃"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="A1"))

    svg.append(draw_node(b3x, 715, b3w, 54, "入档② 结构签名去重 (商集等价类判定)", [
        "Sig(π)={ (阶段, 机器): 工件加工顺序 }；同一调度只保留最优代表元"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="A2"))

    svg.append(draw_node(b3x, 790, b3w, 66, "入档③ 析取式三维新颖性判定", [
        "二分窗口比对已存解: 仅当「质量相近 且 机器分配距离 D_m ≤ 0.05",
        "且 加工顺序距离 D_s ≤ 0.10」同时满足时才拒收；有一项新颖即接纳"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="A3"))

    svg.append(draw_node(b3x, 878, b3w, 62, "入档④ 质量动态剪枝与最远点容量裁剪", [
        "最优刷新后剪除超限旧解; 超过容量(200)时保留最优解，其余按",
        "「到已保留集合的最小结构距离最大」最远点优先法则贪心筛选"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="A4"))

    # D3
    d3_cx, d3_cy = b3x + b3w/2, 985
    svg.append(draw_diamond(d3_cx, d3_cy, 115, 22, "D3 启用档案引导？", "archive_guided_rounds > 0"))

    # 第三栏内部箭头连接 (全面补齐 S8->I1, I1->I2, I2->I3 等所有断点)
    svg.append(f'<line x1="{b3x+b3w/2}" y1="253" x2="{b3x+b3w/2}" y2="280" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="330" x2="{b3x+b3w/2}" y2="355" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="407" x2="{b3x+b3w/2}" y2="432" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="484" x2="{b3x+b3w/2}" y2="{d2_cy-20}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D2 回环到 I1
    i_loop_x = b3x - 6
    svg.append(f'''
    <path d="M {d2_cx - 115} {d2_cy} L {i_loop_x} {d2_cy} L {i_loop_x} 305 L {b3x} 305" fill="none" stroke="{C_ORANGE_BORDER}" stroke-width="1.4" marker-end="url(#arrow-orange)"/>
    <text x="{i_loop_x + 6}" y="{d2_cy - 6}" class="lbl-branch" fill="{C_ORANGE_BORDER}">是: 下一轮</text>
    ''')

    # D2 -> S9
    svg.append(f'<line x1="{d2_cx}" y1="{d2_cy+20}" x2="{d2_cx}" y2="570" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{d2_cx + 8}" y="{d2_cy+15}" class="lbl-branch">否</text>')

    # S9 -> A1 -> A2 -> A3 -> A4 -> D3
    svg.append(f'<line x1="{b3x+b3w/2}" y1="620" x2="{b3x+b3w/2}" y2="645" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="693" x2="{b3x+b3w/2}" y2="715" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="769" x2="{b3x+b3w/2}" y2="790" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="856" x2="{b3x+b3w/2}" y2="878" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b3x+b3w/2}" y1="940" x2="{b3x+b3w/2}" y2="{d3_cy-22}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D1 (否) -> S8
    svg.append(f'''
    <path d="M {d1_cx + 125} {d1_cy} L {C3_X - 10} {d1_cy} L {C3_X - 10} 229 L {b3x} 229" fill="none" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="{C3_X - 45}" y="{d1_cy - 8}" class="lbl-branch">否: PSO完成</text>
    ''')

    # -------------------------------------------------------------
    # 第四栏：④ 档案引导 (可选) 与结果输出 (S10-S15, D4)
    # -------------------------------------------------------------
    b4x = C4_X + 15
    b4w = C4_W - 30

    # S10
    svg.append(draw_node(b4x, 205, b4w, 70, "闭环Ⅰ: 档案排列注入 PSO 重启并回写", [
        "将档案库等优排列赋给 pso.diversity_pool，重置停滞计数；",
        "启动指定代数短跑 PSO，新解全量二次回写冲刷档案库"
    ], bg=C_PURPLE_BG, border=C_PURPLE_BORDER, txt=C_PURPLE_TXT, tag="S10"))

    # S11
    svg.append(draw_node(b4x, 305, b4w, 65, "闭环Ⅱ: 轮次交替种子选择策略", [
        "• 偶数轮(强化 Intensify): 从等优解集中随机挑，小扰动 15%",
        "• 奇数轮(探索 Explore): 挑最孤立解 argmax(Crowding)，大扰动 35%"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S11"))

    # S12
    svg.append(draw_node(b4x, 395, b4w, 55, "按比例扰动种子排列，执行 IG 得到候选解", [
        "种子施加多点换位扰动 + 随机插入扰动后，调用 IG 精修"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S12"))

    # S13
    svg.append(draw_node(b4x, 475, b4w, 85, "按质量或结构多样性接受游走点并入档", [
        "• 接受准则纳入结构多样性: makespan 变好 或 (不同等价类 且",
        "  离起点更远) 均接受为新游走点，允许在等优平原横向移动;",
        "• 每个新产生的候选解均调用 add_solution 尝试入档"
    ], bg=C_ORANGE_BG, border=C_ORANGE_BORDER, txt=C_ORANGE_TXT, tag="S13"))

    # D4
    d4_cx, d4_cy = b4x + b4w/2, 595
    svg.append(draw_diamond(d4_cx, d4_cy, 125, 22, "D4 未停滞且未达最大轮数？", "stagnation < 15 且 rounds < Max"))

    # S14
    svg.append(draw_node(b4x, 655, b4w, 60, "比较档案库首解，更优则更新最终 best", [
        "若引导游走挖掘出比原先全局最优更低的 makespan，",
        "将档案库第 1 名刷新为最终全局最优解"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="S14"))

    # S15
    svg.append(draw_node(b4x, 755, b4w, 160, "补充完整调度数据，多模态输出与工业应用", [
        "• 补充逐工序甘特图数据 (operations, completion_times)",
        "• 输出结构互异的完整多模态等优解集",
        "• 制造分析 (solver_analysis.py): 阶段负荷、瓶颈阶段、利用率",
        "• 学术多模态指标 (multimodal_evaluation.py):",
        "  - 等优解数量 N_ρ (ρ = 0, 1%, 2%, 5%) 与 解集平均多样性",
        "• 工业落地 (demo_fault_switching.py):",
        "  - 突发机器停机时，免重新计算，直接从库中选取完工期受阻",
        "    最小的备选解瞬间顶上，实现 O(k) 毫秒级动态容错响应！"
    ], bg=C_GREEN_BG, border=C_GREEN_BORDER, txt=C_GREEN_TXT, tag="S15"))

    # 第四栏内部连接线
    svg.append(f'<line x1="{b4x+b4w/2}" y1="275" x2="{b4x+b4w/2}" y2="305" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="370" x2="{b4x+b4w/2}" y2="395" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="450" x2="{b4x+b4w/2}" y2="475" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="560" x2="{b4x+b4w/2}" y2="{d4_cy-22}" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D4 回环到 S11 (是: 继续游走)
    g_loop_x = b4x - 6
    svg.append(f'''
    <path d="M {d4_cx - 125} {d4_cy} L {g_loop_x} {d4_cy} L {g_loop_x} 337 L {b4x} 337" fill="none" stroke="{C_ORANGE_BORDER}" stroke-width="1.4" marker-end="url(#arrow-orange)"/>
    <text x="{g_loop_x + 6}" y="{d4_cy - 6}" class="lbl-branch" fill="{C_ORANGE_BORDER}">是: 继续开采</text>
    ''')

    # D4 (否) -> S14 -> S15
    svg.append(f'<line x1="{d4_cx}" y1="{d4_cy+22}" x2="{d4_cx}" y2="655" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{d4_cx + 8}" y="{d4_cy+15}" class="lbl-branch">否</text>')
    svg.append(f'<line x1="{b4x+b4w/2}" y1="715" x2="{b4x+b4w/2}" y2="755" stroke="{C_LINE}" stroke-width="1.5" marker-end="url(#arrow)"/>')

    # D3 -> S10 (是: 启用档案引导)
    svg.append(f'''
    <path d="M {d3_cx + 115} {d3_cy} L {C4_X - 10} {d3_cy} L {C4_X - 10} 240 L {b4x} 240" fill="none" stroke="{C_PURPLE_BORDER}" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
    <text x="{C4_X - 35}" y="{d3_cy - 8}" class="lbl-branch" fill="{C_PURPLE_BORDER}">是</text>
    ''')

    # D3 -> S15 (否: 直接输出，顺畅绕到底部进入 S15 左侧)
    svg.append(f'''
    <path d="M {d3_cx} {d3_cy+22} L {d3_cx} 1030 L {C4_X - 10} 1030 L {C4_X - 10} 835 L {b4x} 835" fill="none" stroke="{C_LINE}" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow)"/>
    <text x="{d3_cx + 12}" y="1022" class="lbl-branch">否: 直接输出</text>
    ''')

    # ================= 底部图例栏 (Legend) =================
    leg_y = 1390
    svg.append(f'''
    <g transform="translate(60, {leg_y})">
        <!-- 常规计算 -->
        <rect x="0" y="0" width="22" height="15" rx="3" fill="{C_BLUE_BG}" stroke="{C_BLUE_BORDER}" stroke-width="1.2"/>
        <text x="30" y="12" class="box-body" fill="#334155">常规计算</text>

        <!-- 启发式 / 局部搜索 -->
        <rect x="130" y="0" width="22" height="15" rx="3" fill="{C_ORANGE_BG}" stroke="{C_ORANGE_BORDER}" stroke-width="1.2"/>
        <text x="160" y="12" class="box-body" fill="#334155">启发式 / 局部搜索</text>

        <!-- 档案操作 -->
        <rect x="310" y="0" width="22" height="15" rx="3" fill="{C_PURPLE_BG}" stroke="{C_PURPLE_BORDER}" stroke-width="1.2"/>
        <text x="340" y="12" class="box-body" fill="#334155">档案操作</text>

        <!-- 判断节点 -->
        <polygon points="460,0 475,7.5 460,15 445,7.5" fill="{C_RED_BG}" stroke="{C_RED_BORDER}" stroke-width="1.2"/>
        <text x="485" y="12" class="box-body" fill="#334155">判断节点</text>

        <!-- 可选分支 -->
        <line x1="580" y1="7.5" x2="615" y2="7.5" stroke="{C_LINE}" stroke-width="1.4" stroke-dasharray="4,3"/>
        <text x="625" y="12" class="box-body" fill="#334155">可选分支 / 跳过链路</text>

        <!-- 结果输出 -->
        <rect x="790" y="0" width="22" height="15" rx="3" fill="{C_GREEN_BG}" stroke="{C_GREEN_BORDER}" stroke-width="1.2"/>
        <text x="820" y="12" class="box-body" fill="#334155">结果输出与评价</text>

        <text x="1260" y="12" class="box-body" fill="#64748B" font-weight="600">S 主步骤 · I 迭代贪婪(IG) · A 档案准入(Archive) · D 判定分支(Decision)</text>
    </g>
    ''')

    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    out_svg = "docs/HFSP混合搜索算法完整求解流程.svg"
    content = generate_complete_flowchart()
    Path(out_svg).write_text(content, encoding="utf-8")
    print("SVG generated successfully.")
