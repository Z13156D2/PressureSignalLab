# PressureSignalLab · 压力传感器信号工具集

[English](README.md) | [简体中文](README.zh-CN.md)

基于 Python 的桌面传感器监测项目，包含气压与环境参数模拟、串口设备采集、电压数据可视化，以及温度补偿实验示例。当前图形界面以中文显示。

项目已按应用源码、历史原型、示例表格、配置和文档分类。默认启动原 `ui_1.py` 对应的气压模拟程序。

## 程序与功能

| 启动名称 | 数据来源 | 主要用途 |
| --- | --- | --- |
| `pressure-demo`（默认） | 模拟数据 | 电流与气压显示、实时曲线、历史记录、统计分析、设置与 Excel 导出；气压单位 hPa。 |
| `pressure-serial` | 真实串口设备 | 气压与温度采集、相对高度估算、历史记录、曲线、Excel 导出及串口调试；气压单位 Pa。 |
| `environment-demo` | 模拟数据 | 气压、相对高度、温度显示，以及趋势、统计和 Excel 导出；气压单位 Pa。 |
| `voltage-dashboard` | Excel + 模拟数据流 | 可选的 PyQt5 电压监测界面，启动时读取示例工作簿的第一个工作表；实际串口连接代码目前被注释。 |

运行 `--list-apps` 可查看全部程序。以 `legacy-` 开头的项目对应早期实验版本，其中部分界面的“串口已连接”为固定展示文字，不代表已连接设备。

## 快速开始

需要 **Python 3.10 或更高版本**。主要面向 Windows；Tk 程序需要 Tkinter 和桌面环境。安装 Windows Python 时请保留 Tcl/Tk 组件。图表中文字体建议使用微软雅黑或黑体。

在项目根目录打开 PowerShell，执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

也可以激活虚拟环境，再选择程序：

```powershell
python main.py --list-apps
python main.py --app pressure-demo
python main.py --app environment-demo
python main.py --app pressure-serial
```

Windows 下双击 `scripts/start.bat` 可启动默认程序。启动脚本优先使用项目中的 `.venv`，也支持从命令行传入上述选项。

使用 Qt 电压界面时，额外安装可选依赖：

```powershell
python -m pip install -r requirements-qt.txt
python main.py --app voltage-dashboard
```

也可使用安装辅助脚本：`python scripts/install_dependencies.py`；加上 `--qt` 可一并安装 Qt 依赖。

## 连接真实串口设备

1. 将 `config/pressure_serial.example.json` 复制为 `config/pressure_serial.local.json`。
2. 根据设备修改 `serial_port` 和 `baudrate`。默认值为 `COM4`、`9600`，程序重连时可能尝试其他波特率。
3. 连接设备，关闭占用同一串口的软件，启动 `pressure-serial`。

当前解析器将输入按 ASCII 解码，再按数值范围识别气压（90,000–110,000 Pa）、温度（10–50 °C）和电压（0–5,000 mV），并可跨接收行缓存、组合数据。这属于针对原设备编写的启发式解析；更换设备时应修改 `PressureSerialApp.parse_binary_data()`。它不是通用二进制协议解码器，也不能正确处理所有带符号数值。

相对高度使用 `(参考气压 - 当前气压) / 12` 估算，参考气压为 `100027.71 Pa`。相关常数位于 `src/sensor_monitor/apps/pressure_serial.py`，实际使用时应按设备和环境标定。

## 目录结构

```text
.
├── main.py                     # 项目统一启动入口
├── src/sensor_monitor/
│   ├── __main__.py             # 应用选择入口
│   ├── storage.py              # 统一路径和独立配置管理
│   ├── apps/                   # 四个主要应用
│   ├── legacy/                 # 历史原型程序
│   └── tools/                  # 原始串口查看与模拟数据包生成
├── config/                     # 示例配置和原始配置参考
├── data/
│   ├── samples/                # 原有六个 Excel 工作簿
│   └── exports/                # 程序导出文件，默认不提交 Git
├── examples/compensation/      # 温度补偿与流程图实验脚本
├── scripts/                    # 安装辅助脚本及 Windows 启动脚本
├── docs/                       # 结构说明和迁移记录
│   └── archive/                # 原有中文说明文档
├── archive/placeholders/       # 原有空白占位文件
├── tests/                      # 配置、路径、入口及数据完整性检查
└── .github/workflows/          # GitHub 自动检查
```

完整的新旧文件名对照见 [项目结构说明](docs/project_structure.md)，表格内容见 [数据目录说明](data/README.md)。所有原文件均已保留；[迁移记录](docs/migration_manifest.json) 保存原始 SHA-256 校验值。Excel 文件仅移动和重命名，未改写内容。

## 配置与数据存放

- `config/<程序模块名>.example.json`：可提交 Git 的示例配置，各程序分别管理。
- `config/<程序模块名>.local.json`：本机配置，启动时优先读取；支持保存设置的程序也会写入此文件。已加入 Git 忽略规则。本机配置覆盖代码中的默认值；本机文件不存在时才读取示例配置。
- `config/original_settings.reference.json`：保留的原始共享配置，不会自动加载。不同程序已拆分配置，避免 Pa 与 hPa 阈值混用。
- `config/color_scheme.reference.json`：原始配色参考文件；现有程序仍在源码中定义配色。
- `data/exports/`：所有程序（含历史版本）的默认 Excel 导出目录。Tk 程序使用时间戳文件名；Qt 程序使用输入的文件名，并限制保存在此目录内，同名文件可能被覆盖。

文件路径以项目位置为基准，不依赖终端当前目录。示例表格会提交 Git，本机配置和新导出的测量数据默认不提交。

## 调试工具与补偿示例

在项目根目录执行可编辑安装后，可直接使用模块命令：

```powershell
python -m pip install -e .
sensor-monitor --list-apps
python -m sensor_monitor.tools.serial_inspector --port COM4 --baudrate 9600
python -m sensor_monitor.tools.packet_generator
python examples/compensation/zero_drift_piecewise.py
python examples/compensation/zero_drift_polynomial.py
python examples/compensation/zero_drift_scaled.py
python examples/compensation/compensation_flowchart.py
```

串口查看工具只读取并打印原始字节。数据包生成器只打印模拟包，不向设备发送；其二进制包格式与 `pressure-serial` 的 ASCII 解析逻辑不同。

补偿示例使用合成数据，保留了原始模型，包括系数扰动，以及 `zero_drift_polynomial.py` 中可能产生 `RankWarning` 的欠定多项式拟合。这些脚本用于实验演示，不代表经过验证的传感器标定结果。

当前项目按源码目录运行，可使用 `pip install -e .`。配置和表格位于 Python 包外，暂不提供脱离源码目录的独立 wheel 分发包。

## 检查项目

```powershell
python -m compileall -q src examples scripts main.py
python -m unittest discover -s tests -v
```

自动检查覆盖无需图形界面的应用枚举、配置隔离、导出路径、原始表格完整性及模拟数据包结构。图形交互与真实串口设备仍需本机验证。GitHub Actions 配置为在 Windows、Python 3.10 和 3.13 上运行这些检查。

可选检查命令 `python scripts/check_gui.py` 会构建主要窗口，并使用临时文件验证 Excel 读写，串口连接使用模拟替代。安装 Qt 依赖后可追加 `--qt` 检查电压界面。此检查需要本机桌面环境，不验证硬件通信。

## 当前限制

- 模拟版和静态版不能用于验证真实设备测量结果。
- 历史数据保存在内存中，关闭程序后会丢失，应及时导出；历史列表也可能超过当前缓冲区容量持续增长。
- 自动保存、声音和主题切换等部分选项沿用早期界面设计，并非每个程序都已完整实现。
- `docs/archive/` 是旧版资料，其中的命令和功能说明可能过时；当前用法以根目录中英文 README 为准。
- Linux/macOS 可能需要额外安装 Tk、调整字体及串口路径，目前未在这些平台验证。

## GitHub 仓库与后续更新

项目仓库：[Z13156D2/PressureSignalLab](https://github.com/Z13156D2/PressureSignalLab)。外层文件夹可继续保留当前名称，项目内部路径不依赖它。

后续修改完成后，在现有项目目录执行：

```powershell
git add .
git status
git commit -m "Update PressureSignalLab"
git push
```

本项目采用 [MIT 许可证](LICENSE)。
