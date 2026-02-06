#!/usr/bin/env python3
"""m07 - DynamoDB CRUD Basics: leaderboard queries, transactions, conditional writes."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, success
from common.cleanup import get_tracked_resources, clear_tracked
from common.session import create_session

from demos.gaming_leaderboard import run as leaderboard_demo
from demos.conditional_writes import run as conditional_demo

DEMOS = {
    "leaderboard": leaderboard_demo,
    "conditional": conditional_demo,
}

DEMO_INFO = {
    "leaderboard": "gaming leaderboard with queries & transactions",
    "conditional": "optimistic locking with conditional writes",
}


def cleanup(args):
    """Delete all DynamoDB tables tracked by m07 demos."""
    resources = get_tracked_resources("m07")
    if not resources:
        info("No tracked resources to clean up.")
        return
    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")
    for r in resources:
        if r["type"] == "dynamodb_table":
            try:
                ddb.delete_table(TableName=r["id"])
                success(f"Deleted table: {r['id']}")
            except Exception as e:
                info(f"Could not delete {r['id']}: {e}")
    clear_tracked("m07")


def main():
    parser = build_parser("m07: DynamoDB CRUD Basics", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m07", "DynamoDB CRUD Basics")
        for fn in DEMOS.values():
            fn(args)


if __name__ == "__main__":
    main()
