"""
Demo: Put EventBridge Event

Publishes a custom event to EventBridge.

Usage:
    python put_event.py --detail '{"orderId": "123", "total": 99.99}' --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Put event to EventBridge")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--detail", required=True, help="JSON event detail")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    events = session.client("events")

    detail = json.loads(args.detail)

    response = events.put_events(Entries=[{
        "Source": "demo.orders",
        "DetailType": "OrderCreated",
        "Detail": json.dumps(detail)
    }])

    print(json.dumps({"put_events": True, "result": response}, indent=2, default=str))


if __name__ == "__main__":
    main()
