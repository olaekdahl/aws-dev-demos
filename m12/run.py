#!/usr/bin/env python3
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, success, header
from common.cleanup import get_tracked_resources, clear_tracked
from common.session import create_session

from demos.signup_signin_flow import run as signup_demo
from demos.token_refresh import run as refresh_demo

DEMOS = {
    "signup-signin": signup_demo,
    "token-refresh": refresh_demo,
}
DEMO_INFO = {
    "signup-signin": "automated User Pool, App Client, sign-up & sign-in",
    "token-refresh": "token refresh flow with before/after comparison",
}

def cleanup(args):
    resources = get_tracked_resources("m12")
    if not resources:
        info("No tracked resources to clean up.")
        return
    session = create_session(args.profile, args.region)
    cognito = session.client("cognito-idp")
    for r in resources:
        if r["type"] == "cognito_user_pool":
            try:
                # Delete all app clients first
                clients = cognito.list_user_pool_clients(UserPoolId=r["id"], MaxResults=60)
                for c in clients.get("UserPoolClients", []):
                    cognito.delete_user_pool_client(UserPoolId=r["id"], ClientId=c["ClientId"])
                # Must delete the domain if one exists
                try:
                    cognito.delete_user_pool(UserPoolId=r["id"])
                except Exception:
                    pass
                success(f"Deleted User Pool: {r['id']}")
            except Exception as e:
                info(f"Could not delete {r['id']}: {e}")
    clear_tracked("m12")

def main():
    parser = build_parser("m12: Cognito Auth", DEMO_INFO)
    args = parser.parse_args()
    if args.cleanup:
        cleanup(args)
        return
    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m12", "Cognito Auth")
        for fn in DEMOS.values():
            fn(args)
        header("\nFastAPI App:")
        info("  Set env vars (shown during signup-signin demo) then:")
        info("  uvicorn m12.api.main:app --reload")

if __name__ == "__main__":
    main()
