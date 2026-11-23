
from sensor_monitor.storage import export_directory

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import os
import random
from datetime import datetime

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class SerialMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("工业气压监测系统")

        # 初始化数据存储
        self.data_buffer = []
        self.sample_count = 0

        # 构建界面
        self.create_interface()

        # 启动数据采集（使用模拟数据）
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

    def current_to_pressure(self, current):
        """模拟电流到气压转换"""
        # 假设电流范围是4-20mA，对应气压范围是0-100hPa
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

    def generate_fake_data(self):
        """生成模拟数据"""
        # 模拟电流数据在4-20mA之间
        current = random.uniform(4, 20)
        pressure = self.current_to_pressure(current)

        return current, pressure

    def data_acquisition(self):
        """数据采集核心逻辑（模拟数据）"""
        try:
            current, pressure = self.generate_fake_data()

            self.data_buffer.append({
                'timestamp': datetime.now(),
                'current': current,
                'pressure': pressure
            })
            self.sample_count += 1

            # 每10次更新一次界面
            if self.sample_count % 10 == 0:
                self.update_interface(current, pressure)

        except Exception as e:
            print(f"数据采集异常: {str(e)}")

        self.master.after(1000, self.data_acquisition)  # 每秒采集一次

    def start_monitoring(self):
        """启动监测（模拟数据）"""
        self.data_acquisition()

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
        """安全关闭资源（没有串口需要关闭）"""
        pass


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x768")


    def on_closing():
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = SerialMonitor(root)
    root.mainloop()
