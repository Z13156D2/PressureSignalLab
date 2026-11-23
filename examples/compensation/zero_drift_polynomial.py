import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置支持中文的字体（可以选择 SimHei 或其他支持中文的字体）
rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
rcParams['axes.unicode_minus'] = False  # 防止负号显示为方块

# --- 1. 模拟数据定义 (基于图像观察) ---

# 温度点 (T)
T_points = np.array([-40, -20, 0, 20, 40])  # °C

# 模拟零点漂移 V_zero(T) - 这是我们要拟合和补偿的目标
V_zero_sim = np.array([50, 20, 0, -20, -50])  # mV

# 模拟灵敏度 S(T) - 原始数据仍包含灵敏度漂移，但我们不对其进行建模和补偿
S_sim = np.array([-59.0, -58.5, -58.0, -57.5, -57.0])  # mV/hPa (斜率为负)

# 使用 V_zero_sim 来定义 base_V
base_V = dict(zip(T_points, V_zero_sim))

# --- 2. 分段最小二乘拟合 V_zero(T)（三段二次或三次多项式）---

# 分段1：-40℃ ≤ T < 0℃（使用二次多项式）
T_seg1_zero = np.array([-40, -20, 0])
Vz_seg1 = np.array([base_V[t] for t in T_seg1_zero])

# 分段2：0℃ ≤ T < 35℃（使用二次多项式）
T_seg2_zero = np.array([0, 20, 35])
Vz_seg2 = np.array([base_V[0], base_V[20], V_zero_sim[2]])  # V35

# 分段3：35℃ ≤ T ≤ 80℃（使用三次多项式）
T_seg3_zero = np.array([35, 40, 80])
Vz_seg3 = np.array([V_zero_sim[2], V_zero_sim[3], V_zero_sim[4]])  # V35, V40, V80

# 统一采用二次多项式拟合
deg1 = deg2 = 2
deg3 = 3  # 最后一段使用三次多项式

# 对系数增加小随机扰动，使得多项式系数更加随机
rng = np.random.default_rng(42)  # 固定种子，便于复现

def randomize_coeffs(coeffs, scale=1e-5):
    """
    在多项式系数上添加小的随机扰动
    scale 控制扰动的量级（这里用1e-5级别）
    """
    noise = rng.uniform(-scale, scale, size=coeffs.shape)
    return coeffs + noise

# 二次拟合
a_seg1 = np.polyfit(T_seg1_zero, Vz_seg1, deg1)
a_seg2 = np.polyfit(T_seg2_zero, Vz_seg2, deg2)
# 三次拟合
a_seg3 = np.polyfit(T_seg3_zero, Vz_seg3, deg3)

# 对拟合系数进行随机扰动
a_seg1 = randomize_coeffs(a_seg1)
a_seg2 = randomize_coeffs(a_seg2)
a_seg3 = randomize_coeffs(a_seg3)

# 创建多项式对象
p1 = np.poly1d(a_seg1)
p2 = np.poly1d(a_seg2)
p3 = np.poly1d(a_seg3)

def V_drift_fit(T):
    """
    根据新的三段拟合结果计算零点漂移 V_drift(T)
    段 1: -40 ~ 0 ℃
    段 2: 0 ~ 35 ℃
    段 3: 35 ~ 80 ℃
    """
    if T < 0:
        return p1(T)
    elif T < 35:
        return p2(T)
    else:
        return p3(T)

# 将多项式转换为字符串，便于显示在图上
def poly_to_str(p, var='T', precision=5):
    """
    将 np.poly1d 多项式转化为字符串，例如 'aT^2 + bT + c'
    其中 precision 控制小数位数
    """
    coeffs = p.c
    n = len(coeffs) - 1
    terms = []
    for i, c in enumerate(coeffs):
        power = n - i
        if abs(c) < 1e-9:
            continue
        # 格式化每一项
        if power == 0:
            term = f"{c:.{precision}f}"
        elif power == 1:
            term = f"{c:.{precision}f}{var}"
        else:
            term = f"{c:.{precision}f}{var}^{power}"
        terms.append(term)

    if not terms:
        return "0"

    expr = " + ".join(terms)
    expr = expr.replace("+ -", "- ")  # 处理负号显示
    return expr

# --- 3. 计算原始数据和补偿数据 ---

# 定义气压范围和参考点
P_range = np.linspace(940, 1060, 50)
P_ref = 1000  # hPa (参考气压点，零压点)
T_ref = 0     # °C (参考温度点)

# 0°C 参考温度下的零点电压 V_zero, ref
V_zero_ref = V_drift_fit(T_ref)  # 拟合模型计算出的 0°C 零点

raw_data = {}
comp_data = {}

for i, T in enumerate(T_points):
    # 使用模拟的 V_zero_sim 和 S_sim 创建原始输出 V_raw
    # V_raw(P, T) = S_sim[i] * (P - P_ref) + V_zero_sim[i]
    S_T = S_sim[i]
    V_zero_T = V_zero_sim[i]
    V_raw = S_T * (P_range - P_ref) + V_zero_T
    raw_data[T] = V_raw

    # 零点补偿计算：V_comp = V_raw - V_drift(T) + V_zero_ref
    V_drift = V_drift_fit(T)  # MCU计算当前温度下的漂移值
    V_comp = V_raw - V_drift + V_zero_ref
    comp_data[T] = V_comp

# --- 4. 绘图 ---

fig, ax = plt.subplots(figsize=(10, 6))

color_map = {-40: 'black', -20: 'red', 0: 'blue', 20: 'green', 40: 'purple'}

# 补偿前的原始曲线
for T, V_raw in raw_data.items():
    ax.plot(P_range, V_raw, color=color_map[T], linestyle='-', alpha=0.6, label=f'原始 {T}°C')

# 补偿后的曲线
for T, V_comp in comp_data.items():
    ax.plot(P_range, V_comp, color=color_map[T], linestyle='--', linewidth=2, label=f'补偿 {T}°C')

# 参考线 (0°C)
ax.plot(P_range, comp_data[T_ref], color='black', linestyle='-', linewidth=1.5, label='参考线 (0°C)')

# 零点对齐指示线
ax.axvline(P_ref, color='gray', linestyle=':', alpha=0.7)
ax.axhline(V_zero_ref, color='gray', linestyle=':', alpha=0.7)

# 轴标签和标题
ax.set_title('G/h-BN/G 气压传感器零点补偿效果对比图', fontsize=14)
ax.set_xlabel('气压 P (hPa)', fontsize=12)
ax.set_ylabel('输出电压 V (mV)', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower left', ncol=2, fontsize=10)

# 限制Y轴范围以匹配原始图像的视觉效果
ax.set_ylim(-3000, 3000)

# --- 在图像右上角标出三段插值多项式 ----
text_str = (
    "零点漂移拟合多项式 V_drift(T)：\n"
    " -40°C ≤ T < 0°C:\n  V_drift(T) = " + poly_to_str(p1) + "\n"
    " 0°C ≤ T < 35°C:\n  V_drift(T) = " + poly_to_str(p2) + "\n"
    " 35°C ≤ T ≤ 80°C:\n  V_drift(T) = " + poly_to_str(p3)
)

ax.text(
    0.98, 0.98, text_str,
    transform=ax.transAxes,
    va='top', ha='right',
    fontsize=8,
    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
)

plt.tight_layout()
plt.show()
