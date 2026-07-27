"""
Tactics analyser for Claude Code Chess (training / debug tool).

This tool is intended for training and position analysis.
It is NOT used automatically during regular play -- both players
receive the same hints via chess_settings.json.

Usage:
  python chess_analyze.py                    Current position + top moves
  python chess_analyze.py e4e3              Board after move e4-e3
  python chess_analyze.py e4e3 d1d3 f7f5   Board after a sequence of moves
  python chess_analyze.py --depth 4         Set search depth (default: 3)
  python chess_analyze.py --top 8           Show more candidate moves
"""

import sys
import os
import json
import copy

# chess.py aus dem gleichen Verzeichnis importieren
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chess import (
    make_move, get_legal_moves, minimax,
    in_check, is_white, update_castling_rights, order_moves,
    INITIAL_BOARD, PROMOTION_CHOICES
)

COMM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_comm")
REQUEST_FILE = os.path.join(COMM_DIR, "chess_request.json")

PIECE_NAMES = {
    "K": "König", "Q": "Dame", "R": "Turm",
    "B": "Läufer", "N": "Springer", "P": "Bauer",
}

# -----------------------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------------------

def uci_to_coords(uci):
    """Convert UCI text to coordinates plus an optional promotion suffix."""
    if len(uci) not in (4, 5):
        return None
    try:
        fc = ord(uci[0].lower()) - ord('a')
        fr = 8 - int(uci[1])
        tc = ord(uci[2].lower()) - ord('a')
        tr = 8 - int(uci[3])
    except (ValueError, IndexError):
        return None
    promo = None
    if len(uci) == 5:
        promo = uci[4].lower()
        if promo not in PROMOTION_CHOICES:
            return None
    if all(0 <= x <= 7 for x in [fr, fc, tr, tc]):
        return (fr, fc, tr, tc, promo)
    return None


def coords_to_uci(fr, fc, tr, tc, promo=None):
    move = chr(ord('a') + fc) + str(8 - fr) + chr(ord('a') + tc) + str(8 - tr)
    if promo:
        move += promo.lower()
    return move


def apply_uci(board, uci, ep_target, castling_rights):
    """Apply a UCI move and return (new_board, new_ep, new_castling_rights)."""
    coords = uci_to_coords(uci)
    if not coords:
        return None, ep_target, castling_rights
    fr, fc, tr, tc, promo = coords
    piece = board[fr][fc]
    new_ep = None
    if piece and piece.upper() == "P" and abs(fr - tr) == 2:
        new_ep = ((fr + tr) // 2, fc)
    new_cr = set(castling_rights)
    if piece:
        update_castling_rights(new_cr, piece, fr, fc, tr, tc)
    new_board = make_move(board, fr, fc, tr, tc, ep_target, promo)
    return new_board, new_ep, new_cr


def replay_history(move_history):
    """Replay the move history and return (board, white_turn, ep_target, castling_rights)."""
    board = copy.deepcopy(INITIAL_BOARD)
    white_turn = True
    ep_target = None
    castling_rights = {"K", "Q", "k", "q"}
    for uci in move_history:
        new_board, ep_target, castling_rights = apply_uci(board, uci, ep_target, castling_rights)
        if new_board:
            board = new_board
        white_turn = not white_turn
    return board, white_turn, ep_target, castling_rights


def material_balance(board):
    """Calculate material balance for both sides."""
    white = {}
    black = {}
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == ".":
                continue
            key = p.upper()
            if key == "K":
                continue
            if is_white(p):
                white[key] = white.get(key, 0) + 1
            else:
                black[key] = black.get(key, 0) + 1
    return white, black


def material_score(board):
    vals = {"Q": 9, "R": 5, "B": 3, "N": 3, "P": 1}
    w, b = material_balance(board)
    ws = sum(vals.get(k, 0) * v for k, v in w.items())
    bs = sum(vals.get(k, 0) * v for k, v in b.items())
    return ws, bs


def fmt_pieces(d):
    order = ["Q", "R", "B", "N", "P"]
    parts = []
    for k in order:
        if k in d:
            parts.append("{}x{}".format(d[k], k))
    return " ".join(parts) if parts else "(keine)"


def draw_board(board, highlight_moves=None, last_move=None):
    """Render the board as ASCII art."""
    HL = set(highlight_moves) if highlight_moves else set()
    LM = set()
    if last_move:
        coords = uci_to_coords(last_move)
        if coords:
            fr, fc, tr, tc, _ = coords
            LM = {(fr, fc), (tr, tc)}

    print("  +--+--+--+--+--+--+--+--+")
    for r in range(8):
        rank = 8 - r
        row = " {} |".format(rank)
        for c in range(8):
            p = board[r][c]
            cell = p if p != "." else " "
            marker = ""
            if (r, c) in HL:
                marker = "*"
            elif (r, c) in LM:
                marker = ">"
            else:
                marker = " "
            row += "{}{}|".format(marker, cell)
        print(row)
        print("  +--+--+--+--+--+--+--+--+")
    print("    a  b  c  d  e  f  g  h")
    print()


def piece_at(board, uci_sq):
    """Return the piece on a given square (e.g. 'e4')."""
    c = ord(uci_sq[0]) - ord('a')
    r = 8 - int(uci_sq[1])
    return board[r][c]


# -----------------------------------------------------------------------
# Kern-Analyse
# -----------------------------------------------------------------------

def analyze_candidates(board, white, ep_target, castling_rights, depth=3, top_n=6):
    """Evaluate all legal moves with minimax and return a sorted candidate list."""
    legal = get_legal_moves(board, white, ep_target, castling_rights)
    if not legal:
        return []

    legal = order_moves(board, legal, white)
    results = []

    for fr, fc, tr, tc in legal:
        piece = board[fr][fc]
        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)
        new_cr = set(castling_rights)
        update_castling_rights(new_cr, piece, fr, fc, tr, tc)
        new_board = make_move(board, fr, fc, tr, tc, ep_target)

        # Aus Sicht des Gegners minimaxen, dann Vorzeichen anpassen
        opp_white = not white
        score = minimax(new_board, depth - 1, -999999, 999999,
                        opp_white, new_ep, new_cr)

        uci = coords_to_uci(fr, fc, tr, tc)
        captured = board[tr][tc]
        results.append((score, uci, fr, fc, tr, tc, captured, piece))

    # Schwarz maximiert negative Werte (Schwarz will niedrigen Score)
    results.sort(key=lambda x: x[0], reverse=white)
    return results[:top_n]


def print_candidates(results, board, white):
    """Print the candidate move list in a formatted layout."""
    sign = 1 if white else -1
    print("  Rang  Zug    Eval   Figur  Schlägt")
    print("  " + "-" * 50)
    for i, (score, uci, fr, fc, tr, tc, captured, piece) in enumerate(results, 1):
        eval_str = "{:+.0f}".format(score * sign)
        cap_str = ""
        if captured != ".":
            cap_str = "x{}({})".format(captured.upper(), PIECE_NAMES.get(captured.upper(), "?"))
        pname = PIECE_NAMES.get(piece.upper(), "?")
        check_mark = ""
        new_board = make_move(board, fr, fc, tr, tc)
        if in_check(new_board, not white):
            check_mark = " +"
        print("  [{:2d}]  {}{}   {:>6}  {:8}  {}".format(
            i, uci, check_mark, eval_str, pname, cap_str))
    print()


# -----------------------------------------------------------------------
# Hauptprogramm
# -----------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    depth = 3
    top_n = 6
    move_args = []

    i = 0
    while i < len(args):
        if args[i] == "--depth" and i + 1 < len(args):
            try:
                depth = int(args[i + 1])
            except ValueError:
                print("Fehler: --depth erwartet eine ganze Zahl, nicht '{}'.".format(args[i + 1]))
                sys.exit(1)
            i += 2
        elif args[i] == "--top" and i + 1 < len(args):
            try:
                top_n = int(args[i + 1])
            except ValueError:
                print("Fehler: --top erwartet eine ganze Zahl, nicht '{}'.".format(args[i + 1]))
                sys.exit(1)
            i += 2
        else:
            move_args.append(args[i])
            i += 1

    # Aktuelle Position laden
    try:
        with open(REQUEST_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Fehler: {} nicht gefunden.".format(REQUEST_FILE))
        sys.exit(1)
    except (json.JSONDecodeError, OSError) as e:
        print("Fehler beim Lesen von {}: {}".format(REQUEST_FILE, e))
        sys.exit(1)

    move_history = data.get("move_history", [])
    board, white_turn, ep_target, castling_rights = replay_history(move_history)
    color_str = "Weiß" if white_turn else "Schwarz"

    print()
    print("=" * 60)
    print("  TAKTIK-ANALYZER  |  {} ist dran  |  Tiefe: {}".format(color_str, depth))
    print("=" * 60)

    # Zuggeschichte anzeigen
    if move_history:
        hist_pairs = []
        for j in range(0, len(move_history), 2):
            w = move_history[j]
            b = move_history[j + 1] if j + 1 < len(move_history) else "..."
            hist_pairs.append("{}.{}/{}".format(j // 2 + 1, w, b))
        print("  Zugfolge: {}".format("  ".join(hist_pairs)))
    print()

    # Brett der aktuellen Position zeichnen
    print("  -- AKTUELLE POSITION --")
    draw_board(board, last_move=move_history[-1] if move_history else None)

    # Materialstand
    ws, bs = material_score(board)
    wm, bm = material_balance(board)
    diff = ws - bs
    diff_str = "(+{} Weiß)".format(diff) if diff > 0 else ("({} Schwarz)".format(-diff) if diff < 0 else "(ausgeglichen)")
    print("  Material:")
    print("    Weiß: {} = {} Punkte".format(fmt_pieces(wm), ws))
    print("    Schwarz: {} = {} Punkte".format(fmt_pieces(bm), bs))
    print("    Bilanz: {}".format(diff_str))
    print()

    # Schach?
    if in_check(board, white_turn):
        print("  *** SCHACH! ***")
        print()

    # Optionale Zugfolge aus Kommandozeile anwenden
    sim_board = copy.deepcopy(board)
    sim_ep = ep_target
    sim_cr = set(castling_rights)
    sim_white = white_turn

    if move_args:
        print("  -- VARIANTEN-ANALYSE --")
        for uci in move_args:
            coords = uci_to_coords(uci)
            if not coords:
                print("  Ungültiger Zug: {}".format(uci))
                continue
            fr, fc, tr, tc, _ = coords
            piece = sim_board[fr][fc]
            if piece == ".":
                print("  Kein Stein auf {}: {}".format(uci[:2], uci))
                continue
            pname = PIECE_NAMES.get(piece.upper(), "?")
            captured = sim_board[tr][tc]
            cap_str = " x{}".format(captured) if captured != "." else ""
            who = "Weiß" if sim_white else "Schwarz"
            print("  Zug: {} {} {}{}".format(who, pname, uci, cap_str))

            sim_board, sim_ep, sim_cr = apply_uci(sim_board, uci, sim_ep, sim_cr)
            sim_white = not sim_white

            draw_board(sim_board, last_move=uci)
            sim_ws, sim_bs = material_score(sim_board)
            sim_diff = sim_ws - sim_bs
            sim_diff_str = "(+{} Weiß)".format(sim_diff) if sim_diff > 0 else ("({} Schwarz)".format(-sim_diff) if sim_diff < 0 else "(ausgeglichen)")
            print("  Material nach Zug: Weiß {} | Schwarz {} | {}".format(sim_ws, sim_bs, sim_diff_str))
            if in_check(sim_board, sim_white):
                print("  *** SCHACH! ***")
            print()

    # Kandidaten-Züge bewerten
    print("  -- TOP {} KANDIDATEN ({} ist dran, Tiefe {}) --".format(
        top_n, "Weiß" if sim_white else "Schwarz", depth))
    print("  Bitte warten...")
    candidates = analyze_candidates(sim_board, sim_white, sim_ep, sim_cr, depth, top_n)
    if candidates:
        print_candidates(candidates, sim_board, sim_white)
        best = candidates[0]
        print("  => Empfehlung: {} ({})".format(
            best[1], PIECE_NAMES.get(best[7].upper(), "?")))
    else:
        print("  Keine legalen Züge!")
    print("=" * 60)


if __name__ == "__main__":
    main()
