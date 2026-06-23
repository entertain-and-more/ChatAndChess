# -*- coding: utf-8 -*-
"""Regressionstests Bugsweep 2026-06-23 (Desktop, /bugsweep-Loop Run 9/15).

BS-1 HOCH: --depth/hint_depth <=0 -> unbegrenzte Minimax-Rekursion (Hang/RecursionError).
BS-2 MITTEL: Bauernumwandlung ohne Suffix ("e7e8") -> als ungueltig verworfen -> Zufallszug.
BS-3 MITTEL: Worker-Endlosschleife bei korruptem Request (Datei nie geloescht).
BS-4 LOW: wait_for_response Crash bei nicht-objekt-foermigem JSON.
BS-5 LOW: --top 0 meldet faelschlich "keine legalen Zuege".
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
_CHESS = (ROOT / "chess.py").read_text(encoding="utf-8")
_ANALYZE = (ROOT / "chess_analyze.py").read_text(encoding="utf-8")


def test_minimax_base_case_has_nonpositive_guard():
    assert "if depth <= 0:" in _CHESS


def test_minimax_terminates_on_negative_depth():
    # Verhaltensbeleg: depth=-1 traf vor dem Fix (== 0) die Basis nie -> unendliche
    # Rekursion (RecursionError). Nach Fix (<= 0) terminiert es mit einer Zahl.
    import sys
    import copy
    import math
    sys.path.insert(0, str(ROOT))
    import chess as c
    board = copy.deepcopy(c.INITIAL_BOARD)
    castling = c.infer_castling_rights_from_board(board)
    result = c.minimax(board, -1, -math.inf, math.inf, True, None, castling)
    assert isinstance(result, (int, float))


def test_depth_and_top_parse_clamped():
    assert _ANALYZE.count("max(1, int(args[i + 1]))") >= 2


def test_promotion_defaults_to_queen_both_modes():
    # Beide Stellen (Worker/Claude-Code + API) defaulten fehlenden promo auf 'q'.
    assert _CHESS.count("promoted in legal_input_moves") >= 2


def test_worker_removes_corrupt_request():
    assert 'REQUEST_FILE + ".bad"' in _CHESS


def test_wait_for_response_isinstance_guard():
    assert "isinstance(data, dict)" in _CHESS
