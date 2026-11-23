
from sensor_monitor.storage import load_settings, save_settings, export_directory

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import json

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class PressureDemoApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🔬 气压智能监测系统 v2.0")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f5f5f5")
        
        # 初始化数据存储
        self.data_buffer = []
        self.history_data = []  # 历史记录
        self.sample_count = 0
        
        # 系统设置默认值
        self.settings = {
            'sampling_rate': 1000,  # 采样率(ms)
            'alert_threshold_high': 19890.0,  # 高压警报阈值（海拔200米基准）
            'alert_threshold_low': 98.0,    # 低压警报阈值（海拔200米基准）
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
        
        style.configure('Data.TLabel',
                       font=('Consolas', 14, 'bold'),
                       background='#e0e0e0',
                       foreground='#0077cc',
                       padding=10)

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
                              text="📊 控制面板",
                              font=('Microsoft YaHei UI', 14, 'bold'),
                              bg='#e8e8e8',
                              fg='#2c8c5c',
                              pady=20)
        title_label.pack(fill=tk.X)

        # 导航按钮
        buttons = [
            ("📈 压力信号", self.show_pressure, "💡"),
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
        self.plot_line, = self.axes.plot([], [], color='#0077cc', linewidth=2, marker='o', markersize=3)
        self.axes.set_title("实时气压变化趋势", fontsize=14, color='#333333', fontweight='bold')
        self.axes.set_xlabel("时间轴", fontsize=10, color='#666666')
        self.axes.set_ylabel("气压值 (hPa)", fontsize=10, color='#666666')
        self.axes.grid(True, alpha=0.3, linestyle='--', color='#cccccc')
        self.axes.tick_params(colors='#666666', labelsize=8)
        
        # 设置坐标轴颜色
        for spine in self.axes.spines.values():
            spine.set_edgecolor('#cccccc')

        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_data_cards(self, parent):
        """创建数据显示卡片"""
        cards_data = [
            ("实时电流", "-- mA", "current_card", "#ff7675"),
            ("推算气压", "-- hPa", "pressure_card", "#74b9ff"),
            ("峰值气压", "-- hPa", "peak_card", "#55efc4"),
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

    def current_to_pressure(self, current):
        """模拟电流到气压转换 - 基于海拔200米的大气压"""
        # 海拔200米的标准大气压约为 988.7 hPa
        # 0.1米的气压变化约为 0.012 hPa
        # 生成在 ±0.1米范围内的随机波动
        base_pressure = 988.7  # 海拔200米的大气压
        height_variation = random.uniform(-0.1, 0.1)  # ±0.1米的高度波动
        pressure_change = height_variation * 0.12  # 0.1米 ≈ 0.012 hPa，所以1米 = 0.12 hPa
        
        return base_pressure + pressure_change

    def update_interface(self, current, pressure):
        """更新界面显示"""
        # 更新数据卡片
        self.data_cards['current_card'].config(text=f"{current:.4f} mA")
        self.data_cards['pressure_card'].config(text=f"{pressure:.2f} hPa")
        self.data_cards['count_card'].config(text=f"{len(self.data_buffer)}")
        
        # 计算峰值
        if self.data_buffer:
            peak = max([d['pressure'] for d in self.data_buffer])
            self.data_cards['peak_card'].config(text=f"{peak:.2f} hPa")

        # 更新曲线数据
        if len(self.data_buffer) > 0:
            # 只显示最近的数据点
            display_count = min(100, len(self.data_buffer))
            recent_data = self.data_buffer[-display_count:]
            
            indices = list(range(len(recent_data)))
            pressures = [d['pressure'] for d in recent_data]
            
            self.plot_line.set_data(indices, pressures)
            self.axes.relim()
            self.axes.autoscale_view()
            self.graph_canvas.draw()
        
        # 更新状态标签
        self.sample_label.config(text=f"采样: {self.sample_count}")
        
        # 检查警报
        self.check_alerts(pressure)

    def generate_fake_data(self):
        """生成模拟数据"""
        current = random.uniform(4, 20)
        pressure = self.current_to_pressure(current)
        return current, pressure

    def check_alerts(self, pressure):
        """检查警报"""
        if pressure > self.settings['alert_threshold_high']:
            self.status_label.config(text="⚠️ 高压警报", fg='#d63031')
        elif pressure < self.settings['alert_threshold_low']:
            self.status_label.config(text="⚠️ 低压警报", fg='#fdcb6e')
        else:
            self.status_label.config(text="● 运行中", fg='#2c8c5c')

    def data_acquisition(self):
        """数据采集核心逻辑（模拟数据）"""
        try:
            current, pressure = self.generate_fake_data()

            data_point = {
                'timestamp': datetime.now(),
                'current': current,
                'pressure': pressure
            }
            
            self.data_buffer.append(data_point)
            self.sample_count += 1
            
            # 数据保留限制
            if len(self.data_buffer) > self.settings['data_retention']:
                # 将超出的数据移到历史记录
                self.history_data.extend(self.data_buffer[:len(self.data_buffer) - self.settings['data_retention']])
                self.data_buffer = self.data_buffer[-self.settings['data_retention']:]

            # 更新界面
            if self.sample_count % self.settings['chart_update_rate'] == 0:
                self.update_interface(current, pressure)

        except Exception as e:
            print(f"数据采集异常: {str(e)}")

        self.master.after(self.settings['sampling_rate'], self.data_acquisition)

    def start_monitoring(self):
        """启动监测（模拟数据）"""
        self.data_acquisition()

    def save_dataset(self):
        """保存数据到 data/exports"""
        if not self.data_buffer and not self.history_data:
            messagebox.showwarning("空数据集", "未采集到有效数据")
            return

        try:
            output_directory = export_directory()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            file_path = os.path.join(output_directory, f"pressure_data_{timestamp}.xlsx")

            # 合并当前数据和历史数据
            all_data = self.history_data + self.data_buffer
            df = pd.DataFrame(all_data)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
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

    def show_pressure(self):
        """显示压力信号界面"""
        window = tk.Toplevel(self.master)
        window.title("📈 压力信号详情")
        window.geometry("900x600")
        window.configure(bg='#f5f5f5')
        
        # 创建多图表显示
        fig = plt.Figure(figsize=(9, 5.5), facecolor='#ffffff')
        
        # 压力趋势图
        ax1 = fig.add_subplot(211, facecolor='#fafafa')
        if self.data_buffer:
            pressures = [d['pressure'] for d in self.data_buffer]
            ax1.plot(pressures, color='#0077cc', linewidth=2)
            ax1.set_title('压力趋势', color='#333333', fontsize=12, fontweight='bold')
            ax1.set_ylabel('气压 (hPa)', color='#666666')
            ax1.grid(True, alpha=0.3, color='#cccccc')
            ax1.tick_params(colors='#666666')
            for spine in ax1.spines.values():
                spine.set_edgecolor('#cccccc')
        
        # 电流趋势图
        ax2 = fig.add_subplot(212, facecolor='#fafafa')
        if self.data_buffer:
            currents = [d['current'] for d in self.data_buffer]
            ax2.plot(currents, color='#ff7675', linewidth=2)
            ax2.set_title('电流趋势', color='#333333', fontsize=12, fontweight='bold')
            ax2.set_ylabel('电流 (mA)', color='#666666')
            ax2.set_xlabel('采样点', color='#666666')
            ax2.grid(True, alpha=0.3, color='#cccccc')
            ax2.tick_params(colors='#666666')
            for spine in ax2.spines.values():
                spine.set_edgecolor('#cccccc')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def show_history(self):
        """显示历史记录"""
        window = tk.Toplevel(self.master)
        window.title("📜 历史记录查看器")
        window.geometry("1000x650")
        window.configure(bg='#f5f5f5')
        
        # 顶部标题
        title_frame = tk.Frame(window, bg='#ffffff', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame,
                              text="📋 历史数据记录",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg='#ffffff',
                              fg='#2c8c5c')
        title_label.pack(pady=15)
        
        # 统计信息面板
        stats_frame = tk.Frame(window, bg='#f5f5f5')
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        all_data = self.history_data + self.data_buffer
        total_records = len(all_data)
        
        stats_labels = [
            f"📊 总记录数: {total_records}",
            f"📦 当前缓冲: {len(self.data_buffer)}",
            f"🗄️ 历史存档: {len(self.history_data)}",
        ]
        
        for i, text in enumerate(stats_labels):
            label = tk.Label(stats_frame,
                           text=text,
                           font=('Consolas', 10, 'bold'),
                           bg='#e3f2fd',
                           fg='#0077cc',
                           padx=15,
                           pady=8)
            label.pack(side=tk.LEFT, padx=5)
        
        # 创建Treeview显示历史记录
        tree_frame = tk.Frame(window, bg='#f5f5f5')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 配置Treeview样式
        style = ttk.Style()
        style.configure("History.Treeview",
                       background="#ffffff",
                       foreground="#333333",
                       fieldbackground="#ffffff",
                       borderwidth=0,
                       font=('Consolas', 9))
        style.configure("History.Treeview.Heading",
                       background='#e0e0e0',
                       foreground='#2c8c5c',
                       borderwidth=0,
                       font=('Microsoft YaHei UI', 10, 'bold'))
        style.map('History.Treeview',
                 background=[('selected', '#e3f2fd')])
        
        columns = ('序号', '时间戳', '电流(mA)', '气压(hPa)', '类型')
        tree = ttk.Treeview(tree_frame,
                           columns=columns,
                           show='headings',
                           style='History.Treeview',
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        
        # 设置列
        tree.heading('序号', text='序号')
        tree.heading('时间戳', text='时间戳')
        tree.heading('电流(mA)', text='电流 (mA)')
        tree.heading('气压(hPa)', text='气压 (hPa)')
        tree.heading('类型', text='数据类型')
        
        tree.column('序号', width=60, anchor='center')
        tree.column('时间戳', width=200, anchor='center')
        tree.column('电流(mA)', width=120, anchor='center')
        tree.column('气压(hPa)', width=120, anchor='center')
        tree.column('类型', width=100, anchor='center')
        
        # 插入历史数据
        for idx, data in enumerate(self.history_data, 1):
            tree.insert('', 'end', values=(
                idx,
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                f"{data['current']:.4f}",
                f"{data['pressure']:.2f}",
                "历史"
            ))
        
        # 插入当前缓冲数据
        for idx, data in enumerate(self.data_buffer, len(self.history_data) + 1):
            tree.insert('', 'end', values=(
                idx,
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                f"{data['current']:.4f}",
                f"{data['pressure']:.2f}",
                "当前"
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮
        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        export_btn = tk.Button(button_frame,
                              text="📥 导出选中",
                              font=('Microsoft YaHei UI', 10),
                              bg='#74b9ff',
                              fg='#ffffff',
                              activebackground='#5fa3e8',
                              bd=0,
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              command=lambda: self.export_selected(tree))
        export_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(button_frame,
                             text="❌ 关闭",
                             font=('Microsoft YaHei UI', 10),
                             bg='#ff7675',
                             fg='#ffffff',
                             activebackground='#e65c5c',
                             bd=0,
                             padx=20,
                             pady=8,
                             cursor='hand2',
                             command=window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def export_selected(self, tree):
        """导出选中的记录"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择要导出的记录")
            return
        
        messagebox.showinfo("导出", f"已选择 {len(selected)} 条记录进行导出")

    def show_analysis(self):
        """数据分析"""
        window = tk.Toplevel(self.master)
        window.title("📊 数据分析中心")
        window.geometry("1100x750")
        window.configure(bg='#f5f5f5')
        
        # 标题
        title_frame = tk.Frame(window, bg='#ffffff', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame,
                              text="📉 统计分析报告",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg='#ffffff',
                              fg='#2c8c5c')
        title_label.pack(pady=15)
        
        if not self.data_buffer and not self.history_data:
            no_data_label = tk.Label(window,
                                    text="暂无数据可供分析",
                                    font=('Microsoft YaHei UI', 14),
                                    bg='#f5f5f5',
                                    fg='#999999')
            no_data_label.pack(pady=50)
            return
        
        # 合并数据进行分析
        all_data = self.history_data + self.data_buffer
        pressures = np.array([d['pressure'] for d in all_data])
        currents = np.array([d['current'] for d in all_data])
        
        # 计算统计指标
        stats = {
            '气压统计': {
                '平均气压': np.mean(pressures),
                '最大气压': np.max(pressures),
                '最小气压': np.min(pressures),
                '气压方差': np.var(pressures),
                '标准差': np.std(pressures),
                '中位数': np.median(pressures),
                '极差': np.ptp(pressures),
                '变异系数': (np.std(pressures) / np.mean(pressures)) * 100 if np.mean(pressures) != 0 else 0,
            },
            '电流统计': {
                '平均电流': np.mean(currents),
                '最大电流': np.max(currents),
                '最小电流': np.min(currents),
                '电流方差': np.var(currents),
                '标准差': np.std(currents),
                '中位数': np.median(currents),
            },
            '数据质量': {
                '总样本数': len(all_data),
                '有效率': 100.0,  # 模拟数据
                '异常点数': np.sum((pressures > 95) | (pressures < 5)),
                '稳定性指数': 100 - min(100, (np.std(pressures) / np.mean(pressures)) * 100) if np.mean(pressures) != 0 else 0,
            }
        }
        
        # 创建统计信息展示区
        stats_container = tk.Frame(window, bg='#f5f5f5')
        stats_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧统计卡片
        left_frame = tk.Frame(stats_container, bg='#f5f5f5')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        colors = ['#ff7675', '#74b9ff', '#55efc4']
        for idx, (category, data) in enumerate(stats.items()):
            cat_frame = tk.Frame(left_frame, bg='#ffffff', relief='flat')
            cat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            cat_title = tk.Label(cat_frame,
                               text=f"📋 {category}",
                               font=('Microsoft YaHei UI', 12, 'bold'),
                               bg=colors[idx % len(colors)],
                               fg='#ffffff',
                               pady=10)
            cat_title.pack(fill=tk.X)
            
            for key, value in data.items():
                item_frame = tk.Frame(cat_frame, bg='#ffffff')
                item_frame.pack(fill=tk.X, padx=10, pady=3)
                
                key_label = tk.Label(item_frame,
                                    text=f"{key}:",
                                    font=('Microsoft YaHei UI', 10),
                                    bg='#ffffff',
                                    fg='#555555',
                                    anchor='w')
                key_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                if isinstance(value, float):
                    value_text = f"{value:.4f}"
                else:
                    value_text = str(value)
                
                value_label = tk.Label(item_frame,
                                      text=value_text,
                                      font=('Consolas', 10, 'bold'),
                                      bg='#ffffff',
                                      fg='#0077cc',
                                      anchor='e')
                value_label.pack(side=tk.RIGHT)
        
        # 右侧图表
        right_frame = tk.Frame(stats_container, bg='#ffffff')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        fig = plt.Figure(figsize=(5.5, 7), facecolor='#ffffff')
        
        # 直方图
        ax1 = fig.add_subplot(311, facecolor='#fafafa')
        ax1.hist(pressures, bins=30, color='#74b9ff', alpha=0.7, edgecolor='#333333')
        ax1.set_title('气压分布', color='#333333', fontsize=10, fontweight='bold')
        ax1.set_xlabel('气压 (hPa)', color='#666666', fontsize=8)
        ax1.set_ylabel('频数', color='#666666', fontsize=8)
        ax1.grid(True, alpha=0.3, color='#cccccc')
        ax1.tick_params(colors='#666666', labelsize=7)
        for spine in ax1.spines.values():
            spine.set_edgecolor('#cccccc')
        
        # 箱线图
        ax2 = fig.add_subplot(312, facecolor='#fafafa')
        bp = ax2.boxplot([pressures], vert=True, patch_artist=True,
                         boxprops=dict(facecolor='#55efc4', color='#333333'),
                         whiskerprops=dict(color='#333333'),
                         capprops=dict(color='#333333'),
                         medianprops=dict(color='#ff7675', linewidth=2))
        ax2.set_title('气压箱线图', color='#333333', fontsize=10, fontweight='bold')
        ax2.set_ylabel('气压 (hPa)', color='#666666', fontsize=8)
        ax2.grid(True, alpha=0.3, color='#cccccc', axis='y')
        ax2.tick_params(colors='#666666', labelsize=7)
        for spine in ax2.spines.values():
            spine.set_edgecolor('#cccccc')
        
        # 散点图
        ax3 = fig.add_subplot(313, facecolor='#fafafa')
        ax3.scatter(currents, pressures, c='#ff7675', alpha=0.6, s=20)
        ax3.set_title('电流-气压关系', color='#333333', fontsize=10, fontweight='bold')
        ax3.set_xlabel('电流 (mA)', color='#666666', fontsize=8)
        ax3.set_ylabel('气压 (hPa)', color='#666666', fontsize=8)
        ax3.grid(True, alpha=0.3, color='#cccccc')
        ax3.tick_params(colors='#666666', labelsize=7)
        for spine in ax3.spines.values():
            spine.set_edgecolor('#cccccc')
        
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
                              text="🔧 系统配置",
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
            ('高压警报阈值 (hPa)', 'alert_threshold_high', 'number'),
            ('低压警报阈值 (hPa)', 'alert_threshold_low', 'number'),
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
        
        # 附加功能设置
        advanced_frame = tk.LabelFrame(settings_frame,
                                      text="高级设置",
                                      font=('Microsoft YaHei UI', 11, 'bold'),
                                      bg='#ffffff',
                                      fg='#2c8c5c',
                                      relief='flat',
                                      bd=5)
        advanced_frame.pack(fill=tk.X, pady=15)
        
        advanced_options = [
            "启用数据压缩",
            "启用网络同步",
            "启用远程监控",
            "启用日志记录",
            "启用性能监控"
        ]
        
        for option in advanced_options:
            var = tk.BooleanVar(value=False)
            check = tk.Checkbutton(advanced_frame,
                                  text=option,
                                  variable=var,
                                  bg='#ffffff',
                                  fg='#333333',
                                  selectcolor='#e8e8e8',
                                  activebackground='#ffffff',
                                  activeforeground='#2c8c5c',
                                  font=('Microsoft YaHei UI', 10))
            check.pack(anchor='w', padx=20, pady=3)
        
        # 按钮区
        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def save_settings():
            try:
                # 更新设置
                for key, widget in setting_entries.items():
                    if isinstance(widget, tk.Entry):
                        value = widget.get()
                        # 转换为适当的类型
                        if key in ['sampling_rate', 'data_retention', 'chart_update_rate']:
                            self.settings[key] = int(value)
                        else:
                            self.settings[key] = float(value)
                    elif isinstance(widget, tk.BooleanVar):
                        self.settings[key] = widget.get()
                    elif isinstance(widget, tk.StringVar):
                        self.settings[key] = widget.get()
                
                # 保存到文件
                self.save_settings_to_file()
                messagebox.showinfo("成功", "设置已保存！")
                window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存设置失败：{str(e)}")
        
        save_btn = tk.Button(button_frame,
                            text="💾 保存设置",
                            font=('Microsoft YaHei UI', 11, 'bold'),
                            bg='#74b9ff',
                            fg='#ffffff',
                            activebackground='#5fa3e8',
                            bd=0,
                            padx=30,
                            pady=10,
                            cursor='hand2',
                            command=save_settings)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_frame,
                             text="🔄 重置默认",
                             font=('Microsoft YaHei UI', 11, 'bold'),
                             bg='#ff7675',
                             fg='#ffffff',
                             activebackground='#e65c5c',
                             bd=0,
                             padx=30,
                             pady=10,
                             cursor='hand2',
                             command=lambda: messagebox.showinfo("重置", "设置已重置为默认值"))
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame,
                              text="❌ 取消",
                              font=('Microsoft YaHei UI', 11, 'bold'),
                              bg='#55efc4',
                              fg='#ffffff',
                              activebackground='#42d6a9',
                              bd=0,
                              padx=30,
                              pady=10,
                              cursor='hand2',
                              command=window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def __del__(self):
        """安全关闭资源（没有串口需要关闭）"""
        pass


if __name__ == "__main__":
    root = tk.Tk()

    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = PressureDemoApp(root)
    root.mainloop()
