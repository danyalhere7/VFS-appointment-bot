"""
appointment_checker.py - Detects available appointment slots on VFS Global.

Improvements in this version:
  - Per-city retry logic (up to MAX_CITY_RETRIES attempts on transient errors)
  - Explicit waits with meaningful timeout values
  - Graceful handling of NetworkError, TimeoutError, and element-not-found
  - Detailed logging of every step outcome
"""

import time
import random
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PWTimeout, Error as PWError

import config
from utils.logger import get_logger

logger = get_logger("appointment_checker")

# Retry settings for transient page / network errors (per city)
MAX_CITY_RETRIES = 3
RETRY_WAIT       = 15  # seconds between retries

# Navigation timeouts
NAV_TIMEOUT      = 90_000   # 90 s – full page load
IDLE_TIMEOUT     = 20_000   # 20 s – networkidle
ELEMENT_TIMEOUT  = 10_000   # 10 s – element wait


@dataclass
class CheckResult:
    city: str
    available: bool
    message: str
    screenshot_path: Optional[str] = None
    error: Optional[str] = None


class AppointmentChecker:
    def __init__(self, page: Page):
        self.page = page

    # ── Public API ────────────────────────────────────────────────────────────

    def check_city(self, city: str) -> CheckResult:
        """
        Check appointment availability for the given city.
        Retries up to MAX_CITY_RETRIES times on transient failures.
        """
        last_error: Optional[str] = None

        for attempt in range(1, MAX_CITY_RETRIES + 1):
            logger.info(
                "Checking %s (attempt %d/%d)…", city, attempt, MAX_CITY_RETRIES
            )
            try:
                self._navigate_to_booking()
                self._select_service()
                self._select_city(city)
                return self._analyse_page(city)

            except PWTimeout as exc:
                last_error = f"Timeout: {exc}"
                logger.warning(
                    "Timeout on %s attempt %d/%d: %s",
                    city, attempt, MAX_CITY_RETRIES, exc,
                )

            except PWError as exc:
                last_error = f"Playwright error: {exc}"
                logger.warning(
                    "Playwright error on %s attempt %d/%d: %s",
                    city, attempt, MAX_CITY_RETRIES, exc,
                )

            except Exception as exc:
                last_error = f"Unexpected error: {exc}"
                logger.error(
                    "Unexpected error on %s attempt %d/%d: %s",
                    city, attempt, MAX_CITY_RETRIES, exc,
                )

            if attempt < MAX_CITY_RETRIES:
                logger.info(
                    "Waiting %d s before retrying %s…", RETRY_WAIT, city
                )
                time.sleep(RETRY_WAIT)

        msg = f"All {MAX_CITY_RETRIES} attempts failed for {city}. Last error: {last_error}"
        logger.error(msg)
        return CheckResult(city=city, available=False, message=msg, error=last_error)

    def check_all_cities(self) -> list[CheckResult]:
        """Check all configured cities and return their results."""
        results = []
        for city in config.CITIES:
            result = self.check_city(city)
            results.append(result)
            # Human-like pause between cities
            time.sleep(random.uniform(3, 8))
        return results

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate_to_booking(self) -> None:
        """Load the VFS booking page and wait for it to be interactive."""
        logger.debug("Navigating to booking page…")
        try:
            self.page.goto(
                config.VFS_BOOKING_URL,
                wait_until="domcontentloaded",
                timeout=NAV_TIMEOUT,
            )
        except PWTimeout:
            logger.warning(
                "Page did not reach domcontentloaded within %d ms — continuing anyway.",
                NAV_TIMEOUT,
            )

        # Best-effort networkidle wait
        try:
            self.page.wait_for_load_state("networkidle", timeout=IDLE_TIMEOUT)
        except PWTimeout:
            logger.debug("networkidle timeout — page may still be loading JS.")

        time.sleep(random.uniform(2.0, 3.5))

    def _select_service(self) -> None:
        """Select Austria → Document Legalization from the service dropdowns."""
        logger.debug(
            "Selecting service: %s — %s", config.VFS_COUNTRY, config.VFS_SERVICE
        )

        country_selectors = [
            "select[id*='country'], select[name*='country']",
            "mat-select[id*='country'], mat-select[name*='country']",
            "[aria-label*='Country'], [placeholder*='Country']",
        ]
        selected_country = self._try_select(country_selectors, config.VFS_COUNTRY)
        if selected_country:
            logger.debug("Country selected: %s", config.VFS_COUNTRY)
        else:
            logger.debug("Country dropdown not found — may already be pre-selected.")

        time.sleep(random.uniform(0.8, 1.5))

        service_selectors = [
            "select[id*='service'], select[name*='service']",
            "mat-select[id*='service'], mat-select[name*='service']",
            "[aria-label*='Service'], [placeholder*='Service']",
            "select[id*='category'], select[name*='category']",
        ]
        selected_service = self._try_select(service_selectors, config.VFS_SERVICE)
        if selected_service:
            logger.debug("Service selected: %s", config.VFS_SERVICE)
        else:
            logger.debug("Service dropdown not found — may already be pre-selected.")

        time.sleep(random.uniform(0.5, 1.2))

    def _select_city(self, city: str) -> None:
        """Select the appointment centre / city from the location dropdown."""
        logger.debug("Selecting city: %s", city)

        city_selectors = [
            "select[id*='center'], select[name*='center']",
            "select[id*='location'], select[name*='location']",
            "mat-select[id*='center'], mat-select[name*='center']",
            "[aria-label*='Center'], [placeholder*='Center']",
            "[aria-label*='Location'], [placeholder*='Location']",
        ]
        selected = self._try_select(city_selectors, city)
        if not selected:
            logger.warning(
                "City dropdown not found for '%s' — continuing with current page state.",
                city,
            )

        # Give the calendar time to update after city selection
        time.sleep(random.uniform(2.5, 4.5))
        try:
            self.page.wait_for_load_state("networkidle", timeout=IDLE_TIMEOUT)
        except PWTimeout:
            logger.debug("networkidle timeout after city select — continuing.")

    # ── Slot detection ────────────────────────────────────────────────────────

    def _analyse_page(self, city: str) -> CheckResult:
        """
        Determine slot availability using a 4-step decision tree:
          1. "No slot" phrases in page text  → NOT available
          2. Clickable calendar dates         → AVAILABLE
          3. DOM elements with 'available'    → AVAILABLE
          4. Default fall-safe                → NOT available
        """
        # Read body text safely
        try:
            body_text = self.page.inner_text("body", timeout=ELEMENT_TIMEOUT).lower()
        except Exception as exc:
            msg = f"Could not read page body for {city}: {exc}"
            logger.error(msg)
            return CheckResult(city=city, available=False, message=msg, error=str(exc))

        # ── Step 1: explicit "no slots" phrases ───────────────────────────────
        for phrase in config.NO_SLOT_PHRASES:
            if phrase in body_text:
                msg = f"No slots for {city} — found phrase: '{phrase}'"
                logger.info(msg)
                return CheckResult(city=city, available=False, message=msg)

        # ── Step 2: clickable calendar dates ──────────────────────────────────
        if self._check_calendar_for_available_dates():
            msg = f"✅ SLOT AVAILABLE for {city}! Clickable calendar date found."
            logger.info(msg)
            return CheckResult(city=city, available=True, message=msg)

        # ── Step 3: explicit "available" DOM elements ─────────────────────────
        available_selectors = [
            ".available-date",
            ".slot-available",
            "td.available",
            "button.available",
            "[class*='available']:not([class*='un'])",
            "td:not(.disabled):not(.unavailable) > button",
        ]
        for sel in available_selectors:
            try:
                elems = self.page.query_selector_all(sel)
                visible = [e for e in elems if e.is_visible() and e.is_enabled()]
                if visible:
                    msg = (
                        f"✅ SLOT AVAILABLE for {city}! "
                        f"{len(visible)} element(s) match '{sel}'."
                    )
                    logger.info(msg)
                    return CheckResult(city=city, available=True, message=msg)
            except Exception:
                pass

        # ── Step 4: default ───────────────────────────────────────────────────
        msg = f"No slots detected for {city} (default fallback)."
        logger.info(msg)
        return CheckResult(city=city, available=False, message=msg)

    def _check_calendar_for_available_dates(self) -> bool:
        """Return True if any non-disabled calendar cell is visible and enabled."""
        calendar_cells = [
            "td.mat-calendar-body-cell:not(.mat-calendar-body-disabled)",
            ".calendar-day:not(.disabled):not(.unavailable)",
            "td[aria-disabled='false']",
            "button.day:not([disabled]):not(.grayed)",
        ]
        for sel in calendar_cells:
            try:
                found = self.page.query_selector_all(sel)
                if any(e.is_visible() and e.is_enabled() for e in found):
                    return True
            except Exception:
                pass
        return False

    # ── Dropdown helper ───────────────────────────────────────────────────────

    def _try_select(self, selectors: list[str], value: str) -> bool:
        """
        Try each selector in order for both native <select> and Angular Material
        dropdowns. Returns True if the value was successfully chosen.
        """
        for sel in selectors:
            try:
                elem = self.page.query_selector(sel)
                if not elem or not elem.is_visible():
                    continue

                tag = elem.evaluate("el => el.tagName.toLowerCase()")

                if tag == "select":
                    try:
                        self.page.select_option(sel, label=value, timeout=ELEMENT_TIMEOUT)
                        return True
                    except Exception:
                        try:
                            self.page.select_option(sel, value=value, timeout=ELEMENT_TIMEOUT)
                            return True
                        except Exception:
                            pass
                else:
                    # Angular Material / custom dropdown
                    elem.click()
                    time.sleep(random.uniform(0.4, 0.8))
                    option_sel = (
                        f"mat-option:has-text('{value}'), "
                        f"li:has-text('{value}'), "
                        f"[role='option']:has-text('{value}')"
                    )
                    try:
                        self.page.click(option_sel, timeout=ELEMENT_TIMEOUT)
                        return True
                    except Exception:
                        pass

            except Exception as exc:
                logger.debug("Selector '%s' failed: %s", sel, exc)

        return False
