"""
Demo: Delete DynamoDB Table

Deletes a DynamoDB table.

Usage:
    python cleanup.py --table mytable --yes --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Delete DynamoDB table")
    parser.add_argument("--table", required=True, help="Table name to delete")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to delete without --yes flag")

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    ddb.delete_table(TableName=args.table)

    print(json.dumps({"table_deleted": args.table}, indent=2))


if __name__ == "__main__":
    main()
