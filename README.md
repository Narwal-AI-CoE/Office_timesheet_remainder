# ⏱️ Office Timesheet Reminder System

An automated timesheet reminder application built for **Narwal AI** that identifies employees with unsubmitted timesheets and sends personalized reminders via **Microsoft Teams** or **Email** using the Microsoft Graph API.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [How It Works](#how-it-works)
- [Reminder Logic](#reminder-logic)

---

## Overview

HR uploads two files — an **Employee Data CSV** and a **Timesheet Report XLSX** — and the system:

1. Identifies employees with `Not Submitted` timesheet entries
2. Classifies them as **Critical** (4+ days) or **Mild** (1–3 days)
3. Auto-suggests a reminder channel — **Teams** for mild, **Email** for critical
4. Lets HR review, select, and send personalized reminders in one click

---

## Project Structure

```
Office_timesheet_remainder/
│
├── app.py                          # Streamlit dashboard (run this)
│
├── scripts/
│   ├── data_processing.py          # Loads & processes employee + timesheet data
│   ├── email_sender.py             # Sends personalized emails via Graph API
│   ├── teams_sender.py             # Sends personalized Teams messages via Graph API
│   ├── graph_auth.py               # App-only token (for email)
│   └── test_teams_auth.py          # Delegated token with device flow (for Teams)
│
├── data/
│   ├── employee_data_Export.csv    # Employee master (upload via UI or place here)
│   └── Timesheet_Report.xlsx       # Timesheet report (upload via UI)
│
├── .env                            # Environment variables (never commit this)
├── .env.example                    # Template for .env
├── requirements.txt                # Python dependencies
└── README.md
```

---

## Prerequisites

- **Python 3.10+**
- **Microsoft 365 account** with access to:
  - Microsoft Graph API (for email sending)
  - Microsoft Teams (for Teams messaging)
- **Azure App Registration** with the following permissions:
  - `Mail.Send` (Application) — for email
  - `Chat.ReadWrite` (Delegated) — for Teams
  - `User.Read` (Delegated) — for Teams auth

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Narwal-AI-CoE/Office_timesheet_remainder.git
cd Office_timesheet_remainder
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, install manually:

```bash
pip install streamlit pandas openpyxl python-dotenv msal requests
```

---

## Configuration

### 1. Create your `.env` file

Copy the example file:

```bash
cp .env.example .env
```

Fill in your values:

```env
# Microsoft Graph — App-only (for Email)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Microsoft Graph — Delegated (for Teams)
TEAMS_TENANT_ID=your-tenant-id
TEAMS_CLIENT_ID=your-teams-client-id

# Sender account
SENDER_EMAIL=autoreminder@narwal.ai

# For testing
TEST_EMAIL=your-test-email@narwal.ai
```

### 2. Domain normalisation

If your employee CSV contains old domain emails (e.g. `narwalinc.com`), the system automatically converts them to `narwal.ai` during processing. This is handled in `data_processing.py`:

```python
df['email'] = df['email'].str.replace('narwalinc.com', 'narwal.ai', regex=False)
```

---

## Running the App

> ⚠️ Always run from the **project root**, not from inside `scripts/`

```bash
streamlit run app.py
```

The app opens at:

```
http://localhost:8501
```

---

## How It Works

### Step 1 — Upload Files
Upload both files via the UI:
- **Employee Data** — exported from your HR system (CSV)
- **Timesheet Report** — Detail Timesheet Live Report (XLSX)

The app saves them with fixed filenames to the `data/` folder regardless of the uploaded filename.

### Step 2 — Process
Click **⚙️ Process & Build Reminder List**. The system:
- Parses the timesheet for `Not Submitted` entries
- Joins with employee master for contact details
- Flags unmatched employees with a warning

### Step 3 — Review
The reminder table shows:
- Employee name & email
- Reporting manager
- Number of days not submitted
- Severity badge (Critical / Mild)
- Auto-suggested channel (Teams / Email)
- Exact missing dates

Use filters to narrow by **Severity**, **Manager**, or **Channel**. Select/deselect individuals or use the header checkbox for bulk selection.

### Step 4 — Send
Click **🚀 Send Reminders**. The app sends personalized messages with the employee's name, specific missing dates, and manager name. A live progress bar tracks each send, and a results log shows success/failure per employee.

---

## Reminder Logic

| Days Not Submitted | Suggested Channel | Severity |
|--------------------|-------------------|----------|
| 1 – 3 days         | Microsoft Teams   | 🟡 Mild  |
| 4+ days            | Email             | 🔴 Critical |

HR can override the channel per employee (Teams / Email / Both) before sending.

---

## Auth Notes

- **Email** uses an **app-only token** (`graph_auth.py`) — no user interaction needed, runs silently.
- **Teams** uses a **delegated token** (`test_teams_auth.py`) — requires a one-time device flow login. The token is cached in `teams_token_cache.json` and refreshed automatically on subsequent runs.

---

## Notes

- The `data/` folder is gitignored — never commit employee data or timesheet files
- The `.env` file should never be committed — add it to `.gitignore`
- `teams_token_cache.json` contains auth tokens — keep it out of version control
