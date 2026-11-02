#!/usr/bin/env python3
"""Platform scope and architecture guardrail tests for ChatAndChess.

Enforces zero-fragmentation policy: ChatAndChess is strictly an offline-first
desktop/CLI terminal game for Windows, macOS, and Linux without rogue mobile or
web companion scaffolds.
"""

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPlatformScope(unittest.TestCase):
    """Test suite ensuring strict adherence to Desktop/CLI scope."""

    def test_no_mobile_or_web_scaffolds_exist(self):
        """Ensure no unwanted mobile/web platform folders are created."""
        forbidden_dirs = [
            "web_companion",
            "flutter_port",
            "android",
            "ios",
            "pwa",
            "capacitor",
            "cordova",
        ]
        for name in forbidden_dirs:
            path = PROJECT_ROOT / name
            self.assertFalse(
                path.exists(),
                f"Forbidden scaffold directory exists: {name} (ChatAndChess is strictly Desktop/CLI)"
            )

    def test_platform_scope_documented_in_exportformat(self):
        """Ensure EXPORTFORMAT.md explicitly declares Web/PWA and Android/iOS as non-targets."""
        doc = (PROJECT_ROOT / "EXPORTFORMAT.md").read_text(encoding="utf-8")
        self.assertIn("Web/PWA: kein Ziel für ChatAndChess", doc)
        self.assertIn("Android/iOS: kein Ziel", doc)

    def test_portierungsplan_aligns_with_architecture(self):
        """Ensure PORTIERUNGSPLAN.md exists and documents the desktop-only scope."""
        plan_path = PROJECT_ROOT / "PORTIERUNGSPLAN.md"
        self.assertTrue(plan_path.is_file(), "PORTIERUNGSPLAN.md missing from repository root")
        plan_text = plan_path.read_text(encoding="utf-8")
        self.assertIn("Desktop-/CLI-App", plan_text)
        self.assertIn("P2: Mobile/Web bewusst nicht verfolgen", plan_text)


if __name__ == "__main__":
    unittest.main()
