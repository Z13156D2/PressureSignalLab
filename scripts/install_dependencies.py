"""Install requirements with the selected Python interpreter."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qt", action="store_true", help="Install optional Qt dependencies")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    requirements = root / ("requirements-qt.txt" if args.qt else "requirements.txt")
    return subprocess.call([sys.executable, "-m", "pip", "install", "-r", str(requirements)])


if __name__ == "__main__":
    raise SystemExit(main())
