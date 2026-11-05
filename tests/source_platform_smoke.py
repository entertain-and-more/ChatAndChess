import copy
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMM_DIR = PROJECT_ROOT / "chess_comm"
REQUEST_FILE = COMM_DIR / "chess_request.json"
RESPONSE_FILE = COMM_DIR / "chess_response.json"
GAMEOVER_FILE = COMM_DIR / "chess_gameover.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chess  # noqa: E402


def build_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("TERM", "xterm")
    return env


def run_command(args, *, input_text=None, timeout=20):
    return subprocess.run(
        [sys.executable, "-u", *args],
        cwd=PROJECT_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=build_env(),
    )


def assert_result(result, label):
    if result.returncode != 0:
        raise AssertionError(
            f"{label} failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def backup_runtime_files():
    backups = {}
    for path in (REQUEST_FILE, RESPONSE_FILE, GAMEOVER_FILE):
        if path.exists():
            backup = path.with_name(path.name + ".codex-bak")
            if backup.exists():
                backup.unlink()
            path.replace(backup)
            backups[path] = backup
    return backups


def restore_runtime_files(backups):
    for path in (REQUEST_FILE, RESPONSE_FILE, GAMEOVER_FILE):
        if path.exists():
            path.unlink()
    for path, backup in backups.items():
        if backup.exists():
            backup.replace(path)


def smoke_menu_quit():
    result = run_command(["chess.py"], input_text="q\n")
    assert_result(result, "Menu quit smoke")
    if "ASCII SCHACH" not in result.stdout or "Auf Wiedersehen!" not in result.stdout:
        raise AssertionError(f"Unexpected menu smoke output:\n{result.stdout}\n{result.stderr}")


def smoke_worker_boot():
    proc = subprocess.Popen(
        [sys.executable, "-u", "chess.py", "--worker"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=build_env(),
    )
    try:
        time.sleep(1.0)
        if sys.platform == "win32":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGINT)
        stdout, _ = proc.communicate(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
            stdout = ""

    # On Windows, we terminate the process, so we don't strict-check the returncode or the exit message.
    if sys.platform != "win32":
        if proc.returncode not in (0, 130):
            raise AssertionError(f"Worker smoke failed with exit code {proc.returncode}\n{stdout}")
        if "[Worker] Beendet." not in stdout:
            raise AssertionError(f"Unexpected worker smoke output (missing end marker):\n{stdout}")

    if "Chess Worker gestartet." not in stdout:
        raise AssertionError(f"Unexpected worker smoke output (missing start marker):\n{stdout}")


def write_request_fixture():
    COMM_DIR.mkdir(exist_ok=True)
    board = copy.deepcopy(chess.INITIAL_BOARD)
    castling_rights = {"K", "Q", "k", "q"}
    data = chess.build_worker_request_data(
        board,
        True,
        chess.get_legal_moves(board, True, None, castling_rights),
        [],
        False,
        en_passant_target=None,
        castling_rights=castling_rights,
    )
    REQUEST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def smoke_analyzer():
    write_request_fixture()
    result = run_command(["chess_analyze.py", "--top", "4"])
    assert_result(result, "Analyzer smoke")
    if "TAKTIK-ANALYZER" not in result.stdout or "TOP 4 KANDIDATEN" not in result.stdout:
        raise AssertionError(f"Unexpected analyzer smoke output:\n{result.stdout}\n{result.stderr}")


def smoke_cli_flags():
    # 1. Version
    res_ver = run_command(["chess.py", "--version"])
    assert_result(res_ver, "CLI --version smoke")
    if "ChatAndChess 1.2.0" not in res_ver.stdout:
        raise AssertionError(f"Unexpected --version output: {res_ver.stdout}")

    # 2. Healthcheck
    res_hc = run_command(["chess.py", "--healthcheck"])
    assert_result(res_hc, "CLI --healthcheck smoke")
    if "[Healthcheck] OK" not in res_hc.stdout:
        raise AssertionError(f"Unexpected --healthcheck output: {res_hc.stdout}")

    # 3. Help
    res_help = run_command(["chess.py", "--help"])
    assert_result(res_help, "CLI --help smoke")
    if "Verwendung:" not in res_help.stdout:
        raise AssertionError(f"Unexpected --help output: {res_help.stdout}")

    # 4. Export initial
    tmp_init = COMM_DIR / "smoke_init.json"
    try:
        res_init = run_command(["chess.py", "--export-initial", str(tmp_init)])
        assert_result(res_init, "CLI --export-initial smoke")
        if not tmp_init.is_file():
            raise AssertionError(f"Initial export file was not created at {tmp_init}")
        data = json.loads(tmp_init.read_text(encoding="utf-8"))
        if data.get("schema") != "chatandchess-game-v1":
            raise AssertionError(f"Unexpected schema in exported json: {data.get('schema')}")
    finally:
        if tmp_init.exists():
            tmp_init.unlink()

    # 5. Export PGN
    tmp_pgn = COMM_DIR / "smoke_game.pgn"
    try:
        res_pgn = run_command([
            "chess.py", "--export-pgn", str(tmp_pgn),
            "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"
        ])
        assert_result(res_pgn, "CLI --export-pgn smoke")
        if not tmp_pgn.is_file():
            raise AssertionError(f"PGN export file was not created at {tmp_pgn}")
        pgn_text = tmp_pgn.read_text(encoding="utf-8")
        if '[Event "ChatAndChess Game"]' not in pgn_text or "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6" not in pgn_text:
            raise AssertionError(f"Unexpected PGN output in smoke test:\n{pgn_text}")
    finally:
        if tmp_pgn.exists():
            tmp_pgn.unlink()

    # 6. FEN output
    res_fen = run_command(["chess.py", "--fen", "e2e4", "e7e5"])
    assert_result(res_fen, "CLI --fen smoke")
    expected_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    if expected_fen not in res_fen.stdout:
        raise AssertionError(f"Unexpected FEN output: {res_fen.stdout}")

    # 7. Translation Parity Gate (Policy P-006 Tier-2)
    res_trans = run_command(["manage_translations.py", "--check"])
    assert_result(res_trans, "Translation Parity Gate smoke")
    if "Translation Parity Gate: PASS" not in res_trans.stdout:
        raise AssertionError(f"Unexpected translation check output: {res_trans.stdout}")


def main():
    backups = backup_runtime_files()
    try:
        smoke_menu_quit()
        smoke_worker_boot()
        smoke_analyzer()
        smoke_cli_flags()
    finally:
        restore_runtime_files(backups)
    print("Platform smoke passed.")


if __name__ == "__main__":
    main()
