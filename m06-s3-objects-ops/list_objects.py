"""
Demo: List S3 Objects

Lists objects in an S3 bucket with optional prefix filter.

Usage:
    python list_objects.py --bucket mybucket --profile myprofile --region us-east-1
    python list_objects.py --bucket mybucket --prefix folder/ --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="List S3 objects")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--prefix", default="", help="Object key prefix filter")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    paginator = s3.get_paginator("list_objects_v2")
    count = 0

    for page in paginator.paginate(Bucket=args.bucket, Prefix=args.prefix):
        for obj in page.get("Contents", []):
            count += 1
            print(json.dumps({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            }))

    print(f"\nTotal objects: {count}")


if __name__ == "__main__":
    main()
