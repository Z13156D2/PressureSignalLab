"""Optional GUI construction/export smoke checks; no physical device is opened.

Run from a desktop session: python scripts/check_gui.py
Add --qt to check the optional Qt dashboard too.
"""

import argparse
import contextlib
from datetime import datetime, timedelta
import importlib
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def fail_dialog(title, message, **kwargs):
    raise AssertionError(f"{title}: {message}")


def check_tk(module_name, class_name, output_directory):
    import tkinter as tk
    from tkinter import messagebox
    from contextlib import ExitStack
    import matplotlib.pyplot as plt
    import pandas as pd

    module = importlib.import_module(f"sensor_monitor.apps.{module_name}")
    app_class = getattr(module, class_name)
    root = tk.Tk()
    root.withdraw()
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(messagebox, "showinfo"))
            stack.enter_context(patch.object(messagebox, "showerror", side_effect=fail_dialog))
            stack.enter_context(patch.object(messagebox, "showwarning", side_effect=fail_dialog))
            if module_name == "pressure_serial":
                stack.enter_context(patch.object(app_class, "init_serial"))
            application = app_class(root)
            now = datetime.now()
            application.data_buffer = []
            for index in range(25):
                sample = {"timestamp": now + timedelta(seconds=index), "pressure": 988.7 + index * 0.001, "current": 12.0 + index * 0.001}
                if module_name != "pressure_demo":
                    sample.update(pressure=99644.4 + index * 0.1, temperature=20.0, altitude=30.4, acq_index=index + 1)
                application.data_buffer.append(sample)
            application.sample_count = 25
            chart_method = "show_charts" if hasattr(application, "show_charts") else "show_pressure"
            for method_name in (chart_method, "show_history", "show_analysis", "show_settings"):
                getattr(application, method_name)()
            before = set(output_directory.glob("*.xlsx"))
            application.save_dataset()
            created = set(output_directory.glob("*.xlsx")) - before
            assert len(created) == 1, f"Expected one export for {module_name}"
            assert len(pd.read_excel(created.pop())) == 25
            if module_name == "pressure_serial":
                with contextlib.redirect_stdout(io.StringIO()):
                    result = application.parse_binary_data(b"temperature 25 pressure 100000 voltage 2500")
                assert result[:3] == (10.0, 100000.0, 25.0), result
            root.update_idletasks()
            print(f"PASS {module_name}: windows constructed and 25 rows exported")
    finally:
        root.destroy()
        plt.close("all")


def check_qt(output_directory):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from sensor_monitor.apps.voltage_dashboard import VoltageDashboard
    import pandas as pd

    qt_application = QApplication.instance() or QApplication([])
    with patch.object(QMessageBox, "information"), patch.object(QMessageBox, "warning", side_effect=fail_dialog), patch.object(QMessageBox, "critical", side_effect=fail_dialog):
        window = VoltageDashboard()
        assert len(window.voltage_data) == 60, "Default workbook did not load"
        window.filename_edit.setText("gui_check.xlsx")
        window.save_data()
        assert len(pd.read_excel(output_directory / "gui_check.xlsx")) == 60
        window.close()
    qt_application.processEvents()
    print("PASS voltage_dashboard: sample workbook loaded and 60 rows exported")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qt", action="store_true")
    args = parser.parse_args()
    from sensor_monitor import storage

    with tempfile.TemporaryDirectory() as folder:
        output_directory = Path(folder) / "exports"
        with patch.object(storage, "EXPORT_DIRECTORY", output_directory), patch.object(storage, "CONFIG_DIRECTORY", Path(folder) / "config"):
            for name, class_name in (("pressure_demo", "PressureDemoApp"), ("environment_demo", "EnvironmentDemoApp"), ("pressure_serial", "PressureSerialApp")):
                check_tk(name, class_name, output_directory)
            if args.qt:
                check_qt(output_directory)


if __name__ == "__main__":
    main()
