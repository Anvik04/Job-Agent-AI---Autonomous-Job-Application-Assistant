from app.portals.browser_portal import BrowserAutomationPortal
from app.portals.playwright_session import session_file_for
from app.profile_service import get_setting

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    PlaywrightTimeoutError = Exception
    sync_playwright = None


class NaukriPortal(BrowserAutomationPortal):
    name = "naukri"
    login_url = "https://www.naukri.com/nlogin/login"
    jobs_url = "https://www.naukri.com/jobs-in-india"

    def _login_if_needed(self, page) -> None:
        page.goto(self.jobs_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if "nlogin" not in page.url.lower():
            return
        email = get_setting("naukri_email", "")
        password = get_setting("naukri_password", "")
        if not email or not password:
            raise RuntimeError("Naukri credentials missing in dashboard settings.")
        page.fill("input[type='text'][placeholder*='Email'], input[type='text'][id*='username']", email)
        page.fill("input[type='password']", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        if "nlogin" in page.url.lower():
            raise RuntimeError("Naukri login failed. Check credentials or CAPTCHA/OTP.")

    def fetch_jobs(self):
        if sync_playwright is None:
            return []

        jobs = []
        session_path = session_file_for(self.name)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = (
                browser.new_context(storage_state=str(session_path))
                if session_path.exists()
                else browser.new_context()
            )
            page = context.new_page()
            try:
                self._login_if_needed(page)
                page.goto(self.jobs_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page.wait_for_selector("article.jobTuple, div.srp-jobtuple-wrapper", timeout=15000)
                cards = page.locator("article.jobTuple, div.srp-jobtuple-wrapper")
                count = min(cards.count(), 20)
                for idx in range(count):
                    card = cards.nth(idx)
                    title_locator = card.locator("a.title, a[title]").first
                    title = title_locator.inner_text().strip() if title_locator.count() else "Job Opening"
                    apply_url = title_locator.get_attribute("href") if title_locator.count() else ""
                    company_locator = card.locator("a.comp-name, a.subTitle, span.comp-name").first
                    company = company_locator.inner_text().strip() if company_locator.count() else "Unknown Company"
                    loc_locator = card.locator("span.locWdth, li.location, span.location").first
                    location = loc_locator.inner_text().strip() if loc_locator.count() else "India"
                    jobs.append(
                        {
                            "external_id": f"nk_{idx}_{abs(hash(apply_url or (title + company)))}",
                            "company": company,
                            "title": title,
                            "location": location,
                            "work_mode": "online" if "remote" in location.lower() else "offline",
                            "job_type": "full-time",
                            "description": f"Naukri listing: {title}",
                            "apply_url": apply_url or self.jobs_url,
                        }
                    )
                context.storage_state(path=str(session_path))
            except Exception:
                jobs = []
            finally:
                context.close()
                browser.close()
        return jobs

    def apply(self, job: dict, profile: dict, cover_letter: str) -> tuple[bool, str]:
        if sync_playwright is None:
            return False, "Playwright not installed. Run: python3 -m pip install -r requirements.txt"

        session_path = session_file_for(self.name)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = (
                browser.new_context(storage_state=str(session_path))
                if session_path.exists()
                else browser.new_context()
            )
            page = context.new_page()
            try:
                self._login_if_needed(page)
                page.goto(job["apply_url"], wait_until="domcontentloaded", timeout=self.timeout_ms)

                apply_btn = page.locator(
                    "button:has-text('Apply'), a:has-text('Apply'), button:has-text('Apply on company site')"
                ).first
                if apply_btn.count() == 0:
                    return False, "Apply button not found on Naukri listing."
                apply_btn.click()
                page.wait_for_timeout(1800)

                if page.locator("textarea").count() > 0:
                    page.locator("textarea").first.fill(cover_letter[:1800])

                # When redirected to external site, we only track and mark as handoff.
                if "naukri.com" not in page.url.lower():
                    context.storage_state(path=str(session_path))
                    return False, "Redirected to external company site. Manual apply may be needed."

                submit_btn = page.locator(
                    "button:has-text('Submit'), button:has-text('Send'), input[type='submit']"
                ).first
                if submit_btn.count() > 0:
                    submit_btn.click()
                    page.wait_for_timeout(2000)
                    context.storage_state(path=str(session_path))
                    return True, "Applied on Naukri via Playwright."
                return True, "Applied action completed; submission confirmation not explicit."
            except PlaywrightTimeoutError:
                return False, "Timeout during Naukri apply flow."
            except Exception as exc:
                return False, f"Naukri apply failed: {exc}"
            finally:
                context.close()
                browser.close()
