"""
Demo: Create S3 Events to SQS Infrastructure

Creates an S3 bucket and SQS queue, configures S3 event notifications to SQS.

Usage:
    python create_infra.py --prefix myprefix --profile myprofile --region us-east-1
"""
import argparse
import json
import uuid
import boto3


def generate_name(prefix: str, suffix: str) -> str:
    """Generate a unique resource name."""
    return f"{prefix}-{suffix}-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create S3 events to SQS infrastructure")
    parser.add_argument("--prefix", default="demo", help="Prefix for resource names")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")
    sqs = session.client("sqs")

    bucket_name = generate_name(args.prefix, "evt-bucket")
    queue_name = generate_name(args.prefix, "evt-queue")

    # Create S3 bucket
    create_params = {"Bucket": bucket_name}
    if args.region != "us-east-1":
        create_params["CreateBucketConfiguration"] = {"LocationConstraint": args.region}
    s3.create_bucket(**create_params)
    s3.get_waiter("bucket_exists").wait(Bucket=bucket_name)
    print(f"Created bucket: {bucket_name}")

    # Create SQS queue
    queue_response = sqs.create_queue(QueueName=queue_name)
    queue_url = queue_response["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    print(f"Created queue: {queue_name}")

    # Set queue policy to allow S3 to send messages
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowS3SendMessage",
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": queue_arn,
            "Condition": {"ArnLike": {"aws:SourceArn": f"arn:aws:s3:::{bucket_name}"}}
        }]
    }
    sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": json.dumps(policy)})

    # Configure S3 event notification to SQS
    s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            "QueueConfigurations": [{
                "QueueArn": queue_arn,
                "Events": ["s3:ObjectCreated:*"]
            }]
        }
    )

    result = {
        "bucket": bucket_name,
        "queue_url": queue_url,
        "queue_arn": queue_arn,
        "region": args.region
    }
    print("\nInfrastructure created:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
