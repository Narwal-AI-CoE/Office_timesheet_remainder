import os
import requests
from test_teams_auth import get_delegated_graph_token
from dotenv import load_dotenv
load_dotenv()


def build_teams_message(first_name: str, not_submitted_dates: str, not_submitted_count: int) -> str:
    """Builds a personalized Teams HTML message."""
    date_lines = "".join(
        f"<li>{d.strip()}</li>" for d in not_submitted_dates.split(",")
    )
    return f"""
    <p>Hi <strong>{first_name}</strong> 👋</p>
    <p>
        Just a quick heads-up — your timesheet hasn't been submitted for
        <strong>{not_submitted_count} day(s)</strong>:
    </p>
    <ul>{date_lines}</ul>
    <p>Could you please submit it at your earliest convenience? Thanks! 🙏</p>
    <p style="color:#888; font-size:12px;">— Narwal Auto Reminder</p>
    """


def send_teams_message(target_user_email: str, message_html: str):
    """
    Sends a 1:1 Teams message to target_user_email via Microsoft Graph API.
    target_user_email : recipient (dynamic, no longer hardcoded)
    message_html      : HTML body of the message
    """
    token = get_delegated_graph_token()
    sender_email = os.getenv("SENDER_EMAIL")   # autoreminder@narwal.ai

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create or retrieve existing 1:1 chat
    chat_payload = {
        "chatType": "oneOnOne",
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{sender_email}')"
            },
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{target_user_email}')"
            }
        ]
    }

    chat_resp = requests.post(
        "https://graph.microsoft.com/v1.0/chats",
        headers=headers,
        json=chat_payload
    )
    chat_resp.raise_for_status()
    chat_id = chat_resp.json()["id"]

    # Send the message
    msg_payload = {
        "body": {
            "contentType": "html",
            "content": message_html
        }
    }

    msg_resp = requests.post(
        f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages",
        headers=headers,
        json=msg_payload
    )
    msg_resp.raise_for_status()


def send_reminder_teams(row) -> dict:
    """
    Convenience wrapper — accepts a reminder_df row (as dict or Series).
    Returns a result dict with success/error info.
    """
    try:
        message_html = build_teams_message(
            first_name          = row["first_name"],
            not_submitted_dates = row["not_submitted_dates"],
            not_submitted_count = row["not_submitted_count"],
        )
        send_teams_message(row["email"], message_html)
        return {"status": "success", "channel": "teams", "email": row["email"]}
    except Exception as e:
        return {"status": "error", "channel": "teams", "email": row["email"], "error": str(e)}


if __name__ == "__main__":
    test_row = {
        "first_name"          : "Test",
        "not_submitted_dates" : "01 May 2025, 02 May 2025",
        "not_submitted_count" : 2,
        "email"               : os.getenv("TEST_EMAIL"),
    }
    result = send_reminder_teams(test_row)
    print(result)