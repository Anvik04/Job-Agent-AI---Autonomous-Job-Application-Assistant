# Job-Agent-AI---Autonomous-Job-Application-Assistant
A local AI-powered desktop app that automatically finds, scores, and applies to internships/jobs (including low-competition locations), writes human-like cover letters, sends alerts, and provides a full tracking dashboard with twice-daily automation.
# Job Agent AI

Autonomous local desktop app that finds, scores, and applies to internships/jobs for you, with a special focus on **less crowded locations** and better opportunity probability.

## Why this project

Applying daily to jobs manually is repetitive and time-consuming.  
Job Agent AI automates the full process on your laptop:

- Finds jobs from supported portals
- Prioritizes suitable roles (including lower-competition cities)
- Auto-applies based on your rules
- Generates human-like cover letters
- Tracks everything in a personal dashboard
- Sends notifications for updates/replies

## Key Features

- **Autonomous daily runs** at 10 AM and 10 PM
- **Frontend dashboard + backend automation** integrated
- **Approval queue** for uncertain/low-score jobs
- **Portal support** (mock + Internshala + Naukri scaffolding/automation)
- **Retry, backoff, and per-portal rate limits**
- **Permanent local storage** (SQLite)
- **Email/Telegram alerts**
- **Native app-style launch on macOS**

## Tech Stack

- Python
- Streamlit (frontend dashboard)
- SQLite (persistent storage)
- APScheduler (automated schedules)
- Playwright (portal/browser automation)
- pywebview (native desktop window launcher)

## How it works

1. You fill profile + preferences in dashboard.
2. Agent scans enabled job portals.
3. Jobs are scored by fit + location opportunity signals.
4. Agent auto-applies (or queues for approval based on rules).
5. Dashboard shows applications, status, digest, and logs.
6. Notifications are sent for progress and cycle summaries.

## Local Setup

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
