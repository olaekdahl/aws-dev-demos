"""
Demo: Enable S3 Bucket Versioning

Enables versioning on an S3 bucket.

Usage:
    python enable_versioning.py --bucket mybucket --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Enable S3 bucket versioning")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    s3.put_bucket_versioning(
        Bucket=args.bucket,
        VersioningConfiguration={"Status": "Enabled"}
    )

    print(json.dumps({"versioning_enabled": args.bucket}, indent=2))


if __name__ == "__main__":
    main()
