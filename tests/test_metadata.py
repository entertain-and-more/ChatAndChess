#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
            "TODO.md",
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
        """Verify pyproject.toml contains required PEP 621 metadata without version bumps."""
        content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "chatandchess"', content)
        self.assertIn('version = "1.2.0"', content)
        self.assertIn('license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md"]', content)
        self.assertIn('Notice = "https://github.com/entertain-and-more/ChatAndChess/blob/master/NOTICE"', content)
        self.assertIn('"Third-Party Licenses" = "https://github.com/entertain-and-more/ChatAndChess/blob/master/THIRD_PARTY_LICENSES.md"', content)

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
        self.assertTrue(llms.startswith("## Last-checked: 2026-09-22"))
        self.assertIn("tests/test_metadata.py", llms)
        self.assertIn("THIRD_PARTY_LICENSES.md", llms)


if __name__ == "__main__":
    unittest.main()
