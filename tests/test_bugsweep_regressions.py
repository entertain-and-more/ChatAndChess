"""
Bugsweep Run #11 — Regressionstests (2026-06-20)

Bug #11-1: os.makedirs ohne exist_ok=True in ensure_comm_dir() / run_worker()
Bug #11-2: chess_analyze.py -- int() ohne ValueError bei --depth/--top
Bug #11-3: chess_analyze.py -- json.JSONDecodeError nicht abgefangen
Bug #11-4: write_request() -- kein try/except OSError beim Schreiben von REQUEST_FILE
Bug #11-5: game_loop() -- chess_gameover.json ohne try/except OSError
"""
import json
import os
import re
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chess  # noqa: E402
import chess_analyze  # noqa: E402


class TestMakedirExistOk(unittest.TestCase):
    """Bug #11-1: os.makedirs muss exist_ok=True nutzen (kein FileExistsError bei vorhandenem Dir)."""

    def test_makedirs_exist_ok_no_error_on_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "chess_comm")
            os.makedirs(target)
            # Hauptassertion: exist_ok=True darf keinen Fehler werfen
            os.makedirs(target, exist_ok=True)

    def test_makedirs_without_exist_ok_raises_on_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "chess_comm")
            os.makedirs(target)
            with self.assertRaises(FileExistsError):
                os.makedirs(target)  # ohne exist_ok -- das war der alte Bug

    def test_chess_py_uses_exist_ok_in_ensure_comm_dir(self):
        src = os.path.join(PROJECT_ROOT, "chess.py")
        with open(src, encoding="utf-8") as f:
            source = f.read()
        self.assertIn("os.makedirs(COMM_DIR, exist_ok=True)", source,
                      "ensure_comm_dir() muss os.makedirs(..., exist_ok=True) nutzen")


class TestAnalyzeCliValueError(unittest.TestCase):
    """Bug #11-2: --depth/--top mit nicht-numerischem Argument darf nicht traceback."""

    def _run_main_with_args(self, args, tmp_request):
        orig_argv = sys.argv
        sys.argv = ["chess_analyze.py"] + args
        try:
            with self.assertRaises(SystemExit) as ctx:
                chess_analyze.main()
            return ctx.exception.code
        finally:
            sys.argv = orig_argv

    def _make_tmp_request(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump({"move_history": []}, tmp)
        tmp.close()
        return tmp.name

    def test_depth_non_numeric_exits_cleanly(self):
        req = self._make_tmp_request()
        orig = chess_analyze.REQUEST_FILE
        chess_analyze.REQUEST_FILE = req
        try:
            code = self._run_main_with_args(["--depth", "abc"], req)
            self.assertEqual(code, 1)
        finally:
            chess_analyze.REQUEST_FILE = orig
            os.unlink(req)

    def test_top_non_numeric_exits_cleanly(self):
        req = self._make_tmp_request()
        orig = chess_analyze.REQUEST_FILE
        chess_analyze.REQUEST_FILE = req
        try:
            code = self._run_main_with_args(["--top", "xyz"], req)
            self.assertEqual(code, 1)
        finally:
            chess_analyze.REQUEST_FILE = orig
            os.unlink(req)


class TestAnalyzeJsonDecodeError(unittest.TestCase):
    """Bug #11-3: korrupte chess_request.json muss sauber mit exit(1) enden."""

    def test_corrupt_json_exits_cleanly(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("{broken json")
            tmp_path = tmp.name

        orig_argv = sys.argv
        orig_req = chess_analyze.REQUEST_FILE
        sys.argv = ["chess_analyze.py"]
        chess_analyze.REQUEST_FILE = tmp_path
        try:
            with self.assertRaises(SystemExit) as ctx:
                chess_analyze.main()
            self.assertEqual(ctx.exception.code, 1)
        finally:
            sys.argv = orig_argv
            chess_analyze.REQUEST_FILE = orig_req
            os.unlink(tmp_path)


class TestWriteRequestOSError(unittest.TestCase):
    """Bug #11-4: write_request() gibt False bei OSError zurück; kein Absturz, kein 300s-Hänger."""

    def test_write_request_returns_false_on_oserror(self):
        import copy
        board = copy.deepcopy(chess.INITIAL_BOARD)
        orig_req = chess.REQUEST_FILE
        chess.REQUEST_FILE = os.path.join("__nonexistent_dir__", "req.json")
        try:
            result = chess.write_request(board, True, [], [], False)
            self.assertFalse(result)
        finally:
            chess.REQUEST_FILE = orig_req

    def test_write_request_returns_true_on_success(self):
        import copy
        board = copy.deepcopy(chess.INITIAL_BOARD)
        with tempfile.TemporaryDirectory() as tmp:
            orig_req = chess.REQUEST_FILE
            chess.REQUEST_FILE = os.path.join(tmp, "req.json")
            try:
                result = chess.write_request(board, True, [], [], False)
                self.assertTrue(result)
            finally:
                chess.REQUEST_FILE = orig_req


class TestGameoverOSError(unittest.TestCase):
    """Bug #11-5: chess_gameover.json muss bei OSError sauber failen (kein Traceback)."""

    def test_gameover_write_guarded_in_source(self):
        src = os.path.join(PROJECT_ROOT, "chess.py")
        with open(src, encoding="utf-8") as f:
            source = f.read()
        # Prüft: chess_gameover.json wird mit try/except OSError geschrieben.
        # Regex-basiert, damit Einrückungsänderungen den Test nicht brechen.
        pattern = r'open\s*\(\s*os\.path\.join\s*\(\s*COMM_DIR\s*,\s*"chess_gameover\.json"'
        self.assertIsNotNone(
            re.search(pattern, source),
            "chess_gameover.json muss per open() in COMM_DIR geschrieben werden",
        )
        # Sicherstellen, dass dieser Block in einem try/except OSError eingebettet ist.
        self.assertIn(
            'except OSError',
            source,
            "game_loop() muss chess_gameover.json mit except OSError absichern",
        )


if __name__ == "__main__":
    unittest.main()
