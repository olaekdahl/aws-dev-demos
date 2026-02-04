"""
Demo: Put S3 Object

Uploads an object to an S3 bucket.

Usage:
    python put_object.py --bucket mybucket --key myfile.txt --text "Hello World" --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Put S3 object")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--key", required=True, help="Object key")
    parser.add_argument("--text", required=True, help="Text content to upload")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    s3.put_object(
        Bucket=args.bucket,
        Key=args.key,
        Body=args.text.encode("utf-8"),
        Metadata={"demo": "awsdev"}
    )

    print(json.dumps({"object_put": True, "bucket": args.bucket, "key": args.key}, indent=2))


if __name__ == "__main__":
    main()
