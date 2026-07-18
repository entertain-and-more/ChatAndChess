import copy
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chess  # noqa: E402


class TerminalAccessibilityTests(unittest.TestCase):
    def test_text_board_lines_describe_initial_position(self):
        lines = chess.text_board_lines(copy.deepcopy(chess.INITIAL_BOARD))

        self.assertEqual(len(lines), 8)
        self.assertIn("Reihe 8: a8 schwarzer Turm", lines[0])
        self.assertIn("e8 schwarzer König", lines[0])
        self.assertEqual(lines[2], "Reihe 6: leer")
        self.assertIn("a2 weißer Bauer", lines[6])
        self.assertIn("e1 weißer König", lines[7])

    def test_print_text_board_exposes_screenreader_heading(self):
        output = io.StringIO()
        with redirect_stdout(output):
            chess.print_text_board(copy.deepcopy(chess.INITIAL_BOARD))

        text = output.getvalue()
        self.assertIn("Textbrett (für Screenreader)", text)
        self.assertIn("Reihe 8:", text)
        self.assertIn("weiße Dame", text)


if __name__ == "__main__":
    unittest.main()
