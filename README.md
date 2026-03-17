# ChatAndChess

Play chess against your personal AI -- or with a friend. Text-based terminal game with multiple opponent modes.

## Screenshot

```
  ============================================
     CHAT AND CHESS  |  Terminal Edition
  ============================================

    [1]  2 Spieler (lokal)
    [2]  Spieler vs Bot (Minimax)
    [3]  Spieler vs Claude (API)
    [4]  Spieler vs Claude Code (Datei-Link)

  Auswahl: 2

  [vs Bot (Tiefe 3)]
  +--+--+--+--+--+--+--+--+
 8 | r|  | b| q|  | r| k|  |
  +--+--+--+--+--+--+--+--+
 7 | p| p| p|  |  | p| p| p|
  +--+--+--+--+--+--+--+--+
 6 |  |  | n|  |  | n|  |  |
  +--+--+--+--+--+--+--+--+
 5 |  |  |  | p| p|  |  |  |
  +--+--+--+--+--+--+--+--+
 4 |  |  | B|  | P|  |  |  |
  +--+--+--+--+--+--+--+--+
 3 |  |  |  |  |  | N|  |  |
  +--+--+--+--+--+--+--+--+
 2 | P| P| P| P|  | P| P| P|
  +--+--+--+--+--+--+--+--+
 1 | R| N| B| Q| K|  |  | R|
  +--+--+--+--+--+--+--+--+
    a  b  c  d  e  f  g  h

  Weiss ist dran. Zug (z.B. e2e4): _
```

## Features

- **4 Game Modes:**
  - **2 Player** -- Local hotseat, play with a friend on the same machine
  - **vs Bot** -- Minimax engine with configurable search depth (1-5)
  - **vs Claude API** -- Play against Claude AI via Anthropic API
  - **vs Claude Code** -- File-based communication for Claude Code integration
- **Full chess rules** -- Castling, en passant, pawn promotion, check/checkmate/stalemate detection
- **Piece-square tables** -- Positional evaluation for smarter bot play
- **Alpha-beta pruning** -- Efficient search with move ordering
- **Tactics Analyzer** -- Standalone tool for position analysis and move evaluation
- **Configurable hint modes:**
  - Gleichzug-Modus (both players see engine hints)
  - Engine-Modus (only AI sees hints)
  - Training-Modus (only human sees hints)
  - Mensch-Modus (no hints for anyone)

## Requirements

- Python 3.10+
- No external dependencies for base game
- Optional: `anthropic` package for Claude API mode (`pip install anthropic`)

## Quick Start

```bash
# Start the game
python chess.py

# Or use the launcher (Windows)
START_CHESS.bat

# Start in worker mode (for Claude Code integration)
python chess.py --worker
```

## How to Play

Enter moves in UCI notation: `e2e4` (from-square to-square).

Special commands during play:
- Type a move like `e2e4`, `g1f3`, `e1g1` (castling)
- Pawn promotion: move to last rank and you will be prompted

## Tactics Analyzer

```bash
# Analyze current position
python chess_analyze.py

# Analyze with custom depth
python chess_analyze.py --depth 4

# Analyze a sequence of moves
python chess_analyze.py e2e4 e7e5 g1f3

# Show more candidate moves
python chess_analyze.py --top 8
```

## Project Structure

```
chess.py              Main game (all modes, engine, rules)
chess_analyze.py      Tactics analyzer (position evaluation, candidate moves)
START_CHESS.bat       Windows launcher
chess_comm/           Communication directory for Claude Code mode
chess_settings.json   Game settings (hint mode, depth, etc.)
```

## License

MIT

---

## English Summary

ChatAndChess is a terminal-based chess game written in Python. Play against a friend locally, challenge a built-in Minimax bot, or face Claude AI through the Anthropic API or Claude Code file-based integration. Features full chess rules, positional evaluation, and a standalone tactics analyzer.
