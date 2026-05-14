import os
import requests
from graph_auth import get_graph_token
from dotenv import load_dotenv
load_dotenv()

def send_email(to_email, subject, html_body):
    token = get_graph_token()

    sender = "autoreminder@narwal.ai"

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
                        "address": "madhuri.mattaparthy@narwal.ai"
                    }
                }
            ]
        },
        "saveToSentItems": True
    }

    url = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in (202, 200):
        raise Exception(response.text)


if __name__ == "__main__":
    send_email(
        os.getenv("TEST_EMAIL"),
        "Timesheet Reminder – Test",
        "<p>This is a test email sent by the bot.</p>"
    )