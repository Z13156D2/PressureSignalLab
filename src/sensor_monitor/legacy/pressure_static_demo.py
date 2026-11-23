"""
Program Name: 气压智能监测系统 v5.0 (静态演示版)
Author: Zhentao Zhou
Date: 2025-11-25
Version: 5.0

Description:
静态演示版本 - 不依赖真实串口设备
1.主界面直接显示预设的气压、温度、高度数值（静态模式）
2.无需串口连接，适用于演示和测试
3.保留数据存储、历史记录管理与 Excel 格式导出
4.保留数据分析功能（平均值、最大值、最小值、标准差）
5.左下角显示"串口已连接"绿色状态

Usage:
1.直接运行程序，无需连接串口设备
2.预设数据：气压 100500 Pa，温度 25.5°C，高度 -39.36 m
3.Excel output: data/exports/

Requirements:
- Python 3.x
- Libraries: tkinter, matplotlib, pandas, numpy

"""

from sensor_monitor.storage import load_settings, save_settings, export_directory



import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("🔬 气压智能监测系统 v5.0")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f5f5f5")

        # 初始化数据存储
        self.data_buffer = []
        self.history_data = []
        self.sample_count = 0

        # 静态演示数据
        self.static_pressure = 0.0  ##99764.9 99644
        self.static_temperature = 0.0   # °C
        self.static_current = 10     # mA
        self.static_height = 0.0      # m (直接指定高度值)
        
        # 高度计算基准（仅用于历史兼容，不再使用）
        self.reference_pressure = 100027.71  # Pa
        self.pressure_drop_per_meter = 12.0  # Pa/m

        # 系统设置默认值
        self.settings = {
            'sampling_rate': 1000,  # 采样周期 (ms) - 静态模式下仅用于模拟
            'alert_threshold_high': 101000.0,
            'alert_threshold_low': 98000.0,
            'data_retention': 1000,
            'auto_save': False,
            'theme': 'light',
            'enable_sound': True,
            'chart_update_rate': 1,
        }

        # 加载历史设置
        self.load_settings()

        # 配置样式
        self.setup_styles()

        # 创建主界面
        self.create_interface()

        # 初始化静态数据
        self.init_static_data()

        # 启动模拟数据采集（用于生成历史数据）
        self.start_monitoring()

    def setup_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            'Sidebar.TButton',
            font=('Microsoft YaHei UI', 11, 'bold'),
            padding=15,
            background='#e0e0e0',
            foreground='#333333',
            borderwidth=0
        )
        style.map(
            'Sidebar.TButton',
            background=[('active', '#d0d0d0'), ('pressed', '#c0c0c0')]
        )

        style.configure('Sidebar.TFrame', background='#e8e8e8', relief='flat')
        style.configure('Content.TFrame', background='#f5f5f5', relief='flat')
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 16, 'bold'),
                       background='#f5f5f5', foreground='#2c8c5c')
        style.configure('Data.TLabel', font=('Consolas', 14, 'bold'),
                       background='#e0e0e0', foreground='#0077cc', padding=10)

    def create_interface(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.master, style='Content.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧导航栏
        sidebar_frame = ttk.Frame(main_frame, width=220, style='Sidebar.TFrame')
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        sidebar_frame.pack_propagate(False)

        title_label = tk.Label(
            sidebar_frame,
            text="📊 控制面板",
            font=('Microsoft YaHei UI', 14, 'bold'),
            bg='#e8e8e8',
            fg='#2c8c5c',
            pady=20
        )
        title_label.pack(fill=tk.X)

        buttons = [
            ("📈 压力信号", self.show_pressure, "💡"),
            ("📜 历史记录", self.show_history, "📋"),
            ("📊 数据分析", self.show_analysis, "📉"),
            ("⚙️ 系统设置", self.show_settings, "🔧"),
            ("💾 导出数据", self.save_dataset, "📁"),
            ("🔄 刷新数据", self.refresh_data, "♻️"),
        ]

        for text, command, icon in buttons:
            btn = tk.Button(
                sidebar_frame,
                text=f"{icon} {text}",
                command=command,
                font=('Microsoft YaHei UI', 10, 'bold'),
                bg='#d0d0d0',
                fg='#333333',
                activebackground='#c0c0c0',
                activeforeground='#2c8c5c',
                bd=0,
                pady=12,
                cursor='hand2'
            )
            btn.pack(fill=tk.X, padx=10, pady=5)

        # 状态指示器 - 绿色"串口已连接"
        status_frame = tk.Frame(sidebar_frame, bg='#e8e8e8')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.status_label = tk.Label(
            status_frame,
            text="● 串口已连接",
            font=('Microsoft YaHei UI', 9),
            bg='#e8e8e8',
            fg='#2c8c5c'  # 绿色
        )
        self.status_label.pack()

        # 右侧内容区域
        content_frame = ttk.Frame(main_frame, style='Content.TFrame')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_panel = tk.Frame(content_frame, bg='#f5f5f5')
        title_panel.pack(fill=tk.X, pady=(0, 20))
        
        main_title = tk.Label(
            title_panel,
            text="气压监测系统",
            font=('Microsoft YaHei UI', 28, 'bold'),
            bg='#f5f5f5',
            fg='#2c8c5c'
        )
        main_title.pack()

        # 三个数据卡片 - 占满整个内容区域
        self.create_large_data_cards(content_frame)

    def create_large_data_cards(self, parent):
        """创建大尺寸数据显示卡片"""
        cards_frame = tk.Frame(parent, bg='#f5f5f5')
        cards_frame.pack(fill=tk.BOTH, expand=True)

        # 配置grid权重，使三个卡片平均分配空间
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_rowconfigure(0, weight=1)

        cards_data = [
            ("实时气压", "-- Pa", "pressure_card", "#74b9ff"),
            ("相对高度", "-- m", "height_card", "#ef8d55"),
            ("实时温度", "-- °C", "temp_card", "#a29bfe"),
        ]

        self.data_cards = {}

        for i, (title, value, key, color) in enumerate(cards_data):
            # 创建卡片容器
            card_container = tk.Frame(cards_frame, bg='#f5f5f5')
            card_container.grid(row=0, column=i, sticky='nsew', padx=15, pady=15)
            
            # 配置容器内部权重
            card_container.grid_rowconfigure(0, weight=1)
            card_container.grid_columnconfigure(0, weight=1)
            
            # 创建圆角卡片效果
            card = tk.Frame(card_container, bg=color, relief='flat', bd=0)
            card.grid(row=0, column=0, sticky='nsew')
            
            # 卡片内部布局
            inner_frame = tk.Frame(card, bg=color)
            inner_frame.place(relx=0.5, rely=0.5, anchor='center')

            # 图标
            icon_map = {
                "pressure_card": "🌡️",
                "height_card": "📏",
                "temp_card": "🌡️"
            }
            
            icon_label = tk.Label(
                inner_frame, 
                text=icon_map.get(key, "📊"),
                font=('Segoe UI Emoji', 80),
                bg=color,
                fg='#ffffff'
            )
            icon_label.pack(pady=(0, 20))

            # 标题
            title_label = tk.Label(
                inner_frame, 
                text=title,
                font=('Microsoft YaHei UI', 24, 'bold'),
                bg=color,
                fg='#ffffff'
            )
            title_label.pack(pady=(0, 30))

            # 数值
            value_label = tk.Label(
                inner_frame,
                text=value,
                font=('Consolas', 24, 'bold'),
                bg=color,
                fg='#ffffff'
            )
            value_label.pack(pady=(0, 20))

            # 添加阴影效果（通过叠加深色边框）
            shadow = tk.Frame(card_container, bg='#cccccc')
            shadow.place(x=5, y=5, relwidth=1, relheight=1)
            shadow.lower()

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

    def init_static_data(self):
        """初始化静态数据显示"""
        # 更新卡片显示静态数据
        self.data_cards['pressure_card'].config(text=f"{self.static_pressure:.2f} Pa")
        self.data_cards['height_card'].config(text=f"{self.static_height:.2f} m")
        self.data_cards['temp_card'].config(text=f"{self.static_temperature:.2f} °C")
        
        # 生成一些初始历史数据用于演示
        for i in range(50):
            # 添加轻微波动
            pressure_variation = self.static_pressure + np.random.normal(0, 50)
            temp_variation = self.static_temperature + np.random.normal(0, 0.5)
            current_variation = self.static_current + np.random.normal(0, 0.2)
            
            data_point = {
                'timestamp': datetime.now(),
                'current': current_variation,
                'pressure': pressure_variation,
                'temperature': temp_variation,
                'acq_index': i + 1
            }
            self.data_buffer.append(data_point)
            self.sample_count += 1

    def update_interface(self):
        """更新界面显示（静态模式下仅用于模拟数据生成）"""
        # 添加轻微波动的新数据点
        pressure_variation = self.static_pressure + np.random.normal(0, 50)
        temp_variation = self.static_temperature + np.random.normal(0, 0.5)
        current_variation = self.static_current + np.random.normal(0, 0.2)
        
        data_point = {
            'timestamp': datetime.now(),
            'current': current_variation,
            'pressure': pressure_variation,
            'temperature': temp_variation,
            'acq_index': self.sample_count + 1
        }

        self.data_buffer.append(data_point)
        self.sample_count += 1

        if len(self.data_buffer) > self.settings['data_retention']:
            overflow = len(self.data_buffer) - self.settings['data_retention']
            self.history_data.extend(self.data_buffer[:overflow])
            self.data_buffer = self.data_buffer[overflow:]

        # 主界面始终显示静态值
        self.data_cards['pressure_card'].config(text=f"{self.static_pressure:.2f} Pa")
        self.data_cards['height_card'].config(text=f"{self.static_height:.2f} m")
        self.data_cards['temp_card'].config(text=f"{self.static_temperature:.2f} °C")

    def data_acquisition(self):
        """数据采集核心逻辑（静态模式 - 仅生成模拟数据）"""
        try:
            self.update_interface()
        except Exception as e:
            print(f"[数据更新异常] {str(e)}")

        self.master.after(self.settings['sampling_rate'], self.data_acquisition)

    def start_monitoring(self):
        """启动监测"""
        self.data_acquisition()

    def save_dataset(self):
        """保存数据"""
        if not self.data_buffer and not self.history_data:
            messagebox.showwarning("空数据集", "未采集到有效数据")
            return

        try:
            output_directory = export_directory()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            file_path = os.path.join(output_directory, f"pressure_data_{timestamp}.xlsx")

            all_data = self.history_data + self.data_buffer
            df = pd.DataFrame(all_data)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            df.to_excel(file_path, index=False, engine='openpyxl')

            messagebox.showinfo("保存成功", f"文件已保存至：\n{file_path}\n记录总数：{len(df)}条")
        except Exception as e:
            messagebox.showerror("保存失败", f"错误原因：\n{str(e)}")

    def refresh_data(self):
        """刷新数据"""
        response = messagebox.askyesno("刷新确认", "确定要清空当前数据缓冲区吗？")
        if response:
            self.history_data.extend(self.data_buffer)
            self.data_buffer = []
            messagebox.showinfo("刷新完成", "数据已刷新")

    def show_pressure(self):
        """显示压力信号"""
        window = tk.Toplevel(self.master)
        window.title("📈 压力信号详情")
        window.geometry("1000x750")
        window.configure(bg='#f5f5f5')

        fig = plt.Figure(figsize=(10, 7), facecolor='#ffffff')

        # 气压趋势
        ax1 = fig.add_subplot(311, facecolor='#fafafa')
        if self.data_buffer:
            pressures = [d['pressure'] for d in self.data_buffer]
            ax1.plot(pressures, linewidth=2.5, color='#0066CC', marker='o', markersize=3)
            ax1.set_title('气压趋势', color='#333333', fontsize=12, fontweight='bold')
            ax1.set_ylabel('气压 (Pa)', color='#0066CC', fontsize=10, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='y', colors='#0066CC')

        # 相对高度趋势
        ax2 = fig.add_subplot(312, facecolor='#fafafa')
        if self.data_buffer:
            # 使用静态高度值加上轻微波动
            heights = [self.static_height + np.random.normal(0, 0.1) for _ in self.data_buffer]
            ax2.plot(heights, linewidth=2.5, color='#FF6600', marker='s', markersize=3)
            ax2.set_title(f'相对高度变化',
                         color='#333333', fontsize=12, fontweight='bold')
            ax2.set_ylabel('相对高度 (m)', color='#FF6600', fontsize=10, fontweight='bold')
            ax2.axhline(y=0, color='#999999', linestyle='--', linewidth=1, alpha=0.5)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='y', colors='#FF6600')

        # 电流趋势
        ax3 = fig.add_subplot(313, facecolor='#fafafa')
        if self.data_buffer:
            currents = [d['current'] for d in self.data_buffer]
            ax3.plot(currents, linewidth=2, color='#ff7675', marker='^', markersize=2)
            ax3.set_title('电流趋势', color='#333333', fontsize=12, fontweight='bold')
            ax3.set_ylabel('电流 (mA)', color='#ff7675', fontsize=10)
            ax3.set_xlabel('采样点', color='#666666', fontsize=10)
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='y', colors='#ff7675')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def show_history(self):
        """显示历史记录"""
        messagebox.showinfo("历史记录", f"当前缓冲: {len(self.data_buffer)} 条\n历史存档: {len(self.history_data)} 条")

    def show_analysis(self):
        """数据分析"""
        if not self.data_buffer:
            messagebox.showinfo("数据分析", "暂无数据")
            return
        
        pressures = np.array([d['pressure'] for d in self.data_buffer])
        msg = f"平均气压: {np.mean(pressures):.2f} Pa\n"
        msg += f"最大气压: {np.max(pressures):.2f} Pa\n"
        msg += f"最小气压: {np.min(pressures):.2f} Pa\n"
        msg += f"标准差: {np.std(pressures):.2f}"
        messagebox.showinfo("数据分析", msg)

    def show_settings(self):
        """系统设置"""
        messagebox.showinfo("系统设置", 
                          f"模式: 静态演示\n"
                          f"气压: {self.static_pressure:.2f} Pa\n"
                          f"温度: {self.static_temperature:.2f} °C\n"
                          f"高度: {self.static_height:.2f} m\n"
                          f"采样率: {self.settings['sampling_rate']} ms")


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitor(root)

    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
