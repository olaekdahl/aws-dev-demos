"""
Demo: DynamoDB Query Examples

Demonstrates GetItem, Query, and conditional PutItem operations.

Usage:
    python query_examples.py --table mytable --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3
import botocore.exceptions


def main():
    parser = argparse.ArgumentParser(description="DynamoDB query examples")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    # Example 1: GetItem - fetch a single item by primary key
    print("=== GetItem: Fetch user profile ===")
    response = ddb.get_item(
        TableName=args.table,
        Key={"PK": {"S": "USER#1"}, "SK": {"S": "PROFILE"}}
    )
    print(json.dumps({"get_item_result": response.get("Item")}, indent=2, default=str))

    # Example 2: Query - fetch all items with same PK and SK prefix
    print("\n=== Query: Fetch user's orders ===")
    response = ddb.query(
        TableName=args.table,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={
            ":pk": {"S": "USER#1"},
            ":sk": {"S": "ORDER#"}
        }
    )
    print(json.dumps({"query_orders_count": len(response.get("Items", []))}, indent=2))
    for item in response.get("Items", []):
        print(json.dumps(item, default=str))

    # Example 3: Conditional PutItem - only write if item doesn't exist
    print("\n=== Conditional PutItem: Create new user ===")
    try:
        ddb.put_item(
            TableName=args.table,
            Item={"PK": {"S": "USER#3"}, "SK": {"S": "PROFILE"}, "name": {"S": "Grace"}},
            ConditionExpression="attribute_not_exists(PK)"
        )
        print(json.dumps({"conditional_put": "success", "result": "created USER#3"}, indent=2))
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        print(json.dumps({"conditional_put": "failed", "code": error_code}, indent=2))


if __name__ == "__main__":
    main()
