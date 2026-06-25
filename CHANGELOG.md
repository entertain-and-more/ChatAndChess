# Changelog

All notable changes to ChatAndChess are documented here.

## Unreleased

- Hardened analyzer history replay and Claude-Code worker request parsing so malformed history or partial request payloads fail without turn-state drift or bare `KeyError`.
- Added `fen`, in-game `export <file.json>`, and `python chess.py --export-initial <file.json>` for portable desktop game handoff via `chatandchess-game-v1.json`.
- Extended the platform smoke to cover JSON export and added `windows-latest` to the Linux/macOS CI matrix.
- Renamed `tests/linux_platform_smoke.py` → `tests/source_platform_smoke.py` (platform-neutral name).
- Extended `.github/workflows/tests.yml` with desktop CI: `os` matrix now covers `ubuntu-latest`, `macos-latest`, and `windows-latest`.
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
