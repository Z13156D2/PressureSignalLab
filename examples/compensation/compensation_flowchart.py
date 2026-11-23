import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from matplotlib import rcParams

# 设置支持中文的字体（可以选择 SimHei 或其他支持中文的字体）
rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
rcParams['axes.unicode_minus'] = False  # 防止负号显示为方块

def draw_flowchart():
    fig, ax = plt.subplots(figsize=(8, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')

    # 定义形状函数
    def draw_shape(center_x, center_y, text, shape='rectangle', **kwargs):
        if shape == 'oval':
            patch = FancyBboxPatch((center_x - 1, center_y - 0.5), 2, 1, boxstyle="round,pad=0.3", **kwargs)
        elif shape == 'diamond':
            patch = plt.Polygon(
                [[center_x, center_y + 0.5], [center_x + 1, center_y],
                 [center_x, center_y - 0.5], [center_x - 1, center_y]], **kwargs
            )
        elif shape == 'process':
            patch = Rectangle((center_x - 1.5, center_y - 0.5), 3, 1, **kwargs)

        ax.add_patch(patch)
        ax.text(center_x, center_y, text, ha='center', va='center', fontsize=10)
        return center_x, center_y

    # 定义连接线函数
    def connect(p1_x, p1_y, p2_x, p2_y, text='', angle='v'):
        if angle == 'v':
            ax.plot([p1_x, p2_x], [p1_y - 0.5, p2_y + 0.5], 'k-')
        elif angle == 'h':
            ax.plot([p1_x + 1, p2_x - 1], [p1_y, p2_y], 'k-')

        if text:
            mid_x = (p1_x + p2_x) / 2
            mid_y = (p1_y + p2_y) / 2
            if angle == 'h':
                ax.text(mid_x, mid_y + 0.2, text, ha='center', va='bottom', fontsize=10)
            else:
                ax.text(mid_x + 0.2, mid_y, text, ha='left', va='center', fontsize=10)

    # 绘制流程图节点
    style = {'facecolor': 'lightblue', 'edgecolor': 'black', 'linewidth': 1.5}

    # 1. 开始
    p_start = draw_shape(5, 12, '开始', shape='oval', **style)
    # 2. 读取温度
    p_read_T = draw_shape(5, 11, '读取温度 T_current', shape='process', **style)
    # 3. 范围判断
    p_range_check = draw_shape(5, 10, 'T_current 是否在 LUT 范围?', shape='diamond', **style)
    # 4. 搜索
    p_search = draw_shape(5, 9, '搜索 T_i 和 T_i+1', shape='process', **style)
    # 5. 提取
    p_extract = draw_shape(5, 8, '提取 V_drift,i 和 V_drift,i+1', shape='process', **style)
    # 6. 插值计算
    p_interp = draw_shape(5, 7, '线性插值计算 V_drift', shape='process', **style)
    # 7. 读取 V_measured
    p_read_V = draw_shape(5, 6, '读取原始输出 V_measured', shape='process', **style)
    # 8. 补偿修正
    p_comp = draw_shape(5, 5, '计算 V_compensated', shape='process', **style)
    # 9. 输出
    p_output = draw_shape(5, 4, '输出 V_compensated', shape='process', **style)
    # 10. 循环判断
    p_continue = draw_shape(5, 3, '是否继续测量?', shape='diamond', **style)
    # 11. 结束
    p_end = draw_shape(5, 2, '结束', shape='oval', **style)
    # 12. 错误处理
    p_error = draw_shape(8, 9, '错误处理/报警', shape='process', **style)

    # 绘制连接线
    connect(*p_start, *p_read_T)
    connect(*p_read_T, *p_range_check)

    # 正常流程 (是)
    connect(*p_range_check, *p_search, text='是')
    connect(*p_search, *p_extract)
    connect(*p_extract, *p_interp)
    connect(*p_interp, *p_read_V)
    connect(*p_read_V, *p_comp)
    connect(*p_comp, *p_output)
    connect(*p_output, *p_continue)

    # 错误流程 (否)
    ax.plot([5.5, 8], [10, 10], 'k-')  # 水平连接到错误处理
    connect(8, 9, *p_error, angle='h', text='否')
    connect(*p_error, 8, 3)  # 从错误处理连接到循环判断
    ax.plot([8, 5.5], [3, 3], 'k-')  # 水平连接回 p_continue

    # 循环
    ax.plot([4.5, 3], [3, 3], 'k-')  # 向左
    ax.plot([3, 3], [3, 9.5], 'k-')  # 向上
    ax.plot([3, 4.5], [9.5, 9.5], 'k-')  # 向右，连接到 p_read_T 上方

    # 结束
    connect(*p_continue, *p_end, text='否')

    plt.title('分段插值温度补偿算法流程图', fontsize=14)
    plt.show()

# 执行绘制
draw_flowchart()
