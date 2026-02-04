"""
Demo: DynamoDB Write with Exponential Backoff Retry

Demonstrates writing to a provisioned table with retry logic.

Usage:
    python write_with_retry.py --table mytable --count 50 --profile myprofile --region us-east-1
"""
import argparse
import json
import random
import time
import boto3
import botocore.exceptions


def with_exponential_backoff(fn, retries=8, base_delay=0.25, max_delay=8.0):
    """Execute function with exponential backoff retry."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except botocore.exceptions.ClientError as e:
            last_error = e
            error_code = e.response.get("Error", {}).get("Code", "")
            # Only retry on throttling errors
            if error_code not in ["ProvisionedThroughputExceededException", "ThrottlingException"]:
                raise
            if attempt == retries:
                raise
            delay = min(max_delay, base_delay * (2 ** attempt))
            delay *= random.uniform(0.6, 1.4)  # Add jitter
            time.sleep(delay)
    raise last_error


def main():
    parser = argparse.ArgumentParser(description="Write to DynamoDB with retry")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--count", type=int, default=50, help="Number of items to write")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ddb = session.client("dynamodb")

    success_count = 0
    for i in range(args.count):
        def put_item():
            return ddb.put_item(
                TableName=args.table,
                Item={"PK": {"S": f"ITEM#{i}"}, "val": {"N": str(i)}}
            )

        try:
            with_exponential_backoff(put_item, retries=10)
            success_count += 1
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            print(json.dumps({"put_failed": True, "item": i, "code": error_code}))

    print(json.dumps({"done": True, "success": success_count, "attempted": args.count}, indent=2))


if __name__ == "__main__":
    main()
