import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
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


def smoke_export_cli():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "chatandchess-game-v1.json"
        result = run_command(["chess.py", "--export-initial", str(target)])
        assert_result(result, "Initial export smoke")
        data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("schema") != "chatandchess-game-v1":
        raise AssertionError(f"Unexpected export schema: {data!r}")
    if "fen" not in data.get("position", {}):
        raise AssertionError(f"Export has no FEN position: {data!r}")


def main():
    backups = backup_runtime_files()
    try:
        smoke_menu_quit()
        smoke_worker_boot()
        smoke_analyzer()
        smoke_export_cli()
    finally:
        restore_runtime_files(backups)
    print("Platform smoke passed.")


if __name__ == "__main__":
    main()
