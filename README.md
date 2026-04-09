# VFS Global Appointment Monitoring Bot 🤖

[![GitHub Actions](https://img.shields.io/badge/Deployment-GitHub%20Actions-blue?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Framework-Playwright-green?logo=playwright&logoColor=white)](https://playwright.dev/python/)

An automated Python bot that monitors **Austria Document Legalization** appointment slots on VFS Global for **Islamabad** and **Lahore**. Designed for high reliability, zero-cost cloud execution, and instant Gmail notifications.

---

## 🚀 Key Features

*   **24/7 Cloud Automation**: Fully integrated with **GitHub Actions**. Runs on a scheduled cron (every 10-15 min) for free without needing your laptop stayed on.
*   **Gmail Notification System**: Professional email alerts using Gmail SMTP with retry logic (3 attempts) and startup configuration testing.
*   **Self-Healing Architecture**:
    *   **Per-City Retries**: If a specific city check fails due to slow VFS servers, the bot retries that city specifically.
    *   **Auto-Recovery**: Detects session expiry and automatically performs a fresh login.
    *   **Exponential Back-off**: Handles transient network/server errors gracefully by waiting and retrying.
*   **Anti-Bot Evasion**: Custom inline JavaScript stealth injection to bypass detection.
*   **Session Persistence**: Saves and loads browser cookies to minimize login frequency and avoid CAPTCHAs.

---

## 📁 Project Structure

```text
├── .github/workflows/
│   └── vfs_check.yml         # GitHub Actions cron schedule & setup
├── main.py                    # Entry point for local 24/7 monitoring
├── check_once.py              # Entry point for Cloud/GitHub Actions execution
├── appointment_checker.py     # Core slot detection logic (hardened timeouts)
├── notification_service.py    # Gmail SMTP alerts with retry logic
├── session_manager.py         # Browser session, cookies & stealth JS
├── captcha_handler.py         # Detection & cloud-friendly skip logic
├── config.py                  # Central configuration (loaded via .env)
├── utils/
│   └── logger.py              # Structured logging (file + console)
├── requirements.txt           # Cloud-optimized dependencies
└── .env.example               # Configuration template
```

---

## 🛠️ Setup Guide (Cloud — Recommended)

This bot is designed to run for **FREE** on GitHub Actions.

1.  **Repository Setup**: Create a **Public** repository on GitHub.
2.  **Add Secrets**: Go to **Settings > Secrets and variables > Actions** and add:
    *   `VFS_EMAIL`: Your VFS account email.
    *   `VFS_PASSWORD`: Your VFS account password.
    *   `EMAIL_SENDER`: Your Gmail address.
    *   `EMAIL_PASSWORD`: Your **Gmail App Password** (16 characters).
    *   `EMAIL_RECEIVER`: Where you want to receive alerts.
3.  **Push Code**: Initialise git and push to your new repo.
    ```bash
    git init
    git add .
    git commit -m "VFS Bot Setup"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    git push -u origin main
    ```
4.  **Enable Actions**: Go to the **Actions** tab on your GitHub repo and enable the workflow. It will now run automatically on a regular schedule.

---

## 💻 Setup Guide (Local)

1.  **Clone & Install**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    playwright install chromium
    ```
2.  **Configure**: Copy `.env.example` to `.env` and fill in your details.
3.  **Run**:
    ```powershell
    python main.py
    ```

---

## 🧩 CAPTCHA & Security

*   **CAPTCHA**: On GitHub Actions, the bot uses fresh IPs for every run, which usually avoids CAPTCHAs. If detected, it sends an email alert and skips to the next run (10 min later).
*   **Security**: Your passwords are **NEVER** stored in the code. They are stored as **GitHub Secrets** (encrypted) or in your local `.env` (which is ignored by git).

---

## ⚠️ Disclaimer

This tool is for educational purposes only. Automated botting may violate VFS Global's Terms of Service. Use at your own risk.
