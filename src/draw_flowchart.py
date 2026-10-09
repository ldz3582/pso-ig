"""draw_flowchart.py —— 绘制规范、工整、折线绕行且不穿插卡片的算法流程图。
"""
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# 设置中文字体与负号支持
matplotlib.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS', 'Heiti SC', 'Songti SC', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def draw_clean_flowchart():
    fig, ax = plt.subplots(figsize=(11, 15), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 背景纯白
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # 1. 顶部主副标题
    ax.text(50, 97.2, "HFSP 调度求解与多模态识别流程图", fontsize=17, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(50, 95.0, "基于固定运行时间终止机制：Time Limit = 0.01 × μ³ × σ (ms)", fontsize=11, ha='center', va='center', color='#475569')

    # 辅助函数：绘制规范圆角矩形卡片
    def card(x, y, w, h, title, subtitle="", tag="", bg="#F8FAFC", border="#3B82F6", title_color="#0F172A"):
        # 阴影层
        shadow = patches.FancyBboxPatch((x + 0.3, y - 0.3), w, h, boxstyle="round,pad=0.5,rounding_size=1.0",
                                        facecolor='#F1F5F9', edgecolor='none', zorder=1)
        ax.add_patch(shadow)
        # 主体框
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.0",
                                      facecolor=bg, edgecolor=border, linewidth=1.8, zorder=2)
        ax.add_patch(rect)
        # 标签 Tag（完美嵌入卡片内部左上角）
        if tag:
            tbox = patches.FancyBboxPatch((x + 1.2, y + h - 2.6), len(tag)*1.6 + 2.0, 1.8,
                                          boxstyle="round,pad=0.1,rounding_size=0.4",
                                          facecolor=border, edgecolor='none', zorder=3)
            ax.add_patch(tbox)
            ax.text(x + 2.2 + len(tag)*0.8, y + h - 1.7, tag, fontsize=7.8, fontweight='bold', color='#FFFFFF', ha='center', va='center', zorder=4)

        # 文字排版
        if subtitle:
            ax.text(x + w/2, y + h/2 + 0.5, title, fontsize=11.5, fontweight='bold', color=title_color, ha='center', va='center', zorder=3)
            ax.text(x + w/2, y + h/2 - 1.3, subtitle, fontsize=9.2, color='#475569', ha='center', va='center', zorder=3)
        else:
            ax.text(x + w/2, y + h/2, title, fontsize=11.5, fontweight='bold', color=title_color, ha='center', va='center', zorder=3)

    # 辅助函数：绘制菱形判定框
    def diamond(cx, cy, r, title, subtitle=""):
        d = patches.RegularPolygon((cx, cy), numVertices=4, radius=r, orientation=0,
                                   facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=1.8, zorder=2)
        ax.add_patch(d)
        ax.text(cx, cy + 0.7, title, fontsize=11.5, fontweight='bold', color='#B45309', ha='center', va='center', zorder=3)
        ax.text(cx, cy - 1.1, subtitle, fontsize=8.8, color='#D97706', ha='center', va='center', zorder=3)

    # 垂直主轴坐标
    cx = 50  # 中心 X 坐标
    w = 60   # 统一卡片宽度
    x_left = cx - w / 2

    # --- 步骤卡片布置 ---
    # 1. 读取算例
    card(x_left, 86.8, w, 5.2, "1. 读取算例与环境初始化", "获取工件数 μ (如10/15) 与阶段数 σ (如5/10)", tag="INPUT", bg="#EFF6FF", border="#3B82F6")

    # 2. 计算固定时间上限
    card(x_left, 77.0, w, 5.8, "2. 自动计算固定运行时间上限 (论文标准公式)", "Time_Limit = 0.01 × μ³ × σ / 1000 (秒)\n[ j10c5: 0.05s | j10c10: 0.10s | j15c5: 0.17s | j15c10: 0.34s ]", tag="TIME BUDGET", bg="#F0FDF4", border="#10B981")

    # 3. 启动计时与初始化
    card(x_left, 67.2, w, 5.5, "3. 种群初始化 & 启动秒表计时", "NEH+SPT/LPT 构造初始优解 + 启动高精度计时器 start_time", tag="INIT", bg="#FAF5FF", border="#A855F7")

    # 4. 核心时间判定 (菱形)
    diamond(cx, 56.5, 6.2, "时间是否耗尽？", "(已耗时 >= Time_Limit ?)")

    # 5. PSO 进化
    card(x_left, 43.5, w, 5.2, "5. 粒子群 (PSO) 迭代进化", "交换序列更新速度与位置 + 惯性权重随时间动态衰减", tag="PSO", bg="#EFF6FF", border="#3B82F6")

    # 6. IG 局部搜索
    card(x_left, 33.5, w, 5.2, "6. 迭代贪婪局部搜索 (IG)", "每 12 代触发：破坏 (摘除工件) + 最优插入重构 + 退火接受", tag="LOCAL SEARCH", bg="#FFF7ED", border="#EA580C")

    # 7. 时间截止，终止搜索
    card(x_left, 20.5, w, 5.0, "7. 倒计时截止，终止搜索循环", "达到规定固定时间上限，立即跳出 while 循环", tag="STOP", bg="#FEF2F2", border="#EF4444")

    # 8. 多模态档案去重
    card(x_left, 11.5, w, 5.2, "8. 最优解多模态识别与去重", "筛选 Makespan 相同的最优解，基于甘特图块特征严格去重", tag="MULTIMODAL", bg="#FDF4FF", border="#C026D3")

    # 9. 输出报表与甘特图
    card(x_left, 2.0, w, 5.2, "9. 导出结果与绘制甘特图", "绘制独立最优多模态甘特图 (.png) + 导出 CSV / JSON 报表", tag="OUTPUT", bg="#F0FDF4", border="#059669")

    # --- 箭头连线系统 (使用整洁的折线直角布线，完全避开所有卡片) ---
    def straight_arrow(y_from, y_to):
        ax.annotate('', xy=(cx, y_to), xytext=(cx, y_from),
                    arrowprops=dict(arrowstyle="->", color="#64748B", lw=2, mutation_scale=14), zorder=5)

    # 垂直主轴箭头
    straight_arrow(86.8, 82.8)
    straight_arrow(77.0, 72.7)
    straight_arrow(67.2, 62.7)

    # 菱形向下分支：【否 (时间未到，继续搜索)】
    ax.annotate('', xy=(cx, 48.7), xytext=(cx, 50.3),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2.2, mutation_scale=15), zorder=5)
    ax.text(cx + 1.8, 49.5, "否 (时间未用完，继续进化)", fontsize=9.5, fontweight='bold', color='#2563EB', va='center')

    # PSO -> IG
    straight_arrow(43.5, 38.7)

    # IG 局部搜索完毕 -> 从左侧整洁折线折返回时间判定框 (绝不穿插文字)
    ax.plot([x_left, 10, 10, cx - 6.2], [36.1, 36.1, 56.5, 56.5], color="#2563EB", lw=2.0, zorder=5)
    ax.annotate('', xy=(cx - 6.2, 56.5), xytext=(cx - 7.5, 56.5),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2.0, mutation_scale=14), zorder=6)
    ax.text(10, 46.5, "下一代\n进化循环", fontsize=9.2, fontweight='bold', color='#2563EB', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#EFF6FF", ec="#BFDBFE", lw=1.2))

    # 菱形右侧分支：【是 (倒计时归零)】 -> 从右侧整洁折线直角下落到步骤7 (绝不穿越卡片)
    ax.plot([cx + 6.2, 90, 90, x_left + w], [56.5, 56.5, 23.0, 23.0], color="#DC2626", lw=2.0, zorder=5)
    ax.annotate('', xy=(x_left + w, 23.0), xytext=(x_left + w + 1.5, 23.0),
                arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2.0, mutation_scale=14), zorder=6)
    ax.text(90, 40.0, "是\n(固定时间已耗尽)", fontsize=9.2, fontweight='bold', color='#DC2626', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FECACA", lw=1.2))

    # 步骤 7 -> 步骤 8 -> 步骤 9
    straight_arrow(20.5, 16.7)
    straight_arrow(11.5, 7.2)

    # 保存图片
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "algorithm_flowchart.png"
    plt.tight_layout()
    plt.savefig(out_file, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    print(f"规范版算法流程图已生成并保存至: {out_file}")

if __name__ == "__main__":
    draw_clean_flowchart()
