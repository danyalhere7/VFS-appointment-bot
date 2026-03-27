"""
main.py - VFS Global Appointment Bot — Main Orchestration Loop

Usage:
    python main.py

Press Ctrl+C to stop the bot gracefully.
"""

import random
import sys
import time
from datetime import datetime

import config
from appointment_checker import AppointmentChecker
from captcha_handler import CaptchaHandler
from notification_service import NotificationService
from session_manager import SessionManager
from utils.logger import get_logger

logger = get_logger("main")

# ── Banner ─────────────────────────────────────────────────────────────────────

BANNER = r"""
 __   _____ ____    ____        _
 \ \ / / __|  __|  | __ )  ___ | |_
  \ V /| _| \__ \  |  _ \ / _ \|  _|
   \_/ |_|  |____| |_.__/ \___/ \__|

  Austria Document Legalization Appointment Monitor
  Notification : Gmail  ({email})
  Monitoring   : {cities}
  Interval     : {min_d}–{max_d} minutes
"""


def print_banner() -> None:
    print(
        BANNER.format(
            email=config.EMAIL_SENDER or "not configured",
            cities=", ".join(config.CITIES),
            min_d=config.MIN_DELAY // 60,
            max_d=config.MAX_DELAY // 60,
        )
    )


# ── Core monitoring loop ───────────────────────────────────────────────────────

def run_monitoring_loop(
    session: SessionManager,
    notifier: NotificationService,
    captcha: CaptchaHandler,
) -> None:
    """
    Infinite monitoring loop.

    Each cycle:
      1. Check for CAPTCHA and resolve it.
      2. Check for session expiry and renew.
      3. Check all cities for available slots.
      4. Send Gmail alert for any slot found.
      5. Sleep a random interval before the next cycle.

    Any transient error is logged; the loop continues automatically.
    A browser restart is attempted only on repeated failures.
    """
    check_count  = 0
    slots_found: set[str] = set()   # avoid duplicate emails within one session
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5      # restart browser after this many consecutive fails

    while True:
        check_count += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("═" * 60)
        logger.info("Check #%d  |  %s", check_count, ts)
        logger.info("═" * 60)

        cycle_ok = False

        try:
            # ── CAPTCHA check ─────────────────────────────────────────────────
            try:
                if captcha.is_captcha_present(session.page):
                    logger.warning("CAPTCHA detected — attempting resolution.")
                    resolved = captcha.handle(session.page)
                    if not resolved:
                        logger.warning("CAPTCHA unresolved — restarting session.")
                        _safe_restart(session)
                        continue
            except Exception as exc:
                logger.error("Error during CAPTCHA check: %s", exc)

            # ── Session expiry check ──────────────────────────────────────────
            try:
                if session.is_session_expired():
                    logger.warning("Session expired — attempting renewal.")
                    session.handle_session_expiry()
            except Exception as exc:
                logger.error("Error during session expiry check: %s", exc)

            # ── Check all cities ──────────────────────────────────────────────
            checker = AppointmentChecker(session.page)
            results = checker.check_all_cities()

            for result in results:
                if result.error:
                    logger.error(
                        "❌ Error checking %s: %s", result.city, result.error
                    )
                    continue

                if result.available:
                    if result.city not in slots_found:
                        logger.info("🎉 SLOT FOUND for %s!", result.city)
                        slots_found.add(result.city)
                        notifier.appointment_found(result.city)
                    else:
                        logger.info(
                            "Slot still available for %s (notification already sent).",
                            result.city,
                        )
                else:
                    logger.info(
                        "City: %-12s | %s", result.city, "No slots ❌"
                    )

            # ── Save cookies ──────────────────────────────────────────────────
            try:
                session._save_cookies()
            except Exception as exc:
                logger.warning("Could not save cookies: %s", exc)

            cycle_ok = True
            consecutive_errors = 0

        except Exception as exc:
            consecutive_errors += 1
            logger.error(
                "Unhandled error in monitoring cycle #%d (%d consecutive): %s",
                check_count, consecutive_errors, exc,
                exc_info=True,
            )

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.warning(
                    "%d consecutive errors — restarting browser session.",
                    consecutive_errors,
                )
                _safe_restart(session)
                consecutive_errors = 0
            else:
                # Short back-off before retrying the same cycle
                backoff = 30 * consecutive_errors
                logger.info("Waiting %d s before retrying…", backoff)
                time.sleep(backoff)
                continue

        # ── Randomised sleep between cycles ───────────────────────────────────
        delay = random.randint(config.MIN_DELAY, config.MAX_DELAY)
        logger.info(
            "Next check in %d s (%.1f min)%s",
            delay,
            delay / 60,
            f"  |  this cycle {'✅' if cycle_ok else '❌'}",
        )
        _countdown_sleep(delay)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_restart(session: SessionManager) -> None:
    """Restart the browser with exponential back-off; exit after 5 consecutive failures."""
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        wait = 30 * attempt
        try:
            session.restart()
            session.navigate(config.VFS_BOOKING_URL)
            logger.info("Browser restarted successfully on attempt %d.", attempt)
            return
        except Exception as exc:
            logger.error(
                "Restart attempt %d/%d failed: %s. Retrying in %d s…",
                attempt, max_retries, exc, wait,
            )
            time.sleep(wait)
    logger.critical("All %d restart attempts failed. Exiting.", max_retries)
    sys.exit(1)


def _countdown_sleep(seconds: int) -> None:
    """Sleep in 30-second chunks, logging a dot each chunk so the terminal stays alive."""
    slept = 0
    while slept < seconds:
        chunk = min(30, seconds - slept)
        time.sleep(chunk)
        slept += chunk


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print_banner()

    notifier = NotificationService()
    session  = SessionManager()
    captcha  = CaptchaHandler(notifier)

    # ── Verify email configuration at startup ──────────────────────────────
    logger.info("Verifying Gmail configuration…")
    if notifier.test_email():
        logger.info("✅ Startup email test passed — Gmail is working.")
    else:
        logger.warning(
            "⚠️  Startup email test FAILED. Check EMAIL_SENDER, EMAIL_PASSWORD, "
            "and EMAIL_RECEIVER in your .env file before leaving the bot unattended."
        )

    # ── Start browser ──────────────────────────────────────────────────────
    try:
        session.start()
        session.navigate(config.VFS_BOOKING_URL)
        logger.info("Browser started. Monitoring loop beginning now.")
    except Exception as exc:
        logger.critical("Failed to start browser session: %s", exc)
        sys.exit(1)

    # ── Run the monitoring loop ────────────────────────────────────────────
    try:
        run_monitoring_loop(session, notifier, captcha)
    except KeyboardInterrupt:
        logger.info("Shutdown requested (Ctrl+C).")
    except Exception as exc:
        logger.critical("Fatal exception in main loop: %s", exc, exc_info=True)
        notifier.send_all(
            title="VFS Bot — Fatal Crash",
            message=(
                f"⚠️ The VFS bot crashed with an unexpected error:\n{exc}\n\n"
                "Please restart it manually."
            ),
        )
    finally:
        try:
            session.stop()
        except Exception:
            pass
        logger.info("VFS Bot stopped. Goodbye.")


if __name__ == "__main__":
    main()
