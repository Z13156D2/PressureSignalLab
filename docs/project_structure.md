# Project structure

Source files use lowercase `snake_case`; Python application classes use `PascalCase`. Directory and file names use English, while the original Chinese UI labels are retained.

- `src/sensor_monitor/apps/`: four main applications.
- `src/sensor_monitor/legacy/`: older prototypes, kept for comparison.
- `src/sensor_monitor/tools/`: serial inspection and synthetic packet generation.
- `data/samples/`: the six original workbooks.
- `data/exports/`: generated measurements, excluded from Git.
- `config/`: separate application settings and original references.
- `examples/compensation/`: standalone synthetic experiments and a flowchart.
- `docs/archive/`: original documentation with historical commands.
- `archive/placeholders/`: the original empty `u_fbl.py`, retained as a placeholder.

The default launcher preserves the original pressure demo. Hardware parsing and compensation models retain their original behavior. File paths now resolve from the repository, each application has separate configuration, and all exports go to `data/exports/`. Importing the serial inspector no longer opens a device. Main application class names now describe their functions. The Qt layout uses integer stretch factors to fix its original startup error.

## File migration

The manifest stores checksums from before reorganization. Code and documentation may subsequently change; workbook checksums remain unchanged.

| Original file | Current path |
| --- | --- |
| `ui_1.py` | `src/sensor_monitor/apps/pressure_demo.py` |
| `ui_4.py` | `src/sensor_monitor/apps/pressure_serial.py` |
| `ui_7.py` | `src/sensor_monitor/apps/environment_demo.py` |
| `sensor_gui.py` | `src/sensor_monitor/apps/voltage_dashboard.py` |
| `ui_2.py` | `src/sensor_monitor/legacy/pressure_serial_diagnostics.py` |
| `ui_3.py` | `src/sensor_monitor/legacy/pressure_serial_prototype.py` |
| `ui_5.py` | `src/sensor_monitor/legacy/pressure_static_demo.py` |
| `ui_6.py` | `src/sensor_monitor/legacy/environment_demo_prototype.py` |
| `serial_1.py` | `src/sensor_monitor/legacy/pressure_demo_basic.py` |
| `SENSOR_GUI_1.py` | `src/sensor_monitor/legacy/distance_static_demo.py` |
| `传感器读取信息.py` | `src/sensor_monitor/legacy/current_serial_monitor.py` |
| `u_fbl.py` | `archive/placeholders/voltage_resolution.py` |
| `buchang.py` | `examples/compensation/zero_drift_piecewise.py` |
| `buchang_1.py` | `examples/compensation/zero_drift_polynomial.py` |
| `buchang_2.py` | `examples/compensation/zero_drift_scaled.py` |
| `liucheng.py` | `examples/compensation/compensation_flowchart.py` |
| `print_data.py` | `src/sensor_monitor/tools/packet_generator.py` |
| `serial_test.py` | `src/sensor_monitor/tools/serial_inspector.py` |
| `install_dependencies.py` | `scripts/install_dependencies.py` |
| `启动程序.bat` | `scripts/start.bat` |
| `README_UI_v2.md` | `docs/archive/ui_v2_features.zh-CN.md` |
| `使用指南.md` | `docs/archive/user_guide.zh-CN.md` |
| `图标说明.txt` | `docs/archive/icon_reference.zh-CN.txt` |
| `界面展示说明.txt` | `docs/archive/interface_overview.zh-CN.txt` |
| `color_scheme.json` | `config/color_scheme.reference.json` |
| `settings.json` | `config/original_settings.reference.json` |
| `112.xlsx` | `data/samples/voltage_baseline.xlsx` |
| `2.xlsx` | `data/samples/voltage_series_02.xlsx` |
| `3.xlsx` | `data/samples/voltage_series_03.xlsx` |
| `pressure_600_700_800hPa_0p4Pa_step_voltage_corrected.xlsx` | `data/samples/pressure_voltage_corrected.xlsx` |
| `pressure_600_700_800hPa_0p4Pa_step_voltage_corrected_1.xlsx` | `data/samples/pressure_voltage_corrected_variant.xlsx` |
| `sensor_data_001.xlsx` | `data/samples/sensor_recording_001.xlsx` |

## Running older prototypes

Use `python main.py --list-apps`, then `python main.py --app <name>`.

| Application | Source module |
| --- | --- |
| `legacy-serial-diagnostics` | `legacy/pressure_serial_diagnostics.py` |
| `legacy-serial-prototype` | `legacy/pressure_serial_prototype.py` |
| `legacy-pressure-static` | `legacy/pressure_static_demo.py` |
| `legacy-environment-demo` | `legacy/environment_demo_prototype.py` |
| `legacy-pressure-basic` | `legacy/pressure_demo_basic.py` |
| `legacy-distance-static` | `legacy/distance_static_demo.py` |
| `legacy-current-serial` | `legacy/current_serial_monitor.py` |

The basic current serial monitor retains automatic port selection and is an early hardware prototype. The original compensation scripts and static prototypes remain available for reference; they are not promoted as validated measurement software.
