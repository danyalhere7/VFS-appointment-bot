"""
captcha_handler.py - Detects and handles CAPTCHA challenges.

Strategy priority:
  1. If CAPTCHA_API_KEY is set → solve automatically via 2Captcha
  2. Otherwise              → notify user and wait for manual resolution
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
            return self._solve_manually(page)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _solve_via_api(self, page: Page) -> bool:
        """Use 2Captcha API to solve reCAPTCHA automatically."""
        try:
            from twocaptcha import TwoCaptcha  # type: ignore

            solver = TwoCaptcha(config.CAPTCHA_API_KEY)

            # Extract sitekey from the page
            sitekey = page.eval_on_selector(
                ".g-recaptcha, iframe[src*='recaptcha']",
                "el => el.getAttribute('data-sitekey') || "
                "new URL(el.src).searchParams.get('k')",
            )

            if not sitekey:
                logger.error("Could not extract reCAPTCHA sitekey.")
                return self._solve_manually(page)

            logger.info("Sending reCAPTCHA to 2Captcha (sitekey: %s…)", sitekey[:8])
            result = solver.recaptcha(sitekey=sitekey, url=page.url)
            token = result["code"]

            # Inject the token and submit
            page.evaluate(
                f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';"
            )
            logger.info("CAPTCHA solved via 2Captcha API.")
            return True

        except Exception as exc:
            logger.error("2Captcha API error: %s", exc)
            return self._solve_manually(page)

    def _solve_manually(self, page: Page) -> bool:
        """Notify user to solve CAPTCHA manually, then wait up to 5 minutes."""
        wait_seconds = 300  # 5 minutes

        msg = (
            "⚠️ CAPTCHA Detected!\n\n"
            "The VFS bot has encountered a CAPTCHA and needs your help.\n"
            f"Please open the browser and solve it within {wait_seconds // 60} minutes.\n"
            f"URL: {page.url}"
        )
        self.notifier.send_all(
            title="VFS Bot — CAPTCHA Required",
            message=msg,
        )
        logger.info(
            "Waiting up to %d seconds for manual CAPTCHA resolution…", wait_seconds
        )

        start = time.time()
        while time.time() - start < wait_seconds:
            time.sleep(10)
            if not self.is_captcha_present(page):
                logger.info("CAPTCHA resolved by user.")
                return True

        logger.error("CAPTCHA not resolved within timeout — will retry next cycle.")
        return False
