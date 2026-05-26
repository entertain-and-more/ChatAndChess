"""ASCII chess game -- 2-player, bot, Claude-API, and Claude-Code mode."""

import copy
import json
import os
import sys
import random
import time

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

# Kommunikationspfad fuer Claude-Code Modus
COMM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_comm")
REQUEST_FILE = os.path.join(COMM_DIR, "chess_request.json")
RESPONSE_FILE = os.path.join(COMM_DIR, "chess_response.json")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_settings.json")
PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CLAUDE_PROMPT.txt")

PIECE_NAMES_DE = {
    "K": "Koenig", "Q": "Dame", "R": "Turm",
    "B": "Laeufer", "N": "Springer", "P": "Bauer",
}


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
            "Zuegen (Tiefe {}) -- dieselbe Liste sieht auch der menschliche Spieler "
            "im Terminal. Nutze diese als Orientierung, triff aber eigene "
            "Entscheidungen und begruende deinen Zug.".format(top_n, depth)
        )
    elif uses_engine and not show_hints:
        mode_name = "ENGINE-MODUS (Nur Claude sieht Engine-Hints -- NICHT FAIR)"
        claude_instr = (
            "Du siehst in chess_request.json das Feld 'top_moves'. "
            "Hinweis: Der menschliche Spieler sieht diese Hints NICHT. "
            "Ueberlege ob das fair ist."
        )
    elif not uses_engine and show_hints:
        mode_name = "TRAINING-MODUS (Nur Mensch sieht Hints, Claude spielt menschlich)"
        claude_instr = (
            "Spiele OHNE Engine-Unterstuetzung -- reines Reasoning und Intuition. "
            "Kein chess_analyze.py aufrufen. Der menschliche Spieler sieht Hints, "
            "du nicht. Das ist der Trainings-Modus fuer den Menschen."
        )
    else:
        mode_name = "MENSCH-MODUS (Keine Hints fuer beide)"
        claude_instr = (
            "Spiele OHNE Engine-Unterstuetzung -- reines Reasoning und Intuition. "
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
        "  Anweisung fuer Claude:",
        "",
    ]
    for part in claude_instr.split(". "):
        lines.append("    " + part.strip() + ("." if not part.strip().endswith(".") else ""))
    lines += [
        "",
        "  Spielablauf:",
        "    1. chess_comm/chess_request.json lesen (Brett, legale Zuege, History)",
        "    2. Zug auswaehlen und in chess_comm/chess_response.json schreiben:",
        '       {"move": "e2e4", "comment": "Begruendung"}',
        "    3. Auf naechsten Request warten (du wirst vom User gerufen)",
        "",
        "  Einstellungen aendern: chess_settings.json bearbeiten,",
        "  dann 'python chess.py --prompt' fuer neuen Prompt.",
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
    print("  Tipp-Zuege (Engine-Bewertung):")
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
    turn = "Weiss" if white_turn else "Schwarz"
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
        cr.discard("K"); cr.discard("Q")
    elif piece == "k":
        cr.discard("k"); cr.discard("q")
    elif piece == "R":
        if (fr, fc) == (7, 7): cr.discard("K")
        elif (fr, fc) == (7, 0): cr.discard("Q")
    elif piece == "r":
        if (fr, fc) == (0, 7): cr.discard("k")
        elif (fr, fc) == (0, 0): cr.discard("q")
    if (tr, tc) == (7, 7): cr.discard("K")
    elif (tr, tc) == (7, 0): cr.discard("Q")
    elif (tr, tc) == (0, 7): cr.discard("k")
    elif (tr, tc) == (0, 0): cr.discard("q")


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
    lines.append("Grossbuchstaben = Weiss, Kleinbuchstaben = Schwarz")
    lines.append("K=Koenig Q=Dame R=Turm B=Laeufer N=Springer P=Bauer")
    return "\n".join(lines)


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
    color = "Weiss" if white else "Schwarz"
    legal_strs = ["{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))
                  for fr, fc, tr, tc in legal_moves]

    history_text = ""
    if move_history:
        history_text = "\nBisherige Zuege: {}\n".format(", ".join(move_history[-20:]))

    prompt = (
        "Du spielst Schach als {}.\n\n"
        "Aktuelles Brett:\n{}\n{}\n"
        "Legale Zuege: {}\n\n"
        "Antworte NUR mit deinem Zug im Format StartfeldZielfeld (z.B. e2e4).\n"
        "Kein weiterer Text, keine Erklaerung. Nur der Zug."
    ).format(color, board_text, history_text, ", ".join(legal_strs))

    try:
        print("  Claude denkt nach...")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text.strip().lower().replace(" ", "").replace("-", "").replace(">", "")
        move_str = ""
        for ch in answer:
            if ch in "abcdefgh12345678":
                move_str += ch
            if len(move_str) == 4:
                break

        if len(move_str) == 4:
            src = parse_pos(move_str[:2])
            dst = parse_pos(move_str[2:4])
            if src and dst:
                fr, fc = src
                tr, tc = dst
                if (fr, fc, tr, tc) in legal_moves:
                    return (fr, fc, tr, tc)
                print("  Claude schlug ungueltigen Zug vor: {}".format(move_str))

        print("  -> Fallback: Zufaelliger Zug")
        input("  [Enter]")
        return random.choice(legal_moves)

    except Exception as e:
        print("  Claude-API Fehler: {}".format(e))
        print("  -> Fallback: Zufaelliger Zug")
        input("  [Enter]")
        return random.choice(legal_moves)


# ---------------------------------------------------------------------------
# Claude-Code Engine (Datei-basierte Kommunikation)
# ---------------------------------------------------------------------------

MODES = [
    {
        "name": "Mensch-Modus",
        "desc": "Fairer Wettkampf -- keine Hints fuer beide, Claude spielt ohne Engine",
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
        "desc": "Keine Hints im Spiel -- aber chess_analyze.py fuer Nachbereitung verfuegbar",
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
            choice = input("  Modus waehlen (1-{}): ".format(len(MODES))).strip()
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
    if not os.path.exists(COMM_DIR):
        os.makedirs(COMM_DIR)
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
    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_worker_request_data(board, white, legal_moves, move_history, check,
                              en_passant_target=None, castling_rights=None):
    """Build the JSON payload for the Claude-Code worker."""
    legal_strs = ["{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))
                  for fr, fc, tr, tc in legal_moves]
    data = {
        "board": board,
        "board_text": board_to_text(board),
        "white_turn": white,
        "color": "Weiss" if white else "Schwarz",
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
        last = history[-1]
        if len(last) >= 4:
            ls = parse_pos(last[:2])
            ld = parse_pos(last[2:4])
            if ls and ld:
                lfr, lfc = ls
                ltr, ltc = ld
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
        if len(ms) >= 4:
            src = parse_pos(ms[:2])
            dst = parse_pos(ms[2:4])
            if src and dst:
                legal_moves.append((src[0], src[1], dst[0], dst[1]))

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
    write_request(board, white, legal_moves, move_history, check,
                  en_passant_target, castling_rights)
    print("  Warte auf Claude Code...")
    print("  (Request geschrieben nach: {})".format(COMM_DIR))

    move_str = wait_for_response()

    # Request aufraeumen
    if os.path.exists(REQUEST_FILE):
        os.remove(REQUEST_FILE)

    if not move_str:
        print("\n  Timeout! Keine Antwort von Claude Code.")
        print("  -> Fallback: Zufaelliger Zug")
        input("  [Enter]")
        return random.choice(legal_moves)

    move_str = move_str.strip().lower()
    if len(move_str) >= 4:
        src = parse_pos(move_str[:2])
        dst = parse_pos(move_str[2:4])
        if src and dst:
            fr, fc = src
            tr, tc = dst
            if (fr, fc, tr, tc) in legal_moves:
                return (fr, fc, tr, tc)

    print("  Ungueltiger Zug von Claude Code: {}".format(move_str))
    print("  -> Fallback: Zufaelliger Zug")
    input("  [Enter]")
    return random.choice(legal_moves)


# ---------------------------------------------------------------------------
# Worker-Modus (wird von Claude Code als Hintergrundprozess gestartet)
# ---------------------------------------------------------------------------

def run_worker():
    """Worker loop: monitors chess_request.json and delegates to the bot engine."""
    print("Chess Worker gestartet.")
    print("Ueberwache: {}".format(COMM_DIR))
    print("Beenden mit Ctrl+C")
    print()

    if not os.path.exists(COMM_DIR):
        os.makedirs(COMM_DIR)

    while True:
        try:
            if os.path.exists(REQUEST_FILE):
                with open(REQUEST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                state = load_worker_state(data)
                board = state["board"]
                white = state["white_turn"]
                legal_moves = state["legal_moves"]
                check = state["check"]
                history = state["move_history"]
                castling_rights = state["castling_rights"]
                en_passant_target = state["en_passant_target"]

                if not legal_moves:
                    print("[Worker] Keine legalen Zuege!")
                    continue

                # Bot-Engine fuer Zugwahl nutzen
                print("[Worker] Berechne Zug fuer {}...".format(
                    "Weiss" if white else "Schwarz"))

                move = bot_choose_move(board, white, en_passant_target,
                                       castling_rights, depth=3)
                if not move:
                    move = random.choice(legal_moves)

                fr, fc, tr, tc = move
                move_str = "{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))

                response = {"move": move_str, "timestamp": time.time()}
                with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
                    json.dump(response, f, ensure_ascii=False)

                print("[Worker] Zug: {}".format(move_str))

                # Request loeschen
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
    print("  Welche Farbe moechtest du spielen?")
    print("    [w]  Weiss")
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

        if not legal:
            render(board, white_turn, last_move_str, check, mode_info)
            if check:
                winner = "Schwarz" if white_turn else "Weiss"
                print("  SCHACHMATT! {} gewinnt!".format(winner))
            else:
                print("  PATT! Unentschieden.")
            if mode == "claude_code":
                # Spielende signalisieren
                end_data = {"board": board, "result": "checkmate" if check else "stalemate",
                            "winner": ("black" if white_turn else "white") if check else "draw"}
                with open(os.path.join(COMM_DIR, "chess_gameover.json"), "w", encoding="utf-8") as f:
                    json.dump(end_data, f, ensure_ascii=False)
            input("\n  [Enter fuer Menue]")
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
                inp = input("  Zug (z.B. e2e4, q=quit): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Spiel beendet.")
                return

            if inp in ("q", "quit", "exit"):
                print("  Spiel beendet.")
                return

            if len(inp) < 4:
                print("  Ungueltiges Format! Nutze z.B. e2e4")
                input("  [Enter]")
                continue

            src = parse_pos(inp[:2])
            dst = parse_pos(inp[2:4])

            if not src or not dst:
                print("  Ungueltiges Feld!")
                input("  [Enter]")
                continue

            fr, fc = src
            tr, tc = dst

            if (fr, fc, tr, tc) not in legal:
                print("  Ungueltiger Zug!")
                input("  [Enter]")
                continue

        elif mode == "bot":
            print("  Bot denkt nach...")
            move = bot_choose_move(board, white_turn, en_passant_target,
                                   castling_rights, bot_depth)
            if not move:
                return
            fr, fc, tr, tc = move

        elif mode == "claude":
            move = claude_choose_move(board, white_turn, legal,
                                      en_passant_target, castling_rights,
                                      move_history)
            if not move:
                return
            fr, fc, tr, tc = move

        elif mode == "claude_code":
            move = claude_code_choose_move(board, white_turn, legal,
                                           move_history, check,
                                           en_passant_target, castling_rights)
            if not move:
                return
            fr, fc, tr, tc = move

        piece = board[fr][fc]

        new_ep = None
        if piece.upper() == "P" and abs(fr - tr) == 2:
            new_ep = ((fr + tr) // 2, fc)

        update_castling_rights(castling_rights, piece, fr, fc, tr, tc)

        board = make_move(board, fr, fc, tr, tc, en_passant_target)
        en_passant_target = new_ep

        move_str = "{}{}".format(pos_to_str(fr, fc), pos_to_str(tr, tc))
        move_history.append(move_str)
        color = "W" if white_turn else "S"
        last_move_str = "{}: {} -> {}".format(color, pos_to_str(fr, fc), pos_to_str(tr, tc))
        white_turn = not white_turn


def main():
    # CLI-Argumente pruefen
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        run_worker()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
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
            print("  Ungueltige Auswahl!")
            input("  [Enter]")


if __name__ == "__main__":
    main()
