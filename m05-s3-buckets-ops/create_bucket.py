"""
Demo: Create S3 Bucket

Creates a new S3 bucket with a unique name.

Usage:
    python create_bucket.py --prefix myprefix --region us-west-2
    python create_bucket.py --profile myprofile --region us-east-1
"""
import argparse
import json
import uuid
import boto3


def generate_bucket_name(prefix: str) -> str:
    """Generate a unique bucket name."""
    return f"{prefix}-bucket-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create an S3 bucket")
    parser.add_argument("--prefix", default="demo", help="Prefix for bucket name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    bucket_name = generate_bucket_name(args.prefix)

    # Create bucket with location constraint (required for non-us-east-1 regions)
    create_params = {"Bucket": bucket_name}
    if args.region != "us-east-1":
        create_params["CreateBucketConfiguration"] = {"LocationConstraint": args.region}

    s3.create_bucket(**create_params)

    # Wait for bucket to exist
    s3.get_waiter("bucket_exists").wait(Bucket=bucket_name)

    print(json.dumps({"bucket_created": bucket_name, "region": args.region}, indent=2))
    print(f"\nBucket name: {bucket_name}")


if __name__ == "__main__":
    main()
