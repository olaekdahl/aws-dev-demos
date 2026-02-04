"""
Demo: List S3 Buckets

Lists all S3 buckets in the account.

Usage:
    python list_buckets.py --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="List S3 buckets")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    response = s3.list_buckets()
    buckets = response.get("Buckets", [])

    print(f"Found {len(buckets)} buckets:\n")
    for bucket in buckets:
        print(json.dumps({
            "name": bucket["Name"],
            "created": bucket["CreationDate"].isoformat()
        }))


if __name__ == "__main__":
    main()
