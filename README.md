# ChatAndChess

[![ChatAndChess tests](https://github.com/entertain-and-more/ChatAndChess/actions/workflows/tests.yml/badge.svg)](https://github.com/entertain-and-more/ChatAndChess/actions/workflows/tests.yml)

Terminal-Schach für lokale Partien, Minimax-Bot, Claude API und Claude-Code-Integration.
Terminal chess for local games, a Minimax bot, Claude API mode, and Claude Code integration.

## Screenshot

![ChatAndChess Gameplay](README/screenshots/gameplay.jpg)

## Funktionen / Features

- **4 Spielmodi / 4 game modes**
  - **2 Player**: lokales Hotseat-Spiel auf einem Rechner
  - **vs Bot**: Minimax-Engine mit einstellbarer Suchtiefe (1-5)
  - **vs Claude API**: optionales Spiel gegen Claude über die Anthropic API
  - **vs Claude Code**: dateibasierte Worker-Kommunikation für Claude Code
    inklusive stabiler Rochade- und En-passant-Zustände im Worker-JSON
- **Vollständige Schachregeln / Full chess rules**
  - Rochade, en passant, Bauernumwandlung, Schach, Matt und Patt
- **Engine-Hilfen / Engine hints**
  - Gleichzug-Modus: beide Seiten sehen Engine-Hinweise
  - Engine-Modus: nur die KI sieht Hinweise
  - Training-Modus: nur der Mensch sieht Hinweise
  - Mensch-Modus: keine Hinweise
- **Analyse / Analysis**
  - Piece-square tables, Alpha-Beta-Pruning und eigenständiger Taktik-Analyzer

## Voraussetzungen / Requirements

- Python 3.10+
- Keine externen Abhängigkeiten für das Basisspiel
- Optional: Paket `anthropic` für den Claude-API-Modus

```bash
pip install -r requirements.txt
```

## Start / Quick Start

```bash
# Spiel starten / start game
python chess.py

# Windows-Starter
START_CHESS.bat

# Worker-Modus für Claude Code
python chess.py --worker
```

## Spielweise / How to Play

Züge werden in UCI-Notation eingegeben: `e2e4` (Startfeld zu Zielfeld).
Moves use UCI notation: `e2e4` (from-square to-square).

- Normale Züge: `e2e4`, `g1f3`
- Rochade: `e1g1` oder `e1c1`
- Bauernumwandlung: Beim Erreichen der letzten Reihe fragt das Programm nach der Figur.

## Taktik-Analyzer / Tactics Analyzer

```bash
# Aktuelle Position analysieren
python chess_analyze.py

# Eigene Suchtiefe
python chess_analyze.py --depth 4

# Zugfolge analysieren
python chess_analyze.py e2e4 e7e5 g1f3

# Mehr Kandidatenzüge anzeigen
python chess_analyze.py --top 8
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile chess.py chess_analyze.py
python tests/source_platform_smoke.py
```

## Datenschutz / Privacy

ChatAndChess speichert Spiel- und Worker-Laufzeitdaten lokal. API-Schlüssel gehören in die
Umgebungsvariable `ANTHROPIC_API_KEY` oder in eine lokale Home-Datei, aber nicht in dieses
Repository.

ChatAndChess keeps runtime data local. API keys belong in the `ANTHROPIC_API_KEY`
environment variable or a local home-directory key file, never in this repository.

Diese lokalen Dateien werden ignoriert / ignored local files:

- `.env`, `.env.*`, `.anthropic_key`, credential and token files
- `chess_settings.json`
- `CLAUDE_PROMPT.txt`
- `chess_comm/`
- `AUFGABEN.txt`, `TEST.txt`, `TESTS.txt`, `TESTERGEBNISSE.txt`
- build outputs such as `build/`, `dist/`, `*.exe`, `*.msi`, and `*.msix`
- local database/cache outputs such as `*.db`, `*.sqlite*`, `.pytest_cache/`, and `htmlcov/`

## Projektstruktur / Project Structure

```
chess.py              Main game (all modes, engine, rules)
chess_analyze.py      Tactics analyzer (position evaluation, candidate moves)
START_CHESS.bat       Windows launcher
build_exe.bat         Optional PyInstaller build helper for Windows
requirements.txt      Base/optional dependency notes
tests/source_platform_smoke.py
                     Platform smoke for menu quit, worker boot, and analyzer (Linux + macOS)
README/screenshots/   Repository screenshots used by the README
chess_comm/           Runtime communication directory (gitignored)
chess_settings.json   Local game settings (gitignored)
```

## License

[MIT](LICENSE)

## Community Docs

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)
- [LLM context](llms.txt)

---

## English Summary

ChatAndChess is a terminal-based chess game written in Python. Play against a friend locally, challenge a built-in Minimax bot, or face Claude AI through the Anthropic API or Claude Code file-based integration. Features full chess rules, positional evaluation, and a standalone tactics analyzer.

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus MIT.

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.

