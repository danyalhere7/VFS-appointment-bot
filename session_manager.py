"""
session_manager.py - Manages the Playwright browser session.

Responsibilities:
  - Launch Chromium with stealth JS (no external package dependencies)
  - Load / save cookies to persist login across restarts
  - Detect session expiry and handle re-login
  - Perform random human-like interactions (mouse jitter, scroll)
"""

import json
import os
import random
import time

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

import config
from utils.logger import get_logger

logger = get_logger("session_manager")


class SessionManager:
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> Page:
        """Launch the browser, load saved cookies, and return the active page."""
        logger.info("Starting browser session (headless=%s)…", config.HEADLESS)
        self._playwright = sync_playwright().start()

        self._browser = self._playwright.chromium.launch(
            headless=config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-gpu",
                "--window-size=1366,768",
            ],
        )

        self._context = self._browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            timezone_id="Asia/Karachi",
        )

        # Apply inline stealth patches (no external package needed)
        self._apply_stealth()

        self.page = self._context.new_page()

        # Load saved cookies if available
        self._load_cookies()

        logger.info("Browser session started.")
        return self.page

    def stop(self) -> None:
        """Save cookies and cleanly close everything."""
        logger.info("Stopping browser session…")
        self._save_cookies()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Browser session stopped.")

    def restart(self) -> Page:
        """Restart the browser session (called on errors or session expiry)."""
        logger.warning("Restarting browser session…")
        try:
            self.stop()
        except Exception:
            pass
        time.sleep(5)
        return self.start()

    # ── Navigation helpers ────────────────────────────────────────────────────

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate to a URL with a human-like pause afterwards."""
        logger.debug("Navigating to: %s", url)
        self.page.goto(url, wait_until=wait_until, timeout=60_000)
        self._human_pause(1.5, 3.0)

    # ── Session expiry detection ──────────────────────────────────────────────

    def is_session_expired(self) -> bool:
        """Return True if the current page shows a session-expired indicator."""
        try:
            text = self.page.inner_text("body").lower()
        except Exception:
            return True  # page unreadable — treat as expired

        for phrase in config.SESSION_EXPIRED_PHRASES:
            if phrase in text:
                logger.warning("Session expiry detected: '%s'", phrase)
                return True
        return False

    def handle_session_expiry(self) -> None:
        """Attempt to restore the session. Re-login if cookies alone are insufficient."""
        logger.info("Handling session expiry — attempting cookie reload…")
        self._load_cookies()
        self.navigate(config.VFS_BOOKING_URL)

        if self.is_session_expired():
            logger.info("Cookie reload insufficient — attempting fresh login…")
            self._do_login()

    # ── Human-behaviour helpers ───────────────────────────────────────────────

    def random_mouse_move(self) -> None:
        """Move the mouse to a random screen position."""
        x = random.randint(100, 1200)
        y = random.randint(100, 700)
        self.page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.4))

    def random_scroll(self) -> None:
        """Scroll a random amount down (and optionally back up)."""
        amount = random.randint(200, 600)
        self.page.mouse.wheel(0, amount)
        time.sleep(random.uniform(0.3, 0.8))
        if random.random() < 0.3:
            self.page.mouse.wheel(0, -random.randint(50, 150))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _apply_stealth(self) -> None:
        """
        Inject stealth JS using Playwright's built-in add_init_script.
        This does NOT require the playwright-stealth package.
        """
        stealth_js = """
        // Hide webdriver flag
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        // Fake plugins list
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ]
        });

        // Fake languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'ur']
        });

        // Add chrome runtime object
        if (!window.chrome) {
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
        }

        // Fix permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
        );

        // Hide automation-related properties
        delete navigator.__proto__.webdriver;
        """
        self._context.add_init_script(stealth_js)

    def _load_cookies(self) -> None:
        """Load cookies from disk into the browser context."""
        if os.path.exists(config.COOKIES_FILE):
            try:
                with open(config.COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                self._context.add_cookies(cookies)
                logger.info("Loaded %d cookies from disk.", len(cookies))
            except Exception as exc:
                logger.warning("Could not load cookies: %s", exc)
        else:
            logger.info("No saved cookies found — starting fresh.")

    def _save_cookies(self) -> None:
        """Persist current browser cookies to disk."""
        try:
            os.makedirs(os.path.dirname(config.COOKIES_FILE), exist_ok=True)
            cookies = self._context.cookies()
            with open(config.COOKIES_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            logger.info("Saved %d cookies to disk.", len(cookies))
        except Exception as exc:
            logger.warning("Could not save cookies: %s", exc)

    def _do_login(self) -> None:
        """Perform a fresh login using credentials from config."""
        if not config.VFS_EMAIL or not config.VFS_PASSWORD:
            logger.error("No VFS credentials configured — cannot auto-login.")
            return

        logger.info("Attempting fresh VFS login…")
        self.navigate(config.VFS_LOGIN_URL)

        try:
            self.page.wait_for_selector(
                "input[type='email'], input[name='email']", timeout=15_000
            )
            self._human_type(
                "input[type='email'], input[name='email']", config.VFS_EMAIL
            )
            self._human_type("input[type='password']", config.VFS_PASSWORD)
            self.page.click("button[type='submit'], input[type='submit']")
            self.page.wait_for_load_state("networkidle", timeout=30_000)
            self._save_cookies()
            logger.info("Fresh login successful.")
        except Exception as exc:
            logger.error("Fresh login failed: %s", exc)

    def _human_type(self, selector: str, text: str) -> None:
        """Type text one character at a time with random delays to mimic humans."""
        elem = self.page.query_selector(selector)
        if not elem:
            return
        elem.click()
        elem.fill("")
        for char in text:
            elem.type(char)
            time.sleep(random.uniform(0.05, 0.18))

    @staticmethod
    def _human_pause(min_s: float, max_s: float) -> None:
        time.sleep(random.uniform(min_s, max_s))
