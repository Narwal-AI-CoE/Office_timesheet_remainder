
import os
import msal

def get_graph_token():
    tenant_id = os.getenv("TEAMS_TENANT_ID")
    client_id = os.getenv("TEAMS_CLIENT_ID")
    client_secret = os.getenv("TEAMS_CLIENT_SECRET")

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )

    token = app.acquire_token_for_client(scopes=scope)

    if "access_token" not in token:
        raise Exception(token)

    return token["access_token"]