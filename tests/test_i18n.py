#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit and contract tests for the ChatAndChess I18N subsystem (Policy P-006 Tier-2).

Run via:
    python -m unittest tests/test_i18n.py
"""

import os
import threading
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

import i18n  # noqa: E402


class TestI18nSubsystem(unittest.TestCase):
    """Test suite for runtime internationalization."""

    def setUp(self):
        """Reset language to default before each test."""
        i18n.set_language("de")

    def tearDown(self):
        """Restore default language."""
        i18n.set_language("de")

    def test_supported_languages_list(self):
        """Verify all 6 Policy P-006 Tier-2 languages are supported."""
        expected = ["de", "en", "es", "zh", "ja", "ru"]
        self.assertEqual(i18n.get_supported_languages(), expected)

    def test_default_language_is_german(self):
        """Verify default language is German for backward compatibility."""
        self.assertEqual(i18n.get_language(), "de")

    def test_set_language_valid(self):
        """Verify switching between all 6 supported languages."""
        for lang in ("en", "es", "zh", "ja", "ru", "de"):
            self.assertTrue(i18n.set_language(lang), f"Failed to set language {lang}")
            self.assertEqual(i18n.get_language(), lang)

    def test_set_language_invalid(self):
        """Verify invalid language codes are rejected without altering state."""
        current = i18n.get_language()
        self.assertFalse(i18n.set_language("xyz"))
        self.assertFalse(i18n.set_language(""))
        self.assertFalse(i18n.set_language("123"))
        self.assertEqual(i18n.get_language(), current)

    def test_language_aliases_normalization(self):
        """Verify aliases like 'spanish', 'en-US', 'de_DE' normalize correctly."""
        cases = [
            ("english", "en"),
            ("EN-US", "en"),
            ("de_DE", "de"),
            ("deutsch", "de"),
            ("spanish", "es"),
            ("español", "es"),
            ("es-es", "es"),
            ("zh-cn", "zh"),
            ("ja_JP", "ja"),
            ("russian", "ru"),
            ("ru-RU", "ru"),
        ]
        for raw, expected in cases:
            norm = i18n.normalize_language_code(raw)
            self.assertEqual(norm, expected, f"Failed normalizing {raw}")

    def test_fallback_chain_hierarchy(self):
        """Verify 4-tier fallback: target -> en -> de."""
        mgr = i18n.get_manager()
        self.assertEqual(mgr.get_fallback_chain("de"), ["de", "en"])
        self.assertEqual(mgr.get_fallback_chain("en"), ["en", "de"])
        self.assertEqual(mgr.get_fallback_chain("es"), ["es", "en", "de"])
        self.assertEqual(mgr.get_fallback_chain("zh"), ["zh", "en", "de"])
        self.assertEqual(mgr.get_fallback_chain("ja"), ["ja", "en", "de"])
        self.assertEqual(mgr.get_fallback_chain("ru"), ["ru", "en", "de"])

    def test_tr_formatting_and_placeholders(self):
        """Verify translation formatting with keyword arguments."""
        i18n.set_language("de")
        de_str = i18n.tr("last_move", move="e2e4")
        self.assertIn("e2e4", de_str)

        i18n.set_language("en")
        en_str = i18n.tr("last_move", move="e2e4")
        self.assertIn("e2e4", en_str)
        self.assertIn("Last move", en_str)

        i18n.set_language("es")
        es_str = i18n.tr("last_move", move="e2e4")
        self.assertIn("e2e4", es_str)
        self.assertIn("Último movimiento", es_str)

    def test_tr_unknown_key_returns_default_or_key(self):
        """Verify fallback when an unregistered key is requested."""
        self.assertEqual(i18n.tr("non_existent_key_12345"), "non_existent_key_12345")
        self.assertEqual(i18n.tr("non_existent_key_12345", default="My Default"), "My Default")

    def test_detect_system_language_env_var(self):
        """Verify environment variable detection."""
        old_val = os.environ.get("CHATANDCHESS_LANG")
        try:
            os.environ["CHATANDCHESS_LANG"] = "es_ES.UTF-8"
            detected = i18n.detect_system_language()
            self.assertEqual(detected, "es")
        finally:
            if old_val is not None:
                os.environ["CHATANDCHESS_LANG"] = old_val
            else:
                os.environ.pop("CHATANDCHESS_LANG", None)

    def test_thread_safety_concurrent_access(self):
        """Verify thread-safe translation lookup under concurrent thread load."""
        errors = []

        def worker(lang_code):
            try:
                for _ in range(50):
                    i18n.tr("app_title")
                    i18n.tr("menu_quit")
                    i18n.tr("piece_knight")
                    i18n.tr("last_move", move="e2e4")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(lang,))
            for lang in ["de", "en", "es", "zh", "ja", "ru"] * 4
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread concurrency errors: {errors}")

    def test_all_six_languages_have_populated_catalogs(self):
        """Verify catalog contains all supported languages with > 100 populated strings."""
        mgr = i18n.get_manager()
        for lang in i18n.get_supported_languages():
            cat = mgr._translations.get(lang, {})
            self.assertGreater(
                len(cat), 100, f"Language '{lang}' has fewer than 100 translated keys"
            )
            # Ensure no keys have empty strings
            empty_keys = [k for k, v in cat.items() if not v or not str(v).strip()]
            self.assertEqual(
                len(empty_keys), 0, f"Language '{lang}' has empty keys: {empty_keys}"
            )


if __name__ == "__main__":
    unittest.main()
