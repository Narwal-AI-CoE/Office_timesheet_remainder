import os
import requests
from graph_auth import get_graph_token
from dotenv import load_dotenv
load_dotenv()

SENDER_EMAIL = "autoreminder@narwal.ai"


def build_email_body(first_name: str, not_submitted_dates: str, manager_name: str) -> str:
    """Builds a personalized HTML email body."""
    dates_list = "".join(
        f"<li>{d.strip()}</li>" for d in not_submitted_dates.split(",")
    )
    return f"""
    <div style="font-family: Segoe UI, Arial, sans-serif; font-size: 14px; color: #1a1a1a; max-width: 600px;">
        <p>Hi {first_name},</p>
        <p>
            This is a reminder that your timesheet has <strong>not been submitted</strong>
            for the following date(s):
        </p>
        <ul style="background:#fff8e1; border-left: 4px solid #f5a623; padding: 10px 10px 10px 30px; border-radius: 4px;">
            {dates_list}
        </ul>
        <p>
            Please log in and submit your timesheet as soon as possible.
            If you have any questions or are facing issues, please reach out to your manager
            <strong>{manager_name}</strong>.
        </p>
        <p style="margin-top: 24px;">
            Thank you,<br/>
            <strong>Narwal Auto Reminder</strong><br/>
            <span style="color: #888; font-size: 12px;">This is an automated message. Please do not reply directly to this email.</span>
        </p>
    </div>
    """


def send_email(to_email: str, subject: str, html_body: str):
    """
    Sends an email via Microsoft Graph API.
    to_email  : recipient email address (dynamic)
    subject   : email subject line
    html_body : HTML content of the email
    """
    token = get_graph_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email        # ← dynamic, no longer hardcoded
                    }
                }
            ]
        },
        "saveToSentItems": True
    }

    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 202):
        raise Exception(f"Email to {to_email} failed: {response.text}")


def send_reminder_email(row) -> dict:
    """
    Convenience wrapper — accepts a reminder_df row (as dict or Series).
    Returns a result dict with success/error info.
    """
    try:
        html_body = build_email_body(
            first_name          = row["first_name"],
            not_submitted_dates = row["not_submitted_dates"],
            manager_name        = row["manager_name"],
        )
        subject = f"Timesheet Submission Reminder — Action Required ({row['not_submitted_count']} day(s) pending)"
        send_email(row["email"], subject, html_body)
        return {"status": "success", "channel": "email", "email": row["email"]}
    except Exception as e:
        return {"status": "error", "channel": "email", "email": row["email"], "error": str(e)}


if __name__ == "__main__":
    # Quick test with a dummy row
    test_row = {
        "first_name"          : "Test",
        "not_submitted_dates" : "01 May 2025, 02 May 2025",
        "not_submitted_count" : 2,
        "manager_name"        : "John Smith",
        "email"               : os.getenv("TEST_EMAIL"),
    }
    result = send_reminder_email(test_row)
    print(result)