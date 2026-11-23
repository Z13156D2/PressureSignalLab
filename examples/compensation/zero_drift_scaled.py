import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置支持中文的字体（可以选择 SimHei 或其他支持中文的字体）
rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
rcParams['axes.unicode_minus'] = False  # 防止负号显示为方块

# ============================================================
# 1) 原始“趋势数据”（你原来用于模拟的趋势，不改动其相对形状）
# ============================================================

T_points = np.array([-40, -20, 0, 20, 40])  # °C

# 原始趋势（只是“形状/趋势”）
V_zero_trend = np.array([50, 20, 0, -20, -50], dtype=float)          # 只是趋势单位（原来是mV量级）
S_trend = np.array([-59.0, -58.5, -58.0, -57.5, -57.0], dtype=float) # 只是趋势单位（原来是mV/hPa量级）

# ============================================================
# 2) 目标坐标轴范围（你要求的真实量级）
# ============================================================

P_min, P_max = 100.0, 1100.0      # hPa
V_top, V_bottom = -8.482, -20.887 # mV（注意：上限更“大”，下限更“小”，会导致y轴反向显示，符合你给的区间写法）

# 我们把“参考压力点”选为 P_min，这样 V_zero(T) 就代表 P=100hPa 时的输出电压
P_ref = P_min

# ============================================================
# 3) 把趋势数据缩放到目标量级（关键改动：曲线数值会变化）
#    - 零点漂移：缩放到约 ±0.8mV 的量级，并把最高点对齐到 V_top
#    - 灵敏度：缩放到约 0.01mV/hPa 量级，并让最坏情况对齐到 V_bottom
# ============================================================

# 3.1 零点漂移缩放：把 trend 的 ±50 缩放为 ±0.8mV（比例 0.016）
k0 = 0.016  # 50 * 0.016 = 0.8 mV
baseline = V_top - V_zero_trend[0] * k0  # 确保 T=-40(趋势=50) 时 V_zero = V_top
V_zero_sim = baseline + V_zero_trend * k0  # 现在是真正 mV 量级的零点（在 P=100hPa）

# 3.2 灵敏度缩放：解一个比例 kS，使得 T=40°C 在 P=1100hPa 时达到 V_bottom
# V(P,T)=S(T)*(P-P_ref)+V_zero(T)
# 取 T=40°C：V_bottom = (S_trend[-1]*kS)*(P_max-P_ref) + V_zero_sim[-1]
kS = (V_bottom - V_zero_sim[-1]) / (S_trend[-1] * (P_max - P_ref))
S_sim = S_trend * kS  # 现在是真正 mV/hPa 量级的灵敏度

# ============================================================
# 4) 分段拟合 V_zero(T)（用于补偿）
#    你原代码里用了 35、80，但没有对应数据点；
#    我这里用“线性插值/外推”补齐 V(35)、V(80)，避免拟合不合理。
# ============================================================

base_V = dict(zip(T_points, V_zero_sim))

# 补齐 35°C（插值）与 80°C（外推）
base_V[35] = np.interp(35, T_points, V_zero_sim)
base_V[80] = V_zero_sim[-1] + (80 - 40) * (V_zero_sim[-1] - V_zero_sim[-2]) / (40 - 20)

# 三段拟合点
T_seg1_zero = np.array([-40, -20, 0])
Vz_seg1 = np.array([base_V[t] for t in T_seg1_zero])

T_seg2_zero = np.array([0, 20, 35])
Vz_seg2 = np.array([base_V[t] for t in T_seg2_zero])

T_seg3_zero = np.array([35, 40, 80])
Vz_seg3 = np.array([base_V[t] for t in T_seg3_zero])

# 统一用二次拟合（更稳：每段3个点 -> 二次刚好）
deg1 = deg2 = deg3 = 2

rng = np.random.default_rng(42)

def randomize_coeffs(coeffs, scale=1e-5):
    noise = rng.uniform(-scale, scale, size=coeffs.shape)
    return coeffs + noise

a_seg1 = randomize_coeffs(np.polyfit(T_seg1_zero, Vz_seg1, deg1))
a_seg2 = randomize_coeffs(np.polyfit(T_seg2_zero, Vz_seg2, deg2))
a_seg3 = randomize_coeffs(np.polyfit(T_seg3_zero, Vz_seg3, deg3))

p1 = np.poly1d(a_seg1)
p2 = np.poly1d(a_seg2)
p3 = np.poly1d(a_seg3)

def V_drift_fit(T):
    if T < 0:
        return p1(T)
    elif T < 35:
        return p2(T)
    else:
        return p3(T)

def poly_to_str(p, var='T', precision=5):
    coeffs = p.c
    n = len(coeffs) - 1
    terms = []
    for i, c in enumerate(coeffs):
        power = n - i
        if abs(c) < 1e-12:
            continue
        if power == 0:
            term = f"{c:.{precision}f}"
        elif power == 1:
            term = f"{c:.{precision}f}{var}"
        else:
            term = f"{c:.{precision}f}{var}^{power}"
        terms.append(term)
    if not terms:
        return "0"
    expr = " + ".join(terms).replace("+ -", "- ")
    return expr

# ============================================================
# 5) 生成原始与补偿数据（曲线数值已在目标量级）
# ============================================================

P_range = np.linspace(P_min, P_max, 200)  # 更平滑
T_ref = 0
V_zero_ref = V_drift_fit(T_ref)

raw_data = {}
comp_data = {}

for i, T in enumerate(T_points):
    S_T = S_sim[i]
    V_zero_T = V_zero_sim[i]
    V_raw = S_T * (P_range - P_ref) + V_zero_T
    raw_data[T] = V_raw

    V_drift = V_drift_fit(T)
    V_comp = V_raw - V_drift + V_zero_ref
    comp_data[T] = V_comp

# ============================================================
# 6) 绘图
# ============================================================

fig, ax = plt.subplots(figsize=(10, 6))

color_map = {-40: 'black', -20: 'red', 0: 'blue', 20: 'green', 40: 'purple'}

# 原始曲线
for T, V_raw in raw_data.items():
    ax.plot(P_range, V_raw, color=color_map[T], linestyle='-', alpha=0.6, label=f'原始 {T}°C')

# 补偿曲线
for T, V_comp in comp_data.items():
    ax.plot(P_range, V_comp, color=color_map[T], linestyle='--', linewidth=2, label=f'补偿 {T}°C')

# 参考线 (0°C)
ax.plot(P_range, comp_data[T_ref], color='black', linestyle='-', linewidth=1.5, label='参考线 (0°C)')

# 指示线：参考压力点、参考零点
ax.axvline(P_ref, color='gray', linestyle=':', alpha=0.7)
ax.axhline(V_zero_ref, color='gray', linestyle=':', alpha=0.7)

ax.set_title('G/h-BN/G 气压传感器零点补偿效果对比图', fontsize=14)
ax.set_xlabel('气压 P (hPa)', fontsize=12)
ax.set_ylabel('输出电压 V (mV)', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower left', ncol=2, fontsize=10)

# 你要求的坐标轴范围（注意：这样会让y轴从 -8.482 向下到 -20.887）
ax.set_xlim(P_min, P_max)
# ax.set_ylim(V_top, V_bottom)
ax.set_ylim(V_bottom, V_top)

# 右上角显示多项式
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
