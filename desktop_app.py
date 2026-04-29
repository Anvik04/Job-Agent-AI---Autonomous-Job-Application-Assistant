import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "runtime_logs"
PID_DIR = DATA_DIR / "pids"

STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"


def _ensure_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PID_DIR.mkdir(parents=True, exist_ok=True)


def _pid_file(name: str) -> Path:
    return PID_DIR / f"{name}.pid"


def _is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid(name: str) -> int:
    path = _pid_file(name)
    if not path.exists():
        return 0
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _write_pid(name: str, pid: int) -> None:
    _pid_file(name).write_text(str(pid))


def _start_detached(command: list[str], log_name: str) -> int:
    log_path = LOG_DIR / log_name
    with open(log_path, "a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            command,
            cwd=str(BASE_DIR),
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    return proc.pid


def _stop_process(name: str) -> None:
    pid = _read_pid(name)
    if not pid:
        return
    if not _is_pid_running(pid):
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        if _is_pid_running(pid):
            os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def ensure_backend_services() -> None:
    _ensure_dirs()

    scheduler_pid = _read_pid("scheduler")
    if not scheduler_pid or not _is_pid_running(scheduler_pid):
        new_pid = _start_detached([sys.executable, "scheduler.py"], "scheduler.log")
        _write_pid("scheduler", new_pid)

    streamlit_pid = _read_pid("streamlit")
    if not streamlit_pid or not _is_pid_running(streamlit_pid) or not _is_port_open(STREAMLIT_PORT):
        new_pid = _start_detached(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "dashboard.py",
                "--server.port",
                str(STREAMLIT_PORT),
                "--browser.gatherUsageStats",
                "false",
            ],
            "streamlit.log",
        )
        _write_pid("streamlit", new_pid)

        for _ in range(40):
            if _is_port_open(STREAMLIT_PORT):
                break
            time.sleep(0.25)


def start(open_browser: bool = True) -> None:
    ensure_backend_services()
    if open_browser:
        webbrowser.open(STREAMLIT_URL)
    print(f"Job Agent app opened at {STREAMLIT_URL}")


def stop() -> None:
    _stop_process("streamlit")
    _stop_process("scheduler")
    print("Job Agent processes stopped.")


def status() -> None:
    scheduler_pid = _read_pid("scheduler")
    streamlit_pid = _read_pid("streamlit")
    scheduler_ok = bool(scheduler_pid and _is_pid_running(scheduler_pid))
    streamlit_ok = bool(streamlit_pid and _is_pid_running(streamlit_pid) and _is_port_open(STREAMLIT_PORT))
    print(f"scheduler_running={scheduler_ok} pid={scheduler_pid}")
    print(f"streamlit_running={streamlit_ok} pid={streamlit_pid} url={STREAMLIT_URL}")


if __name__ == "__main__":
    action = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "start"
    if action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "status":
        status()
    else:
        print("Usage: python3 desktop_app.py [start|stop|status]")
