from app.portals.base import BasePortal
from app.profile_service import get_setting


class BrowserAutomationPortal(BasePortal):
    """
    Playwright-ready base class for real portal integrations.
    Replace placeholder methods with site-specific selectors and flows.
    """

    login_url = ""
    jobs_url = ""

    @property
    def headless(self) -> bool:
        return get_setting("browser_headless", "true").lower() == "true"

    @property
    def timeout_ms(self) -> int:
        raw = get_setting("browser_timeout_ms", "45000")
        try:
            return int(raw)
        except ValueError:
            return 45000

    def fetch_jobs(self):
        return []

    def apply(self, job: dict, profile: dict, cover_letter: str) -> tuple[bool, str]:
        return (
            False,
            "Browser automation not configured yet. Add real selectors, credentials, and CAPTCHA handling.",
        )
