"""
Demo: Boto3 Client vs Resource - S3 Comparison

Demonstrates the difference between boto3 low-level client and high-level resource APIs.

Usage:
    python compare_resource_vs_client.py --profile myprofile
    python compare_resource_vs_client.py  # uses default credentials
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Compare boto3 client vs resource APIs")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)

    # Low-level client API
    s3_client = session.client("s3")
    response = s3_client.list_buckets()
    client_buckets = response.get("Buckets", [])
    print(json.dumps({"method": "client.list_buckets()", "bucket_count": len(client_buckets)}, indent=2))

    # High-level resource API
    s3_resource = session.resource("s3")
    resource_buckets = list(s3_resource.buckets.all())
    print(json.dumps({"method": "resource.buckets.all()", "bucket_count": len(resource_buckets)}, indent=2))

    print("\nNote: Use client for newest APIs/fine-grained control; resource for convenient OO-style operations.")


if __name__ == "__main__":
    main()
