"""
check_once.py - Single-run VFS appointment checker for GitHub Actions.

This script performs ONE check cycle (all cities) and exits.
GitHub Actions calls it on a cron schedule (e.g., every 10 minutes).

All configuration is read from environment variables, which GitHub
passes in from encrypted Repository Secrets.

Exit codes:
  0 — Check completed (slot found or not)
  1 — Fatal startup error (bad config, browser won't start)
"""

import sys
import os
from datetime import datetime

# ── Patch: ensure project root is on sys.path ──────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from appointment_checker import AppointmentChecker
from notification_service import NotificationService
from session_manager import SessionManager
from utils.logger import get_logger

logger = get_logger("check_once")


def main() -> int:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("═" * 60)
    logger.info("VFS Check — %s", ts)
    logger.info("Cities   : %s", ", ".join(config.CITIES))
    logger.info("Service  : %s — %s", config.VFS_COUNTRY, config.VFS_SERVICE)
    logger.info("═" * 60)

    # ── Validate email config before doing any browser work ─────────────────
    if not config.EMAIL_SENDER or not config.EMAIL_APP_PASSWORD or not config.EMAIL_RECEIVER:
        logger.error(
            "Email not configured. Set EMAIL_SENDER, EMAIL_PASSWORD, "
            "and EMAIL_RECEIVER as GitHub Secrets."
        )
        return 1

    notifier = NotificationService()
    session  = SessionManager()

    try:
        # ── Start browser ────────────────────────────────────────────────────
        logger.info("Starting browser (headless)…")
        session.start()
        session.navigate(config.VFS_BOOKING_URL)
        logger.info("Navigation complete.")

        # ── Check all cities ─────────────────────────────────────────────────
        checker = AppointmentChecker(session.page)
        results = checker.check_all_cities()

        slots_found = False
        for result in results:
            if result.error:
                logger.error("Error for %s: %s", result.city, result.error)
                continue

            if result.available:
                logger.info("🎉 SLOT FOUND for %s!", result.city)
                notifier.appointment_found(result.city)
                slots_found = True
            else:
                logger.info("No slots for %-12s ❌", result.city)

        if not slots_found:
            logger.info("No slots available this cycle — will check again next run.")

    except Exception as exc:
        logger.error("Fatal error during check: %s", exc, exc_info=True)
        # Don't exit 1 — GitHub Actions will still mark the run as succeeded
        # so the cron continues running. A failed run won't block future runs.

    finally:
        try:
            session.stop()
        except Exception:
            pass

    logger.info("Check complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
