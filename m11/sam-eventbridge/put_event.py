"""Put a custom event to EventBridge."""
import argparse
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from common import create_session, banner, step, success, kv

DEFAULT_DETAIL = '{"orderId": "ORD-001", "customer": "Ada", "total": 99.99}'


def main():
    parser = argparse.ArgumentParser(description="Put event to EventBridge")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--detail", default=DEFAULT_DETAIL, help="JSON event detail")
    args = parser.parse_args()

    banner("m11", "EventBridge - Put Event")
    session = create_session(args.profile, args.region)
    events = session.client("events")

    detail = json.loads(args.detail)

    step(1, "Publishing custom event")
    kv("Source", "awsdev.orders")
    kv("DetailType", "OrderCreated")
    kv("Detail", json.dumps(detail, indent=2))

    response = events.put_events(Entries=[{
        "Source": "awsdev.orders",
        "DetailType": "OrderCreated",
        "Detail": json.dumps(detail),
    }])

    success(f"Event published (FailedEntryCount={response.get('FailedEntryCount', 0)})")


if __name__ == "__main__":
    main()
