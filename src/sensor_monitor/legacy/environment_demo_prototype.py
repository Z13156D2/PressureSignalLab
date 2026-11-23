
from sensor_monitor.storage import load_settings, save_settings, export_directory

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import random
from datetime import datetime
import os
import json

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("🔬 高精度环境监测系统 v3.0")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f5f5f5")

        # 初始化数据存储
        self.data_buffer = []
        self.history_data = []  # 历史记录
        self.sample_count = 0

        # 系统设置默认值 (已更新为匹配新气压范围)
        self.settings = {
            'sampling_rate': 1000,  # 采样率(ms)
            'alert_threshold_high': 99800.0,  # 高压警报阈值 (Pa)
            'alert_threshold_low': 99500.0,  # 低压警报阈值 (Pa)
            'data_retention': 1000,  # 数据保留数量
            'auto_save': False,  # 自动保存
            'theme': 'light',  # 主题
            'enable_sound': True,  # 启用声音
            'chart_update_rate': 10,  # 图表更新率
        }

        # 加载历史设置
        self.load_settings()

        # 配置样式
        self.setup_styles()

        # 创建主界面
        self.create_interface()

        # 启动数据采集（使用模拟数据）
        self.start_monitoring()

    def setup_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置按钮样式
        style.configure('Sidebar.TButton',
                        font=('Microsoft YaHei UI', 11, 'bold'),
                        padding=15,
                        background='#e0e0e0',
                        foreground='#333333',
                        borderwidth=0)
        style.map('Sidebar.TButton',
                  background=[('active', '#d0d0d0'), ('pressed', '#c0c0c0')])

        # 配置Frame样式
        style.configure('Sidebar.TFrame',
                        background='#e8e8e8',
                        relief='flat')

        style.configure('Content.TFrame',
                        background='#f5f5f5',
                        relief='flat')

        # 配置Label样式
        style.configure('Title.TLabel',
                        font=('Microsoft YaHei UI', 16, 'bold'),
                        background='#f5f5f5',
                        foreground='#2c8c5c')

    def create_interface(self):
        """创建用户界面"""
        # 主容器
        main_frame = ttk.Frame(self.master, style='Content.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧导航栏
        sidebar_frame = ttk.Frame(main_frame, width=220, style='Sidebar.TFrame')
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        sidebar_frame.pack_propagate(False)

        # 标题
        title_label = tk.Label(sidebar_frame,
                               text="📊 监测面板",
                               font=('Microsoft YaHei UI', 14, 'bold'),
                               bg='#e8e8e8',
                               fg='#2c8c5c',
                               pady=20)
        title_label.pack(fill=tk.X)

        # 导航按钮
        buttons = [
            ("📈 趋势详情", self.show_charts, "💡"),
            ("📜 历史记录", self.show_history, "📋"),
            ("📊 数据分析", self.show_analysis, "📉"),
            ("⚙️ 系统设置", self.show_settings, "🔧"),
            ("💾 导出数据", self.save_dataset, "📁"),
            ("🔄 刷新数据", self.refresh_data, "♻️"),
        ]

        for text, command, icon in buttons:
            btn = tk.Button(sidebar_frame,
                            text=f"{icon} {text}",
                            command=command,
                            font=('Microsoft YaHei UI', 10, 'bold'),
                            bg='#d0d0d0',
                            fg='#333333',
                            activebackground='#c0c0c0',
                            activeforeground='#2c8c5c',
                            bd=0,
                            pady=12,
                            cursor='hand2')
            btn.pack(fill=tk.X, padx=10, pady=5)

        # 状态指示器
        status_frame = tk.Frame(sidebar_frame, bg='#e8e8e8')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.status_label = tk.Label(status_frame,
                                     text="● 运行中",
                                     font=('Microsoft YaHei UI', 9),
                                     bg='#e8e8e8',
                                     fg='#2c8c5c')
        self.status_label.pack()

        self.sample_label = tk.Label(status_frame,
                                     text="采样: 0",
                                     font=('Consolas', 9),
                                     bg='#e8e8e8',
                                     fg='#666666')
        self.sample_label.pack()

        # 右侧内容区域
        content_frame = ttk.Frame(main_frame, style='Content.TFrame')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 顶部数据面板
        top_panel = tk.Frame(content_frame, bg='#f5f5f5')
        top_panel.pack(fill=tk.X, pady=(0, 15))

        # 数据卡片
        self.create_data_cards(top_panel)

        # 图表区域
        chart_frame = tk.Frame(content_frame, bg='#ffffff', relief='flat', bd=0)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        # 创建matplotlib图表
        self.figure = plt.Figure(figsize=(10, 5), facecolor='#ffffff')
        self.axes = self.figure.add_subplot(111, facecolor='#fafafa')

        # 绘制实时气压曲线
        self.plot_line, = self.axes.plot([], [], color='#0077cc', linewidth=2, marker='o', markersize=3)
        self.axes.set_title("实时气压变化趋势 (Pa)", fontsize=14, color='#333333', fontweight='bold')
        self.axes.set_xlabel("采样点", fontsize=10, color='#666666')
        self.axes.set_ylabel("气压值 (Pa)", fontsize=10, color='#666666')
        self.axes.grid(True, alpha=0.3, linestyle='--', color='#cccccc')
        self.axes.tick_params(colors='#666666', labelsize=8)

        # 设置坐标轴颜色
        for spine in self.axes.spines.values():
            spine.set_edgecolor('#cccccc')

        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_data_cards(self, parent):
        """创建数据显示卡片 - 已更新标签"""
        # 修改点：更新了卡片的标题和对应的颜色
        cards_data = [
            ("实时气压", "-- Pa", "pressure_card", "#ff7675"),  # 原电流
            ("相对高度", "-- m", "altitude_card", "#74b9ff"),  # 原推算气压
            ("实时温度", "-- °C", "temp_card", "#55efc4"),  # 原峰值气压
            ("采样数量", "0", "count_card", "#fdcb6e"),
        ]

        self.data_cards = {}

        for i, (title, value, key, color) in enumerate(cards_data):
            card = tk.Frame(parent, bg=color, relief='flat', bd=0)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            title_label = tk.Label(card,
                                   text=title,
                                   font=('Microsoft YaHei UI', 10),
                                   bg=color,
                                   fg='#ffffff')
            title_label.pack(pady=(10, 0))

            value_label = tk.Label(card,
                                   text=value,
                                   font=('Consolas', 18, 'bold'),
                                   bg=color,
                                   fg='#ffffff')
            value_label.pack(pady=(0, 10))

            self.data_cards[key] = value_label

    def load_settings(self):
        """加载设置"""
        try:
            self.settings.update(load_settings(__file__))
        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_settings_to_file(self):
        """保存设置到文件"""
        try:
            save_settings(__file__, self.settings)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def generate_fake_data(self):
        """生成符合物理逻辑的模拟数据 - 核心修改点"""

        # 1. 相对高度：标准值 30.40m，随机波动 ±0.1m
        base_altitude = 30.40
        altitude_noise = random.uniform(-0.1, 0.1)
        altitude = base_altitude + altitude_noise

        # 2. 实时气压：标准值 99644.40 Pa (对应30.40m)
        # 波动计算：根据高度波动反向计算气压波动。
        # 物理常识：近地面高度每上升1m，气压下降约12Pa (ρg ≈ 1.2 * 9.8 ≈ 11.76)
        base_pressure = 99644.40
        pressure_change_per_meter = 12.0  # 设定系数

        # 高度增加 -> 气压减少
        pressure_fluctuation = altitude_noise * pressure_change_per_meter
        pressure = base_pressure - pressure_fluctuation

        # 3. 实时温度：标准值 -2.5°C，随机波动 ±0.1°C
        base_temp = -2.5
        temp_noise = random.uniform(-0.1, 0.1)
        temperature = base_temp + temp_noise

        return pressure, altitude, temperature

    def update_interface(self, pressure, altitude, temperature):
        """更新界面显示"""
        # 更新数据卡片
        self.data_cards['pressure_card'].config(text=f"{pressure:.2f} Pa")
        self.data_cards['altitude_card'].config(text=f"{altitude:.4f} m")
        self.data_cards['temp_card'].config(text=f"{temperature:.2f} °C")
        self.data_cards['count_card'].config(text=f"{len(self.data_buffer)}")

        # 更新曲线数据 (绘制气压)
        if len(self.data_buffer) > 0:
            display_count = min(100, len(self.data_buffer))
            recent_data = self.data_buffer[-display_count:]

            indices = list(range(len(recent_data)))
            # 这里绘制气压值
            plot_data = [d['pressure'] for d in recent_data]

            self.plot_line.set_data(indices, plot_data)
            self.axes.relim()
            self.axes.autoscale_view()
            self.graph_canvas.draw()

        # 更新状态标签
        self.sample_label.config(text=f"采样: {self.sample_count}")

        # 检查警报 (基于气压)
        self.check_alerts(pressure)

    def check_alerts(self, pressure):
        """检查警报"""
        if pressure > self.settings['alert_threshold_high']:
            self.status_label.config(text="⚠️ 高压警报", fg='#d63031')
        elif pressure < self.settings['alert_threshold_low']:
            self.status_label.config(text="⚠️ 低压警报", fg='#fdcb6e')
        else:
            self.status_label.config(text="● 运行中", fg='#2c8c5c')

    def data_acquisition(self):
        """数据采集核心逻辑"""
        try:
            # 获取计算后的数据
            pressure, altitude, temperature = self.generate_fake_data()

            data_point = {
                'timestamp': datetime.now(),
                'pressure': pressure,  # 实时气压
                'altitude': altitude,  # 相对高度
                'temperature': temperature  # 实时温度
            }

            self.data_buffer.append(data_point)
            self.sample_count += 1

            # 数据保留限制
            if len(self.data_buffer) > self.settings['data_retention']:
                self.history_data.extend(self.data_buffer[:len(self.data_buffer) - self.settings['data_retention']])
                self.data_buffer = self.data_buffer[-self.settings['data_retention']:]

            # 更新界面
            if self.sample_count % self.settings['chart_update_rate'] == 0:
                self.update_interface(pressure, altitude, temperature)

        except Exception as e:
            print(f"数据采集异常: {str(e)}")

        self.master.after(self.settings['sampling_rate'], self.data_acquisition)

    def start_monitoring(self):
        """启动监测"""
        self.data_acquisition()

    def save_dataset(self):
        """保存数据到 data/exports"""
        if not self.data_buffer and not self.history_data:
            messagebox.showwarning("空数据集", "未采集到有效数据")
            return

        try:
            output_directory = export_directory()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            file_path = os.path.join(output_directory, f"environment_data_{timestamp}.xlsx")

            all_data = self.history_data + self.data_buffer
            df = pd.DataFrame(all_data)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')

            # 重命名列以匹配导出
            df = df.rename(columns={
                'pressure': '实时气压(Pa)',
                'altitude': '相对高度(m)',
                'temperature': '实时温度(°C)'
            })

            df.to_excel(file_path, index=False, engine='openpyxl')

            messagebox.showinfo("保存成功",
                                f"文件已保存至：\n{file_path}\n"
                                f"记录总数：{len(df)}条")

        except Exception as e:
            messagebox.showerror("保存失败", f"错误原因：\n{str(e)}")

    def refresh_data(self):
        """刷新数据"""
        response = messagebox.askyesno("刷新确认", "确定要清空当前数据缓冲区吗？\n历史数据将被保留。")
        if response:
            self.history_data.extend(self.data_buffer)
            self.data_buffer = []
            messagebox.showinfo("刷新完成", "数据已刷新")

    def show_charts(self):
        """显示多图表详情 - 原 show_pressure"""
        window = tk.Toplevel(self.master)
        window.title("📈 多维数据趋势")
        window.geometry("900x700")
        window.configure(bg='#f5f5f5')

        # 创建多图表显示
        fig = plt.Figure(figsize=(9, 6.5), facecolor='#ffffff')

        # 1. 气压趋势图
        ax1 = fig.add_subplot(311, facecolor='#fafafa')
        if self.data_buffer:
            data = [d['pressure'] for d in self.data_buffer]
            ax1.plot(data, color='#ff7675', linewidth=2)
            ax1.set_title('实时气压趋势', color='#333333', fontsize=10, fontweight='bold')
            ax1.set_ylabel('气压 (Pa)', color='#666666', fontsize=8)
            ax1.grid(True, alpha=0.3, color='#cccccc')

        # 2. 高度趋势图
        ax2 = fig.add_subplot(312, facecolor='#fafafa')
        if self.data_buffer:
            data = [d['altitude'] for d in self.data_buffer]
            ax2.plot(data, color='#74b9ff', linewidth=2)
            ax2.set_title('相对高度趋势', color='#333333', fontsize=10, fontweight='bold')
            ax2.set_ylabel('高度 (m)', color='#666666', fontsize=8)
            ax2.grid(True, alpha=0.3, color='#cccccc')

        # 3. 温度趋势图
        ax3 = fig.add_subplot(313, facecolor='#fafafa')
        if self.data_buffer:
            data = [d['temperature'] for d in self.data_buffer]
            ax3.plot(data, color='#55efc4', linewidth=2)
            ax3.set_title('实时温度趋势', color='#333333', fontsize=10, fontweight='bold')
            ax3.set_ylabel('温度 (°C)', color='#666666', fontsize=8)
            ax3.set_xlabel('采样点', color='#666666')
            ax3.grid(True, alpha=0.3, color='#cccccc')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def show_history(self):
        """显示历史记录 - 列名已修改"""
        window = tk.Toplevel(self.master)
        window.title("📜 历史数据记录")
        window.geometry("1100x650")
        window.configure(bg='#f5f5f5')

        # ... (标题和统计面板代码保持结构不变，仅更新变量名) ...
        title_frame = tk.Frame(window, bg='#ffffff', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="📋 历史数据明细",
                               font=('Microsoft YaHei UI', 16, 'bold'), bg='#ffffff', fg='#2c8c5c')
        title_label.pack(pady=15)

        # Treeview配置
        tree_frame = tk.Frame(window, bg='#f5f5f5')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 修改点：列定义
        columns = ('序号', '时间戳', '实时气压', '相对高度', '实时温度')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)

        # 设置列头
        tree.heading('序号', text='序号')
        tree.heading('时间戳', text='时间戳')
        tree.heading('实时气压', text='实时气压 (Pa)')  # 原电流
        tree.heading('相对高度', text='相对高度 (m)')  # 原气压
        tree.heading('实时温度', text='实时温度 (°C)')  # 原数据类型

        tree.column('序号', width=60, anchor='center')
        tree.column('时间戳', width=200, anchor='center')
        tree.column('实时气压', width=120, anchor='center')
        tree.column('相对高度', width=120, anchor='center')
        tree.column('实时温度', width=120, anchor='center')

        # 插入数据
        # 历史数据
        for idx, data in enumerate(self.history_data, 1):
            tree.insert('', 'end', values=(
                idx,
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                f"{data['pressure']:.2f}",
                f"{data['altitude']:.4f}",
                f"{data['temperature']:.2f}"
            ))

        # 当前缓冲
        for idx, data in enumerate(self.data_buffer, len(self.history_data) + 1):
            tree.insert('', 'end', values=(
                idx,
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                f"{data['pressure']:.2f}",
                f"{data['altitude']:.4f}",
                f"{data['temperature']:.2f}"
            ))

        tree.pack(fill=tk.BOTH, expand=True)

    def show_analysis(self):
        """数据分析 - 已更新统计对象"""
        window = tk.Toplevel(self.master)
        window.title("📊 数据分析中心")
        window.geometry("1100x750")
        window.configure(bg='#f5f5f5')

        # ... (标题代码省略) ...

        if not self.data_buffer and not self.history_data:
            return

        all_data = self.history_data + self.data_buffer
        pressures = np.array([d['pressure'] for d in all_data])
        altitudes = np.array([d['altitude'] for d in all_data])
        temps = np.array([d['temperature'] for d in all_data])

        # 计算统计指标
        stats = {
            '实时气压 (Pa)': {
                '平均值': np.mean(pressures),
                '最大值': np.max(pressures),
                '最小值': np.min(pressures),
                '标准差': np.std(pressures),
            },
            '相对高度 (m)': {
                '平均值': np.mean(altitudes),
                '最大值': np.max(altitudes),
                '最小值': np.min(altitudes),
                '标准差': np.std(altitudes),
            },
            '实时温度 (°C)': {
                '平均值': np.mean(temps),
                '最大值': np.max(temps),
                '最小值': np.min(temps),
                '标准差': np.std(temps),
            }
        }

        # 创建统计信息展示区 (代码逻辑与原版相似，只是变量改变)
        stats_container = tk.Frame(window, bg='#f5f5f5')
        stats_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(stats_container, bg='#f5f5f5')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        colors = ['#ff7675', '#74b9ff', '#55efc4']
        for idx, (category, data) in enumerate(stats.items()):
            cat_frame = tk.Frame(left_frame, bg='#ffffff', relief='flat')
            cat_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            cat_title = tk.Label(cat_frame, text=f"📋 {category}",
                                 font=('Microsoft YaHei UI', 12, 'bold'),
                                 bg=colors[idx % len(colors)], fg='#ffffff', pady=10)
            cat_title.pack(fill=tk.X)

            for key, value in data.items():
                item_frame = tk.Frame(cat_frame, bg='#ffffff')
                item_frame.pack(fill=tk.X, padx=10, pady=3)

                tk.Label(item_frame, text=f"{key}:", bg='#ffffff', width=10, anchor='w').pack(side=tk.LEFT)
                tk.Label(item_frame, text=f"{value:.4f}", font=('Consolas', 10, 'bold'),
                         bg='#ffffff', fg='#0077cc').pack(side=tk.RIGHT)

        # 右侧图表 (只绘制气压分布)
        right_frame = tk.Frame(stats_container, bg='#ffffff')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        fig = plt.Figure(figsize=(5.5, 7), facecolor='#ffffff')
        ax1 = fig.add_subplot(211, facecolor='#fafafa')
        ax1.hist(pressures, bins=30, color='#74b9ff', alpha=0.7, edgecolor='#333333')
        ax1.set_title('气压分布直方图', color='#333333', fontsize=10)
        ax1.set_xlabel('气压 (Pa)', fontsize=8)

        ax2 = fig.add_subplot(212, facecolor='#fafafa')
        ax2.scatter(altitudes, pressures, c='#ff7675', alpha=0.6, s=20)
        ax2.set_title('高度-气压关系图', color='#333333', fontsize=10)
        ax2.set_xlabel('高度 (m)', fontsize=8)
        ax2.set_ylabel('气压 (Pa)', fontsize=8)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=right_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def show_settings(self):
        """系统设置"""
        window = tk.Toplevel(self.master)
        window.title("⚙️ 系统设置")
        window.geometry("700x650")
        window.configure(bg='#f5f5f5')

        # 标题
        title_frame = tk.Frame(window, bg='#ffffff', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame,
                               text="🔧 参数配置",
                               font=('Microsoft YaHei UI', 16, 'bold'),
                               bg='#ffffff',
                               fg='#2c8c5c')
        title_label.pack(pady=15)

        # 设置区域
        settings_frame = tk.Frame(window, bg='#f5f5f5')
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 设置项
        setting_entries = {}

        settings_config = [
            ('采样率 (ms)', 'sampling_rate', 'number'),
            ('高压警报阈值 (Pa)', 'alert_threshold_high', 'number'),
            ('低压警报阈值 (Pa)', 'alert_threshold_low', 'number'),
            ('数据保留数量', 'data_retention', 'number'),
            ('图表更新率', 'chart_update_rate', 'number'),
            ('自动保存', 'auto_save', 'bool'),
            ('启用声音', 'enable_sound', 'bool'),
            ('主题', 'theme', 'option'),
        ]

        row = 0
        for label_text, key, input_type in settings_config:
            frame = tk.Frame(settings_frame, bg='#ffffff', pady=5)
            frame.pack(fill=tk.X, pady=5)

            label = tk.Label(frame,
                             text=label_text + ":",
                             font=('Microsoft YaHei UI', 11),
                             bg='#ffffff',
                             fg='#333333',
                             width=20,
                             anchor='w')
            label.pack(side=tk.LEFT, padx=10)

            if input_type == 'number':
                entry = tk.Entry(frame,
                                 font=('Consolas', 11),
                                 bg='#e8e8e8',
                                 fg='#333333',
                                 insertbackground='#333333',
                                 relief='flat',
                                 bd=5)
                entry.insert(0, str(self.settings[key]))
                entry.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
                setting_entries[key] = entry

            elif input_type == 'bool':
                var = tk.BooleanVar(value=self.settings[key])
                check = tk.Checkbutton(frame,
                                       variable=var,
                                       bg='#ffffff',
                                       fg='#333333',
                                       selectcolor='#e8e8e8',
                                       activebackground='#ffffff',
                                       activeforeground='#2c8c5c',
                                       font=('Microsoft YaHei UI', 10))
                check.pack(side=tk.RIGHT, padx=10)
                setting_entries[key] = var

            elif input_type == 'option':
                var = tk.StringVar(value=self.settings[key])
                options = ['dark', 'light']
                menu = ttk.OptionMenu(frame, var, self.settings[key], *options)
                menu.pack(side=tk.RIGHT, padx=10)
                setting_entries[key] = var

            row += 1

        # 按钮区
        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def save_settings():
            try:
                for key, widget in setting_entries.items():
                    if isinstance(widget, tk.Entry):
                        value = widget.get()
                        if key in ['sampling_rate', 'data_retention', 'chart_update_rate']:
                            self.settings[key] = int(value)
                        else:
                            self.settings[key] = float(value)
                    elif isinstance(widget, tk.BooleanVar):
                        self.settings[key] = widget.get()
                    elif isinstance(widget, tk.StringVar):
                        self.settings[key] = widget.get()

                self.save_settings_to_file()
                messagebox.showinfo("成功", "设置已保存！")
                window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存设置失败：{str(e)}")

        save_btn = tk.Button(button_frame, text="💾 保存设置", font=('Microsoft YaHei UI', 11, 'bold'),
                             bg='#74b9ff', fg='#ffffff', bd=0, padx=30, pady=10, command=save_settings)
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(button_frame, text="❌ 取消", font=('Microsoft YaHei UI', 11, 'bold'),
                               bg='#55efc4', fg='#ffffff', bd=0, padx=30, pady=10, command=window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)


if __name__ == "__main__":
    root = tk.Tk()


    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = SerialMonitor(root)
    root.mainloop()