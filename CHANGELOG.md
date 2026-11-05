# Changelog

All notable changes to ChatAndChess are documented here.

## Unreleased

### Tier-2 Multi-Language Architecture & Quality Gating (2026-11-05)
- **TW-CHESS-03 (I18N Runtime Architecture `i18n.py`)**:
  - Implemented standalone thread-safe `TranslationManager` with 4-level fallback hierarchy (`target -> en -> de -> key/default`).
  - Added automatic system language detection from environment (`CHATANDCHESS_LANG`, `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`, `locale.getdefaultlocale`).
  - Added thread-safe global facades `_t()` / `tr()`, `set_language()`, `get_language()`, `get_supported_languages()`, `get_language_name()`.
  - Added defensive Windows console UTF-8 stream reconfiguration (`sys.stdout.reconfigure(encoding='utf-8')`).
- **TW-CHESS-04 (Tier-2 Translation Catalog `locales/translations.json`)**:
  - Authored full translation catalog covering 122 semantic keys across all 6 Tier-2 languages (DE, EN, ES, ZH, JA, RU) with 100% parity.
  - Formatted genuine German umlauts (ä, ö, ü, Ä, Ö, Ü, ß) and authentic chess terminology across Spanish, Chinese, Japanese, and Russian.
- **TW-CHESS-05 (Translation Management CLI `manage_translations.py`)**:
  - Implemented standalone CLI tool with `--check` (exit 0/1 CI gate), `--stats` (coverage statistics table), `--scan` (source scanner), and custom `--dir`.
  - Implemented atomic file persistence with process-isolated staging (`.tmp.<pid>`), `flush()`, `fsync()`, and `stat.S_IWRITE` safety before `os.replace`.
- **TW-CHESS-06 (UI String Decoupling in `chess.py` & `chess_analyze.py`)**:
  - Decoupled user-facing strings, prompts, menus, difficulty selections, move errors, and tactics analyzer banners.
  - Added dynamic in-game command `lang [code]` / `sprache [code]` for runtime language switching.
  - Added multilingual in-game command aliases (`help`/`hilfe`/`ayuda`, `hint`/`tipp`/`consejo`, `quit`/`beenden`/`salir`).
  - Added global `--lang <code>` CLI flag in both `chess.py` and `chess_analyze.py`.
- **TW-CHESS-07 (Tier-2 Spanish Documentation `README_es.md` & Metadata)**:
  - Created complete Spanish documentation `README_es.md` with 1:1 section parity to `README.md` and `README_de.md`.
  - Added trilingual navigation switcher in `README.md`, `README_de.md`, and `README_es.md`.
  - Synchronized `llms.txt` and `pyproject.toml` (added `i18n` and `manage_translations` to `py-modules`).
- **TW-CHESS-08 (Contract Test Suites & CI Gating)**:
  - Implemented `tests/test_i18n.py` (11 contract tests covering language switching, fallbacks, thread safety, and catalog coverage).
  - Implemented `tests/test_manage_translations.py` (5 contract tests covering `--check`, `--stats`, `--scan`, atomic saving, and mismatch detection).
  - Updated `tests/source_platform_smoke.py` with Check 7 verifying `manage_translations.py --check`.
  - Updated `.github/workflows/tests.yml` to compile modules and verify translation parity in CI.
  - Total test suite expanded to 68 tests (100% green via pytest and unittest).

### Packaging, Desktop Launchers & Governance (2026-11-03)
- Created canonical `start.bat` launcher that checks for `dist\ChatAndChess.exe` first and falls back to Python runtime (`py -3` / `python`).
- Built and verified standalone Windows executable `dist\ChatAndChess.exe` with PyInstaller (version 1.2.0, `--version` and `--healthcheck` confirmed passing).
- Added GitHub governance configurations:
  - `.github/dependabot.yml`: Automated weekly security-only dependency updates with PR limit 0.
  - `.github/labels.yml`: Standardized repository taxonomy labels.
- Hardened `.gitignore` against tracking internal logs (`MARKETING-LOG.txt`, `CHECKS-LOG.txt`).
- Extended contract test suite `tests/test_metadata.py` with 3 new tests validating `start.bat`, GitHub governance files, and `.gitignore` log defense (51 passed tests, 100% green).
- Synchronized documentation, badges (Verified/Geprüft-2026--11--03, 51 passed tests), and machine-readable `llms.txt`.
- Fulfilled and closed `TW-CHESS-01` in `AUFGABEN.txt`.

- Implemented full Standard Algebraic Notation (SAN) move converter `move_to_san`:
  - Accurately supports piece moves, pawn advances, pawn diagonal captures, en-passant captures (`exd6`), pawn promotions (e.g. `bxa8=Q+`, `b8=N`), castling (`O-O`, `O-O-O`), disambiguation for ambiguous piece moves (`Nbd2`, `Nfd2`, `R1a4`), and checks/checkmates (`+`, `#`).
- Implemented PGN export engine (`format_pgn`, `replay_moves_to_pgn`):
  - Standard 7-tag roster (`Event`, `Site`, `Date`, `Round`, `White`, `Black`, `Result`).
  - Move numbering with 78-character line wrapping and automatic game-over detection (`1-0`, `0-1`, `1/2-1/2`, `*`).
- Extended `build_game_export` with optional `include_san=True` to compute SAN strings in `chatandchess-game-v1.json` moves.
- Added in-game console commands to `game_loop`:
  - `fen`: Displays current position in FEN format.
  - `export [filepath]`: Exports current game to `chatandchess-game-v1.json` with SAN notation.
  - `pgn [filepath]`: Exports move history to PGN document.
  - `help` / `?`: Displays interactive command help.
  - `hint` / `tipp`: Computes and displays tactical suggestions.
- Implemented headless CLI options in `main()`:
  - `--version` / `-v`: Outputs version `ChatAndChess 1.2.0`.
  - `--healthcheck`: Executes non-interactive engine assertions (board validity, legal move generator, evaluation, FEN, SAN).
  - `--help` / `-h`: Displays CLI usage options.
  - `--export-initial <path>`: Exports initial game state to `chatandchess-game-v1.json`.
  - `--export-pgn <path> [moves...]`: Replays UCI moves and exports PGN.
  - `--fen [moves...]`: Replays UCI moves and prints resulting FEN string with accurate halfmove/fullmove tracking.
- Added comprehensive contract test suites:
  - `tests/test_pgn_and_cli.py`: 14 automated tests for SAN generation, PGN formatting, and all headless CLI options.
  - `tests/test_platform_scope.py`: 3 automated tests verifying strict Desktop/CLI architecture and zero mobile/web scaffold fragmentation.
- Hardened `tests/source_platform_smoke.py` with multi-OS CLI flag testing across all 6 commands.
- Total test suite expanded to 48 passing tests (100% green via pytest).

- Performed Pfad A (Repository-Hygiene & CI-Härtung) updates.
- Hardened CI test matrix in `.github/workflows/tests.yml` to test on `windows-latest` alongside `ubuntu-latest` and `macos-latest`, and added Python 3.13.
- Upgraded `pyproject.toml` to PEP 621/639 compliant string license (`license = "MIT"`), removed conflicting OSI classifier to ensure pip editable builds succeed without error, registered Python 3.13 classifier, `Changelog` URL, `py-modules`, and standardized `[tool.ruff]` configuration.
- Fixed ruff import formatting and trailing whitespaces across codebase and tests.
- Extended contract test suite in `tests/test_metadata.py` to cover CI matrix hardening (multi-OS and Python 3.10-3.13) and PEP 621/639 compliance (31 passing tests).
- Synchronized documentation and test suite badges in `README.md`, `README_de.md`, and `llms.txt`.

- Performed Pfad B (Marketing & Discoverability) enhancements across repository documentation and metadata.
- Added formal `NOTICE` attribution file and comprehensive `THIRD_PARTY_LICENSES.md` (Level 1 SBOM and ten runtime invariants).
- Integrated Mermaid `sequenceDiagram` detailing the Worker IPC protocol and state synchronization lifecycle in both `README.md` and `README_de.md`.
- Added ASCII terminal board preview, target personas (`[PERSONA-01]` to `[PERSONA-04]`), and multi-dimension comparison matrix.
- Updated Shields.io badges (Ruff code style, Zero Dependencies, Bilingual Docs, verified 27 passing tests).
- Standardized `pyproject.toml` with PEP 621 `license-files` and Notice/Licenses URLs while preserving version 1.2.0 freeze.
- Added automated metadata and documentation parity contract tests in `tests/test_metadata.py` (7 tests).
- Updated `llms.txt` header to `Last-checked: 2026-09-22` with 27/27 passing test suite verification notes.
- Performed technical hygiene check: fixed 16 ruff lint errors in `chess.py`, `chess_analyze.py`, and `tests/test_bugsweep_regressions.py` (inline semicolons/colons, unused imports/variables).
- Updated `llms.txt` header to `Last-checked: 2026-07-27` with 20/20 passing test suite verification notes.
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
