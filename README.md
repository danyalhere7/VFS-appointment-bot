# VFS Global Appointment Monitoring Bot 🤖

An automated Python bot that monitors **Austria Document Legalization** appointment slots on VFS Global for **Islamabad** and **Lahore**, and instantly notifies you when a slot becomes available.

---

## 📁 Project Structure

```
New folder/
├── main.py                  # Entry point & monitoring loop
├── config.py                # All settings (loaded from .env)
├── appointment_checker.py   # Slot detection logic
├── notification_service.py  # Telegram / Email / Desktop alerts
├── captcha_handler.py       # CAPTCHA detection & resolution
├── session_manager.py       # Browser session & cookie management
├── utils/
│   └── logger.py            # Rotating file + colored console log
├── session/                 # Auto-saved browser cookies
├── logs/                    # vfs_bot.log written here
├── requirements.txt
├── .env.example             # ← copy this to .env and fill in values
└── README.md
```

---

## ⚙️ Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11 or higher |
| Google Chrome / Chromium | Any recent version |

---

## 🚀 Quick Setup

### 1 — Clone / open the project folder

```powershell
cd "c:\Users\Muhammad Danyal\Desktop\New folder"
```

### 2 — Create a virtual environment and activate it

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

### 4 — Install Playwright browsers

```powershell
playwright install chromium
```

### 5 — Configure the bot

```powershell
copy .env.example .env
notepad .env
```

Fill in at minimum:

| Variable | Description |
|----------|-------------|
| `VFS_EMAIL` | Your VFS account email |
| `VFS_PASSWORD` | Your VFS account password |
| `TELEGRAM_BOT_TOKEN` | Get from [@BotFather](https://t.me/BotFather) on Telegram |
| `TELEGRAM_CHAT_ID` | Get from [@userinfobot](https://t.me/userinfobot) on Telegram |
| `EMAIL_SENDER` | Gmail/Outlook address to send from |
| `EMAIL_PASSWORD` | App password (not your login password) for Gmail |
| `EMAIL_RECEIVER` | Address to receive alerts |

> **Tip:** Email and Telegram are both optional — the bot skips any channel with missing credentials. Desktop notifications always work.

### 6 — Run the bot

```powershell
python main.py
```

The browser will open (visible by default), navigate to VFS, and begin checking every 3–10 minutes.

---

## 🔔 Notification Channels

### Telegram (recommended)
1. Message **@BotFather** on Telegram → `/newbot` → copy the token.
2. Message **@userinfobot** on Telegram → copy your numeric chat ID.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`.

### Email (Gmail)
1. Enable **2-step verification** on your Gmail account.
2. Go to **Google Account → Security → App Passwords** → create one for "Mail".
3. Set `EMAIL_SENDER`, `EMAIL_PASSWORD`, and `EMAIL_RECEIVER` in `.env`.

### Desktop Notifications
Works automatically via `plyer` — no configuration needed.

---

## 🧩 CAPTCHA Handling

| Scenario | Bot Behaviour |
|----------|--------------|
| `CAPTCHA_API_KEY` is set | Solves automatically via **2Captcha** API |
| No API key | Sends you a notification; waits up to 5 minutes for you to solve it manually in the browser |
| Browser visible | Running in non-headless mode significantly reduces CAPTCHA frequency |

> **Recommended:** Keep `HEADLESS=false` in `.env` for the lowest CAPTCHA rate.

---

## 🔐 Session Expiry Handling

1. The bot saves cookies after every successful cycle to `session/cookies.json`.
2. On the next startup, cookies are restored to skip the login page.
3. If the page shows *"Session expired"* or *"Please login again"*, the bot:
   - Reloads saved cookies
   - If that fails, performs a fresh login using `VFS_EMAIL` / `VFS_PASSWORD`
   - Resumes monitoring automatically

---

## 🌆 Changing Monitored Cities or Services

### Change cities
Edit `.env`:
```
CITIES=Islamabad,Lahore,Karachi
```

Or edit `config.py` directly:
```python
CITIES = ["Islamabad", "Lahore", "Karachi"]
```

### Change service
Edit `.env`:
```
VFS_COUNTRY=Austria
VFS_SERVICE=Document Legalization
```

### Change check interval
```
MIN_DELAY=120   # minimum seconds between checks
MAX_DELAY=300   # maximum seconds between checks
```

---

## 🖥️ Running 24/7

### Option A — Keep terminal open (local machine)

```powershell
python main.py
```

### Option B — Windows Task Scheduler (recommended for local 24/7)

1. Open **Task Scheduler** → Create Basic Task.
2. Set trigger: **At startup** or **Daily**.
3. Set action: `python.exe` with argument `main.py` and start-in `"c:\Users\Muhammad Danyal\Desktop\New folder"`.

### Option C — VPS / cloud server (Linux)

```bash
# Install Python, Playwright, etc.
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# Run with nohup (stays alive after SSH disconnect)
nohup python main.py > logs/nohup.log 2>&1 &

# Or as a systemd service for auto-restart on crash
```

---

## 📋 Logs

All events are written to `logs/vfs_bot.log` (rotating, max 5 MB × 5 backups):

| Event | What is logged |
|-------|---------------|
| Each check | Timestamp, city, availability status |
| Slot found | City name, notification channels used |
| CAPTCHA | Detection method, resolution outcome |
| Session expiry | Detection phrase, recovery action |
| Errors | Full traceback |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Browser doesn't open | Run `playwright install chromium` |
| Login fails | Check credentials in `.env`; try `HEADLESS=false` |
| CAPTCHA every run | Use `HEADLESS=false`; add `CAPTCHA_API_KEY` in `.env` |
| Telegram not sending | Verify token and chat ID; test with `python -c "from notification_service import NotificationService; NotificationService().notify_telegram('test')"` |
| Email fails | Use Gmail App Password (not your account password) |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `playwright` | Browser automation |
| `playwright-stealth` | Anti-bot fingerprint evasion |
| `python-dotenv` | Load `.env` config |
| `requests` | Telegram HTTP calls |
| `plyer` | Desktop notifications |
| `2captcha-python` | Optional auto CAPTCHA solving |
| `colorlog` | Colored terminal output |
