#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for manage_translations.py CLI and audit tooling.

Run via:
    python -m unittest tests/test_manage_translations.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

import manage_translations  # noqa: E402


def build_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return env


class TestManageTranslationsTooling(unittest.TestCase):
    """Test suite for translation manager CLI and helper functions."""

    def test_cli_check_returns_zero(self):
        """Verify python manage_translations.py --check exits 0 on valid parity."""
        res = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "manage_translations.py"), "--check"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=build_env(),
        )
        self.assertEqual(
            res.returncode, 0, f"manage_translations.py --check failed: {res.stderr}\n{res.stdout}"
        )
        self.assertIn("Translation Parity Gate: PASS", res.stdout)

    def test_cli_stats_output_contains_all_languages(self):
        """Verify python manage_translations.py --stats outputs 100.0% coverage for all languages."""
        res = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "manage_translations.py"), "--stats"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=build_env(),
        )
        self.assertEqual(res.returncode, 0)
        for lang_code in ("DE", "EN", "ES", "ZH", "JA", "RU"):
            self.assertIn(lang_code, res.stdout, f"Language {lang_code} missing in stats output")
        self.assertIn("100.0%", res.stdout)

    def test_cli_scan_detects_keys(self):
        """Verify python manage_translations.py --scan executes and finds source keys."""
        res = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "manage_translations.py"), "--scan"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=build_env(),
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Source Scan:", res.stdout)
        self.assertIn("keys detected in code", res.stdout)

    def test_atomic_save_roundtrip(self):
        """Verify atomic_save_translations writes and flushes cleanly without temp file leftovers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_translations.json"
            sample_data = {
                "de": {"greeting": "Hallo"},
                "en": {"greeting": "Hello"},
                "es": {"greeting": "Hola"},
                "zh": {"greeting": "你好"},
                "ja": {"greeting": "こんにちは"},
                "ru": {"greeting": "Привет"},
            }
            manage_translations.atomic_save_translations(test_file, sample_data)
            self.assertTrue(test_file.is_file(), "Saved file does not exist")

            with open(test_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["es"]["greeting"], "Hola")

            # Verify no temp files left behind
            temp_files = list(Path(tmpdir).glob("*.tmp.*"))
            self.assertEqual(len(temp_files), 0, f"Found orphan temp files: {temp_files}")

    def test_audit_parity_detects_missing_keys(self):
        """Verify audit_parity detects missing and empty keys accurately."""
        catalog = {
            "de": {"k1": "Wert 1", "k2": "Wert 2"},
            "en": {"k1": "Value 1"},  # k2 missing
            "es": {"k1": "Valor 1", "k2": ""},  # k2 empty
            "zh": {"k1": "值 1", "k2": "值 2"},
            "ja": {"k1": "値 1", "k2": "値 2"},
            "ru": {"k1": "Значение 1", "k2": "Значение 2"},
        }
        is_valid, missing, empty = manage_translations.audit_parity(catalog)
        self.assertFalse(is_valid)
        self.assertIn("en", missing)
        self.assertIn("k2", missing["en"])
        self.assertIn("es", empty)
        self.assertIn("k2", empty["es"])


if __name__ == "__main__":
    unittest.main()
