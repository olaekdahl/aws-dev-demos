#!/usr/bin/env python3
"""m09 - Lambda: deploy, invoke, cold starts, and error handling."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from botocore.exceptions import ClientError
from common.args import build_parser
from common.output import banner, step, success, fail, info, warn, kv
from common.session import create_session
from common.cleanup import get_tracked_resources, clear_tracked

from demos.deploy_and_invoke import run as deploy_demo
from demos.cold_start_measurement import run as cold_start_demo
from demos.error_handling import run as error_demo

DEMOS = {
    "deploy": deploy_demo,
    "cold-start": cold_start_demo,
    "errors": error_demo,
}

DEMO_INFO = {
    "deploy": "deploy and invoke word frequency analyzer",
    "cold-start": "measure cold start vs warm invocations",
    "errors": "explore Lambda error handling patterns",
}


def cleanup(args):
    """Delete all tracked Lambda functions and IAM roles."""
    resources = get_tracked_resources("m09")

    if not resources:
        info("No tracked m09 resources to clean up.")
        return

    banner("m09", "Cleanup")
    info(f"Found {len(resources)} tracked resource(s) to remove.\n")

    session = create_session(args.profile, args.region)
    lam = session.client("lambda")
    iam = session.client("iam")

    # Delete Lambda functions first, then IAM roles (roles may be in use)
    functions = [r for r in resources if r["type"] == "lambda_function"]
    roles = [r for r in resources if r["type"] == "iam_role"]
    others = [r for r in resources if r["type"] not in ("lambda_function", "iam_role")]

    for i, resource in enumerate(functions, 1):
        rid = resource["id"]
        step(i, f"Deleting Lambda function: {rid}")
        try:
            lam.delete_function(FunctionName=rid)
            success(f"Function '{rid}' deleted")
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                info(f"Function '{rid}' already gone -- skipping")
            else:
                fail(f"Could not delete function '{rid}': {exc}")

    offset = len(functions)
    for i, resource in enumerate(roles, offset + 1):
        role_name = resource["id"]
        step(i, f"Deleting IAM role: {role_name}")
        try:
            # Detach all managed policies before deleting the role
            paginator = iam.get_paginator("list_attached_role_policies")
            for page in paginator.paginate(RoleName=role_name):
                for policy in page.get("AttachedPolicies", []):
                    iam.detach_role_policy(
                        RoleName=role_name, PolicyArn=policy["PolicyArn"],
                    )
                    info(f"  Detached policy: {policy['PolicyName']}")

            iam.delete_role(RoleName=role_name)
            success(f"Role '{role_name}' deleted")
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "NoSuchEntity":
                info(f"Role '{role_name}' already gone -- skipping")
            else:
                fail(f"Could not delete role '{role_name}': {exc}")

    for resource in others:
        warn(f"Unknown resource type '{resource['type']}' -- skipping '{resource['id']}'")

    clear_tracked("m09")
    success("m09 cleanup complete -- tracking file cleared")


def main():
    parser = build_parser("m09: Lambda", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m09", "Lambda")
        for name, fn in DEMOS.items():
            fn(args)


if __name__ == "__main__":
    main()
