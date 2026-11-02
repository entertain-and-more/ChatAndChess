"""ASCII chess game -- 2-player, bot, Claude-API, and Claude-Code mode."""

import copy
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

__version__ = "1.2.0"

PIECES = {
    "K": "\u265a", "Q": "\u265b", "R": "\u265c",
    "B": "\u265d", "N": "\u265e", "P": "\u265f",
    "k": "\u2654", "q": "\u2655", "r": "\u2656",
    "b": "\u2657", "n": "\u2658", "p": "\u2659",
}

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}

PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
PST_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
PST_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
PST_ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]
PST_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
PST_KING = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PST = {"P": PST_PAWN, "N": PST_KNIGHT, "B": PST_BISHOP,
       "R": PST_ROOK, "Q": PST_QUEEN, "K": PST_KING}

INITIAL_BOARD = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]

# Kommunikationspfad für Claude-Code Modus
COMM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_comm")
REQUEST_FILE = os.path.join(COMM_DIR, "chess_request.json")
RESPONSE_FILE = os.path.join(COMM_DIR, "chess_response.json")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_settings.json")
PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CLAUDE_PROMPT.txt")

PIECE_NAMES_DE = {
    "K": "König", "Q": "Dame", "R": "Turm",
    "B": "Läufer", "N": "Springer", "P": "Bauer",
}

PROMOTION_CHOICES = ("q", "r", "b", "n")


def load_settings():
    """Load settings from chess_settings.json."""
    defaults = {
        "show_hints": False,
        "top_n": 5,
        "hint_depth": 2,
        "show_recommendation": False,
        "claude_uses_engine": False,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def generate_session_prompt(settings=None):
    """Generate a prompt for Claude Code and save it to CLAUDE_PROMPT.txt."""
    if settings is None:
        settings = load_settings()

    uses_engine = settings.get("claude_uses_engine", False)
    show_hints = settings.get("show_hints", False)
    show_rec = settings.get("show_recommendation", False)
    top_n = settings.get("top_n", 5)
    depth = settings.get("hint_depth", 2)

    if uses_engine and show_hints:
        mode_name = "GLEICHZUG-MODUS (Beide sehen Engine-Hints)"
        claude_instr = (
            "Du siehst in chess_request.json das Feld 'top_moves' mit den Top-{} "
            "Zügen (Tiefe {}) -- dieselbe Liste sieht auch der menschliche Spieler "
            "im Terminal. Nutze diese als Orientierung, triff aber eigene "
            "Entscheidungen und begründe deinen Zug.".format(top_n, depth)
        )
    elif uses_engine and not show_hints:
        mode_name = "ENGINE-MODUS (Nur Claude sieht Engine-Hints -- NICHT FAIR)"
        claude_instr = (
            "Du siehst in chess_request.json das Feld 'top_moves'. "
            "Hinweis: Der menschliche Spieler sieht diese Hints NICHT. "
            "Überlege ob das fair ist."
        )
    elif not uses_engine and show_hints:
        mode_name = "TRAINING-MODUS (Nur Mensch sieht Hints, Claude spielt menschlich)"
        claude_instr = (
            "Spiele OHNE Engine-Unterstützung -- reines Reasoning und Intuition. "
            "Kein chess_analyze.py aufrufen. Der menschliche Spieler sieht Hints, "
            "du nicht. Das ist der Trainings-Modus für den Menschen."
        )
    else:
        mode_name = "MENSCH-MODUS (Keine Hints für beide)"
        claude_instr = (
            "Spiele OHNE Engine-Unterstützung -- reines Reasoning und Intuition. "
            "Kein chess_analyze.py aufrufen. Weder du noch der Mensch bekommen "
            "Engine-Hints. Fairer Wettbewerb auf Augenlinie."
        )

    rec_info = "JA" if show_rec else "NEIN"

    lines = [
        "=" * 60,
        "  CHESS -- CLAUDE CODE SESSION PROMPT",
        "=" * 60,
        "",
        "  Modus: {}".format(mode_name),
        "",
        "  Einstellungen (chess_settings.json):",
        "    show_hints          = {}".format(show_hints),
        "    show_recommendation = {} ({})".format(show_rec, rec_info),
        "    top_n               = {}".format(top_n),
        "    hint_depth          = {}".format(depth),
        "    claude_uses_engine  = {}".format(uses_engine),
        "",
        "  Anweisung für Claude:",
        "",
    ]
    for part in claude_instr.split(". "):
        lines.append("    " + part.strip() + ("." if not part.strip().endswith(".") else ""))
    lines += [
        "",
        "  Spielablauf:",
        "    1. chess_comm/chess_request.json lesen (Brett, legale Züge, History)",
        "    2. Zug auswählen und in chess_comm/chess_response.json schreiben:",
        '       {"move": "e2e4", "comment": "Begründung"}',
        '       Bei Bauernumwandlung z.B. {"move": "e7e8n", "comment": "..."}',
        "    3. Auf nächsten Request warten (du wirst vom User gerufen)",
        "",
        "  Einstellungen ändern: chess_settings.json bearbeiten,",
        "  dann 'python chess.py --prompt' für neuen Prompt.",
        "",
        "=" * 60,
    ]

    prompt_text = "\n".join(lines)
    try:
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(prompt_text)
    except OSError:
        pass
    return prompt_text


def compute_hints(board, white, en_passant_target, castling_rights, depth, top_n):
    """Calculate the top-N moves using a minimax evaluation."""
    legal = get_legal_moves(board, white, en_passant_target, castling_rights)
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
        new_board = make_move(board, fr, fc, tr, tc, en_passant_target)
        score = minimax(new_board, depth - 1, -999999, 999999,
                        not white, new_ep, new_cr)
        uci = "{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))
        captured = board[tr][tc]
        results.append((score, uci, piece, captured))
    results.sort(key=lambda x: x[0], reverse=white)
    return results[:top_n]


def display_hints(hints, white, show_recommendation):
    """Print hint moves to the terminal (for the human player)."""
    if not hints:
        return
    sign = 1 if white else -1
    print()
    print("  Tipp-Züge (Engine-Bewertung):")
    for i, (score, uci, piece, captured) in enumerate(hints, 1):
        eval_str = "{:+.0f}".format(score * sign)
        pname = PIECE_NAMES_DE.get(piece.upper(), "?")
        cap_str = ""
        if captured != ".":
            cap_str = " x{}".format(PIECE_NAMES_DE.get(captured.upper(), captured))
        print("  [{:2d}] {}   {:>6}   {}{}".format(i, uci, eval_str, pname, cap_str))
    if show_recommendation and hints:
        print("  => Empfehlung: {}".format(hints[0][1]))
    print()


# ---------------------------------------------------------------------------
# Basis-Funktionen
# ---------------------------------------------------------------------------

def is_white(piece):
    return piece.isupper()


def same_color(p1, p2):
    return (is_white(p1) and is_white(p2)) or (p1.islower() and p2.islower())


def can_capture_target(piece, target):
    """Kings are never a legal capture target in chess."""
    return target != "." and target.upper() != "K" and not same_color(piece, target)


def pos_to_str(row, col):
    return chr(ord("a") + col) + str(8 - row)


def render(board, white_turn, last_move=None, check=False, mode_info=""):
    os.system("cls" if sys.platform == "win32" else "clear")
    if mode_info:
        print("  [{}]".format(mode_info))
    print()
    print("     A   B   C   D   E   F   G   H")
    print("   +---+---+---+---+---+---+---+---+")
    for r in range(8):
        row_num = 8 - r
        cells = []
        for c in range(8):
            piece = board[r][c]
            if piece == ".":
                bg = "." if (r + c) % 2 == 0 else " "
                cells.append(" {} ".format(bg))
            else:
                symbol = PIECES.get(piece, piece)
                cells.append(" {} ".format(symbol))
        row_str = "|".join(cells)
        print(" {} |{}|".format(row_num, row_str))
        print("   +---+---+---+---+---+---+---+---+")
    print("     A   B   C   D   E   F   G   H")
    print()
    turn = "Weiß" if white_turn else "Schwarz"
    status = "  {} ist am Zug".format(turn)
    if check:
        status += " [SCHACH!]"
    print(status)
    if last_move:
        print("  Letzter Zug: {}".format(last_move))
    print()


def parse_pos(s):
    if len(s) != 2:
        return None
    col = ord(s[0].lower()) - ord("a")
    try:
        row = 8 - int(s[1])
    except ValueError:
        return None
    if 0 <= row <= 7 and 0 <= col <= 7:
        return (row, col)
    return None


def parse_move_text(text):
    """Parse UCI-style move text with an optional promotion suffix."""
    if len(text) not in (4, 5):
        return None
    src = parse_pos(text[:2])
    dst = parse_pos(text[2:4])
    if not src or not dst:
        return None
    promo = None
    if len(text) == 5:
        promo = text[4].lower()
        if promo not in PROMOTION_CHOICES:
            return None
    return (src[0], src[1], dst[0], dst[1], promo)


def move_to_uci(fr, fc, tr, tc, promo=None):
    """Format a move tuple as UCI text, preserving promotion info."""
    move = "{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))
    if promo:
        move += promo.lower()
    return move


def is_promotion_move(board, fr, fc, tr):
    """Return True when the move is a pawn promotion move."""
    piece = board[fr][fc]
    return piece != "." and piece.upper() == "P" and tr in (0, 7)


def expand_legal_moves(board, legal_moves):
    """Expand promotion moves into explicit q/r/b/n variants."""
    expanded = []
    for move in legal_moves:
        if len(move) == 4:
            fr, fc, tr, tc = move
            promo = None
        else:
            fr, fc, tr, tc, promo = move
        if promo is not None:
            expanded.append((fr, fc, tr, tc, promo.lower()))
        elif is_promotion_move(board, fr, fc, tr):
            for choice in PROMOTION_CHOICES:
                expanded.append((fr, fc, tr, tc, choice))
        else:
            expanded.append((fr, fc, tr, tc, None))
    return expanded


def prompt_for_promotion_choice(prompt_fn=input):
    """Ask the user which piece to promote to."""
    while True:
        try:
            choice = prompt_fn("  Bauernumwandlung (q/r/b/n, Enter=q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if not choice:
            return "q"
        if choice in PROMOTION_CHOICES:
            return choice
        print("  Bitte q, r, b oder n eingeben.")


def resolve_player_move(board, move_text, legal_moves, prompt_fn=input):
    """Resolve player input into a validated move tuple with promotion info."""
    parsed = parse_move_text(move_text)
    if parsed is None:
        return None
    fr, fc, tr, tc, promo = parsed
    if is_promotion_move(board, fr, fc, tr):
        if promo is None:
            promo = prompt_for_promotion_choice(prompt_fn)
            if promo is None:
                return None
    elif promo is not None:
        return None
    candidate = (fr, fc, tr, tc, promo)
    return candidate if candidate in legal_moves else None


def in_bounds(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7


# ---------------------------------------------------------------------------
# Zugberechnung
# ---------------------------------------------------------------------------

def get_raw_moves(board, r, c, en_passant_target=None, castling_rights=None):
    piece = board[r][c]
    if piece == ".":
        return []
    moves = []
    white = is_white(piece)
    p = piece.upper()

    if p == "P":
        direction = -1 if white else 1
        start_row = 6 if white else 1
        nr = r + direction
        if in_bounds(nr, c) and board[nr][c] == ".":
            moves.append((nr, c))
            nr2 = r + 2 * direction
            if r == start_row and board[nr2][c] == ".":
                moves.append((nr2, c))
        for dc in [-1, 1]:
            nc = c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if can_capture_target(piece, target):
                    moves.append((nr, nc))
                if en_passant_target and (nr, nc) == en_passant_target:
                    moves.append((nr, nc))

    elif p == "N":
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target == "." or can_capture_target(piece, target):
                    moves.append((nr, nc))

    elif p == "B":
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target == ".":
                    moves.append((nr, nc))
                elif can_capture_target(piece, target):
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif p == "R":
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target == ".":
                    moves.append((nr, nc))
                elif can_capture_target(piece, target):
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif p == "Q":
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                        (0, 1), (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target == ".":
                    moves.append((nr, nc))
                elif can_capture_target(piece, target):
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif p == "K":
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                        (0, 1), (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target == "." or can_capture_target(piece, target):
                    moves.append((nr, nc))
        if castling_rights:
            back_row = 7 if white else 0
            if r == back_row and c == 4:
                key_k = "K" if white else "k"
                key_q = "Q" if white else "q"
                if key_k in castling_rights:
                    if (board[back_row][5] == "."
                            and board[back_row][6] == "."):
                        rook = "R" if white else "r"
                        if board[back_row][7] == rook:
                            if (not is_square_attacked(board, back_row, 4, not white)
                                    and not is_square_attacked(board, back_row, 5, not white)
                                    and not is_square_attacked(board, back_row, 6, not white)):
                                moves.append((back_row, 6))
                if key_q in castling_rights:
                    if (board[back_row][3] == "."
                            and board[back_row][2] == "."
                            and board[back_row][1] == "."):
                        rook = "R" if white else "r"
                        if board[back_row][0] == rook:
                            if (not is_square_attacked(board, back_row, 4, not white)
                                    and not is_square_attacked(board, back_row, 3, not white)
                                    and not is_square_attacked(board, back_row, 2, not white)):
                                moves.append((back_row, 2))
    return moves


def is_square_attacked(board, r, c, by_white):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece == ".":
                continue
            if is_white(piece) != by_white:
                continue
            p = piece.upper()
            if p == "P":
                direction = -1 if by_white else 1
                if row + direction == r and abs(col - c) == 1:
                    return True
            elif p == "N":
                dr, dc = abs(row - r), abs(col - c)
                if sorted([dr, dc]) == [1, 2]:
                    return True
            elif p == "B":
                if abs(row - r) == abs(col - c) and abs(row - r) > 0:
                    dr = 1 if r > row else -1
                    dc_s = 1 if c > col else -1
                    nr, nc = row + dr, col + dc_s
                    blocked = False
                    while (nr, nc) != (r, c):
                        if board[nr][nc] != ".":
                            blocked = True
                            break
                        nr += dr
                        nc += dc_s
                    if not blocked:
                        return True
            elif p == "R":
                if row == r or col == c:
                    if row == r:
                        step = 1 if c > col else -1
                        blocked = False
                        for cc in range(col + step, c, step):
                            if board[row][cc] != ".":
                                blocked = True
                                break
                        if not blocked:
                            return True
                    else:
                        step = 1 if r > row else -1
                        blocked = False
                        for rr in range(row + step, r, step):
                            if board[rr][col] != ".":
                                blocked = True
                                break
                        if not blocked:
                            return True
            elif p == "Q":
                if row == r or col == c:
                    if row == r:
                        step = 1 if c > col else -1
                        blocked = False
                        for cc in range(col + step, c, step):
                            if board[row][cc] != ".":
                                blocked = True
                                break
                        if not blocked:
                            return True
                    else:
                        step = 1 if r > row else -1
                        blocked = False
                        for rr in range(row + step, r, step):
                            if board[rr][col] != ".":
                                blocked = True
                                break
                        if not blocked:
                            return True
                if abs(row - r) == abs(col - c) and abs(row - r) > 0:
                    dr = 1 if r > row else -1
                    dc_s = 1 if c > col else -1
                    nr, nc = row + dr, col + dc_s
                    blocked = False
                    while (nr, nc) != (r, c):
                        if board[nr][nc] != ".":
                            blocked = True
                            break
                        nr += dr
                        nc += dc_s
                    if not blocked:
                        return True
            elif p == "K":
                if abs(row - r) <= 1 and abs(col - c) <= 1 and (row, col) != (r, c):
                    return True
    return False


def find_king(board, white):
    king = "K" if white else "k"
    for r in range(8):
        for c in range(8):
            if board[r][c] == king:
                return (r, c)
    return None


def in_check(board, white):
    pos = find_king(board, white)
    if pos is None:
        return False
    kr, kc = pos
    return is_square_attacked(board, kr, kc, not white)


def make_move(board, fr, fc, tr, tc, en_passant_target=None, promo=None):
    new_board = copy.deepcopy(board)
    piece = new_board[fr][fc]
    captured = new_board[tr][tc]

    if (piece.upper() == "P" and en_passant_target
            and (tr, tc) == en_passant_target and captured == "."):
        new_board[fr][tc] = "."

    if piece.upper() == "K" and abs(fc - tc) == 2:
        if tc == 6:
            new_board[fr][5] = new_board[fr][7]
            new_board[fr][7] = "."
        elif tc == 2:
            new_board[fr][3] = new_board[fr][0]
            new_board[fr][0] = "."

    new_board[tr][tc] = piece
    new_board[fr][fc] = "."

    if piece.upper() == "P" and (tr == 0 or tr == 7):
        if promo:
            new_board[tr][tc] = promo.upper() if is_white(piece) else promo.lower()
        else:
            new_board[tr][tc] = "Q" if is_white(piece) else "q"

    return new_board


def get_legal_moves(board, white, en_passant_target=None, castling_rights=None):
    legal = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "." or is_white(piece) != white:
                continue
            raw = get_raw_moves(board, r, c, en_passant_target, castling_rights)
            for tr, tc in raw:
                new_board = make_move(board, r, c, tr, tc, en_passant_target)
                if not in_check(new_board, white):
                    legal.append((r, c, tr, tc))
    return legal


def update_castling_rights(cr, piece, fr, fc, tr, tc):
    if piece == "K":
        cr.discard("K")
        cr.discard("Q")
    elif piece == "k":
        cr.discard("k")
        cr.discard("q")
    elif piece == "R":
        if (fr, fc) == (7, 7):
            cr.discard("K")
        elif (fr, fc) == (7, 0):
            cr.discard("Q")
    elif piece == "r":
        if (fr, fc) == (0, 7):
            cr.discard("k")
        elif (fr, fc) == (0, 0):
            cr.discard("q")
    if (tr, tc) == (7, 7):
        cr.discard("K")
    elif (tr, tc) == (7, 0):
        cr.discard("Q")
    elif (tr, tc) == (0, 7):
        cr.discard("k")
    elif (tr, tc) == (0, 0):
        cr.discard("q")


def board_to_text(board):
    lines = []
    lines.append("  a b c d e f g h")
    for r in range(8):
        row_num = 8 - r
        row_chars = []
        for c in range(8):
            p = board[r][c]
            row_chars.append(p if p != "." else ".")
        lines.append("{} {}".format(row_num, " ".join(row_chars)))
    lines.append("  a b c d e f g h")
    lines.append("")
    lines.append("Großbuchstaben = Weiß, Kleinbuchstaben = Schwarz")
    lines.append("K=König Q=Dame R=Turm B=Läufer N=Springer P=Bauer")
    return "\n".join(lines)


def board_to_fen(board, white_to_move, castling_rights, en_passant_target,
                 halfmove=0, fullmove=1):
    """Return a FEN string for the given position."""
    ranks = []
    for row in range(8):
        empty = 0
        rank_str = ""
        for col in range(8):
            piece = board[row][col]
            if piece == ".":
                empty += 1
            else:
                if empty:
                    rank_str += str(empty)
                    empty = 0
                rank_str += piece
        if empty:
            rank_str += str(empty)
        ranks.append(rank_str)
    board_fen = "/".join(ranks)
    side = "w" if white_to_move else "b"
    castling_str = ""
    for flag in ("K", "Q", "k", "q"):
        if flag in castling_rights:
            castling_str += flag
    if not castling_str:
        castling_str = "-"
    if en_passant_target is not None:
        ep_row, ep_col = en_passant_target
        ep_str = chr(ord("a") + ep_col) + str(8 - ep_row)
    else:
        ep_str = "-"
    return f"{board_fen} {side} {castling_str} {ep_str} {halfmove} {fullmove}"


def move_to_san(board, fr, fc, tr, tc, promo=None, en_passant_target=None, castling_rights=None):
    """Return standard algebraic notation (SAN) for the specified move."""
    if castling_rights is None:
        castling_rights = set()
    piece = board[fr][fc]
    white = is_white(piece)
    piece_type = piece.upper()

    # 1. Castling
    if piece_type == "K":
        if tr == fr and tc == fc + 2:
            base = "O-O"
        elif tr == fr and tc == fc - 2:
            base = "O-O-O"
        else:
            base = None
        if base:
            next_board = make_move(board, fr, fc, tr, tc, en_passant_target, promo)
            next_cr = set(castling_rights)
            update_castling_rights(next_cr, piece, fr, fc, tr, tc)
            next_ep = None
            if in_check(next_board, not white):
                if not get_legal_moves(next_board, not white, next_ep, next_cr):
                    return base + "#"
                return base + "+"
            return base

    # 2. Pawn
    if piece_type == "P":
        if fc != tc:
            base = chr(ord("a") + fc) + "x" + pos_to_str(tr, tc)
        else:
            base = pos_to_str(tr, tc)
        if promo:
            base += "=" + promo.upper()
    else:
        # Piece move with disambiguation
        candidates = []
        for m in get_legal_moves(board, white, en_passant_target, castling_rights):
            cfr, cfc, ctr, ctc = m[:4]
            if (ctr, ctc) == (tr, tc) and (cfr, cfc) != (fr, fc) and board[cfr][cfc].upper() == piece_type:
                candidates.append((cfr, cfc))
        dis = ""
        if candidates:
            same_file = any(cfc == fc for cfr, cfc in candidates)
            same_rank = any(cfr == fr for cfr, cfc in candidates)
            if not same_file:
                dis = chr(ord("a") + fc)
            elif not same_rank:
                dis = str(8 - fr)
            else:
                dis = chr(ord("a") + fc) + str(8 - fr)
        cap = "x" if (board[tr][tc] != "." or (en_passant_target and (tr, tc) == en_passant_target)) else ""
        base = piece_type + dis + cap + pos_to_str(tr, tc)

    # 3. Check / Checkmate Suffix
    next_board = make_move(board, fr, fc, tr, tc, en_passant_target, promo)
    next_cr = set(castling_rights)
    update_castling_rights(next_cr, piece, fr, fc, tr, tc)
    next_ep = None
    if piece_type == "P" and abs(fr - tr) == 2:
        next_ep = ((fr + tr) // 2, fc)
    if in_check(next_board, not white):
        if not get_legal_moves(next_board, not white, next_ep, next_cr):
            return base + "#"
        return base + "+"
    return base


def format_pgn(san_moves, result="*", headers=None):
    """Format a list of SAN move strings into a standard PGN document."""
    if headers is None:
        headers = {}
    today_str = datetime.now().strftime("%Y.%m.%d")
    default_headers = [
        ("Event", headers.get("Event", "ChatAndChess Game")),
        ("Site", headers.get("Site", "Local")),
        ("Date", headers.get("Date", today_str)),
        ("Round", headers.get("Round", "1")),
        ("White", headers.get("White", "White")),
        ("Black", headers.get("Black", "Black")),
        ("Result", headers.get("Result", result)),
    ]
    lines = [f'[{k} "{v}"]' for k, v in default_headers]
    lines.append("")

    move_chunks = []
    for i in range(0, len(san_moves), 2):
        move_num = (i // 2) + 1
        w_move = san_moves[i]
        if i + 1 < len(san_moves):
            b_move = san_moves[i + 1]
            move_chunks.append(f"{move_num}. {w_move} {b_move}")
        else:
            move_chunks.append(f"{move_num}. {w_move}")

    if result:
        move_chunks.append(result)

    current_line = []
    current_len = 0
    for chunk in move_chunks:
        add_len = len(chunk) + (1 if current_line else 0)
        if current_len + add_len > 78:
            lines.append(" ".join(current_line))
            current_line = [chunk]
            current_len = len(chunk)
        else:
            current_line.append(chunk)
            current_len += add_len
    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines) + "\n"


def replay_moves_to_pgn(moves, event="ChatAndChess Game", site="Local", date=None,
                        round_num="1", white="Player", black="Bot", result=None):
    """Replay a list of UCI move strings, compute SAN and return formatted PGN."""
    board = copy.deepcopy(INITIAL_BOARD)
    white_turn = True
    castling_rights = {"K", "Q", "k", "q"}
    en_passant_target = None
    san_list = []

    for uci in moves:
        parsed = parse_move_text(uci)
        if not parsed:
            continue
        fr, fc, tr, tc, promo = parsed
        san = move_to_san(board, fr, fc, tr, tc, promo, en_passant_target, castling_rights)
        san_list.append(san)

        piece = board[fr][fc]
        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)
        update_castling_rights(castling_rights, piece, fr, fc, tr, tc)
        board = make_move(board, fr, fc, tr, tc, en_passant_target, promo)
        en_passant_target = new_ep
        white_turn = not white_turn

    if result is None:
        legal = get_legal_moves(board, white_turn, en_passant_target, castling_rights)
        if not legal:
            if in_check(board, white_turn):
                result = "1-0" if not white_turn else "0-1"
            else:
                result = "1/2-1/2"
        else:
            result = "*"

    headers = {
        "Event": event,
        "Site": site,
        "Round": round_num,
        "White": white,
        "Black": black,
        "Result": result,
    }
    if date:
        headers["Date"] = date
    return format_pgn(san_list, result=result, headers=headers)


def build_game_export(board, white, castling_rights, en_passant_target,
                      move_history, mode_kind="local", bot_depth=None,
                      include_san=False):
    """Return a chatandchess-game-v1.json compatible dict."""
    fen = board_to_fen(board, white, castling_rights, en_passant_target)
    castling_str = "".join(f for f in ("K", "Q", "k", "q") if f in castling_rights) or "-"
    ep_str = None
    if en_passant_target is not None:
        r, c = en_passant_target
        ep_str = chr(ord("a") + c) + str(8 - r)

    san_list = []
    if include_san and move_history:
        tmp_board = copy.deepcopy(INITIAL_BOARD)
        tmp_cr = {"K", "Q", "k", "q"}
        tmp_ep = None
        for uci in move_history:
            parsed = parse_move_text(uci)
            if parsed:
                p_fr, p_fc, p_tr, p_tc, p_pr = parsed
                san_val = move_to_san(tmp_board, p_fr, p_fc, p_tr, p_tc, p_pr, tmp_ep, tmp_cr)
                san_list.append(san_val)
                p_piece = tmp_board[p_fr][p_fc]
                p_new_ep = ((p_fr + p_tr) // 2, p_fc) if p_piece.upper() == "P" and abs(p_fr - p_tr) == 2 else None
                update_castling_rights(tmp_cr, p_piece, p_fr, p_fc, p_tr, p_tc)
                tmp_board = make_move(tmp_board, p_fr, p_fc, p_tr, p_tc, tmp_ep, p_pr)
                tmp_ep = p_new_ep
            else:
                san_list.append(None)

    moves = []
    for i, m in enumerate(move_history):
        by = "white" if i % 2 == 0 else "black"
        san_val = san_list[i] if i < len(san_list) else None
        moves.append({"uci": m, "san": san_val, "by": by})

    return {
        "schema": "chatandchess-game-v1",
        "app": "ChatAndChess",
        "position": {
            "fen": fen,
            "side_to_move": "white" if white else "black",
            "castling_rights": castling_str,
            "en_passant": ep_str,
        },
        "moves": moves,
        "mode": {
            "kind": mode_kind,
            "bot_depth": bot_depth,
            "hints_enabled": False,
        },
        "notes": [],
    }


def export_initial_game(filepath):
    """Export the starting position to a JSON file."""
    board = copy.deepcopy(INITIAL_BOARD)
    castling_rights = {"K", "Q", "k", "q"}
    data = build_game_export(board, True, castling_rights, None, [], mode_kind="local")
    target = Path(filepath)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Initial game exported to: {target}")


def export_pgn_cli(out_path, moves):
    """Replay moves and export the resulting game to a PGN file."""
    pgn_text = replay_moves_to_pgn(moves)
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(pgn_text)
    print(f"PGN exported ({len(moves)} moves) to: {target}")


def export_fen_cli(moves):
    """Replay moves and print the resulting FEN string."""
    board = copy.deepcopy(INITIAL_BOARD)
    white = True
    castling_rights = {"K", "Q", "k", "q"}
    en_passant_target = None
    halfmove = 0
    fullmove = 1
    for uci in moves:
        parsed = parse_move_text(uci)
        if not parsed:
            print(f"FEHLER: Ungültiger Zug: {uci}", file=sys.stderr)
            sys.exit(1)
        fr, fc, tr, tc, promo = parsed
        piece = board[fr][fc]
        target_piece = board[tr][tc]
        if piece.upper() == "P" or target_piece != ".":
            halfmove = 0
        else:
            halfmove += 1
        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)
        update_castling_rights(castling_rights, piece, fr, fc, tr, tc)
        board = make_move(board, fr, fc, tr, tc, en_passant_target, promo)
        en_passant_target = new_ep
        if not white:
            fullmove += 1
        white = not white
    print(board_to_fen(board, white, castling_rights, en_passant_target, halfmove=halfmove, fullmove=fullmove))


def run_healthcheck():
    """Run non-interactive engine self-tests and return True on success."""
    board = copy.deepcopy(INITIAL_BOARD)
    cr = {"K", "Q", "k", "q"}
    legal = get_legal_moves(board, True, None, cr)
    if len(legal) != 20:
        print(f"[Healthcheck] FAIL: Expected 20 initial legal moves, got {len(legal)}")
        return False
    fen = board_to_fen(board, True, cr, None)
    if fen != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
        print(f"[Healthcheck] FAIL: Unexpected initial FEN: {fen}")
        return False
    san_e4 = move_to_san(board, 6, 4, 4, 4, None, None, cr)
    if san_e4 != "e4":
        print(f"[Healthcheck] FAIL: Expected e4, got {san_e4}")
        return False
    score = evaluate_board(board)
    if score != 0:
        print(f"[Healthcheck] FAIL: Initial board evaluation not balanced: {score}")
        return False
    print(f"[Healthcheck] OK - ChatAndChess {__version__} engine healthy.")
    return True


def print_cli_help():
    """Print command line usage information."""
    print(f"ChatAndChess v{__version__} - Terminal Chess in Python")
    print()
    print("Verwendung:")
    print("  python chess.py                     Startet das interaktive Spiel")
    print("  python chess.py --version           Zeigt die Version an")
    print("  python chess.py --healthcheck       Führt automatische Engine-Selbsttests aus")
    print("  python chess.py --export-initial <p> Schreibt Startposition als chatandchess-game-v1.json")
    print("  python chess.py --export-pgn <p> [m] Replay von UCI-Zügen und Export nach PGN")
    print("  python chess.py --fen [m...]        Gibt FEN nach Zugfolge auf stdout aus")
    print("  python chess.py --worker            Startet den Claude-Code Hintergrund-Worker")
    print("  python chess.py --prompt            Generiert den Claude-Code System-Prompt")
    print("  python chess.py --help              Zeigt diese Hilfe an")


# ---------------------------------------------------------------------------
# Bot-Engine (Minimax + Alpha-Beta)
# ---------------------------------------------------------------------------

def evaluate_board(board):
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == ".":
                continue
            p = piece.upper()
            val = PIECE_VALUES.get(p, 0)
            pst = PST.get(p)
            if pst:
                if is_white(piece):
                    val += pst[r * 8 + c]
                else:
                    val += pst[(7 - r) * 8 + c]
            if is_white(piece):
                score += val
            else:
                score -= val
    return score


def order_moves(board, moves, white):
    scored = []
    for move in moves:
        fr, fc, tr, tc = move
        s = 0
        target = board[tr][tc]
        if target != ".":
            s += 10 * PIECE_VALUES.get(target.upper(), 0) - PIECE_VALUES.get(board[fr][fc].upper(), 0)
        if board[fr][fc].upper() == "P" and (tr == 0 or tr == 7):
            s += 800
        scored.append((s, move))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]


def minimax(board, depth, alpha, beta, maximizing, en_passant_target, castling_rights):
    white = maximizing
    legal = get_legal_moves(board, white, en_passant_target, castling_rights)

    if not legal:
        if in_check(board, white):
            return -99999 if maximizing else 99999
        return 0

    if depth == 0:
        return evaluate_board(board)

    legal = order_moves(board, legal, white)

    if maximizing:
        max_eval = -999999
        for fr, fc, tr, tc in legal:
            piece = board[fr][fc]
            new_ep = None
            if piece.upper() == "P" and abs(fr - tr) == 2:
                new_ep = ((fr + tr) // 2, fc)
            new_cr = set(castling_rights)
            update_castling_rights(new_cr, piece, fr, fc, tr, tc)
            new_board = make_move(board, fr, fc, tr, tc, en_passant_target)
            val = minimax(new_board, depth - 1, alpha, beta, False, new_ep, new_cr)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 999999
        for fr, fc, tr, tc in legal:
            piece = board[fr][fc]
            new_ep = None
            if piece.upper() == "P" and abs(fr - tr) == 2:
                new_ep = ((fr + tr) // 2, fc)
            new_cr = set(castling_rights)
            update_castling_rights(new_cr, piece, fr, fc, tr, tc)
            new_board = make_move(board, fr, fc, tr, tc, en_passant_target)
            val = minimax(new_board, depth - 1, alpha, beta, True, new_ep, new_cr)
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval


def bot_choose_move(board, white, en_passant_target, castling_rights, depth=3):
    legal = get_legal_moves(board, white, en_passant_target, castling_rights)
    if not legal:
        return None
    legal = order_moves(board, legal, white)
    best_move = None
    best_val = -999999 if white else 999999

    for fr, fc, tr, tc in legal:
        piece = board[fr][fc]
        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)
        new_cr = set(castling_rights)
        update_castling_rights(new_cr, piece, fr, fc, tr, tc)
        new_board = make_move(board, fr, fc, tr, tc, en_passant_target)
        val = minimax(new_board, depth - 1, -999999, 999999, not white, new_ep, new_cr)

        if white:
            if val > best_val:
                best_val = val
                best_move = (fr, fc, tr, tc)
        else:
            if val < best_val:
                best_val = val
                best_move = (fr, fc, tr, tc)

    return best_move


# ---------------------------------------------------------------------------
# Claude-API Engine
# ---------------------------------------------------------------------------

def claude_choose_move(board, white, legal_moves, en_passant_target, castling_rights, move_history):
    try:
        import anthropic
    except ImportError:
        print("  FEHLER: anthropic-Paket nicht installiert!")
        print("  Installiere mit: pip install anthropic")
        input("  [Enter]")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        key_file = os.path.join(os.path.expanduser("~"), ".anthropic_key")
        if os.path.exists(key_file):
            with open(key_file, "r", encoding="utf-8") as f:
                api_key = f.read().strip()
    if not api_key:
        print("  FEHLER: Kein ANTHROPIC_API_KEY gefunden!")
        print("  Setze die Umgebungsvariable oder lege ~/.anthropic_key an.")
        input("  [Enter]")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    board_text = board_to_text(board)
    color = "Weiß" if white else "Schwarz"
    legal_input_moves = expand_legal_moves(board, legal_moves)
    legal_strs = [move_to_uci(fr, fc, tr, tc, promo)
                  for fr, fc, tr, tc, promo in legal_input_moves]

    history_text = ""
    if move_history:
        history_text = "\nBisherige Züge: {}\n".format(", ".join(move_history[-20:]))

    prompt = (
        "Du spielst Schach als {}.\n\n"
        "Aktuelles Brett:\n{}\n{}\n"
        "Legale Züge: {}\n\n"
        "Antworte NUR mit deinem Zug im Format StartfeldZielfeld"
        " (z.B. e2e4, bei Umwandlung e7e8q).\n"
        "Kein weiterer Text, keine Erklärung. Nur der Zug."
    ).format(color, board_text, history_text, ", ".join(legal_strs))

    try:
        print("  Claude denkt nach...")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text.strip().lower()
        match = re.search(r"[a-h][1-8][a-h][1-8][qrbn]?", answer)
        if match:
            parsed = parse_move_text(match.group(0))
            if parsed:
                fr, fc, tr, tc, promo = parsed
                candidate = (fr, fc, tr, tc, promo)
                if candidate in legal_input_moves:
                    return candidate
                print("  Claude schlug ungültigen Zug vor: {}".format(match.group(0)))

        print("  -> Fallback: Zufälliger Zug")
        input("  [Enter]")
        return random.choice(legal_input_moves)

    except Exception as e:
        print("  Claude-API Fehler: {}".format(e))
        print("  -> Fallback: Zufälliger Zug")
        input("  [Enter]")
        return random.choice(legal_input_moves)


# ---------------------------------------------------------------------------
# Claude-Code Engine (Datei-basierte Kommunikation)
# ---------------------------------------------------------------------------

MODES = [
    {
        "name": "Mensch-Modus",
        "desc": "Fairer Wettkampf -- keine Hints für beide, Claude spielt ohne Engine",
        "settings": {"show_hints": False, "show_recommendation": False, "claude_uses_engine": False},
    },
    {
        "name": "Training-Modus",
        "desc": "Du siehst Engine-Hints + Empfehlung, Claude spielt ohne Engine-Hilfe",
        "settings": {"show_hints": True, "show_recommendation": True, "claude_uses_engine": False},
    },
    {
        "name": "Gleichzug-Modus",
        "desc": "Beide sehen dieselben Engine-Hints -- gleiche Informationsbasis",
        "settings": {"show_hints": True, "show_recommendation": True, "claude_uses_engine": True},
    },
    {
        "name": "Analyse-Modus",
        "desc": "Keine Hints im Spiel -- aber chess_analyze.py für Nachbereitung verfügbar",
        "settings": {"show_hints": False, "show_recommendation": False, "claude_uses_engine": False},
    },
]


def choose_game_mode():
    """Display the mode selection menu and return the chosen settings."""
    print()
    print("  +-----------------------------------------+")
    print("  |        CLAUDE CODE -- SPIELMODUS        |")
    print("  +-----------------------------------------+")
    for i, m in enumerate(MODES, 1):
        print("  [{}] {}".format(i, m["name"]))
        print("      {}".format(m["desc"]))
        print()
    while True:
        try:
            choice = input("  Modus wählen (1-{}): ".format(len(MODES))).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(MODES):
            selected = MODES[int(choice) - 1]
            # Settings speichern (top_n und hint_depth beibehalten)
            current = load_settings()
            current.update(selected["settings"])
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2, ensure_ascii=False)
            except OSError:
                pass
            return current
        print("  Bitte 1-{} eingeben.".format(len(MODES)))


def ensure_comm_dir():
    os.makedirs(COMM_DIR, exist_ok=True)
    # Alte Dateien aufraeumen
    for f in [REQUEST_FILE, RESPONSE_FILE]:
        if os.path.exists(f):
            os.remove(f)
    # Modusauswahl + Prompt anzeigen
    settings = choose_game_mode()
    if settings is None:
        return
    print()
    prompt = generate_session_prompt(settings)
    print(prompt)
    print("  >> Kopiere den obigen Text zu Claude Code um den Modus zu setzen. <<")
    print()
    input("  [Enter zum Starten]")


def write_request(board, white, legal_moves, move_history, check,
                  en_passant_target=None, castling_rights=None):
    """Write a move request for Claude Code."""
    settings = load_settings()
    data = build_worker_request_data(
        board,
        white,
        legal_moves,
        move_history,
        check,
        en_passant_target=en_passant_target,
        castling_rights=castling_rights,
    )
    data["settings"] = settings
    if settings.get("claude_uses_engine") and castling_rights is not None:
        cr = castling_rights if isinstance(castling_rights, set) else set(castling_rights)
        hints = compute_hints(board, white, en_passant_target, cr,
                              settings.get("hint_depth", 2),
                              settings.get("top_n", 5))
        sign = 1 if white else -1
        data["top_moves"] = [
            {
                "move": uci,
                "eval": round(score * sign, 1),
                "piece": PIECE_NAMES_DE.get(piece.upper(), piece),
                "captures": PIECE_NAMES_DE.get(cap.upper(), "") if cap != "." else "",
            }
            for score, uci, piece, cap in hints
        ]
        if settings.get("show_recommendation") and hints:
            data["recommendation"] = hints[0][1]
    try:
        with open(REQUEST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print("  FEHLER: Anfrage-Datei konnte nicht geschrieben werden: {}".format(e))
        return False


def build_worker_request_data(board, white, legal_moves, move_history, check,
                              en_passant_target=None, castling_rights=None):
    """Build the JSON payload for the Claude-Code worker."""
    legal_input_moves = expand_legal_moves(board, legal_moves)
    legal_strs = [move_to_uci(fr, fc, tr, tc, promo)
                  for fr, fc, tr, tc, promo in legal_input_moves]
    data = {
        "board": board,
        "board_text": board_to_text(board),
        "white_turn": white,
        "color": "Weiß" if white else "Schwarz",
        "legal_moves": legal_strs,
        "move_history": move_history,
        "check": check,
        "timestamp": time.time(),
    }
    if en_passant_target is not None:
        data["en_passant_target"] = list(en_passant_target)
    if castling_rights is not None:
        cr = castling_rights if isinstance(castling_rights, set) else set(castling_rights)
        data["castling_rights"] = sorted(cr)
    return data


def infer_castling_rights_from_board(board):
    """Fallback for older requests that do not carry explicit castling rights."""
    castling_rights = {"K", "Q", "k", "q"}

    if board[7][4] != "K":
        castling_rights.discard("K")
        castling_rights.discard("Q")
    if board[0][4] != "k":
        castling_rights.discard("k")
        castling_rights.discard("q")
    if board[7][7] != "R":
        castling_rights.discard("K")
    if board[7][0] != "R":
        castling_rights.discard("Q")
    if board[0][7] != "r":
        castling_rights.discard("k")
    if board[0][0] != "r":
        castling_rights.discard("q")

    return castling_rights


def infer_en_passant_target_from_history(board, history):
    """Fallback for older requests that do not carry explicit en-passant state."""
    en_passant_target = None
    if history:
        parsed = parse_move_text(history[-1])
        if parsed:
            lfr, lfc, ltr, ltc, _ = parsed
            if board[ltr][ltc].upper() == "P" and abs(lfr - ltr) == 2:
                en_passant_target = ((lfr + ltr) // 2, lfc)
    return en_passant_target


def load_worker_state(data):
    """Parse a Claude-Code request payload into typed worker state."""
    board = data["board"]
    white = data["white_turn"]
    legal_strs = data["legal_moves"]
    check = data.get("check", False)
    history = data.get("move_history", [])

    legal_moves = []
    for ms in legal_strs:
        parsed = parse_move_text(ms)
        if parsed:
            legal_moves.append(parsed)

    castling_raw = data.get("castling_rights")
    if castling_raw is not None:
        castling_rights = set(castling_raw)
    else:
        castling_rights = infer_castling_rights_from_board(board)

    en_passant_raw = data.get("en_passant_target")
    if en_passant_raw is not None:
        en_passant_target = tuple(en_passant_raw)
    else:
        en_passant_target = infer_en_passant_target_from_history(board, history)

    return {
        "board": board,
        "white_turn": white,
        "legal_moves": legal_moves,
        "check": check,
        "move_history": history,
        "castling_rights": castling_rights,
        "en_passant_target": en_passant_target,
    }


def wait_for_response(timeout=300):
    """Wait for a response from Claude Code. Returns the move string."""
    start = time.time()
    dots = 0
    while time.time() - start < timeout:
        if os.path.exists(RESPONSE_FILE):
            time.sleep(0.3)  # kurz warten bis Schreiben abgeschlossen
            read_attempts = 0
            while read_attempts < 3:
                try:
                    with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    os.remove(RESPONSE_FILE)
                    return data.get("move", "")
                except (json.JSONDecodeError, FileNotFoundError, OSError):
                    read_attempts += 1
                    time.sleep(0.5)
            print("\n  FEHLER: Response-Datei konnte nach 3 Versuchen nicht gelesen werden.")
            try:
                os.remove(RESPONSE_FILE)
            except OSError:
                pass
            return None
        time.sleep(1)
        dots += 1
        # Fortschrittsanzeige aktualisieren
        if dots % 5 == 0:
            elapsed = int(time.time() - start)
            sys.stdout.write("\r  Warte auf Claude Code... ({}s)  ".format(elapsed))
            sys.stdout.flush()
    return None


def claude_code_choose_move(board, white, legal_moves, move_history, check,
                            en_passant_target=None, castling_rights=None):
    """Write the move request and wait for a Claude Code response."""
    legal_input_moves = expand_legal_moves(board, legal_moves)
    if not write_request(board, white, legal_moves, move_history, check,
                         en_passant_target, castling_rights):
        print("  -> Fallback: Zufälliger Zug (Request-Datei nicht schreibbar)")
        input("  [Enter]")
        return random.choice(legal_input_moves)
    print("  Warte auf Claude Code...")
    print("  (Request geschrieben nach: {})".format(COMM_DIR))

    move_str = wait_for_response()

    # Request aufräumen
    if os.path.exists(REQUEST_FILE):
        os.remove(REQUEST_FILE)

    if not move_str:
        print("\n  Timeout! Keine Antwort von Claude Code.")
        print("  -> Fallback: Zufälliger Zug")
        input("  [Enter]")
        return random.choice(legal_input_moves)

    move_str = move_str.strip().lower()
    parsed = parse_move_text(move_str)
    if parsed:
        if parsed in legal_input_moves:
            return parsed
        fr, fc, tr, tc, promo = parsed
        if promo is None and is_promotion_move(board, fr, fc, tr):
            queen_promo = (fr, fc, tr, tc, "q")
            if queen_promo in legal_input_moves:
                return queen_promo

    print("  Ungültiger Zug von Claude Code: {}".format(move_str))
    print("  -> Fallback: Zufälliger Zug")
    input("  [Enter]")
    return random.choice(legal_input_moves)


# ---------------------------------------------------------------------------
# Worker-Modus (wird von Claude Code als Hintergrundprozess gestartet)
# ---------------------------------------------------------------------------

def run_worker():
    """Worker loop: monitors chess_request.json and delegates to the bot engine."""
    print("Chess Worker gestartet.")
    print("Überwache: {}".format(COMM_DIR))
    print("Beenden mit Ctrl+C")
    print()

    os.makedirs(COMM_DIR, exist_ok=True)

    while True:
        try:
            if os.path.exists(REQUEST_FILE):
                with open(REQUEST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                state = load_worker_state(data)
                board = state["board"]
                white = state["white_turn"]
                legal_moves = state["legal_moves"]
                castling_rights = state["castling_rights"]
                en_passant_target = state["en_passant_target"]

                if not legal_moves:
                    print("[Worker] Keine legalen Züge!")
                    continue

                # Bot-Engine für Zugwahl nutzen
                print("[Worker] Berechne Zug für {}...".format(
                    "Weiß" if white else "Schwarz"))

                move = bot_choose_move(board, white, en_passant_target,
                                       castling_rights, depth=3)
                if not move:
                    move = random.choice(legal_moves)

                if len(move) == 5:
                    fr, fc, tr, tc, promo = move
                else:
                    fr, fc, tr, tc = move
                    promo = None
                if is_promotion_move(board, fr, fc, tr) and not promo:
                    promo = "q"
                move_str = move_to_uci(fr, fc, tr, tc, promo)

                response = {"move": move_str, "timestamp": time.time()}
                with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
                    json.dump(response, f, ensure_ascii=False)

                print("[Worker] Zug: {}".format(move_str))

                # Request löschen
                if os.path.exists(REQUEST_FILE):
                    os.remove(REQUEST_FILE)

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n[Worker] Beendet.")
            break
        except Exception as e:
            print("[Worker] Fehler: {}".format(e))
            time.sleep(2)


# ---------------------------------------------------------------------------
# Spielschleife
# ---------------------------------------------------------------------------

def show_menu():
    os.system("cls" if sys.platform == "win32" else "clear")
    print()
    print("  ================================================")
    print("       ASCII SCHACH")
    print("  ================================================")
    print()
    print("    [1]  2 Spieler (lokal)")
    print("    [2]  Spieler vs Bot (Minimax)")
    print("    [3]  Spieler vs Claude (API)")
    print("    [4]  Spieler vs Claude Code (Datei-Link)")
    print("    [q]  Beenden")
    print()
    choice = input("  Auswahl: ").strip().lower()
    return choice


def choose_color():
    print()
    print("  Welche Farbe möchtest du spielen?")
    print("    [w]  Weiß")
    print("    [s]  Schwarz")
    print()
    c = input("  Auswahl: ").strip().lower()
    if c in ("s", "schwarz", "b", "black"):
        return False
    return True


def choose_difficulty():
    print()
    print("  Bot-Staerke (Suchtiefe):")
    print("    [1]  Leicht (Tiefe 2)")
    print("    [2]  Mittel (Tiefe 3)")
    print("    [3]  Schwer (Tiefe 4)")
    print()
    c = input("  Auswahl [1-3]: ").strip()
    if c == "1":
        return 2
    elif c == "3":
        return 4
    return 3


def game_loop(mode, player_white=True, bot_depth=3):
    board = copy.deepcopy(INITIAL_BOARD)
    white_turn = True
    last_move_str = None
    en_passant_target = None
    castling_rights = {"K", "Q", "k", "q"}
    move_history = []

    if mode == "2p":
        mode_info = "2 Spieler"
    elif mode == "bot":
        mode_info = "vs Bot (Tiefe {})".format(bot_depth)
    elif mode == "claude":
        mode_info = "vs Claude API"
    else:
        mode_info = "vs Claude Code"

    if mode == "claude_code":
        ensure_comm_dir()

    while True:
        check = in_check(board, white_turn)
        legal = get_legal_moves(board, white_turn, en_passant_target, castling_rights)
        legal_input_moves = expand_legal_moves(board, legal)

        if not legal:
            render(board, white_turn, last_move_str, check, mode_info)
            if check:
                winner = "Schwarz" if white_turn else "Weiß"
                print("  SCHACHMATT! {} gewinnt!".format(winner))
            else:
                print("  PATT! Unentschieden.")
            if mode == "claude_code":
                # Spielende signalisieren
                end_data = {"board": board, "result": "checkmate" if check else "stalemate",
                            "winner": ("black" if white_turn else "white") if check else "draw"}
                try:
                    with open(os.path.join(COMM_DIR, "chess_gameover.json"), "w", encoding="utf-8") as f:
                        json.dump(end_data, f, ensure_ascii=False)
                except OSError as e:
                    print("  WARNUNG: Spielende-Signal konnte nicht geschrieben werden: {}".format(e))
            input("\n  [Enter für Menü]")
            return

        render(board, white_turn, last_move_str, check, mode_info)

        is_human = False
        if mode == "2p":
            is_human = True
        else:
            is_human = (white_turn == player_white)

        settings = load_settings()
        if is_human and settings.get("show_hints"):
            print("  Berechne Tipps...")
            hints = compute_hints(board, white_turn, en_passant_target, castling_rights,
                                  settings.get("hint_depth", 2), settings.get("top_n", 5))
            display_hints(hints, white_turn, settings.get("show_recommendation", False))

        if is_human:
            try:
                inp = input("  Zug (z.B. e2e4, e7e8q, q=quit, fen, export, pgn, help): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Spiel beendet.")
                return

            inp_clean = inp.lower()
            if inp_clean in ("q", "quit", "exit"):
                print("  Spiel beendet.")
                return

            if inp_clean == "fen":
                current_fen = board_to_fen(board, white_turn, castling_rights, en_passant_target)
                print("\n  Aktuelle FEN-Position:")
                print(f"  {current_fen}\n")
                try:
                    input("  [Enter zum Weiterspielen]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            if inp_clean.startswith("export"):
                parts = inp.split(maxsplit=1)
                target_path = parts[1].strip() if len(parts) > 1 else "chatandchess-game-v1.json"
                try:
                    export_data = build_game_export(board, white_turn, castling_rights, en_passant_target,
                                                    move_history, mode_kind=mode, bot_depth=bot_depth,
                                                    include_san=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                    print(f"\n  Partie erfolgreich exportiert nach: {target_path}")
                except OSError as e:
                    print(f"\n  FEHLER beim Export: {e}")
                try:
                    input("  [Enter zum Weiterspielen]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            if inp_clean.startswith("pgn"):
                parts = inp.split(maxsplit=1)
                target_path = parts[1].strip() if len(parts) > 1 else "partie.pgn"
                try:
                    pgn_text = replay_moves_to_pgn(move_history)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(pgn_text)
                    print(f"\n  PGN erfolgreich exportiert nach: {target_path}")
                except OSError as e:
                    print(f"\n  FEHLER beim PGN-Export: {e}")
                try:
                    input("  [Enter zum Weiterspielen]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            if inp_clean in ("help", "?", "hilfe"):
                print("\n  Verfügbare Befehle:")
                print("    e2e4, e7e8q : Normaler Zug bzw. Bauernumwandlung")
                print("    fen         : Zeigt die aktuelle FEN-Notation")
                print("    export [pfad]: Exportiert die Partie als chatandchess-game-v1.json")
                print("    pgn [pfad]  : Exportiert die Züge im PGN-Format")
                print("    tipp / hint : Berechnet und zeigt Taktik-Tipps")
                print("    q / quit    : Beendet das aktuelle Spiel\n")
                try:
                    input("  [Enter zum Weiterspielen]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            if inp_clean in ("hint", "tipp", "tipps", "hints"):
                hints = compute_hints(board, white_turn, en_passant_target, castling_rights, 2, 5)
                display_hints(hints, white_turn, True)
                try:
                    input("  [Enter zum Weiterspielen]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            if len(inp_clean) < 4:
                print("  Ungültiges Format! Nutze z.B. e2e4 oder 'help'")
                try:
                    input("  [Enter]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            move = resolve_player_move(board, inp_clean, legal_input_moves)
            if move is None:
                print("  Ungültiges Feld!")
                try:
                    input("  [Enter]")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            fr, fc, tr, tc, promo = move

        elif mode == "bot":
            print("  Bot denkt nach...")
            move = bot_choose_move(board, white_turn, en_passant_target,
                                   castling_rights, bot_depth)
            if not move:
                return
            fr, fc, tr, tc = move
            promo = "q" if is_promotion_move(board, fr, fc, tr) else None

        elif mode == "claude":
            move = claude_choose_move(board, white_turn, legal,
                                      en_passant_target, castling_rights,
                                      move_history)
            if not move:
                return
            fr, fc, tr, tc, promo = move

        elif mode == "claude_code":
            move = claude_code_choose_move(board, white_turn, legal,
                                           move_history, check,
                                           en_passant_target, castling_rights)
            if not move:
                return
            fr, fc, tr, tc, promo = move

        piece = board[fr][fc]

        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)

        update_castling_rights(castling_rights, piece, fr, fc, tr, tc)

        board = make_move(board, fr, fc, tr, tc, en_passant_target, promo)
        en_passant_target = new_ep

        move_str = move_to_uci(fr, fc, tr, tc, promo)
        move_history.append(move_str)
        color = "W" if white_turn else "S"
        last_move_str = "{}: {} -> {}".format(color, pos_to_str(fr, fc), pos_to_str(tr, tc))
        white_turn = not white_turn


def main():
    # CLI-Argumente prüfen
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--version", "-v"):
            print(f"ChatAndChess {__version__}")
            return
        if arg in ("--healthcheck", "--health"):
            success = run_healthcheck()
            sys.exit(0 if success else 1)
        if arg in ("--help", "-h"):
            print_cli_help()
            return
        if arg == "--export-initial":
            if len(sys.argv) < 3:
                print("FEHLER: Pfad für den Initial-Export fehlt. Verwendung: --export-initial <datei.json>", file=sys.stderr)
                sys.exit(2)
            export_initial_game(sys.argv[2])
            return
        if arg == "--export-pgn":
            if len(sys.argv) < 3:
                print("FEHLER: Ausgabepfad fehlt. Verwendung: --export-pgn <datei.pgn> [zug1 zug2 ...]", file=sys.stderr)
                sys.exit(2)
            out_path = sys.argv[2]
            moves = sys.argv[3:]
            export_pgn_cli(out_path, moves)
            return
        if arg == "--fen":
            moves = sys.argv[2:]
            export_fen_cli(moves)
            return
        if arg == "--worker":
            run_worker()
            return
        if arg == "--prompt":
            prompt = generate_session_prompt()
            print(prompt)
            print("\n  Gespeichert unter: {}".format(PROMPT_FILE))
            return

    while True:
        choice = show_menu()
        if choice == "1":
            game_loop("2p")
        elif choice == "2":
            player_white = choose_color()
            depth = choose_difficulty()
            game_loop("bot", player_white=player_white, bot_depth=depth)
        elif choice == "3":
            player_white = choose_color()
            game_loop("claude", player_white=player_white)
        elif choice == "4":
            player_white = choose_color()
            print()
            print("  Claude-Code Modus:")
            print("  Das Spiel schreibt Zuganfragen nach:")
            print("  {}".format(COMM_DIR))
            print()
            print("  Starte den Worker in einem zweiten Terminal:")
            print("  python chess.py --worker")
            print()
            print("  Oder lass Claude Code direkt antworten.")
            input("  [Enter zum Starten]")
            game_loop("claude_code", player_white=player_white)
        elif choice in ("q", "quit", "exit"):
            print("  Auf Wiedersehen!")
            break
        else:
            print("  Ungültige Auswahl!")
            input("  [Enter]")


if __name__ == "__main__":
    main()
