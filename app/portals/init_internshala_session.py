from app.portals.playwright_session import session_file_for

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None


def main():
    if sync_playwright is None:
        print("Playwright not installed. Run: python3 -m pip install -r requirements.txt")
        return

    session_file = session_file_for("internshala")
    session_file.parent.mkdir(parents=True, exist_ok=True)

    print("Opening browser for Internshala manual login.")
    print("After login completes, return to terminal and press Enter.")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-crash-reporter"],
        )
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://internshala.com/login/user")
        input("Press Enter after login is complete...")
        context.storage_state(path=str(session_file))
        context.close()
        browser.close()
    print(f"Session saved: {session_file}")


if __name__ == "__main__":
    main()
