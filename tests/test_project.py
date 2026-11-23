"""Regression checks for project paths, migration integrity and launch selection."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sensor_monitor import storage
from sensor_monitor.__main__ import APPLICATIONS, main
from sensor_monitor.tools.packet_generator import generate_sensor_data_packet


class ProjectTests(unittest.TestCase):
    def test_launcher_runs_from_another_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--list-apps"], cwd=folder, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), set(APPLICATIONS))

    def test_list_apps_does_not_load_gui(self):
        with patch("sensor_monitor.__main__.runpy.run_module") as run_module:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--list-apps"]), 0)
            run_module.assert_not_called()

    def test_all_application_modules_exist(self):
        for module in APPLICATIONS.values():
            with self.subTest(module=module):
                self.assertIsNotNone(importlib.util.find_spec(f"sensor_monitor.{module}"))

    def test_settings_are_isolated_and_examples_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            example = directory / "pressure_demo.example.json"
            example.write_text('{"sampling_rate": 1000}', encoding="utf-8")
            with patch.object(storage, "CONFIG_DIRECTORY", directory):
                self.assertEqual(storage.load_settings("pressure_demo.py"), {"sampling_rate": 1000})
                storage.save_settings("pressure_demo.py", {"sampling_rate": 200})
                self.assertEqual(storage.load_settings("pressure_demo.py"), {"sampling_rate": 200})
                self.assertEqual(storage.load_settings("environment_demo.py"), {})
                self.assertEqual(json.loads(example.read_text()), {"sampling_rate": 1000})
                self.assertFalse(list(directory.glob("*.tmp")))

    def test_invalid_settings_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "pressure_demo.local.json").write_text("[]", encoding="utf-8")
            with patch.object(storage, "CONFIG_DIRECTORY", directory):
                with self.assertRaises(ValueError):
                    storage.load_settings("pressure_demo.py")

    def test_export_directory_is_created_on_demand(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "data" / "exports"
            with patch.object(storage, "EXPORT_DIRECTORY", directory):
                self.assertEqual(storage.export_directory(), directory)
                self.assertTrue(directory.is_dir())

    def test_original_workbooks_are_preserved(self):
        manifest = json.loads((ROOT / "docs/migration_manifest.json").read_text(encoding="utf-8"))
        workbooks = [entry for entry in manifest if entry["original"].endswith(".xlsx")]
        self.assertEqual(len(workbooks), 6)
        for entry in workbooks:
            with self.subTest(file=entry["current"]):
                contents = (ROOT / entry["current"]).read_bytes()
                self.assertEqual(hashlib.sha256(contents).hexdigest(), entry["original_sha256"])

    def test_every_original_file_has_a_destination(self):
        manifest = json.loads((ROOT / "docs/migration_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 32)
        for entry in manifest:
            self.assertTrue((ROOT / entry["current"]).is_file(), entry["current"])

    def test_packet_payload_matches_encoded_bytes(self):
        packet, samples, is_left = generate_sensor_data_packet()
        self.assertEqual(len(packet), 32)
        self.assertEqual(struct.unpack(">I", packet[:4])[0], 0xAAA000AA)
        self.assertEqual(list(struct.unpack(">10H", packet[4:24])), samples)
        self.assertEqual(struct.unpack(">2H", packet[24:28]), (0 if is_left else 20, 0))
        self.assertEqual(struct.unpack(">I", packet[-4:])[0], 0xFFFF00FF)


if __name__ == "__main__":
    unittest.main()
