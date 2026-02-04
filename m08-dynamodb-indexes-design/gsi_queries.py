"""
Demo: DynamoDB GSI Queries

Demonstrates querying using both base table and GSI.

Usage:
    python gsi_queries.py --table mytable --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="DynamoDB GSI query examples")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    # Query base table - get all orders for a user
    print("=== Base Table Query: User's orders ===")
    response = ddb.query(
        TableName=args.table,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": {"S": "USER#1"}}
    )
    print(json.dumps({"base_query_user_orders": len(response.get("Items", []))}, indent=2))

    # Query GSI - get all shipped orders (different access pattern)
    print("\n=== GSI Query: All shipped orders ===")
    response = ddb.query(
        TableName=args.table,
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :pk",
        ExpressionAttributeValues={":pk": {"S": "STATUS#SHIPPED"}}
    )
    print(json.dumps({"gsi_query_shipped": len(response.get("Items", []))}, indent=2))
    for item in response.get("Items", []):
        print(json.dumps(item, default=str))


if __name__ == "__main__":
    main()
