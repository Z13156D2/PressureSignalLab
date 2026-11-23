from pathlib import Path
from sensor_monitor.storage import SAMPLE_DIRECTORY, export_directory

import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QLineEdit, 
                             QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import serial
import serial.tools.list_ports
from datetime import datetime


class VoltageDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("石墨烯压力传感器测试窗口")
        self.setGeometry(100, 100, 1400, 800)
        
        # 数据存储
        self.voltage_data = []
        self.time_data = []
        self.is_collecting = False
        self.data_counter = 0
        
        # 串口对象
        self.serial1 = None
        self.serial2 = None
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 初始化UI
        self.init_ui()
        
        # 尝试读取Excel文件
        self.load_excel_data()
    
    def init_ui(self):
        # 主widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局（垂直）
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 添加标题
        title_label = QLabel("🔬 石墨烯压力传感器测试窗口")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #1a252f;
                padding: 20px;
                margin: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 内容布局（水平）
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # 左侧控制面板（占2/5）
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel, 2)
        
        # 右侧区域（占3/5）
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # 按 18:32 分配按钮与图表区域；Qt 的 stretch 参数必须为整数。
        button_panel = self.create_button_panel()
        right_layout.addWidget(button_panel, 18)
        
        # 右下：图表区域
        plot_panel = self.create_plot_panel()
        right_layout.addWidget(plot_panel, 32)
        
        content_layout.addWidget(right_widget, 3)
    
    def create_control_panel(self):
        """创建左侧控制面板"""
        group_box = QGroupBox("⚙ 控制面板")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 36px;
                font-weight: bold;
                border: 3px solid #3498db;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: white;
                border-radius: 4px;
            }
        """)
        main_layout = QVBoxLayout()
        
        # 通用标签样式
        label_style = "QLabel { font-size: 36px; font-weight: bold; color: #34495e; margin-top: 5px; padding: 5px; }"
        combo_style = """
            QComboBox {
                font-size: 34px;
                font-weight: bold;
                padding: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                min-height: 55px;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
                background-color: #ecf0f1;
            }
            QComboBox::drop-down {
                width: 50px;
                border-left: 2px solid #bdc3c7;
            }
            QComboBox QAbstractItemView {
                font-size: 34px;
                font-weight: bold;
                selection-background-color: #3498db;
            }
        """
        lineedit_style = """
            QLineEdit {
                font-size: 34px;
                font-weight: bold;
                padding: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                min-height: 55px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #ecf0f1;
            }
        """
        
        # 创建网格布局用于双列显示
        from PyQt5.QtWidgets import QGridLayout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # 第一列 - 串口1选择
        label1 = QLabel("📡 串口1选择")
        label1.setStyleSheet(label_style)
        grid_layout.addWidget(label1, 0, 0)
        self.com1_combo = QComboBox()
        self.com1_combo.setStyleSheet(combo_style)
        self.update_serial_ports(self.com1_combo)
        self.com1_combo.setCurrentText("COM3")
        grid_layout.addWidget(self.com1_combo, 1, 0)
        
        # 第二列 - 串口2选择
        label2 = QLabel("📡 串口2选择")
        label2.setStyleSheet(label_style)
        grid_layout.addWidget(label2, 0, 1)
        self.com2_combo = QComboBox()
        self.com2_combo.setStyleSheet(combo_style)
        self.update_serial_ports(self.com2_combo)
        self.com2_combo.setCurrentText("COM4")
        grid_layout.addWidget(self.com2_combo, 1, 1)
        
        # 第一列 - 1通道电压
        label4 = QLabel("⚡ 1通道电压")
        label4.setStyleSheet(label_style)
        grid_layout.addWidget(label4, 2, 0)
        self.voltage_combo = QComboBox()
        self.voltage_combo.setStyleSheet(combo_style)
        self.voltage_combo.addItems(["3.3V", "5V", "12V", "24V"])
        self.voltage_combo.setCurrentText("5V")
        grid_layout.addWidget(self.voltage_combo, 3, 0)
        
        # 第二列 - 频率
        label6 = QLabel("🔊 频率")
        label6.setStyleSheet(label_style)
        grid_layout.addWidget(label6, 2, 1)
        self.freq_combo = QComboBox()
        self.freq_combo.setStyleSheet(combo_style)
        self.freq_combo.addItems(["10Hz", "20Hz", "38.4Hz", "50Hz", "100Hz", "7Hz"])
        self.freq_combo.setCurrentText("7Hz")
        grid_layout.addWidget(self.freq_combo, 3, 1)
        
        # 第一列 - 电压类型
        label5 = QLabel("📊 电压类型")
        label5.setStyleSheet(label_style)
        grid_layout.addWidget(label5, 4, 0)
        self.wave_type_combo = QComboBox()
        self.wave_type_combo.setStyleSheet(combo_style)
        self.wave_type_combo.addItems(["正弦波", "方波", "三角波", "锯齿波"])
        self.wave_type_combo.setCurrentText("方波")
        grid_layout.addWidget(self.wave_type_combo, 5, 0)
        
        # 文件名称（跨两列）
        label3 = QLabel("📁 文件名称")
        label3.setStyleSheet(label_style)
        grid_layout.addWidget(label3, 6, 0, 1, 2)
        self.filename_edit = QLineEdit()
        self.filename_edit.setStyleSheet(lineedit_style)
        self.filename_edit.setText("sensor_data_001")
        grid_layout.addWidget(self.filename_edit, 7, 0, 1, 2)
        
        main_layout.addLayout(grid_layout)
        
        group_box.setLayout(main_layout)
        return group_box
    
    def create_button_panel(self):
        """创建按钮面板"""
        group_box = QGroupBox("🎛 操作控制")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: 3px solid #9b59b6;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        button_style_start = """
            QPushButton {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                background-color: #27ae60;
                min-height: 40px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """
        
        button_style_stop = """
            QPushButton {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                background-color: #e74c3c;
                min-height: 40px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #ec7063;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """
        
        button_style_save = """
            QPushButton {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                background-color: #3498db;
                min-height: 40px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2874a6;
            }
        """
        
        button_style_settings = """
            QPushButton {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                background-color: #f39c12;
                min-height: 40px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f8c471;
            }
            QPushButton:pressed {
                background-color: #d68910;
            }
        """
        
        button_style_refresh = """
            QPushButton {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                background-color: #95a5a6;
                min-height: 40px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #aab7b8;
            }
            QPushButton:pressed {
                background-color: #797d7f;
            }
        """
        
        self.start_btn = QPushButton("▶ 开始采集")
        self.start_btn.setStyleSheet(button_style_start)
        self.start_btn.clicked.connect(self.start_collection)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ 结束采集")
        self.stop_btn.setStyleSheet(button_style_stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_collection)
        layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("💾 保存数据")
        self.save_btn.setStyleSheet(button_style_save)
        self.save_btn.clicked.connect(self.save_data)
        layout.addWidget(self.save_btn)
        
        self.settings_btn = QPushButton("⚙ 系统设置")
        self.settings_btn.setStyleSheet(button_style_settings)
        self.settings_btn.clicked.connect(self.system_settings)
        layout.addWidget(self.settings_btn)
        
        # 刷新串口按钮
        self.refresh_btn = QPushButton("🔄 刷新串口")
        self.refresh_btn.setStyleSheet(button_style_refresh)
        self.refresh_btn.clicked.connect(self.refresh_serial_ports)
        layout.addWidget(self.refresh_btn)
        
        group_box.setLayout(layout)
        return group_box
    
    def create_plot_panel(self):
        """创建右侧图表面板"""
        group_box = QGroupBox("📈 电压-时间曲线")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: 3px solid #e74c3c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px; 
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 30)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(10, 7.5))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 设置图表样式
        self.ax.set_xlabel('时间 (秒)', fontsize=16, fontweight='bold')
        self.ax.set_ylabel('电压 (V)', fontsize=16, fontweight='bold')
        self.ax.set_title('电压实时监测曲线', fontsize=18, fontweight='bold', pad=20)
        self.ax.grid(True, linestyle='--', alpha=0.6, linewidth=1.2)
        self.ax.tick_params(labelsize=13, width=2, length=6)
        
        # 设置边框粗细
        for spine in self.ax.spines.values():
            spine.set_linewidth(2)
        
        # 调整子图布局，给所有标签足够的显示空间
        self.figure.subplots_adjust(bottom=0.11, top=0.92, left=0.09, right=0.98)
        
        layout.addWidget(self.canvas)
        group_box.setLayout(layout)
        
        return group_box
    
    def update_serial_ports(self, combo_box):
        """更新可用串口列表"""
        ports = serial.tools.list_ports.comports()
        combo_box.clear()
        for port in ports:
            combo_box.addItem(port.device)
        
        # 添加默认选项
        if combo_box.findText("COM3") == -1:
            combo_box.addItem("COM3")
        if combo_box.findText("COM4") == -1:
            combo_box.addItem("COM4")
    
    def refresh_serial_ports(self):
        """刷新串口列表"""
        self.update_serial_ports(self.com1_combo)
        self.update_serial_ports(self.com2_combo)
        QMessageBox.information(self, "提示", "串口列表已刷新")
    
    def load_excel_data(self):
        """从Excel文件加载数据"""
        try:
            df = pd.read_excel(SAMPLE_DIRECTORY / 'pressure_voltage_corrected.xlsx')  #pressure_600_700_800hPa_0p4Pa_step_voltage_corrected
            
            # 第二列是时间，第三列是电压
            if len(df.columns) >= 3:
                # 获取时间数据（第二列，索引为1）
                time_col = df.iloc[:, 1].dropna()
                # 获取电压数据（第三列，索引为2）
                voltage_col = df.iloc[:, 2].dropna()
                
                # 确保时间和电压数据长度一致
                min_len = min(len(time_col), len(voltage_col))
                # 转换时间数据为秒（假设时间索引，每个点0.1秒）
                self.time_data = [i * 0.1 for i in range(min_len)]
                self.voltage_data = voltage_col.iloc[:min_len].tolist()
                
                # 绘制初始数据
                self.plot_data()
                
                QMessageBox.information(self, "✅ 成功", f"成功加载数据，共 {len(self.voltage_data)} 个数据点")
            else:
                raise ValueError("Excel文件列数不足，需要至少3列数据")
        except FileNotFoundError:
            QMessageBox.warning(self, "⚠ 警告", "未找到 data/samples/pressure_voltage_corrected.xlsx，将使用模拟数据")
            # 使用示例数据
            self.voltage_data = [80.534 + np.random.randn() * 0.001 for _ in range(100)]
            self.time_data = [i * 0.1 for i in range(100)]
            self.plot_data()
        except Exception as e:
            QMessageBox.critical(self, "❌ 错误", f"读取Excel文件时出错: {str(e)}")
    
    def plot_data(self):
        """绘制数据"""
        self.ax.clear()
        
        if self.time_data and self.voltage_data:
            self.ax.plot(self.time_data, self.voltage_data, '-', linewidth=2.5, label='电压', 
                        marker='o', markersize=4, markevery=max(1, len(self.time_data)//50),
                        color='#3498db', markerfacecolor='#e74c3c', markeredgecolor='#c0392b', 
                        markeredgewidth=1.5)
            self.ax.set_xlabel('时间 (秒)', fontsize=16, fontweight='bold')
            self.ax.set_ylabel('电压 (V)', fontsize=16, fontweight='bold')
            self.ax.set_title('电压实时监测曲线', fontsize=18, fontweight='bold', pad=15)
            self.ax.grid(True, linestyle='--', alpha=0.6, linewidth=1.2)
            self.ax.legend(fontsize=14, loc='best', framealpha=0.9, edgecolor='black', 
                          fancybox=True, shadow=True)
            self.ax.tick_params(labelsize=13, width=2, length=6)
            
            # 设置x轴刻度：每1秒一个主刻度，每0.1秒一个次刻度
            if len(self.time_data) > 0:
                import matplotlib.ticker as ticker
                # 主刻度每1秒
                self.ax.xaxis.set_major_locator(ticker.MultipleLocator(1.0))
                # 次要刻度每0.1秒
                self.ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
            
            # 设置边框粗细
            for spine in self.ax.spines.values():
                spine.set_linewidth(2)
            
        self.canvas.draw()
    
    def start_collection(self):
        """开始数据采集"""
        try:
            # 尝试打开串口（实际使用时需要配置波特率等参数）
            # self.serial1 = serial.Serial(self.com1_combo.currentText(), 9600, timeout=1)
            # self.serial2 = serial.Serial(self.com2_combo.currentText(), 9600, timeout=1)
            
            self.is_collecting = True
            self.data_counter = 0
            
            # 清空现有数据
            self.voltage_data = []
            self.time_data = []
            
            # 启动定时器（100ms = 0.1秒）
            self.timer.start(100)
            
            # 更新按钮状态
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            QMessageBox.information(self, "提示", "开始采集数据")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开串口: {str(e)}")
    
    def stop_collection(self):
        """停止数据采集"""
        self.is_collecting = False
        self.timer.stop()
        
        # 关闭串口
        if self.serial1:
            self.serial1.close()
        if self.serial2:
            self.serial2.close()
        
        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        QMessageBox.information(self, "提示", f"采集结束，共采集 {len(self.voltage_data)} 个数据点")
    
    def update_data(self):
        """更新数据（模拟数据采集）"""
        if not self.is_collecting:
            return
        
        # 模拟从串口读取数据
        # 这里使用随机数据模拟，实际应从串口读取
        new_voltage = 80.534 + np.sin(self.data_counter * 0.1) * 0.005 + np.random.randn() * 0.0005
        new_time = self.data_counter * 0.1
        
        self.voltage_data.append(new_voltage)
        self.time_data.append(new_time)
        
        self.data_counter += 1
        
        # 限制显示最近的1000个数据点
        if len(self.voltage_data) > 1000:
            self.voltage_data.pop(0)
            self.time_data.pop(0)
        
        # 更新图表
        self.plot_data()
    
    def save_data(self):
        """保存数据到Excel文件"""
        try:
            if not self.voltage_data:
                QMessageBox.warning(self, "警告", "没有数据可保存")
                return
            
            # 创建DataFrame
            df = pd.DataFrame({
                '时间': self.time_data,
                '电压': self.voltage_data
            })
            
            # 生成文件名
            filename = self.filename_edit.text()
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            # 保存到Excel
            filename = str(export_directory() / Path(filename).name)
            df.to_excel(filename, index=False)
            
            QMessageBox.information(self, "成功", f"数据已保存到 {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存数据时出错: {str(e)}")
    
    def system_settings(self):
        """系统设置"""
        settings_info = f"""
当前设置:
串口1: {self.com1_combo.currentText()}
串口2: {self.com2_combo.currentText()}
文件名: {self.filename_edit.text()}
通道电压: {self.voltage_combo.currentText()}
电压类型: {self.wave_type_combo.currentText()}
频率: {self.freq_combo.currentText()}
        """
        QMessageBox.information(self, "系统设置", settings_info)
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        if self.is_collecting:
            reply = QMessageBox.question(self, '确认退出',
                                        '数据采集正在进行，确定要退出吗？',
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.stop_collection()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置中文字体
    from matplotlib import rcParams
    rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    rcParams['axes.unicode_minus'] = False
    
    window = VoltageDashboard()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
