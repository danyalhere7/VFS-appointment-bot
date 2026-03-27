"""
config.py - Central configuration for the VFS Global appointment bot.
All sensitive values are loaded from a .env file.
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# ── VFS Login Credentials ─────────────────────────────────────────────────────
VFS_EMAIL    = os.getenv("VFS_EMAIL", "")
VFS_PASSWORD = os.getenv("VFS_PASSWORD", "")

# ── VFS Target URLs ───────────────────────────────────────────────────────────
VFS_BASE_URL    = "https://visa.vfsglobal.com/pak/en/aut"
VFS_BOOKING_URL = "https://visa.vfsglobal.com/pak/en/aut/book-an-appointment"
VFS_LOGIN_URL   = "https://visa.vfsglobal.com/pak/en/aut/login"

# ── Service Configuration ─────────────────────────────────────────────────────
VFS_COUNTRY = os.getenv("VFS_COUNTRY", "Austria")
VFS_SERVICE = os.getenv("VFS_SERVICE", "Document Legalization")

# Cities to monitor (comma-separated string → list)
CITIES = [c.strip() for c in os.getenv("CITIES", "Islamabad,Lahore").split(",")]

# ── Timing ────────────────────────────────────────────────────────────────────
MIN_DELAY = int(os.getenv("MIN_DELAY", "180"))   # seconds
MAX_DELAY = int(os.getenv("MAX_DELAY", "600"))   # seconds

# ── Browser Settings ──────────────────────────────────────────────────────────
HEADLESS        = os.getenv("HEADLESS", "false").lower() == "true"
COOKIES_FILE    = os.path.join(os.path.dirname(__file__), "session", "cookies.json")
USER_AGENT      = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


# ── Gmail Notifications ──────────────────────────────────────────────────────
# EMAIL_APP_PASSWORD must be a Gmail App Password (16-char), NOT your login password.
EMAIL_SENDER      = os.getenv("EMAIL_SENDER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_PASSWORD", "")   # env key kept as EMAIL_PASSWORD for back-compat
EMAIL_RECEIVER    = os.getenv("EMAIL_RECEIVER", "")
SMTP_HOST         = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT         = int(os.getenv("SMTP_PORT", "587"))

# ── CAPTCHA ───────────────────────────────────────────────────────────────────
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

# ── Phrases indicating NO slots available ─────────────────────────────────────
NO_SLOT_PHRASES = [
    "no appointment slots available",
    "no slots available",
    "no available appointments",
    "there are no available",
    "currently no appointments",
    "fully booked",
]

# ── Phrases indicating session expiry ────────────────────────────────────────
SESSION_EXPIRED_PHRASES = [
    "session expired",
    "please login again",
    "your session has expired",
    "sign in to continue",
    "log in to continue",
]

# ── CAPTCHA detection selectors ───────────────────────────────────────────────
CAPTCHA_SELECTORS = [
    "iframe[src*='recaptcha']",
    ".g-recaptcha",
    "#recaptcha",
    "iframe[title='reCAPTCHA']",
]
