# Changelog

All notable changes to ChatAndChess are documented here.

## Unreleased

- Added `pyproject.toml` (PEP 621 compliance, keywords, classifiers, pytest configuration).
- Enhanced `README.md` with Shields.io badges, bi-lingual navigation (`README.md` / `README_de.md`), GitHub Markdown Callouts (`> [!NOTE]`, `> [!TIP]`), quick feature overview table, and Mermaid architecture & dataflow diagram.
- Created `README_de.md` for complete German documentation parity.
- Standardized `llms.txt`: updated `Last-checked: 2026-07-25`, expanded repository capabilities overview, and added search phrases.
- Updated repository topic tags (`terminal-chess`, `python3`, `minimax-algorithm`, `claude-ai`, `llm-agent`, `offline-first`).

## 2026-06-11

- Renamed `tests/linux_platform_smoke.py` → `tests/source_platform_smoke.py` (platform-neutral name).
- Extended `.github/workflows/tests.yml` with macOS CI: `os` matrix now covers `ubuntu-latest` and `macos-latest`.
- Added a GitHub Actions test workflow for Python 3.10, 3.11, and 3.12.
- Updated community workflow actions and first-interaction input names.
- Added `llms.txt` and linked the local test command from the README.
- Moved the gameplay screenshot into `README/screenshots/` to match the repository documentation policy.
- Expanded the README with clearer German/English setup, usage, privacy, and project-structure notes.
- Extended `.gitignore` for local database files and common Python test/cache outputs.
- Added repository health files: MIT license, contributing guide, code of conduct, security policy, and dependency notes.
- Documented the Windows build helper and runtime communication directory in the README.
- Hardened `.gitignore` for build output, local secrets, runtime communication files, and local task files.
- Preserved castling rights and en-passant state in the Claude-Code worker payload so worker turns do not lose legal move context.
- Filtered illegal king-capture targets out of generated legal move lists and covered the worker state roundtrip with `tests/test_worker_state.py`.
- Moved English description before German in README.md (EN-first convention).
- Standardized `llms.txt`: `Last-checked` header at line 1, `Audience` section added, `Search Phrases` as fenced code block.
