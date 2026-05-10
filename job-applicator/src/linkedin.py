"""
LinkedIn browser automation using Playwright + playwright-stealth.

Responsibilities:
  - Login (with session persistence and MFA handling)
  - Job search (pagination, scraping job cards)
  - Easy Apply submission (multi-step form handling, CV upload)
"""
from __future__ import annotations

import logging
import random
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)
from playwright_stealth import stealth_sync

from src.config import AppSettings, LinkedInConfig
from src.tracker import (
    STATUS_ALREADY_APPLIED,
    STATUS_APPLIED,
    STATUS_ERROR,
    STATUS_PENDING_MANUAL,
    STATUS_SKIPPED_TOO_MANY_QUESTIONS,
)

logger = logging.getLogger(__name__)

# Chrome UA for Chromium — keeps fingerprint consistent
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# LinkedIn URL filter param mappings
_REMOTE_PARAMS: Dict[str, str] = {
    "remote": "2",
    "hybrid": "3",
    "onsite": "1",
}
_JOB_TYPE_PARAMS: Dict[str, str] = {
    "full-time": "F",
    "part-time": "P",
    "contract": "C",
    "internship": "I",
}

# Form field labels we know how to prefill (lowercase)
_PREFILLABLE_LABELS = {
    "first name", "last name", "full name", "name",
    "email", "email address", "phone", "phone number", "mobile",
    "linkedin profile", "linkedin url", "profile url",
    "city", "location", "address",
    "years of experience", "years experience",
    "are you legally authorized", "work authorization",
    "require sponsorship", "visa sponsorship",
    "resume", "cv", "upload resume", "upload cv",
}


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ManualInterventionRequired(Exception):
    """Raised when LinkedIn requires human interaction (CAPTCHA, etc.)."""


class LinkedInRateLimitError(Exception):
    """Raised when LinkedIn restricts the account."""


# ---------------------------------------------------------------------------
# LinkedInSession
# ---------------------------------------------------------------------------

class LinkedInSession:
    """
    Context-manager wrapper around a Playwright browser session targeting LinkedIn.

    Usage:
        with LinkedInSession(li_config, app_settings, tracker, dry_run=False) as session:
            session.login()
            jobs = session.search_jobs("Security Analyst", max_pages=3)
            status = session.apply_easy_apply(jobs[0])
    """

    # ── Selectors ─────────────────────────────────────────────────────────────
    # All selectors use semantic attributes (aria-label, role, data-*, text)
    # so they remain stable across LinkedIn CSS class changes.
    SEL_EMAIL      = 'input[autocomplete="username"]'
    SEL_PASSWORD   = 'input[autocomplete="current-password"]'
    SEL_SIGN_IN    = 'button[type="submit"]'
    SEL_MFA_INPUT  = 'input[name="pin"]'
    SEL_JOB_CARD   = '[data-job-id]'
    SEL_EASY_APPLY = 'button:has-text("Easy Apply")'
    SEL_NEXT       = 'button:has-text("Next")'
    SEL_REVIEW     = 'button:has-text("Review")'
    SEL_SUBMIT     = 'button:has-text("Submit application")'
    SEL_DISMISS    = 'button[aria-label="Dismiss"]'
    SEL_DISCARD    = 'button:has-text("Discard")'
    SEL_PAGINATION = 'button[aria-label="View next page"]'

    def __init__(
        self,
        li_config: LinkedInConfig,
        app_settings: AppSettings,
        dry_run: bool = False,
    ) -> None:
        self._cfg = li_config
        self._settings = app_settings
        self._dry_run = dry_run
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._cv_text: Optional[str] = None

    def __enter__(self) -> "LinkedInSession":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self._settings.headless,
            slow_mo=50,
            args=["--disable-blink-features=AutomationControlled"],
        )
        session_file = self._cfg.session_path / "state.json"
        if session_file.exists():
            logger.debug("Loading saved session from %s", session_file)
            self._context = self._browser.new_context(
                storage_state=str(session_file),
                user_agent=_USER_AGENT,
                viewport={"width": 1366, "height": 768},
            )
        else:
            self._context = self._browser.new_context(
                user_agent=_USER_AGENT,
                viewport={"width": 1366, "height": 768},
            )
        self._page = self._context.new_page()
        stealth_sync(self._page)

    def stop(self) -> None:
        if self._context:
            try:
                self._save_session()
            except Exception as exc:
                logger.warning("Could not save session: %s", exc)
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # ── Login ────────────────────────────────────────────────────────────────

    def login(self) -> None:
        """
        Log in to LinkedIn. Reuses saved session if valid; falls back to
        full credential login. Handles MFA prompts.
        """
        page = self._page
        page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded")
        self._random_delay()

        if self._is_logged_in():
            logger.info("Reusing existing LinkedIn session.")
            return

        logger.info("Logging in to LinkedIn as %s…", self._cfg.email)
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        self._random_delay()

        # Fill credentials with human-like typing
        page.locator(self.SEL_EMAIL).click()
        page.keyboard.type(self._cfg.email, delay=random.randint(60, 140))
        page.locator(self.SEL_PASSWORD).click()
        page.keyboard.type(self._cfg.password, delay=random.randint(60, 140))
        self._random_delay(0.5, 1.5)
        page.locator(self.SEL_SIGN_IN).click()

        try:
            page.wait_for_url("**/feed**", timeout=10_000)
            self._save_session()
            logger.info("Login successful.")
            return
        except PlaywrightTimeoutError:
            pass

        # Check for MFA
        try:
            page.wait_for_selector(self.SEL_MFA_INPUT, timeout=5_000)
            self._handle_mfa()
            return
        except PlaywrightTimeoutError:
            pass

        # Check for CAPTCHA / checkpoint
        if "checkpoint" in page.url or "challenge" in page.url:
            raise ManualInterventionRequired(
                "LinkedIn CAPTCHA detected. Run with --no-headless, solve the CAPTCHA "
                "manually, then re-run. The session will be saved for future runs."
            )

        # Check for account restriction
        self._check_rate_limit()

        raise ManualInterventionRequired(
            f"Login did not reach /feed. Current URL: {page.url}\n"
            "Try running with --no-headless to debug."
        )

    def _handle_mfa(self) -> None:
        page = self._page
        logger.warning(
            "\n[ACTION REQUIRED] LinkedIn MFA detected.\n"
            "Open the browser at: %s\n"
            "Complete the verification, then press Enter here to continue…",
            page.url,
        )
        input()
        try:
            page.wait_for_url("**/feed**", timeout=120_000)
            self._save_session()
            logger.info("MFA completed. Session saved.")
        except PlaywrightTimeoutError:
            raise ManualInterventionRequired(
                "Timed out waiting for LinkedIn feed after MFA. "
                "Please complete verification and re-run."
            )

    def _is_logged_in(self) -> bool:
        try:
            self._page.wait_for_url("**/feed**", timeout=5_000)
            return True
        except PlaywrightTimeoutError:
            return False

    def _save_session(self) -> None:
        session_dir = self._cfg.session_path
        session_dir.mkdir(parents=True, exist_ok=True)
        self._context.storage_state(path=str(session_dir / "state.json"))

    def _check_rate_limit(self) -> None:
        url = self._page.url
        if "authwall" in url or "restricted" in url.lower():
            raise LinkedInRateLimitError(
                "LinkedIn has restricted this account. "
                "Wait 24 hours before trying again."
            )

    # ── Search ───────────────────────────────────────────────────────────────

    def search_jobs(self, role: str, max_pages: int) -> List[dict]:
        """
        Search LinkedIn Jobs for `role` and return raw job dicts.
        Paginates up to max_pages result pages.
        """
        url = self._build_search_url(role)
        logger.info("Searching: %s", url)
        self._page.goto(url, wait_until="domcontentloaded")
        self._random_delay()

        all_jobs: List[dict] = []
        for page_num in range(1, max_pages + 1):
            self._check_rate_limit()
            cards = self._scrape_job_cards()
            logger.debug("Page %d: scraped %d job cards.", page_num, len(cards))
            all_jobs.extend(cards)

            if page_num < max_pages and not self._paginate_to_next():
                logger.debug("No more pages for role '%s'.", role)
                break
            self._random_delay()

        return all_jobs

    def _build_search_url(self, role: str) -> str:
        from src.config import FilterConfig  # avoid circular at module level
        params: Dict[str, str] = {
            "keywords": role,
            "refresh": "true",
        }

        # Remote / work-type filter
        remote = self._get_filter_config_remote()
        if remote and remote != "any":
            params["f_WT"] = _REMOTE_PARAMS.get(remote, "")

        # Job type filter
        job_types = self._get_filter_config_job_types()
        if job_types:
            codes = [_JOB_TYPE_PARAMS[jt] for jt in job_types if jt in _JOB_TYPE_PARAMS]
            if codes:
                params["f_JT"] = ",".join(codes)

        return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)

    # These two helpers avoid storing the full config in this class; instead
    # main.py passes the relevant slices via build_search_url being called
    # directly from search_jobs which has access to settings already.
    # We store them on the instance so _build_search_url can read them.
    def set_filter_config(self, remote_preference: str, job_types: List[str]) -> None:
        self._remote_preference = remote_preference
        self._job_types = job_types

    def _get_filter_config_remote(self) -> str:
        return getattr(self, "_remote_preference", "any")

    def _get_filter_config_job_types(self) -> List[str]:
        return getattr(self, "_job_types", [])

    def _scrape_job_cards(self) -> List[dict]:
        """Extract job data from all cards visible on the current search page."""
        page = self._page
        jobs: List[dict] = []

        try:
            page.wait_for_selector(self.SEL_JOB_CARD, timeout=10_000)
        except PlaywrightTimeoutError:
            logger.warning("No job cards found on page.")
            return jobs

        cards = page.locator(self.SEL_JOB_CARD).all()
        for card in cards:
            try:
                job_id = card.get_attribute("data-job-id")
                if not job_id:
                    continue

                # Title — look for the most prominent link/heading inside the card
                title = ""
                try:
                    title = card.locator("a[href*='/jobs/view/']").first.inner_text(timeout=2000).strip()
                except Exception:
                    pass

                # Company name
                company = ""
                try:
                    company = card.locator(".job-card-container__primary-description, [class*='company']").first.inner_text(timeout=2000).strip()
                except Exception:
                    pass

                # Location
                location = ""
                try:
                    location = card.locator("[class*='location'], [class*='Location']").first.inner_text(timeout=2000).strip()
                except Exception:
                    pass

                # Salary text (not always present on cards)
                salary_text = ""
                try:
                    salary_text = card.locator("[class*='salary'], [class*='compensation']").first.inner_text(timeout=1000).strip()
                except Exception:
                    pass

                # Easy Apply badge on the card
                easy_apply = False
                try:
                    badge = card.locator("li:has-text('Easy Apply'), span:has-text('Easy Apply')")
                    easy_apply = badge.count() > 0
                except Exception:
                    pass

                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary_text": salary_text or None,
                    "salary_min": None,
                    "salary_max": None,
                    "easy_apply": easy_apply,
                    "job_type": None,
                    "description_snippet": "",
                    "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                })
            except Exception as exc:
                logger.debug("Error scraping card: %s", exc)

        return jobs

    def scrape_job_detail(self, job_id: str) -> dict:
        """
        Navigate to a job detail page and extract richer information.
        Used when exclude_keywords filtering requires the description.
        """
        page = self._page
        page.goto(
            f"https://www.linkedin.com/jobs/view/{job_id}/",
            wait_until="domcontentloaded",
        )
        self._random_delay()
        self._check_rate_limit()

        detail: dict = {
            "description_snippet": "",
            "job_type": None,
            "salary_text": None,
            "easy_apply": False,
        }

        try:
            desc = page.locator(".jobs-description__content, [class*='description']").first.inner_text(timeout=5000)
            detail["description_snippet"] = desc[:600]
        except Exception:
            pass

        try:
            # Job type is often in a criteria list
            criteria = page.locator(".jobs-unified-top-card__job-insight, [class*='criteria']").all_inner_texts()
            for text in criteria:
                lower = text.lower()
                for jt in ("full-time", "part-time", "contract", "internship"):
                    if jt in lower:
                        detail["job_type"] = jt
                        break
        except Exception:
            pass

        try:
            detail["easy_apply"] = page.locator(self.SEL_EASY_APPLY).count() > 0
        except Exception:
            pass

        return detail

    def _paginate_to_next(self) -> bool:
        page = self._page
        try:
            btn = page.locator(self.SEL_PAGINATION)
            if btn.count() == 0:
                return False
            if btn.get_attribute("disabled") is not None:
                return False
            btn.click()
            page.wait_for_selector(self.SEL_JOB_CARD, state="attached", timeout=10_000)
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception as exc:
            logger.debug("Pagination error: %s", exc)
            return False

    # ── Easy Apply ───────────────────────────────────────────────────────────

    def apply_easy_apply(self, job: dict) -> str:
        """
        Attempt to submit an Easy Apply application for `job`.
        Returns a STATUS_* constant from tracker.
        """
        page = self._page
        job_id = job["id"]
        url = job.get("url", f"https://www.linkedin.com/jobs/view/{job_id}/")

        logger.info("Applying to: %s — %s", job.get("title"), job.get("company"))

        try:
            page.goto(url, wait_until="domcontentloaded")
            self._random_delay()
            self._check_rate_limit()

            # Already applied?
            if self._is_already_applied():
                logger.info("Already applied to job %s.", job_id)
                return STATUS_ALREADY_APPLIED

            # Click Easy Apply button
            btn = page.locator(self.SEL_EASY_APPLY).first
            if btn.count() == 0 or not btn.is_visible():
                logger.debug("No Easy Apply button found for job %s.", job_id)
                return STATUS_PENDING_MANUAL

            btn.click()
            self._random_delay(1, 3)

            # Handle the multi-step form
            result = self._fill_easy_apply_form()

            if result == "too_many_questions":
                self._dismiss_modal()
                return STATUS_SKIPPED_TOO_MANY_QUESTIONS

            if self._dry_run:
                logger.info("[DRY RUN] Would submit application for job %s.", job_id)
                self._dismiss_modal()
                return STATUS_APPLIED

            # Submit
            submit_btn = page.locator(self.SEL_SUBMIT).first
            if submit_btn.is_visible(timeout=5_000):
                submit_btn.click()
                self._random_delay(2, 4)
                logger.info("Application submitted for job %s.", job_id)
                return STATUS_APPLIED

            logger.warning("Submit button not found for job %s.", job_id)
            self._dismiss_modal()
            return STATUS_ERROR

        except ManualInterventionRequired:
            raise
        except LinkedInRateLimitError:
            raise
        except Exception as exc:
            logger.error("Error applying to job %s: %s", job_id, exc)
            self._dismiss_modal(silent=True)
            return STATUS_ERROR
        finally:
            time.sleep(self._settings.inter_application_delay)

    def _is_already_applied(self) -> bool:
        try:
            badge = self._page.locator(
                "span:has-text('Applied'), .jobs-apply-button--applied"
            )
            return badge.count() > 0
        except Exception:
            return False

    def _fill_easy_apply_form(self) -> str:
        """
        Step through the Easy Apply multi-step form.
        Returns "ok" when the review/submit step is reached, or
        "too_many_questions" if threshold is exceeded.
        """
        page = self._page
        max_steps = 15

        for step in range(max_steps):
            self._random_delay(0.5, 1.5)

            custom_count = self._count_custom_questions()
            if custom_count > self._settings.max_custom_questions:
                logger.info(
                    "Skipping: %d custom questions > limit %d.",
                    custom_count,
                    self._settings.max_custom_questions,
                )
                return "too_many_questions"

            self._fill_current_step()

            if self._is_review_step() or self._is_submit_visible():
                return "ok"

            if not self._click_next():
                logger.debug("No Next button found at step %d.", step)
                break

        return "ok"

    def _count_custom_questions(self) -> int:
        """Count form fields that can't be automatically prefilled."""
        page = self._page
        custom = 0
        try:
            # Find all visible form fields
            inputs = page.locator(
                "input:visible, textarea:visible, select:visible"
            ).all()
            for inp in inputs:
                input_type = inp.get_attribute("type") or "text"
                if input_type in ("file", "hidden", "submit", "button"):
                    continue

                # Get associated label text
                label_text = self._get_label_text(inp).lower()

                is_prefillable = any(
                    known in label_text for known in _PREFILLABLE_LABELS
                )

                # textareas are always custom (open-ended)
                tag = inp.evaluate("el => el.tagName.toLowerCase()")
                if tag == "textarea":
                    custom += 1
                elif not is_prefillable and label_text:
                    custom += 1
        except Exception as exc:
            logger.debug("Error counting custom questions: %s", exc)
        return custom

    def _fill_current_step(self) -> None:
        """Fill all visible form fields on the current step."""
        page = self._page

        # CV file upload
        try:
            file_inputs = page.locator("input[type='file']").all()
            for fi in file_inputs:
                if fi.is_visible():
                    fi.set_input_files(str(self._cfg.cv_path))
                    self._random_delay(0.5, 1.5)
        except Exception as exc:
            logger.debug("File input error: %s", exc)

        # Text/email/tel inputs
        try:
            text_inputs = page.locator(
                "input[type='text']:visible, input[type='email']:visible, "
                "input[type='tel']:visible, input[type='number']:visible"
            ).all()
            for inp in text_inputs:
                label = self._get_label_text(inp).lower()
                value = self._prefill_value_for(label)
                if value and not inp.input_value():
                    inp.click()
                    page.keyboard.type(value, delay=random.randint(40, 100))
                    self._random_delay(0.3, 0.8)
        except Exception as exc:
            logger.debug("Text input error: %s", exc)

        # Select dropdowns
        try:
            selects = page.locator("select:visible").all()
            for sel in selects:
                label = self._get_label_text(sel).lower()
                value = self._prefill_select_for(label, sel)
                if value:
                    sel.select_option(label=value)
                    self._random_delay(0.3, 0.8)
        except Exception as exc:
            logger.debug("Select error: %s", exc)

        # Radio buttons (Yes/No questions)
        try:
            radios = page.locator("input[type='radio']:visible").all()
            for radio in radios:
                label = self._get_label_text(radio).lower()
                if "yes" in label:
                    if not radio.is_checked():
                        radio.click()
                    break
        except Exception as exc:
            logger.debug("Radio error: %s", exc)

    def _get_label_text(self, element) -> str:
        """Retrieve the label text associated with a form element."""
        try:
            label_id = element.get_attribute("id")
            if label_id:
                label = self._page.locator(f"label[for='{label_id}']")
                if label.count():
                    return label.first.inner_text(timeout=1000).strip()

            # Try aria-label
            aria = element.get_attribute("aria-label")
            if aria:
                return aria.strip()

            # Try placeholder
            placeholder = element.get_attribute("placeholder")
            if placeholder:
                return placeholder.strip()

            # Walk up DOM to find nearest label or legend
            return element.evaluate("""el => {
                let node = el.parentElement;
                for (let i = 0; i < 4; i++) {
                    if (!node) break;
                    const label = node.querySelector('label, legend, h3, h4');
                    if (label) return label.innerText;
                    node = node.parentElement;
                }
                return '';
            }""").strip()
        except Exception:
            return ""

    def _prefill_value_for(self, label: str) -> str:
        """Return a default value for a known text field label."""
        cv_text = self._get_cv_text()

        if any(k in label for k in ("first name", "firstname")):
            return self._extract_from_cv(cv_text, r"^([A-Z][a-z]+)", "") or ""
        if any(k in label for k in ("last name", "lastname", "surname")):
            return self._extract_from_cv(cv_text, r"^[A-Z][a-z]+\s+([A-Z][a-z]+)", "") or ""
        if "email" in label:
            return self._cfg.email
        if any(k in label for k in ("phone", "mobile", "telephone")):
            return self._extract_from_cv(cv_text, r"(\+?[\d\s\-\(\)]{10,})", "") or ""
        if any(k in label for k in ("years of experience", "years experience")):
            return "3"
        if any(k in label for k in ("city", "location", "address")):
            return ""
        if any(k in label for k in ("linkedin", "profile url")):
            return ""
        return ""

    def _prefill_select_for(self, label: str, select_element) -> Optional[str]:
        """Return the best option label for a known select field."""
        try:
            options = select_element.locator("option").all_inner_texts()
        except Exception:
            options = []

        if any(k in label for k in ("authorized", "authorization", "legally")):
            return next((o for o in options if "yes" in o.lower()), None)
        if any(k in label for k in ("sponsorship", "sponsor", "visa")):
            return next((o for o in options if "no" in o.lower()), None)
        if any(k in label for k in ("years of experience", "experience")):
            return next((o for o in options if "3" in o or "2" in o), None)

        # Default: pick first non-blank option
        return next((o for o in options if o.strip() and o.strip() != "Select an option"), None)

    def _is_review_step(self) -> bool:
        try:
            return self._page.locator(
                "h3:has-text('Review'), h2:has-text('Review your application')"
            ).count() > 0
        except Exception:
            return False

    def _is_submit_visible(self) -> bool:
        try:
            btn = self._page.locator(self.SEL_SUBMIT)
            return btn.count() > 0 and btn.first.is_visible()
        except Exception:
            return False

    def _click_next(self) -> bool:
        page = self._page
        try:
            for selector in (self.SEL_NEXT, self.SEL_REVIEW):
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    self._random_delay(1, 2)
                    return True
            return False
        except Exception as exc:
            logger.debug("Next button click error: %s", exc)
            return False

    def _dismiss_modal(self, silent: bool = False) -> None:
        page = self._page
        try:
            dismiss = page.locator(self.SEL_DISMISS).first
            if dismiss.is_visible(timeout=3_000):
                dismiss.click()
                self._random_delay(0.5, 1.5)
                # Confirm discard dialog if it appears
                discard = page.locator(self.SEL_DISCARD).first
                if discard.is_visible(timeout=3_000):
                    discard.click()
                    self._random_delay(0.5, 1.0)
        except Exception as exc:
            if not silent:
                logger.debug("Dismiss modal error: %s", exc)

    # ── CV text extraction ───────────────────────────────────────────────────

    def _get_cv_text(self) -> str:
        if self._cv_text is not None:
            return self._cv_text
        try:
            import pdfplumber
            with pdfplumber.open(str(self._cfg.cv_path)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            self._cv_text = "\n".join(pages)
        except Exception as exc:
            logger.warning("Could not extract CV text: %s", exc)
            self._cv_text = ""
        return self._cv_text

    def _extract_from_cv(self, text: str, pattern: str, default: str) -> str:
        import re
        if not text:
            return default
        m = re.search(pattern, text, re.MULTILINE)
        return m.group(1).strip() if m else default

    # ── Delays ───────────────────────────────────────────────────────────────

    def _random_delay(
        self,
        lo: Optional[float] = None,
        hi: Optional[float] = None,
    ) -> None:
        lo = lo if lo is not None else self._settings.min_delay
        hi = hi if hi is not None else self._settings.max_delay
        time.sleep(random.uniform(lo, hi))
