"""
Demo: Seed DynamoDB Table with GSI Data

Populates a DynamoDB table with sample data including GSI attributes.

Usage:
    python seed.py --table mytable --profile myprofile --region us-east-1
"""
import argparse
import json
from datetime import datetime, timezone
import boto3


def main():
    parser = argparse.ArgumentParser(description="Seed DynamoDB table with GSI data")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    now = datetime.now(timezone.utc).isoformat()

    # Sample items with GSI attributes for alternate access patterns
    items = [
        {
            "PK": {"S": "USER#1"}, "SK": {"S": "ORDER#100"},
            "status": {"S": "PENDING"}, "created": {"S": now},
            "GSI1PK": {"S": "STATUS#PENDING"}, "GSI1SK": {"S": "USER#1#ORDER#100"}
        },
        {
            "PK": {"S": "USER#2"}, "SK": {"S": "ORDER#200"},
            "status": {"S": "SHIPPED"}, "created": {"S": now},
            "GSI1PK": {"S": "STATUS#SHIPPED"}, "GSI1SK": {"S": "USER#2#ORDER#200"}
        },
        {
            "PK": {"S": "USER#1"}, "SK": {"S": "ORDER#101"},
            "status": {"S": "SHIPPED"}, "created": {"S": now},
            "GSI1PK": {"S": "STATUS#SHIPPED"}, "GSI1SK": {"S": "USER#1#ORDER#101"}
        },
    ]

    for item in items:
        ddb.put_item(TableName=args.table, Item=item)

    print(json.dumps({"seeded": True, "table": args.table, "count": len(items)}, indent=2))


if __name__ == "__main__":
    main()
