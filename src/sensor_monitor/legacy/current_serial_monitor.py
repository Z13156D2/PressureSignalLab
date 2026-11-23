
from sensor_monitor.storage import export_directory

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import re
import os
from datetime import datetime

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def find_serial_port():
    """自动检测可用串口"""
    ports = serial.tools.list_ports.comports()
    return ports[0].device if ports else None


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("工业气压监测系统")

        # 初始化数据存储
        self.data_buffer = []
        self.sample_count = 0

        # 配置串口（自动检测）
        self.serial_port = serial.Serial(
            port=find_serial_port() or 'COM3',
            baudrate=9600,
            timeout=1
        )

        # 构建界面
        self.create_interface()

        # 启动数据采集
        self.start_monitoring()

    def create_interface(self):
        """创建用户界面"""
        # 主容器
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 实时数据显示
        self.data_panel = ttk.Frame(main_frame)
        self.data_panel.pack(fill=tk.X)

        self.current_display = ttk.Label(
            self.data_panel,
            text="实时电流: -- mA",
            font=('Microsoft YaHei', 12, 'bold')
        )
        self.current_display.pack(side=tk.LEFT, padx=20)

        self.pressure_display = ttk.Label(
            self.data_panel,
            text="推算气压: -- hPa",
            font=('Microsoft YaHei', 12, 'bold')
        )
        self.pressure_display.pack(side=tk.LEFT, padx=20)

        # 波形显示区域
        self.figure, self.axes = plt.subplots(figsize=(8, 4))
        self.plot_line, = self.axes.plot([], [])
        self.axes.set_title("气压变化趋势", fontsize=10)
        self.axes.set_xlabel("时间轴")
        self.axes.set_ylabel("气压值 (hPa)")
        self.axes.grid(True)

        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 控制面板
        control_panel = ttk.Frame(main_frame)
        control_panel.pack(fill=tk.X, pady=10)

        self.save_btn = ttk.Button(
            control_panel,
            text="保存数据集",
            command=self.save_dataset
        )
        self.save_btn.pack(side=tk.RIGHT, padx=20)

    def parse_current(self, raw_data):
        """解析电流数据"""
        pattern = r'C:([+-]\d+\.\d+)mA'
        match = re.search(pattern, raw_data)
        return float(match.group(1)) if match else None

    def current_to_pressure(self, current):
        """4-20mA 转 0-100hPa"""
        return (current - 20) * (-6.25) if current else None

    def update_interface(self, current, pressure):
        """更新界面显示"""
        self.current_display.config(text=f"实时电流: {current:.4f} mA")
        self.pressure_display.config(text=f"推算气压: {pressure:.2f} hPa")

        # 更新曲线数据
        timestamps = [d['timestamp'] for d in self.data_buffer]
        pressures = [d['pressure'] for d in self.data_buffer]
        self.plot_line.set_data(timestamps, pressures)
        self.axes.relim()
        self.axes.autoscale_view()
        self.graph_canvas.draw()

    def data_acquisition(self):
        """数据采集核心逻辑"""
        if self.serial_port.is_open:
            try:
                raw_line = self.serial_port.readline().decode('utf-8').strip()
                current = self.parse_current(raw_line)
                pressure = self.current_to_pressure(current)

                if current and pressure:
                    self.data_buffer.append({
                        'timestamp': datetime.now(),
                        'current': current,
                        'pressure': pressure
                    })
                    self.sample_count += 1

                    if self.sample_count % 10 == 0:
                        self.update_interface(current, pressure)

            except Exception as e:
                print(f"数据采集异常: {str(e)}")

            self.master.after(50, self.data_acquisition)

    def start_monitoring(self):
        """启动监测"""
        if not self.serial_port.is_open:
            try:
                self.serial_port.open()
                self.data_acquisition()
            except serial.SerialException as e:
                error_msg = (
                    "无法打开串口设备！\n"
                    "请检查：\n"
                    "1. 设备是否连接\n"
                    "2. 端口号是否正确\n"
                    "3. 是否被其他程序占用\n"
                    f"错误详情：{str(e)}"
                )
                messagebox.showerror("硬件错误", error_msg)
                self.master.destroy()

    def save_dataset(self):
        """保存数据到 data/exports"""
        if not self.data_buffer:
            messagebox.showwarning("空数据集", "未采集到有效数据")
            return

        try:
            output_directory = export_directory()
            file_path = os.path.join(output_directory, f"sensor_data_{datetime.now():%Y%m%d_%H%M%S_%f}.xlsx")

            df = pd.DataFrame(self.data_buffer)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            df.to_excel(file_path, index=False, engine='openpyxl')

            messagebox.showinfo("保存成功",
                                f"文件已保存至：\n{file_path}\n"
                                f"记录总数：{len(df)}条")

            self.data_buffer = []
        except Exception as e:
            messagebox.showerror("保存失败", f"错误原因：\n{str(e)}")

    def __del__(self):
        """安全关闭串口"""
        if hasattr(self, 'serial_port') and self.serial_port.is_open:
            self.serial_port.close()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x768")


    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = SerialMonitor(root)
    root.mainloop()