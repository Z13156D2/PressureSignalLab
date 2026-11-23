
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
import struct
import serial

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("🔬 气压智能监测系统 v3.0 (二进制解析)")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f5f5f5")

        # 初始化数据存储
        self.data_buffer = []
        self.history_data = []
        self.sample_count = 0

        # 串口对象
        self.serial = None
        
        # 数据缓存（用于多行数据组合）
        self._last_v1 = 0.0
        self._last_temperature = None
        self._last_pressure = None
        self._last_acq_idx = None

        # 系统设置默认值
        self.settings = {
            'sampling_rate': 50,  # 采样周期 (ms)
            'alert_threshold_high': 101000.0,
            'alert_threshold_low': 98000.0,
            'data_retention': 1000,
            'auto_save': False,
            'theme': 'light',
            'enable_sound': True,
            'chart_update_rate': 1,
            'serial_port': 'COM4',
            'baudrate': 9600,
        }

        # 加载历史设置
        self.load_settings()

        # 配置样式
        self.setup_styles()

        # 创建主界面
        self.create_interface()

        # 初始化串口
        self.init_serial()

        # 启动数据采集
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
            ("🔌 串口测试", self.test_serial, "🔍"),
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

        # 状态指示器
        status_frame = tk.Frame(sidebar_frame, bg='#e8e8e8')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.status_label = tk.Label(
            status_frame,
            text="● 运行中",
            font=('Microsoft YaHei UI', 9),
            bg='#e8e8e8',
            fg='#2c8c5c'
        )
        self.status_label.pack()

        self.sample_label = tk.Label(
            status_frame,
            text="采样: 0",
            font=('Consolas', 9),
            bg='#e8e8e8',
            fg='#666666'
        )
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

        self.figure = plt.Figure(figsize=(10, 6), facecolor='#ffffff')
        
        # 上方图表：气压
        self.axes_pressure = self.figure.add_subplot(211, facecolor='#fafafa')
        self.plot_pressure, = self.axes_pressure.plot([], [], linewidth=2.5, marker='o', markersize=4, color='#0066CC', label='气压')
        self.axes_pressure.set_title("实时气压变化趋势", fontsize=12, color='#333333', fontweight='bold')
        self.axes_pressure.set_xlabel("采样点", fontsize=9, color='#666666')
        self.axes_pressure.set_ylabel("气压值 (Pa)", fontsize=9, color='#0066CC', fontweight='bold')
        self.axes_pressure.grid(True, alpha=0.3, linestyle='--')
        self.axes_pressure.tick_params(axis='y', colors='#0066CC', labelsize=8)
        self.axes_pressure.tick_params(axis='x', colors='#666666', labelsize=8)
        
        # 下方图表：相对高度
        self.axes_height = self.figure.add_subplot(212, facecolor='#fafafa')
        self.plot_height, = self.axes_height.plot([], [], linewidth=2.5, marker='s', markersize=4, color='#FF6600', label='相对高度')
        self.axes_height.set_title("相对高度变化", fontsize=12, color='#333333', fontweight='bold')
        self.axes_height.set_xlabel("采样点", fontsize=9, color='#666666')
        self.axes_height.set_ylabel("相对高度 (m)", fontsize=9, color='#FF6600', fontweight='bold')
        self.axes_height.grid(True, alpha=0.3, linestyle='--')
        self.axes_height.tick_params(axis='y', colors='#FF6600', labelsize=8)
        self.axes_height.tick_params(axis='x', colors='#666666', labelsize=8)
        self.axes_height.axhline(y=0, color='#999999', linestyle='--', linewidth=1, alpha=0.5)

        for spine in self.axes_pressure.spines.values():
            spine.set_edgecolor('#cccccc')
        for spine in self.axes_height.spines.values():
            spine.set_edgecolor('#cccccc')
        
        self.figure.tight_layout()

        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 高度计算基准 实时调节
        self.reference_pressure = 100027.71  # Pa
        self.pressure_drop_per_meter = 12.0  # Pa/m

    def create_data_cards(self, parent):
        """创建数据显示卡片"""
        cards_data = [
            ("实时电流", "-- mA", "current_card", "#ff7675"),
            ("实时气压", "-- Pa", "pressure_card", "#74b9ff"),
            ("相对高度", "-- m", "height_card", "#ef8d55"),
            ("实时温度", "-- °C", "temp_card", "#a29bfe"),
            ("采样数量", "0", "count_card", "#fdcb6e"),
        ]

        self.data_cards = {}

        for i, (title, value, key, color) in enumerate(cards_data):
            card = tk.Frame(parent, bg=color, relief='flat', bd=0)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            title_label = tk.Label(card, text=title, font=('Microsoft YaHei UI', 10),
                                  bg=color, fg='#ffffff')
            title_label.pack(pady=(10, 0))

            value_label = tk.Label(card, text=value, font=('Consolas', 18, 'bold'),
                                  bg=color, fg='#ffffff')
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

    def init_serial(self):
        """初始化串口"""
        port = self.settings.get('serial_port', 'COM4')
        baudrate = self.settings.get('baudrate', 9600)
        
        baudrates_to_try = [baudrate, 115200, 9600, 19200, 38400, 57600]
        
        for baud in baudrates_to_try:
            try:
                print(f"\n{'='*60}")
                print(f"尝试打开串口: {port} @ {baud} bps")
                
                self.serial = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1.0,
                    write_timeout=1.0
                )
                
                print(f"✓ 串口 {port} 已成功打开")
                print(f"  - 波特率: {baud}")
                print(f"  - is_open: {self.serial.is_open}")
                
                self.serial.setDTR(False)
                self.serial.setRTS(False)
                print(f"  - DTR=False, RTS=False")
                
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                print(f"  - 缓冲区已清空")
                
                import time
                time.sleep(0.5)
                waiting = self.serial.in_waiting
                print(f"  - 等待0.5秒后 in_waiting: {waiting}")
                
                self.settings['baudrate'] = baud
                
                if hasattr(self, 'status_label'):
                    self.status_label.config(text=f"● 串口已连接 ({port}@{baud})", fg='#2c8c5c')
                
                print(f"{'='*60}\n")
                return
                
            except serial.SerialException as e:
                print(f"✗ 波特率 {baud} 失败: {e}")
                self.serial = None
                continue
            except Exception as e:
                print(f"✗ 波特率 {baud} 未知错误: {e}")
                self.serial = None
                continue
        
        print(f"\n{'='*60}")
        print(f"❌ 所有波特率尝试失败！")
        print(f"请检查串口设置")
        print(f"{'='*60}\n")
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"⚠️ 串口未连接", fg='#d63031')

    def parse_binary_data(self, raw_data):
        """
        直接解析原始字节数据
        查找特定的数据模式并提取数值
        """
        try:
            # 将字节转换为可打印的字符串（忽略错误）
            text = raw_data.decode('ascii', errors='ignore')
            
            # 显示原始数据（HEX和文本）
            hex_str = ' '.join([f'{b:02X}' for b in raw_data[:50]])
            if len(raw_data) > 50:
                hex_str += '...'
            print(f"[原始HEX] {hex_str}")
            print(f"[原始TXT] {text[:100]}")
            
            # 方法1: 直接在字节中查找数字模式
            # 提取所有数字序列（整数和浮点数）
            import re
            
            # 从文本中提取所有数字
            numbers = re.findall(r'\d+\.?\d*', text)
            print(f"[提取数字] {numbers}")
            
            if len(numbers) >= 2:
                # 假设格式: 温度 气压 或 CH1值 v1值
                # 根据数值大小判断是什么数据
                
                nums = [float(n) for n in numbers if n]
                
                # 查找可能的气压值 (通常在95000-105000范围)
                pressure = None
                temperature = None
                v1_voltage = None
                
                for num in nums:
                    if 90000 <= num <= 110000:  # 可能是气压 (Pa)
                        pressure = num
                        print(f"  [识别] 气压: {num} Pa")
                    elif 10 <= num <= 50:  # 可能是温度 (°C)
                        temperature = num
                        print(f"  [识别] 温度: {num} °C")
                    elif 0 <= num <= 5000:  # 可能是电压 (mV)
                        v1_voltage = num
                        print(f"  [识别] 电压: {num} mV")
                
                # 更新缓存
                if v1_voltage is not None:
                    self._last_v1 = v1_voltage
                if temperature is not None:
                    self._last_temperature = temperature
                if pressure is not None:
                    self._last_pressure = pressure
                
                # 查找采集次数
                acq_match = re.search(r'第\s*(\d+)', text)
                if acq_match:
                    self._last_acq_idx = int(acq_match.group(1))
                    print(f"  [识别] 采集次数: {self._last_acq_idx}")
                
                # 如果有温度和气压，返回完整数据
                if self._last_temperature is not None and self._last_pressure is not None:
                    current_ma = (self._last_v1 / 5000.0) * 20.0
                    
                    print(f"[数据组合] 电流={current_ma:.4f}mA, 气压={self._last_pressure:.2f}Pa, "
                          f"温度={self._last_temperature:.2f}°C, 次数={self._last_acq_idx}")
                    
                    return current_ma, self._last_pressure, self._last_temperature, self._last_acq_idx
            
            return None, None, None, None
            
        except Exception as e:
            print(f"[解析异常] {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None

    def update_interface(self, current, pressure, temperature=None, acq_index=None):
        """更新界面显示"""
        if current is not None and 'current_card' in self.data_cards:
            self.data_cards['current_card'].config(text=f"{current:.4f} mA")
        if pressure is not None and 'pressure_card' in self.data_cards:
            self.data_cards['pressure_card'].config(text=f"{pressure:.2f} Pa")
        if temperature is not None and 'temp_card' in self.data_cards:
            self.data_cards['temp_card'].config(text=f"{temperature:.2f} °C")
        if 'count_card' in self.data_cards:
            self.data_cards['count_card'].config(text=f"{len(self.data_buffer)}")
        
        # 更新相对高度卡片
        if pressure is not None and 'height_card' in self.data_cards:
            relative_height = (self.reference_pressure - pressure) / self.pressure_drop_per_meter
            self.data_cards['height_card'].config(text=f"{relative_height:.2f} m")

        if len(self.data_buffer) > 0:
            display_count = min(100, len(self.data_buffer))
            recent_data = self.data_buffer[-display_count:]

            indices = list(range(len(recent_data)))
            pressures = [d['pressure'] for d in recent_data]
            
            # 计算相对高度：每升高1米，气压降低12Pa
            # 高度 = (基准气压 - 当前气压) / 12
            heights = [(self.reference_pressure - p) / self.pressure_drop_per_meter for p in pressures]

            # 更新气压图表
            self.plot_pressure.set_data(indices, pressures)
            self.axes_pressure.relim()
            self.axes_pressure.autoscale_view()
            
            # 更新高度图表
            self.plot_height.set_data(indices, heights)
            self.axes_height.relim()
            self.axes_height.autoscale_view()
            
            self.graph_canvas.draw()

        if acq_index is not None:
            self.sample_label.config(text=f"采样: {acq_index}")
        else:
            self.sample_label.config(text=f"采样: {self.sample_count}")

        if pressure is not None:
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
            if self.serial and self.serial.is_open:
                try:
                    raw_data = self.serial.readline()
                    
                    if raw_data:
                        if not hasattr(self, '_data_count'):
                            self._data_count = 0
                        self._data_count += 1
                        
                        # 每5次显示一次（减少日志量）
                        if self._data_count % 5 == 1:
                            print(f"\n{'='*60}")
                            print(f"[数据接收 #{self._data_count}]")
                        
                        current, pressure, temperature, acq_idx = self.parse_binary_data(raw_data)
                        
                        if current is not None and pressure is not None:
                            data_point = {
                                'timestamp': datetime.now(),
                                'current': current,
                                'pressure': pressure,
                                'temperature': temperature,
                                'acq_index': acq_idx if acq_idx is not None else self.sample_count + 1
                            }

                            self.data_buffer.append(data_point)
                            self.sample_count += 1
                            print(f"[✓ 数据采集] 第 {self.sample_count} 个数据点已保存")

                            if len(self.data_buffer) > self.settings['data_retention']:
                                overflow = len(self.data_buffer) - self.settings['data_retention']
                                self.history_data.extend(self.data_buffer[:overflow])
                                self.data_buffer = self.data_buffer[overflow:]

                            self.update_interface(current, pressure, temperature, data_point['acq_index'])
                    else:
                        if not hasattr(self, '_no_data_count'):
                            self._no_data_count = 0
                        self._no_data_count += 1
                        
                        if self._no_data_count % 100 == 1:
                            print(f"[串口读取] 连续 {self._no_data_count} 次无数据")
                                
                except Exception as e:
                    print(f"[读取异常] {e}")
                    import traceback
                    traceback.print_exc()

            else:
                if not hasattr(self, '_reconnect_count'):
                    self._reconnect_count = 0
                
                self._reconnect_count += 1
                if self._reconnect_count % 50 == 0:
                    print(f"[串口状态] 串口未连接，尝试重新连接...")
                    self.init_serial()
                    
                if hasattr(self, 'status_label'):
                    self.status_label.config(text="⚠️ 串口未连接", fg='#d63031')
        except Exception as e:
            print(f"[数据采集异常] {str(e)}")
            import traceback
            traceback.print_exc()

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
            pressures = [d['pressure'] for d in self.data_buffer]
            heights = [(self.reference_pressure - p) / self.pressure_drop_per_meter for p in pressures]
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
        """显示历史记录 - 简化版"""
        messagebox.showinfo("历史记录", f"当前缓冲: {len(self.data_buffer)} 条\n历史存档: {len(self.history_data)} 条")

    def show_analysis(self):
        """数据分析 - 简化版"""
        if not self.data_buffer:
            messagebox.showinfo("数据分析", "暂无数据")
            return
        
        pressures = np.array([d['pressure'] for d in self.data_buffer])
        msg = f"平均气压: {np.mean(pressures):.2f} Pa\n"
        msg += f"最大气压: {np.max(pressures):.2f} Pa\n"
        msg += f"最小气压: {np.min(pressures):.2f} Pa\n"
        msg += f"标准差: {np.std(pressures):.2f}"
        messagebox.showinfo("数据分析", msg)

    def test_serial(self):
        """串口测试工具"""
        window = tk.Toplevel(self.master)
        window.title("🔌 串口测试工具")
        window.geometry("900x650")
        window.configure(bg='#f5f5f5')

        title_label = tk.Label(window, text="📡 串口实时监控 (二进制解析模式)",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg='#f5f5f5', fg='#2c8c5c')
        title_label.pack(pady=10)

        text_frame = tk.Frame(window, bg='#f5f5f5')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, font=('Consolas', 9),
                             bg='#1e1e1e', fg='#00ff00',
                             insertbackground='#00ff00',
                             yscrollcommand=scrollbar.set, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert('1.0', f"{'='*80}\n")
        text_widget.insert('end', f"串口测试工具 (二进制解析) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        text_widget.insert('end', f"{'='*80}\n\n")

        counter = {'count': 0, 'running': True}

        def read_serial_data():
            if not counter['running']:
                return
                
            try:
                if self.serial and self.serial.is_open:
                    raw_data = self.serial.readline()
                    
                    if raw_data:
                        counter['count'] += 1
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        
                        hex_str = ' '.join([f'{b:02X}' for b in raw_data[:40]])
                        if len(raw_data) > 40:
                            hex_str += '...'
                        
                        txt = raw_data.decode('ascii', errors='ignore').strip()
                        
                        text_widget.insert('end', f"[{timestamp}] #{counter['count']} ({len(raw_data)} bytes)\n")
                        text_widget.insert('end', f"  HEX: {hex_str}\n")
                        text_widget.insert('end', f"  TXT: {txt}\n")
                        
                        # 提取数字
                        import re
                        nums = re.findall(r'\d+\.?\d*', txt)
                        if nums:
                            text_widget.insert('end', f"  数字: {nums}\n")
                        
                        text_widget.insert('end', "\n")
                        text_widget.see('end')
            except Exception as e:
                text_widget.insert('end', f"[错误] {e}\n")

            if counter['running']:
                window.after(100, read_serial_data)

        read_serial_data()

        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def close_window():
            counter['running'] = False
            window.destroy()

        close_btn = tk.Button(button_frame, text="❌ 关闭",
                             font=('Microsoft YaHei UI', 10, 'bold'),
                             bg='#ff7675', fg='#ffffff', bd=0,
                             padx=20, pady=8, cursor='hand2',
                             command=close_window)
        close_btn.pack(side=tk.RIGHT, padx=5)

        window.protocol("WM_DELETE_WINDOW", close_window)

    def show_settings(self):
        """系统设置 - 简化版"""
        messagebox.showinfo("系统设置", 
                          f"串口: {self.settings['serial_port']}\n"
                          f"波特率: {self.settings['baudrate']}\n"
                          f"采样率: {self.settings['sampling_rate']} ms")

    def __del__(self):
        """安全关闭资源"""
        try:
            if hasattr(self, 'serial') and self.serial and self.serial.is_open:
                self.serial.close()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitor(root)

    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            try:
                if app.serial and app.serial.is_open:
                    app.serial.close()
            except Exception:
                pass
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
