import copy
import sys
import unittest


PROJECT_ROOT = r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\ENTERTAINMENT\GAMES\chess"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chess  # noqa: E402


class WorkerStateTests(unittest.TestCase):
    def test_worker_request_preserves_castling_rights_and_en_passant_target(self):
        board = copy.deepcopy(chess.INITIAL_BOARD)
        castling_rights = {"K", "Q", "k", "q"}
        en_passant_target = (3, 4)

        sequence = [
            (7, 6, 5, 5),  # g1f3
            (1, 0, 2, 0),  # a7a6
            (7, 5, 6, 4),  # f1e2
            (2, 0, 3, 0),  # a6a5
            (7, 4, 6, 4),  # e1e2
            (3, 0, 4, 0),  # a5a4
            (6, 4, 7, 4),  # e2e1
        ]
        move_history = []
        for fr, fc, tr, tc in sequence:
            chess.update_castling_rights(castling_rights, board[fr][fc], fr, fc, tr, tc)
            board = chess.make_move(board, fr, fc, tr, tc)
            move_history.append("{}{}".format(chess.pos_to_str(fr, fc), chess.pos_to_str(tr, tc)))

        data = chess.build_worker_request_data(
            board,
            True,
            chess.get_legal_moves(board, True, None, castling_rights),
            move_history,
            False,
            en_passant_target=en_passant_target,
            castling_rights=castling_rights,
        )

        self.assertEqual(data["castling_rights"], ["k", "q"])
        self.assertEqual(data["en_passant_target"], [3, 4])

        loaded = chess.load_worker_state(data)
        self.assertEqual(loaded["castling_rights"], castling_rights)
        self.assertEqual(loaded["en_passant_target"], en_passant_target)
        self.assertNotIn((7, 4, 7, 6), loaded["legal_moves"])

    def test_legal_moves_do_not_allow_capturing_the_enemy_king(self):
        board = [["." for _ in range(8)] for _ in range(8)]
        board[7][4] = "K"
        board[0][4] = "k"
        board[1][4] = "Q"

        legal = chess.get_legal_moves(board, True, None, set())

        self.assertNotIn((1, 4, 0, 4), legal)


if __name__ == "__main__":
    unittest.main()
