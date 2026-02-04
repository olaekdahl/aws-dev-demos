"""
Demo: Consume Messages from SQS (Fan-out Pattern)

Polls an SQS queue that receives messages from SNS topic.

Usage:
    python consume.py --queue-url https://sqs.../myqueue --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Consume messages from SQS")
    parser.add_argument("--queue-url", required=True, help="SQS queue URL")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sqs = session.client("sqs")

    print("Polling for messages (Ctrl+C to stop)...\n")

    while True:
        response = sqs.receive_message(
            QueueUrl=args.queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10
        )

        messages = response.get("Messages", [])
        if not messages:
            print(json.dumps({"poll": "no messages"}))
            continue

        for message in messages:
            body = json.loads(message["Body"])
            # Handle SNS-wrapped messages
            payload = json.loads(body["Message"]) if "Message" in body else body
            print(json.dumps({"received": True, "payload": payload}, indent=2))
            sqs.delete_message(QueueUrl=args.queue_url, ReceiptHandle=message["ReceiptHandle"])


if __name__ == "__main__":
    main()
