# Sensor Monitor Toolkit

[English](README.md) | [简体中文](README.zh-CN.md)

A Python desktop project for pressure and environmental monitoring, serial device experiments, voltage data visualization, and temperature compensation demonstrations. The interfaces currently use Chinese labels.

The project separates runnable applications, earlier prototypes, sample workbooks, configuration, and documentation. The default application preserves the original `ui_1.py` launch behavior.

## Applications

| Application | Data source | Description |
| --- | --- | --- |
| `pressure-demo` (default) | Simulated | Current and pressure cards, trends, history, statistics, settings, and Excel export; pressure in hPa. |
| `pressure-serial` | Serial device | Pressure and temperature collection, estimated relative height, history, charts, Excel export, and serial diagnostics; pressure in Pa. |
| `environment-demo` | Simulated | Pressure, relative altitude, temperature, trends, statistics, and Excel export; pressure in Pa. |
| `voltage-dashboard` | Excel + simulated stream | Optional PyQt5 voltage dashboard; loads the first sheet of the bundled pressure/voltage workbook. Its serial connection code is currently commented out. |

Additional prototypes are available through `--list-apps`. Names beginning with `legacy-` identify earlier experimental implementations; some display a fixed “connected” status without a real device.

## Quick start

Use Python **3.10 or later**. Windows is the primary platform; the Tk applications need Tkinter and a desktop session. Select Tcl/Tk when installing Python on Windows. Chinese fonts such as Microsoft YaHei or SimHei improve chart rendering.

Run these commands from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Or activate the virtual environment, then run:

```powershell
python main.py --list-apps
python main.py --app pressure-demo
python main.py --app environment-demo
python main.py --app pressure-serial
```

Double-click `scripts/start.bat` to launch the default application on Windows. It uses the repository's `.venv` when available. Command-line options can also be passed to the batch file.

For the Qt dashboard, install the optional requirements first:

```powershell
python -m pip install -r requirements-qt.txt
python main.py --app voltage-dashboard
```

The installation helper is also available: `python scripts/install_dependencies.py` or `python scripts/install_dependencies.py --qt`.

## Serial device setup

1. Copy `config/pressure_serial.example.json` to `config/pressure_serial.local.json`.
2. Set `serial_port` and `baudrate` for your device. The defaults are `COM4` and `9600`; the application may try other baud rates when reconnecting.
3. Connect the device, close other programs using its port, and launch `pressure-serial`.

The current parser decodes ASCII and identifies values by numeric ranges: pressure at 90,000–110,000 Pa, temperature at 10–50 °C, and voltage at 0–5,000 mV. It combines values across received lines. This is a device-specific heuristic; adapt `PressureSerialApp.parse_binary_data()` to your actual protocol. It is not a general binary packet decoder, and it does not correctly support all signed values.

Relative height uses `(reference_pressure - pressure) / 12`, with a reference pressure of `100027.71 Pa`. These constants are in `src/sensor_monitor/apps/pressure_serial.py` and should be calibrated for your setup.

## Files and directories

```text
.
├── main.py                     # Unified source-checkout entry point
├── src/sensor_monitor/
│   ├── __main__.py             # Application selector
│   ├── storage.py              # Paths and per-application configuration
│   ├── apps/                   # Four main applications
│   ├── legacy/                 # Earlier prototypes
│   └── tools/                  # Raw serial inspector and packet generator
├── config/                     # Example configuration and original references
├── data/
│   ├── samples/                # Six original Excel workbooks
│   └── exports/                # Generated files; excluded from Git
├── examples/compensation/      # Standalone simulation and flowchart scripts
├── scripts/                    # Dependency installer and Windows launcher
├── docs/                       # Directory guide and migration records
│   └── archive/                # Original Chinese documentation
├── archive/placeholders/       # Original empty placeholder
├── tests/                      # Configuration, path, CLI and data integrity checks
└── .github/workflows/          # Automated checks on push and pull request
```

See [the project structure guide](docs/project_structure.md) for every renamed file, and [the sample data catalog](data/README.md) for workbook contents. All original files were retained. The [migration manifest](docs/migration_manifest.json) records their original SHA-256 checksums; workbooks were moved without changing their contents.

## Configuration and exports

- `config/<application_module>.example.json`: versioned settings for that application.
- `config/<application_module>.local.json`: local overrides, preferred at startup and written by applications that save settings. These files are excluded from Git. Local keys are merged over the defaults in code; example files are used only when no local file exists.
- `config/original_settings.reference.json`: the original shared settings, retained for reference and not loaded automatically. Each application now has separate settings to keep Pa and hPa thresholds apart.
- `config/color_scheme.reference.json`: original design reference; applications currently define their colors in code.
- `data/exports/`: default output for all Excel exports, including legacy applications. Tk applications use timestamped filenames; the Qt dashboard uses the entered filename within this directory and can overwrite an existing file of that name.

Paths resolve from the repository location, independent of the terminal's current working directory. Sample data is tracked; newly exported measurements and local configuration are ignored.

## Tools and compensation examples

Install the project in editable mode from the repository root to use module commands:

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

The inspector only reads and prints serial bytes. The packet generator prints synthetic packets and does not transmit them. Its packet format is separate from the ASCII heuristic used by `pressure-serial`.

Compensation scripts use synthetic data and retain the original numerical models, including coefficient perturbations and an underdetermined polynomial fit in `zero_drift_polynomial.py` that can emit a `RankWarning`. They are illustrative experiments, not validated sensor calibration results.

This project is intended to run from a source checkout, optionally installed with `pip install -e .`. Configuration and workbooks live outside the Python package; a standalone wheel distribution is not provided.

## Checks

```powershell
python -m compileall -q src examples scripts main.py
python -m unittest discover -s tests -v
```

Automated checks cover application discovery without a display, settings isolation, output paths, original workbook integrity, and synthetic packet structure. GUI interaction and real serial devices require local verification. GitHub Actions runs the checks on Windows with Python 3.10 and 3.13.

An optional smoke check constructs the main windows and verifies Excel input/output using temporary files and a mocked serial connection: `python scripts/check_gui.py`. Add `--qt` after installing Qt dependencies to include the voltage dashboard. This requires a local desktop session; it does not test hardware communication.

## Current limitations

- Simulated and static applications do not validate hardware measurements.
- History is held in memory and is lost when the application closes unless exported. The history list can grow beyond the current buffer limit.
- Some settings, including automatic saving, sound, and theme selection, are inherited UI options and are not fully implemented in every application.
- The original documentation in `docs/archive/` describes earlier versions and can contain outdated commands or feature claims. Use the root READMEs for current instructions.
- Linux/macOS may require separate Tk installation, font changes, and serial port configuration; they have not been verified here.

## Preparing a GitHub repository

Suggested repository name: **`sensor-monitor-toolkit`**. The parent folder can keep its current name; internal paths do not depend on it.

Create an empty repository on GitHub, then run from this directory (replace the remote URL):

```powershell
git init -b main
git add .
git status
git commit -m "Organize sensor monitoring toolkit"
git remote add origin https://github.com/YOUR_USERNAME/sensor-monitor-toolkit.git
git push -u origin main
```

No license has been selected. Add a `LICENSE` file reflecting your intended permissions before presenting this project as licensed open-source software.
