#!/usr/bin/env python3
"""m08 - DynamoDB Advanced: GSI access patterns, throughput retry, TTL expiring data."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, success
from common.cleanup import get_tracked_resources, clear_tracked
from common.session import create_session

from demos.gsi_access_patterns import run as gsi_demo
from demos.throughput_retry import run as throughput_demo
from demos.ttl_expiring_data import run as ttl_demo
from demos.query_vs_scan import run as query_scan_demo

DEMOS = {
    "gsi": gsi_demo,
    "throughput": throughput_demo,
    "ttl": ttl_demo,
    "query-scan": query_scan_demo,
}

DEMO_INFO = {
    "gsi": "GSI unlock alternate access patterns",
    "throughput": "exponential backoff under throttling",
    "ttl": "auto-expiring data with TTL",
    "query-scan": "Query vs Scan performance comparison",
}


def cleanup(args):
    """Delete all DynamoDB tables tracked by m08 demos."""
    resources = get_tracked_resources("m08")
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

    clear_tracked("m08")
    success("Cleanup complete")


def main():
    parser = build_parser("m08: DynamoDB Advanced", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m08", "DynamoDB Advanced")
        for fn in DEMOS.values():
            fn(args)


if __name__ == "__main__":
    main()
