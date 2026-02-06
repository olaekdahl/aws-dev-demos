#!/usr/bin/env python3
"""m04 - IAM: assume roles, permission detective, and policy simulation."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info
from common.cleanup import get_tracked_resources, clear_tracked

from demos.assume_role import run as assume_role_demo
from demos.access_denied_detective import run as detective_demo
from demos.policy_simulator import run as simulator_demo

MODULE = "m04"

DEMOS = {
    "assume-role": assume_role_demo,
    "detective": detective_demo,
    "policy-simulator": simulator_demo,
}

DEMO_INFO = {
    "assume-role": "create and assume a temporary IAM role",
    "detective": "test real API calls and show allowed/denied matrix",
    "policy-simulator": "simulate permissions via IAM policy simulator",
}


def _cleanup(args):
    """Remove any tracked resources left over from previous runs."""
    from common import create_session
    from botocore.exceptions import ClientError

    resources = get_tracked_resources(MODULE)
    if not resources:
        info("No tracked resources to clean up.")
        return

    session = create_session(args.profile, args.region)
    iam = session.client("iam")

    readonly_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"

    for res in reversed(resources):
        rtype = res.get("type", "")
        rid = res.get("id", "")
        info(f"Cleaning up {rtype}: {rid}")

        if rtype == "iam-role":
            # Detach known managed policies before deleting
            try:
                iam.detach_role_policy(RoleName=rid, PolicyArn=readonly_arn)
            except ClientError:
                pass
            try:
                iam.delete_role(RoleName=rid)
                info(f"  Deleted role {rid}")
            except ClientError as exc:
                info(f"  Could not delete role {rid}: {exc.response['Error']['Message']}")
        else:
            info(f"  Unknown resource type {rtype} -- skipping")

    clear_tracked(MODULE)
    info("Cleanup complete.")


def main():
    parser = build_parser("m04: IAM - Roles, Permissions & Policy Simulation", DEMO_INFO)
    parser.add_argument(
        "--role-arn",
        default=None,
        help="ARN of an existing role to assume (for assume-role demo)",
    )
    args = parser.parse_args()

    if args.cleanup:
        _cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m04", "IAM - Roles, Permissions & Policy Simulation")
        for name, fn in DEMOS.items():
            fn(args)


if __name__ == "__main__":
    main()
