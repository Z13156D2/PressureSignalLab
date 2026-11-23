
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
import re
import serial

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("🔬 气压智能监测系统 v2.0")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f5f5f5")

        # 初始化数据存储
        self.data_buffer = []
        self.history_data = []  # 历史记录
        self.sample_count = 0

        # 串口对象
        self.serial = None

        # 系统设置默认值（气压单位：Pa）
        self.settings = {
            'sampling_rate': 100,  # 采样周期 (ms) - 减小以更快检测数据
            'alert_threshold_high': 101000.0,  # 高压警报阈值 (Pa)
            'alert_threshold_low': 98000.0,  # 低压警报阈值 (Pa)
            'data_retention': 1000,  # 数据保留数量
            'auto_save': False,  # 自动保存
            'theme': 'light',  # 主题
            'enable_sound': True,  # 启用声音
            'chart_update_rate': 1,  # 图表更新率（每多少个样本刷新一次曲线）- 改为1实时更新
            'serial_port': 'COM4',  # 串口号，按实际修改，例如 '/dev/ttyUSB0'
            'baudrate': 9600,  # 波特率，常见值: 9600, 115200, 19200, 38400, 57600
        }

        # 加载历史设置
        self.load_settings()

        # 配置样式
        self.setup_styles()

        # 创建主界面
        self.create_interface()

        # 初始化串口
        self.init_serial()

        # 启动数据采集（串口实时数据）
        self.start_monitoring()

    def setup_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置按钮样式
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

        # 配置Frame样式
        style.configure(
            'Sidebar.TFrame',
            background='#e8e8e8',
            relief='flat'
        )

        style.configure(
            'Content.TFrame',
            background='#f5f5f5',
            relief='flat'
        )

        # 配置Label样式
        style.configure(
            'Title.TLabel',
            font=('Microsoft YaHei UI', 16, 'bold'),
            background='#f5f5f5',
            foreground='#2c8c5c'
        )

        style.configure(
            'Data.TLabel',
            font=('Consolas', 14, 'bold'),
            background='#e0e0e0',
            foreground='#0077cc',
            padding=10
        )

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
        title_label = tk.Label(
            sidebar_frame,
            text="📊 控制面板",
            font=('Microsoft YaHei UI', 14, 'bold'),
            bg='#e8e8e8',
            fg='#2c8c5c',
            pady=20
        )
        title_label.pack(fill=tk.X)

        # 导航按钮
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

        # 创建matplotlib图表（实时气压曲线，单位：Pa）
        self.figure = plt.Figure(figsize=(10, 5), facecolor='#ffffff')
        self.axes = self.figure.add_subplot(111, facecolor='#fafafa')
        self.plot_line, = self.axes.plot([], [], linewidth=2, marker='o', markersize=3)
        self.axes.set_title("实时气压变化趋势", fontsize=14, color='#333333', fontweight='bold')
        self.axes.set_xlabel("采样点", fontsize=10, color='#666666')
        self.axes.set_ylabel("气压值 (Pa)", fontsize=10, color='#666666')
        self.axes.grid(True, alpha=0.3, linestyle='--')
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
            ("实时气压", "-- Pa", "pressure_card", "#74b9ff"),
            ("峰值气压", "-- Pa", "peak_card", "#55efc4"),
            ("实时温度", "-- °C", "temp_card", "#a29bfe"),
            ("采样数量", "0", "count_card", "#fdcb6e"),
        ]

        self.data_cards = {}

        for i, (title, value, key, color) in enumerate(cards_data):
            card = tk.Frame(parent, bg=color, relief='flat', bd=0)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            title_label = tk.Label(
                card,
                text=title,
                font=('Microsoft YaHei UI', 10),
                bg=color,
                fg='#ffffff'
            )
            title_label.pack(pady=(10, 0))

            value_label = tk.Label(
                card,
                text=value,
                font=('Consolas', 18, 'bold'),
                bg=color,
                fg='#ffffff'
            )
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
        
        # 尝试多个常见波特率
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
                print(f"  - 数据位: {self.serial.bytesize}")
                print(f"  - 校验位: {self.serial.parity}")
                print(f"  - 停止位: {self.serial.stopbits}")
                print(f"  - 超时: {self.serial.timeout}s")
                print(f"  - is_open: {self.serial.is_open}")
                print(f"  - in_waiting: {self.serial.in_waiting}")
                
                # 设置DTR和RTS为False
                self.serial.setDTR(False)
                self.serial.setRTS(False)
                print(f"  - DTR=False, RTS=False")
                
                # 清空缓冲区
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                print(f"  - 缓冲区已清空")
                
                # 等待一小段时间检测数据
                import time
                time.sleep(0.5)
                waiting = self.serial.in_waiting
                print(f"  - 等待0.5秒后 in_waiting: {waiting}")
                
                # 保存成功的波特率
                self.settings['baudrate'] = baud
                
                if hasattr(self, 'status_label'):
                    self.status_label.config(text=f"● 串口已连接 ({port}@{baud})", fg='#2c8c5c')
                
                print(f"{'='*60}\n")
                return  # 成功则退出
                
            except serial.SerialException as e:
                print(f"✗ 波特率 {baud} 失败: {e}")
                self.serial = None
                continue
            except Exception as e:
                print(f"✗ 波特率 {baud} 未知错误: {e}")
                self.serial = None
                continue
        
        # 所有波特率都失败
        print(f"\n{'='*60}")
        print(f"❌ 所有波特率尝试失败！")
        print(f"请检查:")
        print(f"  1) 串口号是否正确 (当前: {port})")
        print(f"  2) USB设备是否已连接")
        print(f"  3) 驱动程序是否已安装")
        print(f"  4) 串口是否被其他程序占用")
        print(f"  5) 设备是否需要特殊的握手信号 (DTR/RTS)")
        print(f"{'='*60}\n")
        
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"⚠️ 串口未连接", fg='#d63031')

    def parse_serial_data(self, line):
        """
        解析一行串口数据:
        格式1: 温度: 25.74 度, 气压: 99894.46 Pa
        格式2: 第58次采集
        格式3: CH1=65535 v1: 2500mv
        返回: (current_mA, pressure_Pa, temperature_C, acq_index)
        """
        try:
            print(f"[原始数据] {line}")  # 输出原始数据用于调试
            
            # 提取 CH1 和 v1 电压（mV）
            # 匹配: CH1=65535 v1:2500mv 或 CH1=65535 v1: 2500mv
            ch1_match = re.search(r'CH1\s*=\s*(\d+)', line, re.IGNORECASE)
            v1_match = re.search(r'v1\s*:\s*(\d+)\s*mv', line, re.IGNORECASE)
            
            # 提取温度 - 匹配: 温度: 25.74 度
            temp_match = re.search(r'温度\s*:\s*([-]?\d+(?:\.\d+)?)\s*度', line)
            
            # 提取气压（Pa）- 匹配: 气压: 99894.46 Pa
            press_match = re.search(r'气压\s*:\s*([-]?\d+(?:\.\d+)?)\s*Pa', line)
            
            # 提取采集次数 - 匹配: 第58次采集
            count_match = re.search(r'第\s*(\d+)\s*次采集', line)

            # 调试输出匹配结果
            if ch1_match:
                print(f"  [匹配] CH1: {ch1_match.group(1)}")
            
            if v1_match:
                print(f"  [匹配] v1: {v1_match.group(1)} mv")
            else:
                print("  [未匹配] v1 电压")
                
            if temp_match:
                print(f"  [匹配] 温度: {temp_match.group(1)} 度")
            else:
                print("  [未匹配] 温度")
                
            if press_match:
                print(f"  [匹配] 气压: {press_match.group(1)} Pa")
            else:
                print("  [未匹配] 气压")
                
            if count_match:
                print(f"  [匹配] 采集次数: {count_match.group(1)}")

            # 根据匹配结果决定如何处理
            # 情况1: 有温度和气压数据的行
            if temp_match and press_match:
                temp_c = float(temp_match.group(1))
                press_pa = float(press_match.group(1))
                
                # 如果当前行没有v1数据，使用上一次的v1值
                if v1_match:
                    v1_mv = float(v1_match.group(1))
                    self._last_v1 = v1_mv  # 保存最后一次的v1值
                elif hasattr(self, '_last_v1'):
                    v1_mv = self._last_v1
                else:
                    v1_mv = 0.0
                    self._last_v1 = 0.0
                
                # 如果当前行没有采集次数，使用上一次的值
                if count_match:
                    acq_idx = int(count_match.group(1))
                    self._last_acq_idx = acq_idx
                elif hasattr(self, '_last_acq_idx'):
                    acq_idx = self._last_acq_idx
                else:
                    acq_idx = None
                
                # 计算电流：0~5V 对应 0~20mA
                current_ma = (v1_mv / 5000.0) * 20.0
                
                print(f"  [解析成功] 电流={current_ma:.4f}mA, 气压={press_pa:.2f}Pa, 温度={temp_c:.2f}°C, 次数={acq_idx}")
                return current_ma, press_pa, temp_c, acq_idx
            
            # 情况2: 只有采集次数的行
            elif count_match:
                acq_idx = int(count_match.group(1))
                self._last_acq_idx = acq_idx
                print(f"  [信息] 仅更新采集次数: {acq_idx}")
                return None, None, None, acq_idx
            
            # 情况3: 只有CH1和v1的行
            elif v1_match:
                v1_mv = float(v1_match.group(1))
                self._last_v1 = v1_mv
                print(f"  [信息] 仅更新电压: v1={v1_mv}mv")
                return None, None, None, None
            
            else:
                print("  [解析失败] 未识别的数据格式")
                return None, None, None, None

        except Exception as e:
            print(f"  [异常] 解析串口数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None

    def update_interface(self, current, pressure, temperature=None, acq_index=None):
        """更新界面显示"""
        # 更新数据卡片
        if current is not None and 'current_card' in self.data_cards:
            self.data_cards['current_card'].config(text=f"{current:.4f} mA")
        if pressure is not None and 'pressure_card' in self.data_cards:
            self.data_cards['pressure_card'].config(text=f"{pressure:.2f} Pa")
        if temperature is not None and 'temp_card' in self.data_cards:
            self.data_cards['temp_card'].config(text=f"{temperature:.2f} °C")
        if 'count_card' in self.data_cards:
            self.data_cards['count_card'].config(text=f"{len(self.data_buffer)}")

        # 计算峰值气压
        if self.data_buffer and 'peak_card' in self.data_cards:
            valid_pressures = [d['pressure'] for d in self.data_buffer if d.get('pressure') is not None]
            if valid_pressures:
                peak = max(valid_pressures)
                self.data_cards['peak_card'].config(text=f"{peak:.2f} Pa")

        # 更新曲线数据（实时气压曲线）
        if len(self.data_buffer) > 0:
            display_count = min(100, len(self.data_buffer))
            recent_data = self.data_buffer[-display_count:]

            indices = list(range(len(recent_data)))
            pressures = [d['pressure'] for d in recent_data]

            self.plot_line.set_data(indices, pressures)
            self.axes.relim()
            self.axes.autoscale_view()
            self.graph_canvas.draw()

        # 更新状态标签（显示采集次数）
        if acq_index is not None:
            self.sample_label.config(text=f"采样: {acq_index}")
        else:
            self.sample_label.config(text=f"采样: {self.sample_count}")

        # 检查警报
        if pressure is not None:
            self.check_alerts(pressure)

    def check_alerts(self, pressure):
        """检查警报（单位：Pa）"""
        if pressure > self.settings['alert_threshold_high']:
            self.status_label.config(text="⚠️ 高压警报", fg='#d63031')
        elif pressure < self.settings['alert_threshold_low']:
            self.status_label.config(text="⚠️ 低压警报", fg='#fdcb6e')
        else:
            self.status_label.config(text="● 运行中", fg='#2c8c5c')

    def data_acquisition(self):
        """数据采集核心逻辑（只使用实际串口数据，不再使用模拟数据）"""
        try:
            if self.serial and self.serial.is_open:
                line = ""
                try:
                    # 方法1: 使用 readline() 阻塞读取（推荐）
                    # 即使 in_waiting 为 0，readline 也会等待直到收到换行符或超时
                    raw_data = self.serial.readline()
                    
                    if raw_data:
                        # 显示原始字节
                        if not hasattr(self, '_last_raw_log'):
                            self._last_raw_log = 0
                        
                        # 每10次打印一次原始字节（避免刷屏）
                        self._last_raw_log += 1
                        if self._last_raw_log % 10 == 1:
                            print(f"[原始字节] {raw_data[:100]}...") if len(raw_data) > 100 else print(f"[原始字节] {raw_data}")
                        
                        # 尝试多种编码
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'ascii', 'latin1']:
                            try:
                                line = raw_data.decode(encoding, errors='ignore').strip()
                                if line and len(line) > 10:  # 有效数据长度检查
                                    if self._last_raw_log % 10 == 1:
                                        print(f"[解码成功] 使用 {encoding}: {line[:100]}...")
                                    break
                            except:
                                continue
                    else:
                        # readline 超时，没有读到数据
                        if not hasattr(self, '_no_data_count'):
                            self._no_data_count = 0
                        self._no_data_count += 1
                        
                        # 每100次报告一次
                        if self._no_data_count % 100 == 1:
                            print(f"[串口读取] 连续 {self._no_data_count} 次无数据 (in_waiting={self.serial.in_waiting})")
                            print(f"           可能原因: 1) 设备未发送数据 2) 波特率不匹配 3) 数据格式不正确")
                            print(f"           当前 DTR=False, RTS=False")
                                
                except UnicodeDecodeError as e:
                    print(f"[解码错误] {e}")
                    line = ""
                except Exception as e:
                    print(f"[读取异常] {e}")
                    import traceback
                    traceback.print_exc()
                    line = ""

                if line:
                    # 重置无数据计数
                    if hasattr(self, '_no_data_count'):
                        self._no_data_count = 0
                        
                    current, pressure, temperature, acq_idx = self.parse_serial_data(line)
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
                        print(f"[数据采集] ✓ 成功采集第 {self.sample_count} 个数据点")

                        # 数据保留限制
                        if len(self.data_buffer) > self.settings['data_retention']:
                            overflow = len(self.data_buffer) - self.settings['data_retention']
                            self.history_data.extend(self.data_buffer[:overflow])
                            self.data_buffer = self.data_buffer[overflow:]

                        # 更新界面
                        self.update_interface(current, pressure, temperature, data_point['acq_index'])
            else:
                # 串口未打开，尝试重新连接
                if not hasattr(self, '_reconnect_count'):
                    self._reconnect_count = 0
                
                self._reconnect_count += 1
                if self._reconnect_count % 50 == 0:
                    print(f"[串口状态] 串口未连接，尝试重新连接... (尝试 {self._reconnect_count} 次)")
                    self.init_serial()
                    
                if hasattr(self, 'status_label'):
                    self.status_label.config(text="⚠️ 串口未连接", fg='#d63031')
        except Exception as e:
            print(f"[数据采集异常] {str(e)}")
            import traceback
            traceback.print_exc()

        # 定时再次采集
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
            file_path = os.path.join(output_directory, f"pressure_data_{timestamp}.xlsx")

            # 合并当前数据和历史数据
            all_data = self.history_data + self.data_buffer
            df = pd.DataFrame(all_data)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            df.to_excel(file_path, index=False, engine='openpyxl')

            messagebox.showinfo(
                "保存成功",
                f"文件已保存至：\n{file_path}\n"
                f"记录总数：{len(df)}条"
            )

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

        # 压力趋势图（Pa）
        ax1 = fig.add_subplot(211, facecolor='#fafafa')
        if self.data_buffer:
            pressures = [d['pressure'] for d in self.data_buffer]
            ax1.plot(pressures, linewidth=2)
            ax1.set_title('压力趋势', color='#333333', fontsize=12, fontweight='bold')
            ax1.set_ylabel('气压 (Pa)', color='#666666')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(colors='#666666')
            for spine in ax1.spines.values():
                spine.set_edgecolor('#cccccc')

        # 电流趋势图
        ax2 = fig.add_subplot(212, facecolor='#fafafa')
        if self.data_buffer:
            currents = [d['current'] for d in self.data_buffer]
            ax2.plot(currents, linewidth=2)
            ax2.set_title('电流趋势', color='#333333', fontsize=12, fontweight='bold')
            ax2.set_ylabel('电流 (mA)', color='#666666')
            ax2.set_xlabel('采样点', color='#666666')
            ax2.grid(True, alpha=0.3)
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
        window.geometry("1100x650")
        window.configure(bg='#f5f5f5')

        # 顶部标题
        title_frame = tk.Frame(window, bg='#ffffff', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="📋 历史数据记录",
            font=('Microsoft YaHei UI', 16, 'bold'),
            bg='#ffffff',
            fg='#2c8c5c'
        )
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
            label = tk.Label(
                stats_frame,
                text=text,
                font=('Consolas', 10, 'bold'),
                bg='#e3f2fd',
                fg='#0077cc',
                padx=15,
                pady=8
            )
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
        style.configure(
            "History.Treeview",
            background="#ffffff",
            foreground="#333333",
            fieldbackground="#ffffff",
            borderwidth=0,
            font=('Consolas', 9)
        )
        style.configure(
            "History.Treeview.Heading",
            background='#e0e0e0',
            foreground='#2c8c5c',
            borderwidth=0,
            font=('Microsoft YaHei UI', 10, 'bold')
        )
        style.map('History.Treeview', background=[('selected', '#e3f2fd')])

        columns = ('序号', '时间戳', '电流(mA)', '气压(Pa)', '温度(°C)', '类型')
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            style='History.Treeview',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)

        # 设置列
        tree.heading('序号', text='序号')
        tree.heading('时间戳', text='时间戳')
        tree.heading('电流(mA)', text='电流 (mA)')
        tree.heading('气压(Pa)', text='气压 (Pa)')
        tree.heading('温度(°C)', text='温度 (°C)')
        tree.heading('类型', text='数据类型')

        tree.column('序号', width=60, anchor='center')
        tree.column('时间戳', width=200, anchor='center')
        tree.column('电流(mA)', width=120, anchor='center')
        tree.column('气压(Pa)', width=120, anchor='center')
        tree.column('温度(°C)', width=120, anchor='center')
        tree.column('类型', width=100, anchor='center')

        # 插入历史数据
        for idx, data in enumerate(self.history_data, 1):
            temp = data.get('temperature', None)
            tree.insert(
                '',
                'end',
                values=(
                    idx,
                    data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    f"{data['current']:.4f}",
                    f"{data['pressure']:.2f}",
                    f"{temp:.2f}" if temp is not None else "--",
                    "历史"
                )
            )

        # 插入当前缓冲数据
        for idx, data in enumerate(self.data_buffer, len(self.history_data) + 1):
            temp = data.get('temperature', None)
            tree.insert(
                '',
                'end',
                values=(
                    idx,
                    data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    f"{data['current']:.4f}",
                    f"{data['pressure']:.2f}",
                    f"{temp:.2f}" if temp is not None else "--",
                    "当前"
                )
            )

        tree.pack(fill=tk.BOTH, expand=True)

        # 底部按钮
        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        export_btn = tk.Button(
            button_frame,
            text="📥 导出选中",
            font=('Microsoft YaHei UI', 10),
            bg='#74b9ff',
            fg='#ffffff',
            activebackground='#5fa3e8',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=lambda: self.export_selected(tree)
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(
            button_frame,
            text="❌ 关闭",
            font=('Microsoft YaHei UI', 10),
            bg='#ff7675',
            fg='#ffffff',
            activebackground='#e65c5c',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

    def export_selected(self, tree):
        """导出选中的记录（演示用，可自行扩展为真实导出 Excel/CSV）"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择要导出的记录")
            return

        messagebox.showinfo("导出", f"已选择 {len(selected)} 条记录进行导出（示例）。")

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

        title_label = tk.Label(
            title_frame,
            text="📉 统计分析报告",
            font=('Microsoft YaHei UI', 16, 'bold'),
            bg='#ffffff',
            fg='#2c8c5c'
        )
        title_label.pack(pady=15)

        if not self.data_buffer and not self.history_data:
            no_data_label = tk.Label(
                window,
                text="暂无数据可供分析",
                font=('Microsoft YaHei UI', 14),
                bg='#f5f5f5',
                fg='#999999'
            )
            no_data_label.pack(pady=50)
            return

        # 合并数据进行分析
        all_data = self.history_data + self.data_buffer
        pressures = np.array([d['pressure'] for d in all_data])
        currents = np.array([d['current'] for d in all_data])

        # 计算统计指标（气压单位：Pa）
        stats = {
            '气压统计': {
                '平均气压 (Pa)': np.mean(pressures),
                '最大气压 (Pa)': np.max(pressures),
                '最小气压 (Pa)': np.min(pressures),
                '气压方差': np.var(pressures),
                '标准差': np.std(pressures),
                '中位数 (Pa)': np.median(pressures),
                '极差 (Pa)': np.ptp(pressures),
                '变异系数(%)': (np.std(pressures) / np.mean(pressures)) * 100 if np.mean(pressures) != 0 else 0,
            },
            '电流统计': {
                '平均电流 (mA)': np.mean(currents),
                '最大电流 (mA)': np.max(currents),
                '最小电流 (mA)': np.min(currents),
                '电流方差': np.var(currents),
                '标准差': np.std(currents),
                '中位数 (mA)': np.median(currents),
            },
            '数据质量': {
                '总样本数': len(all_data),
                '有效率(%)': 100.0,
                '异常点数(气压过高/过低)': int(np.sum((pressures > 110000) | (pressures < 90000))),
                '稳定性指数(%)': 100 - min(100, (np.std(pressures) / np.mean(pressures)) * 100) if np.mean(
                    pressures) != 0 else 0,
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

            cat_title = tk.Label(
                cat_frame,
                text=f"📋 {category}",
                font=('Microsoft YaHei UI', 12, 'bold'),
                bg=colors[idx % len(colors)],
                fg='#ffffff',
                pady=10
            )
            cat_title.pack(fill=tk.X)

            for key, value in data.items():
                item_frame = tk.Frame(cat_frame, bg='#ffffff')
                item_frame.pack(fill=tk.X, padx=10, pady=3)

                key_label = tk.Label(
                    item_frame,
                    text=f"{key}:",
                    font=('Microsoft YaHei UI', 10),
                    bg='#ffffff',
                    fg='#555555',
                    anchor='w'
                )
                key_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

                if isinstance(value, float):
                    value_text = f"{value:.4f}"
                else:
                    value_text = str(value)

                value_label = tk.Label(
                    item_frame,
                    text=value_text,
                    font=('Consolas', 10, 'bold'),
                    bg='#ffffff',
                    fg='#0077cc',
                    anchor='e'
                )
                value_label.pack(side=tk.RIGHT)

        # 右侧图表
        right_frame = tk.Frame(stats_container, bg='#ffffff')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        fig = plt.Figure(figsize=(5.5, 7), facecolor='#ffffff')

        # 气压直方图（Pa）
        ax1 = fig.add_subplot(311, facecolor='#fafafa')
        ax1.hist(pressures, bins=30, alpha=0.7, edgecolor='#333333')
        ax1.set_title('气压分布 (Pa)', color='#333333', fontsize=10, fontweight='bold')
        ax1.set_xlabel('气压 (Pa)', color='#666666', fontsize=8)
        ax1.set_ylabel('频数', color='#666666', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(colors='#666666', labelsize=7)
        for spine in ax1.spines.values():
            spine.set_edgecolor('#cccccc')

        # 气压箱线图（Pa）
        ax2 = fig.add_subplot(312, facecolor='#fafafa')
        ax2.boxplot([pressures], vert=True, patch_artist=True)
        ax2.set_title('气压箱线图 (Pa)', color='#333333', fontsize=10, fontweight='bold')
        ax2.set_ylabel('气压 (Pa)', color='#666666', fontsize=8)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(colors='#666666', labelsize=7)
        for spine in ax2.spines.values():
            spine.set_edgecolor('#cccccc')

        # 电流-气压关系散点图
        ax3 = fig.add_subplot(313, facecolor='#fafafa')
        ax3.scatter(currents, pressures, alpha=0.6, s=20)
        ax3.set_title('电流-气压关系', color='#333333', fontsize=10, fontweight='bold')
        ax3.set_xlabel('电流 (mA)', color='#666666', fontsize=8)
        ax3.set_ylabel('气压 (Pa)', color='#666666', fontsize=8)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(colors='#666666', labelsize=7)
        for spine in ax3.spines.values():
            spine.set_edgecolor('#cccccc')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=right_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def test_serial(self):
        """测试串口连接和数据接收"""
        window = tk.Toplevel(self.master)
        window.title("🔌 串口测试工具")
        window.geometry("800x600")
        window.configure(bg='#f5f5f5')

        # 标题
        title_label = tk.Label(
            window,
            text="📡 串口实时监控",
            font=('Microsoft YaHei UI', 16, 'bold'),
            bg='#f5f5f5',
            fg='#2c8c5c'
        )
        title_label.pack(pady=10)

        # 串口状态
        status_frame = tk.Frame(window, bg='#ffffff', relief='flat')
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        port = self.settings.get('serial_port', 'COM4')
        is_open = self.serial and self.serial.is_open
        status_text = f"串口: {port} | 状态: {'✅ 已连接' if is_open else '❌ 未连接'}"
        
        status_label = tk.Label(
            status_frame,
            text=status_text,
            font=('Consolas', 12, 'bold'),
            bg='#ffffff',
            fg='#2c8c5c' if is_open else '#d63031',
            pady=10
        )
        status_label.pack()

        # 数据显示区域
        text_frame = tk.Frame(window, bg='#f5f5f5')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            text_frame,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#00ff00',
            insertbackground='#00ff00',
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert('1.0', f"{'='*80}\n")
        text_widget.insert('end', f"串口测试工具 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        text_widget.insert('end', f"{'='*80}\n\n")
        text_widget.insert('end', f"串口配置:\n")
        text_widget.insert('end', f"  端口: {port}\n")
        text_widget.insert('end', f"  波特率: 9600\n")
        text_widget.insert('end', f"  数据位: 8\n")
        text_widget.insert('end', f"  停止位: 1\n")
        text_widget.insert('end', f"  校验位: None\n\n")
        
        if is_open:
            text_widget.insert('end', "✅ 串口已打开，等待数据...\n\n")
        else:
            text_widget.insert('end', "❌ 串口未打开！\n")
            text_widget.insert('end', "请检查：\n")
            text_widget.insert('end', "  1. 串口号是否正确\n")
            text_widget.insert('end', "  2. 设备是否已连接\n")
            text_widget.insert('end', "  3. 驱动程序是否已安装\n")
            text_widget.insert('end', "  4. 串口是否被其他程序占用\n\n")

        # 接收数据计数
        counter = {'count': 0, 'running': True}

        def read_serial_data():
            """实时读取串口数据"""
            if not counter['running']:
                return
                
            try:
                if self.serial and self.serial.is_open:
                    # 显示 in_waiting 状态
                    waiting = self.serial.in_waiting
                    
                    # 使用阻塞读取，不依赖 in_waiting
                    raw_data = self.serial.readline()
                    
                    if raw_data:
                        counter['count'] += 1
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        
                        # 显示原始字节
                        hex_str = ' '.join([f'{b:02X}' for b in raw_data[:20]])
                        if len(raw_data) > 20:
                            hex_str += '...'
                        
                        # 尝试解码
                        line = raw_data.decode('utf-8', errors='ignore').strip()
                        
                        text_widget.insert('end', f"[{timestamp}] #{counter['count']} (waiting={waiting}, bytes={len(raw_data)})\n")
                        text_widget.insert('end', f"  HEX: {hex_str}\n")
                        text_widget.insert('end', f"  TXT: {line}\n\n")
                        text_widget.see('end')
                    else:
                        # 每隔一段时间显示一次状态
                        if counter['count'] % 50 == 0:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            text_widget.insert('end', f"[{timestamp}] 无数据 (in_waiting={waiting})\n")
                            text_widget.see('end')
                        counter['count'] += 1
            except Exception as e:
                text_widget.insert('end', f"[错误] {e}\n")
                text_widget.see('end')

            if counter['running']:
                window.after(100, read_serial_data)

        # 启动数据读取
        read_serial_data()

        # 按钮区
        button_frame = tk.Frame(window, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def reconnect():
            text_widget.insert('end', f"\n{'='*80}\n")
            text_widget.insert('end', f"尝试重新连接串口...\n")
            text_widget.see('end')
            self.init_serial()
            is_open_new = self.serial and self.serial.is_open
            if is_open_new:
                text_widget.insert('end', f"✅ 重新连接成功！\n\n")
                status_label.config(text=f"串口: {port} | 状态: ✅ 已连接", fg='#2c8c5c')
            else:
                text_widget.insert('end', f"❌ 重新连接失败！\n\n")
                status_label.config(text=f"串口: {port} | 状态: ❌ 未连接", fg='#d63031')
            text_widget.see('end')

        reconnect_btn = tk.Button(
            button_frame,
            text="🔄 重新连接",
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#74b9ff',
            fg='#ffffff',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=reconnect
        )
        reconnect_btn.pack(side=tk.LEFT, padx=5)

        def clear_text():
            text_widget.delete('1.0', 'end')
            counter['count'] = 0
            text_widget.insert('1.0', f"{'='*80}\n清空显示 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n\n")

        clear_btn = tk.Button(
            button_frame,
            text="🗑️ 清空显示",
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#fdcb6e',
            fg='#ffffff',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=clear_text
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        def close_window():
            counter['running'] = False
            window.destroy()

        close_btn = tk.Button(
            button_frame,
            text="❌ 关闭",
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#ff7675',
            fg='#ffffff',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=close_window
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        window.protocol("WM_DELETE_WINDOW", close_window)

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

        title_label = tk.Label(
            title_frame,
            text="🔧 系统配置",
            font=('Microsoft YaHei UI', 16, 'bold'),
            bg='#ffffff',
            fg='#2c8c5c'
        )
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
            ('串口号', 'serial_port', 'text'),
            ('自动保存', 'auto_save', 'bool'),
            ('启用声音', 'enable_sound', 'bool'),
            ('主题', 'theme', 'option'),
        ]

        for label_text, key, input_type in settings_config:
            frame = tk.Frame(settings_frame, bg='#ffffff', pady=5)
            frame.pack(fill=tk.X, pady=5)

            label = tk.Label(
                frame,
                text=label_text + ":",
                font=('Microsoft YaHei UI', 11),
                bg='#ffffff',
                fg='#333333',
                width=20,
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=10)

            if input_type == 'number':
                entry = tk.Entry(
                    frame,
                    font=('Consolas', 11),
                    bg='#e8e8e8',
                    fg='#333333',
                    insertbackground='#333333',
                    relief='flat',
                    bd=5
                )
                entry.insert(0, str(self.settings[key]))
                entry.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
                setting_entries[key] = entry

            elif input_type == 'bool':
                var = tk.BooleanVar(value=self.settings[key])
                check = tk.Checkbutton(
                    frame,
                    variable=var,
                    bg='#ffffff',
                    fg='#333333',
                    selectcolor='#e8e8e8',
                    activebackground='#ffffff',
                    activeforeground='#2c8c5c',
                    font=('Microsoft YaHei UI', 10)
                )
                check.pack(side=tk.RIGHT, padx=10)
                setting_entries[key] = var

            elif input_type == 'option':
                var = tk.StringVar(value=self.settings[key])
                options = ['dark', 'light']
                menu = ttk.OptionMenu(frame, var, self.settings[key], *options)
                menu.pack(side=tk.RIGHT, padx=10)
                setting_entries[key] = var

            elif input_type == 'text':
                entry = tk.Entry(
                    frame,
                    font=('Consolas', 11),
                    bg='#e8e8e8',
                    fg='#333333',
                    insertbackground='#333333',
                    relief='flat',
                    bd=5
                )
                entry.insert(0, str(self.settings.get(key, "")))
                entry.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
                setting_entries[key] = entry

        # 附加功能设置（示意）
        advanced_frame = tk.LabelFrame(
            settings_frame,
            text="高级设置",
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg='#ffffff',
            fg='#2c8c5c',
            relief='flat',
            bd=5
        )
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
            check = tk.Checkbutton(
                advanced_frame,
                text=option,
                variable=var,
                bg='#ffffff',
                fg='#333333',
                selectcolor='#e8e8e8',
                activebackground='#ffffff',
                activeforeground='#2c8c5c',
                font=('Microsoft YaHei UI', 10)
            )
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
                        if key in ['sampling_rate', 'data_retention', 'chart_update_rate']:
                            self.settings[key] = int(value)
                        elif key in ['alert_threshold_high', 'alert_threshold_low']:
                            self.settings[key] = float(value)
                        elif key == 'serial_port':
                            self.settings[key] = value
                        else:
                            self.settings[key] = value
                    elif isinstance(widget, tk.BooleanVar):
                        self.settings[key] = widget.get()
                    elif isinstance(widget, tk.StringVar):
                        self.settings[key] = widget.get()

                # 保存到文件
                self.save_settings_to_file()
                messagebox.showinfo("成功", "设置已保存！\n注意：修改串口号后建议重启程序。")
                window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存设置失败：{str(e)}")

        save_btn = tk.Button(
            button_frame,
            text="💾 保存设置",
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg='#74b9ff',
            fg='#ffffff',
            activebackground='#5fa3e8',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(
            button_frame,
            text="🔄 重置默认",
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg='#ff7675',
            fg='#ffffff',
            activebackground='#e65c5c',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=lambda: messagebox.showinfo("重置", "暂未实现：请手动修改参数或删除 config/pressure_serial_diagnostics.local.json")
        )
        reset_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg='#55efc4',
            fg='#ffffff',
            activebackground='#42d6a9',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

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
