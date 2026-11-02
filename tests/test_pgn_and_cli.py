#!/usr/bin/env python3
"""Contract and regression test suite for SAN notation, PGN export, and CLI commands.

Tests move_to_san, replay_moves_to_pgn, format_pgn, build_game_export,
and non-interactive CLI arguments in ChatAndChess.
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chess  # noqa: E402


class TestSanNotation(unittest.TestCase):
    """Test standard algebraic notation (SAN) generation."""

    def setUp(self):
        self.board = copy.deepcopy(chess.INITIAL_BOARD)
        self.cr = {"K", "Q", "k", "q"}

    def test_pawn_opening_moves(self):
        san_e4 = chess.move_to_san(self.board, 6, 4, 4, 4, None, None, self.cr)
        self.assertEqual(san_e4, "e4")
        san_d4 = chess.move_to_san(self.board, 6, 3, 4, 3, None, None, self.cr)
        self.assertEqual(san_d4, "d4")
        san_c4 = chess.move_to_san(self.board, 6, 2, 4, 2, None, None, self.cr)
        self.assertEqual(san_c4, "c4")
        san_Nf3 = chess.move_to_san(self.board, 7, 6, 5, 5, None, None, self.cr)
        self.assertEqual(san_Nf3, "Nf3")

    def test_pawn_capture_and_en_passant(self):
        # 1. e4 a6 2. e5 d5 3. exd6 (en passant)
        board = copy.deepcopy(chess.INITIAL_BOARD)
        cr = {"K", "Q", "k", "q"}
        ep = None
        moves = ["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"]
        sans = []
        for uci in moves:
            fr, fc, tr, tc, promo = chess.parse_move_text(uci)
            san = chess.move_to_san(board, fr, fc, tr, tc, promo, ep, cr)
            sans.append(san)
            p = board[fr][fc]
            new_ep = ((fr + tr) // 2, fc) if p.upper() == "P" and abs(fr - tr) == 2 else None
            chess.update_castling_rights(cr, p, fr, fc, tr, tc)
            board = chess.make_move(board, fr, fc, tr, tc, ep, promo)
            ep = new_ep

        self.assertEqual(sans, ["e4", "a6", "e5", "d5", "exd6"])

    def test_pawn_promotion(self):
        # 1. Diagonal capture promotion: b7 -> a8=Q+ (capturing rook on a8, giving check to e8)
        custom_board = [
            list("r...k..r"),
            list(".P......"),  # Pawn on b7 (row 1, col 1)
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("R...K..R"),
        ]
        san_capture_promo = chess.move_to_san(custom_board, 1, 1, 0, 0, "q", None, set())
        self.assertEqual(san_capture_promo, "bxa8=Q+")

        # 2. Straight push promotion: b7 -> b8=N (b8 empty, no check)
        san_b8 = chess.move_to_san(custom_board, 1, 1, 0, 1, "n", None, set())
        self.assertEqual(san_b8, "b8=N")

    def test_castling_kingside_and_queenside(self):
        custom_board = [
            list("r...k..r"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("R...K..R"),
        ]
        cr = {"K", "Q", "k", "q"}
        # White kingside: e1g1 (7,4 -> 7,6)
        san_kingside = chess.move_to_san(custom_board, 7, 4, 7, 6, None, None, cr)
        self.assertEqual(san_kingside, "O-O")
        # White queenside: e1c1 (7,4 -> 7,2)
        san_queenside = chess.move_to_san(custom_board, 7, 4, 7, 2, None, None, cr)
        self.assertEqual(san_queenside, "O-O-O")

    def test_scholars_mate_and_fools_mate(self):
        # Scholar's Mate: 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
        sm_moves = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
        pgn = chess.replay_moves_to_pgn(sm_moves)
        self.assertIn("1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0", pgn)
        self.assertIn('[Result "1-0"]', pgn)

        # Fool's Mate: 1. f3 e5 2. g4 Qh4# 0-1
        fm_moves = ["f2f3", "e7e5", "g2g4", "d8h4"]
        fm_pgn = chess.replay_moves_to_pgn(fm_moves)
        self.assertIn("1. f3 e5 2. g4 Qh4# 0-1", fm_pgn)
        self.assertIn('[Result "0-1"]', fm_pgn)

    def test_disambiguation(self):
        # Two white knights that can both move to empty square d2: Nb1 and Nf3
        board = [
            list("r...k..r"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list(".....N.."),  # f3: row 5, col 5
            list("PPP.PPPP"),  # d2 (row 6, col 3) is empty
            list(".N..K..R"),  # b1: row 7, col 1
        ]
        cr = {"K", "Q", "k", "q"}
        # Nb1d2 (7,1 -> 6,3)
        san_b1d2 = chess.move_to_san(board, 7, 1, 6, 3, None, None, cr)
        self.assertEqual(san_b1d2, "Nbd2")
        # Nf3d2 (5,5 -> 6,3)
        san_f3d2 = chess.move_to_san(board, 5, 5, 6, 3, None, None, cr)
        self.assertEqual(san_f3d2, "Nfd2")


class TestPgnAndExport(unittest.TestCase):
    """Test PGN formatting and JSON game export integration."""

    def test_format_pgn_headers_and_roster(self):
        sans = ["e4", "e5", "Nf3", "Nc6", "Bb5"]
        headers = {"Event": "World Championship", "White": "Kasparov", "Black": "Karpov"}
        pgn = chess.format_pgn(sans, result="*", headers=headers)
        self.assertIn('[Event "World Championship"]', pgn)
        self.assertIn('[White "Kasparov"]', pgn)
        self.assertIn('[Black "Karpov"]', pgn)
        self.assertIn("1. e4 e5 2. Nf3 Nc6 3. Bb5 *", pgn)

    def test_build_game_export_includes_san_when_requested(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        history = ["e2e4", "e7e5", "g1f3"]
        export = chess.build_game_export(board, False, {"K", "Q", "k", "q"}, None, history, include_san=True)
        self.assertEqual(export["schema"], "chatandchess-game-v1")
        self.assertEqual(len(export["moves"]), 3)
        self.assertEqual(export["moves"][0]["san"], "e4")
        self.assertEqual(export["moves"][1]["san"], "e5")
        self.assertEqual(export["moves"][2]["san"], "Nf3")


class TestCommandLineInterface(unittest.TestCase):
    """Test CLI argument handling via subprocess execution."""

    def _run_cli(self, args):
        cmd = [sys.executable, "-u", str(PROJECT_ROOT / "chess.py"), *args]
        return subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10)

    def test_version_flag(self):
        res = self._run_cli(["--version"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("ChatAndChess 1.2.0", res.stdout)

    def test_healthcheck_flag(self):
        res = self._run_cli(["--healthcheck"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("[Healthcheck] OK", res.stdout)
        self.assertIn("ChatAndChess 1.2.0 engine healthy.", res.stdout)

    def test_help_flag(self):
        res = self._run_cli(["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("Verwendung:", res.stdout)
        self.assertIn("--export-initial", res.stdout)
        self.assertIn("--export-pgn", res.stdout)
        self.assertIn("--fen", res.stdout)

    def test_export_initial_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "initial.json"
            res = self._run_cli(["--export-initial", str(out_file)])
            self.assertEqual(res.returncode, 0)
            self.assertTrue(out_file.is_file())
            data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "chatandchess-game-v1")
            self.assertEqual(data["position"]["fen"], "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_export_pgn_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "game.pgn"
            res = self._run_cli(["--export-pgn", str(out_file), "e2e4", "e7e5", "g1f3", "b8c6"])
            self.assertEqual(res.returncode, 0)
            self.assertTrue(out_file.is_file())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn('[Event "ChatAndChess Game"]', content)
            self.assertIn("1. e4 e5 2. Nf3 Nc6 *", content)

    def test_fen_flag(self):
        res = self._run_cli(["--fen", "e2e4", "c7c5", "g1f3"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2", res.stdout)


if __name__ == "__main__":
    unittest.main()
