"""
Demo: Create SNS/SQS Fan-out Infrastructure

Creates an SNS topic with multiple SQS subscribers for fan-out pattern.

Usage:
    python create_infra.py --prefix myprefix --region us-east-1
"""
import argparse
import json
import uuid
import boto3


def generate_name(prefix: str, suffix: str) -> str:
    """Generate a unique resource name."""
    return f"{prefix}-{suffix}-{uuid.uuid4().hex[:8]}".lower()


def main():
    parser = argparse.ArgumentParser(description="Create SNS/SQS fan-out infrastructure")
    parser.add_argument("--prefix", default="demo", help="Prefix for resource names")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sns = session.client("sns")
    sqs = session.client("sqs")

    # Create SNS topic
    topic_response = sns.create_topic(Name=generate_name(args.prefix, "topic"))
    topic_arn = topic_response["TopicArn"]
    print(f"Created topic: {topic_arn}")

    queue_urls = []

    # Create SQS queues and subscribe to topic
    for suffix in ["svc-a", "svc-b"]:
        queue_name = generate_name(args.prefix, suffix)
        queue_response = sqs.create_queue(QueueName=queue_name)
        queue_url = queue_response["QueueUrl"]
        queue_arn = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["QueueArn"]
        )["Attributes"]["QueueArn"]

        # Set queue policy to allow SNS to send messages
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "AllowSNSPublish",
                "Effect": "Allow",
                "Principal": {"Service": "sns.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": queue_arn,
                "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}
            }]
        }
        sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": json.dumps(policy)})

        # Subscribe queue to topic
        sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn)
        queue_urls.append(queue_url)
        print(f"Created queue and subscribed: {queue_name}")

    result = {"topic_arn": topic_arn, "queue_urls": queue_urls}
    print("\nInfrastructure created:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
