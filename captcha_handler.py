"""
captcha_handler.py - Detects and handles CAPTCHA challenges.

On GitHub Actions (headless cloud):
  - CAPTCHA is unlikely since each run uses a fresh IP
  - If detected, logs a warning and sends a Gmail alert
  - Waits briefly then continues (cannot solve manually in cloud mode)
"""

import time
from playwright.sync_api import Page

import config
from utils.logger import get_logger
from notification_service import NotificationService

logger = get_logger("captcha_handler")


class CaptchaHandler:
    def __init__(self, notifier: NotificationService):
        self.notifier = notifier

    # ── Public API ────────────────────────────────────────────────────────────

    def is_captcha_present(self, page: Page) -> bool:
        """Return True if a CAPTCHA widget is detected on the page."""
        for selector in config.CAPTCHA_SELECTORS:
            try:
                elem = page.query_selector(selector)
                if elem and elem.is_visible():
                    logger.warning("CAPTCHA detected via selector: %s", selector)
                    return True
            except Exception:
                pass
        return False

    def handle(self, page: Page) -> bool:
        """
        Attempt to resolve a CAPTCHA.
        Returns True if resolved, False if unresolvable.
        """
        logger.warning("CAPTCHA encountered — attempting resolution.")

        if config.CAPTCHA_API_KEY:
            return self._solve_via_api(page)
        else:
            return self._notify_and_skip(page)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _solve_via_api(self, page: Page) -> bool:
        """Use 2Captcha API to solve reCAPTCHA automatically (if key is configured)."""
        try:
            from twocaptcha import TwoCaptcha  # type: ignore

            solver = TwoCaptcha(config.CAPTCHA_API_KEY)
            sitekey = page.eval_on_selector(
                ".g-recaptcha, iframe[src*='recaptcha']",
                "el => el.getAttribute('data-sitekey') || "
                "new URL(el.src).searchParams.get('k')",
            )

            if not sitekey:
                logger.error("Could not extract reCAPTCHA sitekey.")
                return self._notify_and_skip(page)

            logger.info("Sending reCAPTCHA to 2Captcha (sitekey: %s…)", sitekey[:8])
            result = solver.recaptcha(sitekey=sitekey, url=page.url)
            token = result["code"]
            page.evaluate(
                f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';"
            )
            logger.info("CAPTCHA solved via 2Captcha API.")
            return True

        except Exception as exc:
            logger.error("2Captcha API error: %s", exc)
            return self._notify_and_skip(page)

    def _notify_and_skip(self, page: Page) -> bool:
        """
        Send a Gmail alert about the CAPTCHA and skip this run.
        In cloud/headless mode we cannot solve manually, so we just
        let the next scheduled run try again from a fresh IP.
        """
        msg = (
            "⚠️ CAPTCHA Detected on VFS Website\n\n"
            "The automated check was blocked by a CAPTCHA.\n"
            "This is rare — the next run in 10 minutes will use a fresh IP and likely succeed.\n"
            f"URL: {page.url}"
        )
        try:
            self.notifier.send_all(
                title="VFS Bot — CAPTCHA Encountered",
                message=msg,
            )
        except Exception as exc:
            logger.error("Could not send CAPTCHA notification: %s", exc)

        logger.info("CAPTCHA: skipping this run — next run will retry automatically.")
        return False
