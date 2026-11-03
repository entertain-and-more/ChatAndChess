#!/usr/bin/env python3
"""Metadata, SBOM, CI, and Documentation Parity Contract Tests for ChatAndChess.

Run via:
    python -m unittest tests/test_metadata.py
"""

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestChatAndChessMetadata(unittest.TestCase):
    """Metadata contract and documentation parity test suite."""

    def test_core_documents_exist_and_non_empty(self):
        """Verify all core governance and documentation files are present."""
        required = [
            "README.md",
            "README_de.md",
            "SECURITY.md",
            "LICENSE",
            "NOTICE",
            "THIRD_PARTY_LICENSES.md",
            "CHANGELOG.md",
            "EXPORTFORMAT.md",
            "llms.txt",
            "pyproject.toml",
        ]
        for filename in required:
            filepath = PROJECT_ROOT / filename
            self.assertTrue(filepath.is_file(), f"Required file missing: {filename}")
            content = filepath.read_text(encoding="utf-8")
            self.assertGreater(
                len(content.strip()), 20, f"File {filename} is unexpectedly empty"
            )

    def test_notice_file_integrity(self):
        """Verify NOTICE file contains author and ecosystem attribution."""
        notice = (PROJECT_ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("ChatAndChess", notice)
        self.assertIn("Lukas Geiger", notice)
        self.assertIn("entertain-and-more", notice)
        self.assertIn("open-bricks", notice)

    def test_third_party_licenses_and_sbom(self):
        """Verify THIRD_PARTY_LICENSES.md contains Level 1 SBOM and runtime invariants."""
        sbom = (PROJECT_ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        self.assertIn("Level 1 SBOM", sbom)
        self.assertIn("Python Standard Library", sbom)
        self.assertIn("Zero-Copyleft Guarantee", sbom)
        self.assertIn("RunAsInvoker", sbom)
        for inv_id in ("INV-LOCAL-01", "INV-RUNAS-02", "INV-STATE-03", "INV-SLA-10"):
            self.assertIn(inv_id, sbom, f"Missing invariant: {inv_id}")

    def test_pyproject_toml_configuration(self):
        """Verify pyproject.toml contains required PEP 621/639 metadata without version bumps."""
        content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "chatandchess"', content)
        self.assertIn('version = "1.2.0"', content)
        self.assertIn('license = "MIT"', content)
        self.assertNotIn("License :: OSI Approved", content)
        self.assertIn('"Programming Language :: Python :: 3.13"', content)
        self.assertIn('license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md"]', content)
        self.assertIn('Changelog = "https://github.com/entertain-and-more/ChatAndChess/blob/master/CHANGELOG.md"', content)
        self.assertIn('Notice = "https://github.com/entertain-and-more/ChatAndChess/blob/master/NOTICE"', content)
        self.assertIn('"Third-Party Licenses" = "https://github.com/entertain-and-more/ChatAndChess/blob/master/THIRD_PARTY_LICENSES.md"', content)
        self.assertIn("[tool.ruff]", content)

    def test_ci_matrix_hardening(self):
        """Verify CI workflow matrix covers Linux, macOS, Windows and Python 3.10 through 3.13."""
        ci_path = PROJECT_ROOT / ".github" / "workflows" / "tests.yml"
        self.assertTrue(ci_path.is_file(), "CI test workflow tests.yml missing")
        ci_content = ci_path.read_text(encoding="utf-8")
        for os_name in ("ubuntu-latest", "macos-latest", "windows-latest"):
            self.assertIn(os_name, ci_content, f"Missing OS in CI matrix: {os_name}")
        for py_ver in ('"3.10"', '"3.11"', '"3.12"', '"3.13"'):
            self.assertIn(py_ver, ci_content, f"Missing Python version in CI matrix: {py_ver}")

    def test_readme_bilingual_parity(self):
        """Verify README.md and README_de.md maintain structural parity."""
        en_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

        self.assertIn("## Table of Contents", en_text)
        self.assertIn("## Inhaltsverzeichnis", de_text)

        # Both must include sequence diagrams and architecture diagrams
        self.assertEqual(en_text.count("```mermaid"), 2)
        self.assertEqual(de_text.count("```mermaid"), 2)

        # Both must link to each other
        self.assertIn("[English](README.md) | [Deutsch](README_de.md)", en_text)
        self.assertIn("[English](README.md) | [Deutsch](README_de.md)", de_text)

        # Both must contain target personas
        for p in ("[PERSONA-01]", "[PERSONA-02]", "[PERSONA-03]", "[PERSONA-04]"):
            self.assertIn(p, en_text)
            self.assertIn(p, de_text)

    def test_mermaid_syntax_safety(self):
        """Ensure sequenceDiagram blocks contain no semicolons in labels."""
        for md_name in ("README.md", "README_de.md"):
            content = (PROJECT_ROOT / md_name).read_text(encoding="utf-8")
            seq_blocks = re.findall(r"```mermaid\s+sequenceDiagram(.*?)```", content, re.DOTALL)
            for block in seq_blocks:
                self.assertNotIn(";", block, f"Forbidden semicolon found in {md_name} sequence diagram")

    def test_llms_txt_standardization(self):
        """Verify llms.txt has current Last-checked header and mentions test suite."""
        llms = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(
            llms.startswith("## Last-checked: 2026-10-31")
            or llms.startswith("## Last-checked: 2026-11-03")
        )
        self.assertIn("tests/test_metadata.py", llms)
        self.assertIn("THIRD_PARTY_LICENSES.md", llms)

    def test_github_governance_files(self):
        """Verify dependabot.yml and labels.yml exist and contain expected configurations."""
        dependabot_path = PROJECT_ROOT / ".github" / "dependabot.yml"
        self.assertTrue(dependabot_path.is_file(), "dependabot.yml missing")
        dep_content = dependabot_path.read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: \"pip\"", dep_content)
        self.assertIn("open-pull-requests-limit: 0", dep_content)

        labels_path = PROJECT_ROOT / ".github" / "labels.yml"
        self.assertTrue(labels_path.is_file(), "labels.yml missing")
        labels_content = labels_path.read_text(encoding="utf-8")
        self.assertIn("name: bug", labels_content)
        self.assertIn("name: enhancement", labels_content)

    def test_start_bat_launcher(self):
        """Verify start.bat launcher exists and contains executable check."""
        start_bat = PROJECT_ROOT / "start.bat"
        self.assertTrue(start_bat.is_file(), "start.bat missing")
        content = start_bat.read_text(encoding="utf-8")
        self.assertIn("ChatAndChess.exe", content)
        self.assertIn("chess.py", content)

    def test_internal_logs_not_tracked(self):
        """Ensure internal log files are in .gitignore."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("MARKETING-LOG.txt", gitignore)
        self.assertIn("CHECKS-LOG.txt", gitignore)

    def test_icons_and_assets(self):
        """Verify icon assets exist and are valid."""
        for name in ("ChatAndChess.ico", "ChatAndChess.png", "assets/icon.png", "assets/app_icon.ico"):
            p = PROJECT_ROOT / name
            self.assertTrue(p.is_file(), f"Asset missing: {name}")
            self.assertGreater(p.stat().st_size, 100, f"Asset too small: {name}")


if __name__ == "__main__":
    unittest.main()
