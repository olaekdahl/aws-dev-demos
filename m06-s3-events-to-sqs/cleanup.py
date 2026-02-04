"""
Demo: Cleanup S3 Events to SQS Infrastructure

Deletes the bucket and SQS queue created by create_infra.py.

Usage:
    python cleanup.py --bucket mybucket --queue-url https://sqs.../myqueue --yes --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Cleanup S3 events to SQS infrastructure")
    parser.add_argument("--bucket", required=True, help="Bucket name to delete")
    parser.add_argument("--queue-url", required=True, help="SQS queue URL to delete")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to delete without --yes flag")

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")
    sqs = session.client("sqs")

    # Delete all objects in the bucket
    paginator = s3.get_paginator("list_objects_v2")
    total_deleted = 0

    for page in paginator.paginate(Bucket=args.bucket):
        objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
        if objects:
            s3.delete_objects(Bucket=args.bucket, Delete={"Objects": objects, "Quiet": True})
            total_deleted += len(objects)
            print(json.dumps({"deleted_objects": len(objects)}))

    # Delete the bucket
    s3.delete_bucket(Bucket=args.bucket)

    # Delete the queue
    sqs.delete_queue(QueueUrl=args.queue_url)

    print(json.dumps({
        "cleanup_done": True,
        "bucket_deleted": args.bucket,
        "queue_deleted": args.queue_url,
        "total_objects_deleted": total_deleted
    }, indent=2))


if __name__ == "__main__":
    main()
