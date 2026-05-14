import os
import msal

TOKEN_CACHE = "teams_token_cache.json"

def get_delegated_graph_token():
    tenant_id = os.getenv("TEAMS_TENANT_ID")
    client_id = os.getenv("TEAMS_CLIENT_ID")

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ["Chat.ReadWrite", "User.Read"]

    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE):
        cache.deserialize(open(TOKEN_CACHE, "r").read())

    app = msal.PublicClientApplication(
        client_id,
        authority=authority,
        token_cache=cache
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
    else:
        flow = app.initiate_device_flow(scopes=scopes)
        print(flow["message"])   # shows device login instructions
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise Exception(result)

    with open(TOKEN_CACHE, "w") as f:
        f.write(cache.serialize())

    return result["access_token"]