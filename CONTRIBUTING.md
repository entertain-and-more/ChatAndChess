# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für Ihr Interesse an Beiträgen zu ChatAndChess.

### Beiträge

- Fehler bitte über GitHub Issues mit einer kurzen Reproduktion melden
- Verbesserungen an Engine, Spielregeln, UI-Texten oder Doku sind willkommen
- Kleine, klar abgegrenzte Pull Requests sind bevorzugt

### Lokaler Start

```bash
python chess.py
```

Der Analyzer erwartet eine laufende Claude-Code-Partie mit
`chess_comm/chess_request.json`:

```bash
python chess_analyze.py --depth 3
```

Optional für den Claude-API-Modus:

```bash
pip install -r requirements.txt
```

### Richtlinien

- Python-Code bitte lesbar und möglichst ohne unnötige Abhängigkeiten halten
- Keine API-Keys, lokalen Prompt-Dateien oder privaten Testdaten committen
- Bestehende Spielmodi nicht stillschweigend im Verhalten ändern
- Änderungen an Spielregeln immer im README dokumentieren

---

## English

Thank you for your interest in contributing to ChatAndChess.

### Contributions

- Report bugs through GitHub Issues with a short reproduction path
- Improvements to the engine, rules, UX text, or documentation are welcome
- Prefer small, focused pull requests

### Local Run

```bash
python chess.py
```

The analyzer expects an active Claude Code game with
`chess_comm/chess_request.json`:

```bash
python chess_analyze.py --depth 3
```

Optional for Claude API mode:

```bash
pip install -r requirements.txt
```

### Guidelines

- Keep Python code readable and avoid unnecessary dependencies
- Do not commit API keys, local prompt files, or private test data
- Do not change gameplay behavior silently across modes
- Document rule or UX changes in the README
