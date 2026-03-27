"""
logger.py - Colored console + rotating file logger for the VFS bot.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ── Optional colorlog ────────────────────────────────────────────────────────
try:
    import colorlog
    _HAS_COLOR = True
except ImportError:
    _HAS_COLOR = False

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "vfs_bot.log")


def get_logger(name: str = "vfs_bot") -> logging.Logger:
    """
    Return a logger that writes to:
      - stdout (colored if colorlog is installed)
      - logs/vfs_bot.log (rotating, max 5 MB × 5 backups)
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:          # already configured
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # ── Console handler ──────────────────────────────────────────────────────
    if _HAS_COLOR:
        color_fmt = (
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s"
            " | %(cyan)s%(name)s%(reset)s | %(message)s"
        )
        console_formatter = colorlog.ColoredFormatter(
            color_fmt,
            datefmt=date_fmt,
            log_colors={
                "DEBUG":    "white",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        )
    else:
        console_formatter = logging.Formatter(fmt, datefmt=date_fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

    # ── File handler (rotating) ──────────────────────────────────────────────
    fh = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    logger.addHandler(fh)

    return logger
