"""
Demo: Create Provisioned DynamoDB Table

Creates a DynamoDB table with provisioned throughput (RCU/WCU = 1).
Useful for demonstrating throughput limits and retry behavior.

Usage:
    python create_provisioned_table.py --prefix myprefix --profile myprofile --region us-east-1
"""
import argparse
import json
import uuid
import boto3


def generate_table_name(prefix: str) -> str:
    """Generate a unique table name."""
    return f"{prefix}-throughput-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create provisioned DynamoDB table")
    parser.add_argument("--prefix", default="demo", help="Prefix for table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    table_name = generate_table_name(args.prefix)

    ddb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Wait for table to be active
    ddb.get_waiter("table_exists").wait(TableName=table_name)

    print(json.dumps({
        "table_created": table_name,
        "billing_mode": "PROVISIONED",
        "rcu": 1,
        "wcu": 1
    }, indent=2))
    print(f"\nTable name: {table_name}")


if __name__ == "__main__":
    main()
