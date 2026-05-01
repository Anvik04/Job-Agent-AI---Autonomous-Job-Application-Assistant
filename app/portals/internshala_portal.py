from app.portals.browser_portal import BrowserAutomationPortal
from app.portals.playwright_session import session_file_for
from app.profile_service import get_setting

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    PlaywrightTimeoutError = Exception
    sync_playwright = None


class InternshalaPortal(BrowserAutomationPortal):
    name = "internshala"
    login_url = "https://internshala.com/login/user"
    jobs_url = "https://internshala.com/internships/"

    def _login_if_needed(self, page) -> None:
        page.goto(self.login_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        if "login" not in page.url.lower():
            return
        email = get_setting("internshala_email", "")
        password = get_setting("internshala_password", "")
        if not email or not password:
            raise RuntimeError("Internshala credentials missing in dashboard settings.")
        page.fill("input[name='email']", email)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(2500)
        if "login" in page.url.lower():
            raise RuntimeError("Internshala login failed. Check credentials or CAPTCHA.")

    def fetch_jobs(self):
        if sync_playwright is None:
            return []

        jobs = []
        session_path = session_file_for(self.name)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-crash-reporter"],
            )
            context = (
                browser.new_context(storage_state=str(session_path))
                if session_path.exists()
                else browser.new_context()
            )
            page = context.new_page()

            try:
                self._login_if_needed(page)
                page.goto(self.jobs_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page.wait_for_selector("div.individual_internship, div.internship_meta", timeout=15000)

                cards = page.locator("div.individual_internship, div.internship_meta")
                if cards.count() == 0:
                    raise RuntimeError("Internshala page loaded but internship cards not found for known selectors.")
                count = min(cards.count(), 15)
                for idx in range(count):
                    card = cards.nth(idx)
                    title_el = card.locator(
                        "a.job-title-href, a[href*='internship-details'], a:has-text('Internship')"
                    ).first
                    title = title_el.inner_text().strip() if title_el.count() else ""

                    company_el = card.locator(
                        "p.company-name, span.company-name, a.company-name"
                    ).first
                    company = company_el.inner_text().strip() if company_el.count() else ""

                    loc_el = card.locator(
                        "div.row-1-item.locations, span.locations, li.location, span.location"
                    ).first
                    location = loc_el.inner_text().strip() if loc_el.count() else ""

                    href = title_el.get_attribute("href") or ""
                    apply_url = href if href.startswith("http") else f"https://internshala.com{href}" if href else ""
                    if not apply_url:
                        apply_url = f"{self.jobs_url}#intern_{idx}"
                    jobs.append(
                        {
                            "external_id": f"is_{idx}_{abs(hash(apply_url + title + company))}",
                            "company": company or "Unknown Company",
                            "title": title or "Internship",
                            "location": location or "India",
                            "work_mode": "online" if "work from home" in (location or "").lower() else "offline",
                            "job_type": "internship",
                            "description": f"Internshala listing: {title or 'Internship'}",
                            "apply_url": apply_url,
                        }
                    )
                context.storage_state(path=str(session_path))
            except Exception as exc:
                raise RuntimeError(f"Internshala fetch_jobs failed: {exc}")
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
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-crash-reporter"],
            )
            context = (
                browser.new_context(storage_state=str(session_path))
                if session_path.exists()
                else browser.new_context()
            )
            page = context.new_page()
            try:
                self._login_if_needed(page)
                page.goto(job["apply_url"], wait_until="domcontentloaded", timeout=self.timeout_ms)

                apply_btn = page.locator("button:has-text('Apply now'), a:has-text('Apply now')").first
                if apply_btn.count() == 0:
                    return False, "Apply button not found on Internshala listing."
                apply_btn.click()
                page.wait_for_timeout(1200)

                if page.locator("textarea").count() > 0:
                    page.locator("textarea").first.fill(cover_letter[:1800])
                if page.locator("input[type='file']").count() > 0:
                    return False, "Resume upload field detected. Auto-upload path not configured."

                submit_btn = page.locator(
                    "button:has-text('Submit'), button:has-text('Apply'), input[type='submit']"
                ).first
                if submit_btn.count() == 0:
                    return False, "Submit button not detected after opening apply flow."
                submit_btn.click()
                page.wait_for_timeout(2000)
                context.storage_state(path=str(session_path))
                return True, "Applied on Internshala via Playwright."
            except PlaywrightTimeoutError:
                return False, "Timeout during Internshala apply flow."
            except Exception as exc:
                return False, f"Internshala apply failed: {exc}"
            finally:
                context.close()
                browser.close()
