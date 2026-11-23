"""Launch a named application without importing unused GUI backends."""

import argparse
import runpy

APPLICATIONS = {
    "pressure-demo": "apps.pressure_demo",
    "pressure-serial": "apps.pressure_serial",
    "environment-demo": "apps.environment_demo",
    "voltage-dashboard": "apps.voltage_dashboard",
    "legacy-serial-diagnostics": "legacy.pressure_serial_diagnostics",
    "legacy-serial-prototype": "legacy.pressure_serial_prototype",
    "legacy-pressure-static": "legacy.pressure_static_demo",
    "legacy-environment-demo": "legacy.environment_demo_prototype",
    "legacy-pressure-basic": "legacy.pressure_demo_basic",
    "legacy-distance-static": "legacy.distance_static_demo",
    "legacy-current-serial": "legacy.current_serial_monitor",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sensor Monitor / 传感器监测工具集")
    parser.add_argument("--app", choices=APPLICATIONS, default="pressure-demo", help="Application to launch (default: pressure-demo)")
    parser.add_argument("--list-apps", action="store_true", help="List applications without opening a GUI")
    args = parser.parse_args(argv)
    if args.list_apps:
        print("\n".join(APPLICATIONS))
        return 0
    try:
        runpy.run_module(f"sensor_monitor.{APPLICATIONS[args.app]}", run_name="__main__")
    except ModuleNotFoundError as error:
        parser.exit(1, f"Missing dependency: {error.name}. Install requirements.txt; for voltage-dashboard also install requirements-qt.txt.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
