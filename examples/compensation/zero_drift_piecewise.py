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

# --- 2. 分段最小二乘拟合 V_zero(T) ---

# 分段策略 (与前例相同，用于演示分段拟合流程)
# Segment 1: T < -20°C (线性拟合)
# Segment 2: -20°C <= T < 20°C (二次拟合)
# Segment 3: T >= 20°C (线性拟合)

# 拟合系数计算
T_seg1_zero = T_points[T_points <= -20]
Vz_seg1 = V_zero_sim[T_points <= -20]
a_seg1 = np.polyfit(T_seg1_zero, Vz_seg1, 1)  # Segment 1: 线性拟合

T_seg2_zero = T_points[(T_points > -40) & (T_points < 40)]  # -20, 0, 20
Vz_seg2 = V_zero_sim[(T_points > -40) & (T_points < 40)]
a_seg2 = np.polyfit(T_seg2_zero, Vz_seg2, 2)  # Segment 2: 二次拟合

T_seg3_zero = T_points[T_points >= 20]
Vz_seg3 = V_zero_sim[T_points >= 20]
a_seg3 = np.polyfit(T_seg3_zero, Vz_seg3, 1)  # Segment 3: 线性拟合

def V_drift_fit(T):
    """
    根据分段拟合系数计算零点漂移 V_drift(T)
    """
    # np.poly1d(coeffs) 用于方便地计算多项式的值
    if T < -20:
        return np.poly1d(a_seg1)(T)
    elif T < 20:
        return np.poly1d(a_seg2)(T)
    else:
        return np.poly1d(a_seg3)(T)

# --- 3. 计算原始数据和补偿数据 ---

# 定义气压范围和参考点
P_range = np.linspace(940, 1060, 50)
P_ref = 1000  # hPa (参考气压点，零压点)
T_ref = 0  # °C (参考温度点)

# 0°C 参考温度下的零点电压 V_zero, ref
V_zero_ref = V_drift_fit(T_ref)  # 拟合模型计算出的 0°C 零点 (应接近 0 mV)

raw_data = {}
comp_data = {}

for i, T in enumerate(T_points):
    # 使用模拟的 V_zero_sim 和 S_sim 创建原始输出 V_raw
    # V_raw(P, T) = S_sim[i] * (P - P_ref) + V_zero_sim[i]
    S_T = S_sim[i]
    V_zero_T = V_zero_sim[i]
    V_raw = S_T * (P_range - P_ref) + V_zero_T
    raw_data[T] = V_raw

    # 零点补偿计算 - 关键步骤
    # V_comp = V_raw - V_drift(T) + V_zero, ref
    V_drift = V_drift_fit(T)  # MCU计算当前温度下的漂移值
    V_comp = V_raw - V_drift + V_zero_ref
    comp_data[T] = V_comp

# --- 4. 绘图 ---

fig, ax = plt.subplots(figsize=(10, 6))

color_map = {-40: 'black', -20: 'red', 0: 'blue', 20: 'green', 40: 'purple'}

# --- 绘制补偿前的原始曲线 (发散线) ---
for T, V_raw in raw_data.items():
    ax.plot(P_range, V_raw, color=color_map[T], linestyle='-', alpha=0.6, label=f'原始 {T}°C')

# --- 绘制补偿后的曲线 (零点收敛线) ---
for T, V_comp in comp_data.items():
    # 补偿后的曲线使用粗虚线，以区分原始数据
    ax.plot(P_range, V_comp, color=color_map[T], linestyle='--', linewidth=2, label=f'补偿 {T}°C')

# --- 绘制参考线 (0°C) ---
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

plt.show()
