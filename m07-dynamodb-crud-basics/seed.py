"""
Demo: Seed DynamoDB Table

Populates a DynamoDB table with sample data.

Usage:
    python seed.py --table mytable --profile myprofile --region us-east-1
"""
import argparse
import json
from datetime import datetime, timezone
import boto3


def main():
    parser = argparse.ArgumentParser(description="Seed DynamoDB table with sample data")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    now = datetime.now(timezone.utc).isoformat()

    # Sample items using single-table design pattern
    items = [
        {"PK": {"S": "USER#1"}, "SK": {"S": "PROFILE"}, "name": {"S": "Ada"}, "created": {"S": now}},
        {"PK": {"S": "USER#1"}, "SK": {"S": "ORDER#100"}, "total": {"N": "19.99"}, "created": {"S": now}},
        {"PK": {"S": "USER#1"}, "SK": {"S": "ORDER#101"}, "total": {"N": "9.99"}, "created": {"S": now}},
        {"PK": {"S": "USER#2"}, "SK": {"S": "PROFILE"}, "name": {"S": "Linus"}, "created": {"S": now}},
    ]

    for item in items:
        ddb.put_item(TableName=args.table, Item=item)

    print(json.dumps({"seeded": True, "table": args.table, "count": len(items)}, indent=2))


if __name__ == "__main__":
    main()
