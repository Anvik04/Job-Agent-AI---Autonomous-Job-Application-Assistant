import sys
import webbrowser

from desktop_app import STREAMLIT_URL, ensure_backend_services, start as start_browser_mode, status, stop

try:
    import webview
except Exception:  # pragma: no cover
    webview = None


def start_native_window() -> None:
    ensure_backend_services()
    if webview is None:
        webbrowser.open(STREAMLIT_URL)
        print("pywebview not installed. Opened browser fallback.")
        return
    webview.create_window("Job Agent", STREAMLIT_URL, width=1280, height=860, resizable=True)
    webview.start()


if __name__ == "__main__":
    action = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "start"
    if action == "start":
        start_native_window()
    elif action == "start-browser":
        start_browser_mode(open_browser=True)
    elif action == "stop":
        stop()
    elif action == "status":
        status()
    else:
        print("Usage: python3 desktop_window.py [start|start-browser|stop|status]")
