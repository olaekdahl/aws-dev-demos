"""
Demo: Send Messages to SQS for Lambda Event Source

Sends messages to an SQS queue that triggers a Lambda function.

Usage:
    python send_messages.py --queue-url https://sqs.../myqueue --region us-east-1
    python send_messages.py --queue-url https://sqs.../myqueue --count 20 --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Send messages to SQS")
    parser.add_argument("--queue-url", required=True, help="SQS queue URL")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--count", type=int, default=10, help="Number of messages to send")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sqs = session.client("sqs")

    for i in range(args.count):
        sqs.send_message(QueueUrl=args.queue_url, MessageBody=json.dumps({"i": i}))

    print(json.dumps({"sent": True, "count": args.count}, indent=2))


if __name__ == "__main__":
    main()
