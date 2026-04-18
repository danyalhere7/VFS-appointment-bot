# VFS Global Appointment Monitoring Bot 🤖

[![GitHub Actions](https://img.shields.io/badge/Deployment-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/danyalhere7/VFS-appointment-bot/actions)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Framework-Playwright-45BA4B?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Runs](https://img.shields.io/badge/GitHub%20Actions%20Runs-536%2B%20Successful-brightgreen?logo=githubactions)](https://github.com/danyalhere7/VFS-appointment-bot/actions)
[![Uptime](https://img.shields.io/badge/Uptime-24%2F7%20Automated-blue)](https://github.com/danyalhere7/VFS-appointment-bot/actions)

An automated Python bot that monitors **Austria Document Legalization** appointment slots on VFS Global for **Islamabad** and **Lahore**. Built for 100% reliability, zero-cost cloud execution, and instant Gmail alerts — running fully unattended on GitHub Actions.

---

## 📊 Real-World Impact

> These are **live, verifiable numbers** pulled directly from GitHub Actions — not estimates.

| Metric | Value |
|---|---|
| ✅ **Successful GitHub Actions Runs** | **536+** (and counting — verified via [Actions tab](https://github.com/danyalhere7/VFS-appointment-bot/actions)) |
| 🏙️ **City Slot Checks Performed** | **1,072+** (2 cities × 536 runs: Islamabad + Lahore) |
| ⏰ **Check Frequency** | Every **10 minutes**, 24 hours/day, 7 days/week |
| 📧 **Email Notification System** | Instant Gmail alerts on slot detection (SMTP with 3-retry logic) |
| ☁️ **Infrastructure Cost** | **$0.00** — 100% free on GitHub Actions public repo |
| 🔁 **Automation Cadence** | **~144 automated checks per day** |
| 🛡️ **Uptime Since Deployment** | Continuous — self-healing with auto-recovery on session expiry |

> **Verification:** Go to [Actions → VFS Appointment Check](https://github.com/danyalhere7/VFS-appointment-bot/actions/workflows/vfs_check.yml) to see every individual run logged with timestamp, duration, and conclusion.

---

## 🚀 Key Features

*   **24/7 Cloud Automation**: Fully integrated with **GitHub Actions**. Runs on a scheduled cron (`4,14,24,34,44,54 * * * *`) — every 10 minutes — for free without your laptop ever being on.
*   **Instant Gmail Alerts**: Professional email notifications using Gmail SMTP with 3-attempt retry logic and startup configuration validation.
*   **Self-Healing Architecture**:
    *   **Per-City Retries**: If a city check fails due to slow VFS servers, the bot retries that city only.
    *   **Auto-Recovery**: Detects session expiry and automatically re-logs in.
    *   **Exponential Back-off**: Handles transient network/server errors gracefully.
*   **Anti-Bot Evasion**: Custom inline JavaScript stealth injection bypasses detection mechanisms.
*   **Session Persistence**: Saves and reloads browser cookies to minimize login frequency and avoid CAPTCHAs.
*   **Run Logging**: Every execution uploads a structured log artifact to GitHub Actions (retained 7 days), making all activity auditable.

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
├── Dockerfile                 # Multi-stage production container setup
├── docker-compose.yml         # Local containerized testing
├── deploy_gcp.sh              # Serverless GCP deployment script
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
4.  **Enable Actions**: Go to the **Actions** tab on your GitHub repo and enable the workflow. It will now run automatically every 10 minutes.

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

## 🐳 Docker Deployment (Local Containerization)

We use a **multi-stage build** leveraging a minimal `python:3.11-slim-bookworm` Debian image. This isolates dependencies and avoids needing Playwright or specific browsers installed on the host OS.

1.  **Configure**: Copy `.env.example` to `.env` and fill in your details.
2.  **Run with Compose**:
    ```bash
    # Build the image and run a single bot checking cycle
    docker compose up --build
    ```
    *(Logs are mapped to `./logs` and browser cookies mapped to `./session` via Docker volume mounts for persistence).*

---

## ☁️ Enterprise Cloud Deployment (GCP Cloud Run)

Beyond GitHub Actions, this bot is architected to run on **Google Cloud Platform (GCP)** leveraging serverless container infrastructure.

**Architecture:** Docker Container → GCP Artifact Registry → Cloud Run Job (scales to 0) → Cloud Scheduler (cron trigger).

1.  **Ensure Prerequisites**: GCP project created, billing enabled (covered by Free Tier), and `gcloud` CLI authenticated.
2.  **Execute the Deployment Script**:
    ```bash
    chmod +x deploy_gcp.sh
    ./deploy_gcp.sh
    ```
3.  **What the script automates**:
    *   Enables necessary GCP APIs (Cloud Run, Scheduler, Artifact Registry).
    *   Builds the Playwright container via Cloud Build.
    *   Deploys a **Cloud Run Job** configuring memory, timeouts, and required environment variables.
    *   Creates a **Cloud Scheduler** trigger to execute the Job via HTTP POST every 10 minutes.

---

## 🧩 CAPTCHA & Security

*   **CAPTCHA**: On GitHub Actions, the bot uses fresh IPs for every run, which typically avoids CAPTCHAs entirely. If detected, it sends an email alert and gracefully skips to the next scheduled run.
*   **Security**: Credentials are **NEVER** stored in code. They live in **GitHub Secrets** (encrypted at rest) or in your local `.env` (git-ignored).

---

## ⚠️ Disclaimer

This tool is for educational purposes only. Automated monitoring may violate VFS Global's Terms of Service. Use at your own risk and responsibility.
