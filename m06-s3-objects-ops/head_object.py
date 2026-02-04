"""
Demo: Head S3 Object

Retrieves metadata about an S3 object without downloading it.

Usage:
    python head_object.py --bucket mybucket --key myfile.txt --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Get S3 object metadata")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--key", required=True, help="Object key")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    head = s3.head_object(Bucket=args.bucket, Key=args.key)

    print(json.dumps({
        "bucket": args.bucket,
        "key": args.key,
        "size": head.get("ContentLength"),
        "etag": head.get("ETag"),
        "content_type": head.get("ContentType"),
        "last_modified": head.get("LastModified").isoformat() if head.get("LastModified") else None,
        "metadata": head.get("Metadata")
    }, indent=2))


if __name__ == "__main__":
    main()
