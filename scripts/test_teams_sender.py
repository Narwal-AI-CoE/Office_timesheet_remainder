from dotenv import load_dotenv
load_dotenv()

import os
import requests
from test_teams_auth import get_delegated_graph_token


def send_teams_message(target_user_email, message_html):
    token = get_delegated_graph_token()

    sender_email = os.getenv("SENDER_EMAIL")  # autoreminder@narwal.ai

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # ✅ CREATE 1:1 CHAT WITH TWO USERS
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

    # ✅ SEND MESSAGE
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

    print("✅ Teams message sent successfully")


# ✅ TEST
if __name__ == "__main__":
    send_teams_message(
        "madhuri.mattaparthy@narwal.ai",
        "<b>Timesheet Reminder</b><br/>Please submit your timesheet today."
    )