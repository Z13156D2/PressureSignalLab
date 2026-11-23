"""Run a source checkout without requiring an editable installation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sensor_monitor.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
