"""
Demo: Create DynamoDB Table with GSI

Creates a DynamoDB table with a Global Secondary Index for alternate access patterns.

Usage:
    python create_table_with_gsi.py --prefix myprefix --profile myprofile --region us-east-1
"""
import argparse
import json
import uuid
import boto3


def generate_table_name(prefix: str) -> str:
    """Generate a unique table name."""
    return f"{prefix}-orders-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create DynamoDB table with GSI")
    parser.add_argument("--prefix", default="demo", help="Prefix for table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    table_name = generate_table_name(args.prefix)

    ddb.create_table(
        TableName=table_name,
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[{
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"},
        }]
    )

    # Wait for table to be active
    ddb.get_waiter("table_exists").wait(TableName=table_name)

    print(json.dumps({"table_created_with_gsi": table_name, "gsi_name": "GSI1"}, indent=2))
    print(f"\nTable name: {table_name}")


if __name__ == "__main__":
    main()
