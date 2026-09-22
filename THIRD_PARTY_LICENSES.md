# Third-Party Licenses & Level 1 SBOM Inventory

**Project:** `ChatAndChess` (Terminal Chess, Minimax Bot, Claude API & Claude Code Worker Integration)
**License:** [MIT License](LICENSE)
**Audit Date:** 2026-09-22
**Repository:** [entertain-and-more/ChatAndChess](https://github.com/entertain-and-more/ChatAndChess)
**Organization:** [entertain-and-more](https://github.com/entertain-and-more)
**Umbrella Ecosystem:** [open-bricks](https://github.com/open-bricks)

---

## Runtime Architecture & Zero-Dependency Core

`ChatAndChess` is an offline-first, terminal-based chess application engineered in pure Python 3.10+. The core game loop, move generation, rules engine (castling, en passant, promotion, checkmate detection), Minimax bot engine with alpha-beta pruning, and file-based Claude Code worker IPC require **zero external dependencies**.

### Core Engine & Runtime

| Component / Library | Version / Scope | License | Type | Purpose |
|---|---|---|---|---|
| **Python Standard Library** | `>=3.10` | PSFL-2.0 | Core Runtime | Built-in modules: `math`, `json`, `os`, `sys`, `time`, `random`, `copy`, `subprocess`. Zero network calls, zero telemetry. |
| **Terminal ANSI / UTF-8 Console** | Native Terminal | Public Standard | Presentation | Standard terminal rendering for chess board, notation, and move history on Windows, Linux, and macOS. |

---

## Optional Runtime Dependencies (Opt-In)

The following packages are strictly optional and only loaded when explicitly invoking the corresponding feature mode:

| Component / Package | Version / Constraint | License | Project URL | Purpose |
|---|---|---|---|---|
| **`anthropic`** | `>=0.18.0` | MIT | [anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) | Used exclusively for the optional `vs Claude API` game mode when configured with an API key. |
| **`PySide6`** | `>=6.5.0` | LGPL-3.0 (dynamic) | [pyside/pyside-setup](https://wiki.qt.io/Qt_for_Python) | Optional GUI presentation extension hook (dynamic linking, unbundled). |

---

## Development, Testing & Verification Dependencies

The following tools are used strictly in development environments, static analysis, and CI automation pipelines:

| Tool / Framework | Version / Scope | License | Project URL | Purpose |
|---|---|---|---|---|
| **Python unittest** | Built-in (3.10+) | PSFL-2.0 | [python.org](https://docs.python.org/3/library/unittest.html) | Native unit test suite execution without external packages. |
| **pytest** | `>=7.0` | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Alternative automated test runner for local testing. |
| **Ruff** | `>=0.6.0` | MIT / Apache-2.0 | [astral-sh/ruff](https://github.com/astral-sh/ruff) | High-performance Python code style enforcement and linter. |

---

## Zero-Copyleft Guarantee & Unprivileged Execution

- **Zero-Copyleft Guarantee:** All game logic, bot algorithms, tactics evaluation routines, and worker IPC handlers in this repository are governed strictly by the permissive [MIT License](LICENSE). No GPL, AGPL, or viral copyleft code is bundled into the distribution.
- **Unprivileged User Mode (`RunAsInvoker`):** All execution paths (`python chess.py`, `python chess_analyze.py`, `python chess.py --worker`) operate strictly in user space. No administrative privileges, root permissions, or service registrations are ever required.

---

## Governance & Runtime Invariants

`ChatAndChess` adheres to ten foundational governance and runtime invariants:

| Invariant | Category | Description | Verification Method |
|---|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero Egress | Base game and worker operate 100% offline with zero outbound network calls. | `tests/source_platform_smoke.py` & `SECURITY.md` |
| `INV-RUNAS-02` | Unprivileged User Mode | Executables and scripts run under unprivileged user accounts (`RunAsInvoker`). | `START_CHESS.bat` & `SECURITY.md` |
| `INV-STATE-03` | Stateless Worker IPC | Worker communication uses discrete JSON files with full legal move and state context. | `tests/test_worker_state.py` |
| `INV-RULES-04` | Full FIDE Rule Compliance | Castling rights, en passant targets, promotion, checkmate, and stalemate are fully verified. | `tests/test_bugsweep_regressions.py` |
| `INV-EXPORT-05` | Portable Export Architecture | FEN and `chatandchess-game-v1.json` export support without proprietary cloud tie-in. | `tests/test_export.py` & `EXPORTFORMAT.md` |
| `INV-DEPS-06` | Zero Mandatory Dependencies | The terminal game runs on any standard Python 3.10+ installation without `pip install`. | `pyproject.toml` & `requirements.txt` |
| `INV-BOUND-07` | Bounded Engine Search | Minimax bot operates within user-defined depth limits (1–5) with alpha-beta pruning. | `chess.py` (`bot_choose_move`) |
| `INV-PRIV-08` | Privacy & Secret Quarantine | API keys, runtime communication tokens, and settings are strictly gitignored. | `.gitignore` & `SECURITY.md` |
| `INV-DOCS-09` | Bilingual Documentation Parity | Complete feature parity between English (`README.md`) and German (`README_de.md`). | `tests/test_metadata.py` |
| `INV-SLA-10` | 48-Hour Security Response SLA | Security vulnerability reports receive an initial response within 48 hours. | `SECURITY.md` |
