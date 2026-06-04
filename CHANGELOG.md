# Changelog

All notable changes to ChatAndChess are documented here.

## Unreleased

- Added `tests/linux_platform_smoke.py` to validate the Linux source path for
  `python chess.py`, `python chess.py --worker`, and `python chess_analyze.py`.
- Extended `.github/workflows/tests.yml` to run the Linux platform smoke on
  `ubuntu-latest`.
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
