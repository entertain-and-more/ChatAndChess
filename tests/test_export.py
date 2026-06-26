import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chess  # noqa: E402


class FenTests(unittest.TestCase):
    def test_initial_fen(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        fen = chess.board_to_fen(board, True, {"K", "Q", "k", "q"}, None)
        self.assertEqual(fen, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_fen_after_e4(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        board[4][4] = "P"
        board[6][4] = "."
        en_passant = (5, 4)  # e3
        fen = chess.board_to_fen(board, False, {"K", "Q", "k", "q"}, en_passant)
        self.assertEqual(
            fen,
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        )

    def test_fen_no_castling(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        fen = chess.board_to_fen(board, True, set(), None)
        self.assertTrue(fen.endswith("w - - 0 1"))

    def test_fullmove_number_from_history(self):
        self.assertEqual(chess.current_fullmove_number([]), 1)
        self.assertEqual(chess.current_fullmove_number(["e2e4"]), 1)
        self.assertEqual(chess.current_fullmove_number(["e2e4", "e7e5"]), 2)


class GameExportTests(unittest.TestCase):
    def test_export_schema_keys(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        result = chess.build_game_export(board, True, {"K", "Q", "k", "q"}, None, [], "local")
        self.assertEqual(result["schema"], "chatandchess-game-v1")
        self.assertEqual(result["app"], "ChatAndChess")
        self.assertIn("created_at", result)
        self.assertIn("fen", result["position"])
        self.assertEqual(result["position"]["side_to_move"], "white")
        self.assertEqual(result["moves"], [])
        self.assertEqual(result["notes"], [])

    def test_export_moves(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        history = ["e2e4", "e7e5"]
        result = chess.build_game_export(board, True, set(), None, history, "bot")
        self.assertEqual(len(result["moves"]), 2)
        self.assertEqual(result["moves"][0], {"uci": "e2e4", "san": None, "by": "white"})
        self.assertEqual(result["moves"][1], {"uci": "e7e5", "san": None, "by": "black"})
        self.assertEqual(result["mode"]["kind"], "bot")
        self.assertTrue(result["position"]["fen"].endswith("w - - 0 2"))

    def test_write_game_export_utf8_json(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        data = chess.build_game_export(
            board,
            True,
            {"K", "Q", "k", "q"},
            None,
            [],
            "local",
            created_at="2026-06-21T00:00:00Z",
        )
        data["notes"].append("Test mit äöü")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chatandchess-game-v1.json"
            written = chess.write_game_export(target, data)
            self.assertEqual(Path(written), target)
            loaded = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema"], "chatandchess-game-v1")
        self.assertEqual(loaded["notes"], ["Test mit äöü"])

    def test_export_initial_cli_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "initial.json"
            result = subprocess.run(
                [sys.executable, "chess.py", "--export-initial", str(target)],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Export geschrieben", result.stdout)
            loaded = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema"], "chatandchess-game-v1")
        self.assertEqual(
            loaded["position"]["fen"],
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        )


class PgnExportTests(unittest.TestCase):
    def test_pgn_opening_uses_san_and_result_marker(self):
        pgn = chess.build_pgn_export(
            ["e2e4", "e7e5", "g1f3"],
            date="2026.06.26",
        )
        self.assertIn('[Event "ChatAndChess Game"]', pgn)
        self.assertIn('[Date "2026.06.26"]', pgn)
        self.assertIn("1. e4 e5 2. Nf3 *", pgn)

    def test_pgn_detects_checkmate_result(self):
        pgn = chess.build_pgn_export(
            ["f2f3", "e7e5", "g2g4", "d8h4"],
            date="2026.06.26",
        )
        self.assertIn('[Result "0-1"]', pgn)
        self.assertIn("1. f3 e5 2. g4 Qh4# 0-1", pgn)

    def test_pgn_castling_notation(self):
        pgn = chess.build_pgn_export(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1e2", "g8f6", "e1g1"],
            date="2026.06.26",
        )
        self.assertIn("4. O-O *", pgn)

    def test_export_pgn_cli_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "game.pgn"
            result = subprocess.run(
                [
                    sys.executable,
                    "chess.py",
                    "--export-pgn",
                    str(target),
                    "e2e4",
                    "e7e5",
                    "g1f3",
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PGN geschrieben", result.stdout)
            text = target.read_text(encoding="utf-8")
        self.assertIn('[App "ChatAndChess"]', text)
        self.assertIn("1. e4 e5 2. Nf3 *", text)


if __name__ == "__main__":
    unittest.main()
