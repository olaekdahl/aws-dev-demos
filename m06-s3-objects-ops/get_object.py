"""
Demo: Get S3 Object

Retrieves an object from an S3 bucket.

Usage:
    python get_object.py --bucket mybucket --key myfile.txt --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Get S3 object")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--key", required=True, help="Object key")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    response = s3.get_object(Bucket=args.bucket, Key=args.key)
    body = response["Body"].read().decode("utf-8", errors="replace")

    print(json.dumps({"object_get": True, "bucket": args.bucket, "key": args.key, "size": len(body)}))
    print("\nContent:")
    print(body)


if __name__ == "__main__":
    main()
