import json
import time
import base64
from common import create_session, banner, step, success, info, kv, table, get_tracked_resources

def run(args):
    banner("m12", "Token Refresh Flow")

    # Check if we have a tracked user pool from the signup demo
    resources = get_tracked_resources("m12")
    pool_resources = [r for r in resources if r["type"] == "cognito_user_pool"]

    if not pool_resources:
        info("No tracked User Pool found. Run the signup-signin demo first:")
        info("  python run.py --demo signup-signin")
        return

    session = create_session(args.profile, args.region)
    cognito = session.client("cognito-idp")
    pool_id = pool_resources[-1]["id"]  # Use the most recent

    # Get the app client
    step(1, "Finding app client for User Pool")
    clients = cognito.list_user_pool_clients(UserPoolId=pool_id, MaxResults=10)
    if not clients["UserPoolClients"]:
        info("No app clients found. Run signup-signin demo first.")
        return
    client_id = clients["UserPoolClients"][0]["ClientId"]
    kv("Pool ID", pool_id)
    kv("Client ID", client_id)

    # Sign in to get initial tokens
    step(2, "Signing in to get initial tokens")
    auth = cognito.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "demo@example.com", "PASSWORD": "DemoPass1!"},
    )
    tokens = auth["AuthenticationResult"]

    # Decode and show initial token expiry
    def decode_exp(token):
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        claims = json.loads(base64.b64decode(payload_b64))
        return claims.get("exp"), claims.get("iat")

    old_exp, old_iat = decode_exp(tokens["IdToken"])
    kv("Initial token exp", old_exp)
    success("Got initial tokens")

    # Wait a moment then refresh
    step(3, "Waiting 2 seconds then refreshing tokens")
    time.sleep(2)

    refresh = cognito.initiate_auth(
        ClientId=client_id,
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": tokens["RefreshToken"]},
    )
    new_tokens = refresh["AuthenticationResult"]
    new_exp, new_iat = decode_exp(new_tokens["IdToken"])

    # Compare
    step(4, "Comparing old vs new tokens")
    table(
        ["Property", "Original", "Refreshed"],
        [
            ["ID Token", tokens["IdToken"][:30] + "...", new_tokens["IdToken"][:30] + "..."],
            ["iat (issued at)", str(old_iat), str(new_iat)],
            ["exp (expires)", str(old_exp), str(new_exp)],
            ["Tokens differ?", "", "yes" if tokens["IdToken"] != new_tokens["IdToken"] else "no"],
        ],
        col_width=30,
    )

    success("Token refresh successful - new tokens issued with updated timestamps")
