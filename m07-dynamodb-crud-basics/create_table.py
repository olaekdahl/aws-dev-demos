"""
Demo: Create DynamoDB Table

Creates a DynamoDB table with partition and sort key.

Usage:
    python create_table.py --prefix myprefix --region us-east-1
    python create_table.py --billing-mode PROVISIONED --profile myprofile --region us-west-2
"""
import argparse
import json
import uuid
import boto3


def generate_table_name(prefix: str) -> str:
    """Generate a unique table name."""
    return f"{prefix}-users-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create DynamoDB table")
    parser.add_argument("--prefix", default="demo", help="Prefix for table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--billing-mode", choices=["PAY_PER_REQUEST", "PROVISIONED"], default="PAY_PER_REQUEST")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    table_name = generate_table_name(args.prefix)

    params = {
        "TableName": table_name,
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"}
        ],
        "BillingMode": args.billing_mode
    }

    if args.billing_mode == "PROVISIONED":
        params["ProvisionedThroughput"] = {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}

    ddb.create_table(**params)

    # Wait for table to be active
    ddb.get_waiter("table_exists").wait(TableName=table_name)

    print(json.dumps({"table_created": table_name, "billing_mode": args.billing_mode}, indent=2))
    print(f"\nTable name: {table_name}")


if __name__ == "__main__":
    main()
