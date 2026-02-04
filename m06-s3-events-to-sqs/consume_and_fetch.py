"""
Demo: Consume S3 Event Notifications from SQS

Polls SQS queue for S3 event notifications and fetches the uploaded objects.

Usage:
    python consume_and_fetch.py --queue-url https://sqs.../myqueue --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Consume S3 events from SQS and fetch objects")
    parser.add_argument("--queue-url", required=True, help="SQS queue URL")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sqs = session.client("sqs")
    s3 = session.client("s3")

    print("Polling for messages (Ctrl+C to stop)...\n")

    while True:
        response = sqs.receive_message(
            QueueUrl=args.queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10,
            VisibilityTimeout=30
        )

        messages = response.get("Messages", [])
        if not messages:
            print(json.dumps({"poll": "no messages"}))
            continue

        for message in messages:
            body = json.loads(message["Body"])

            # Handle SNS-wrapped messages
            event = json.loads(body["Message"]) if "Message" in body else body

            # Extract S3 event details
            record = event["Records"][0]
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]

            # Fetch the object
            obj = s3.get_object(Bucket=bucket, Key=key)
            data = obj["Body"].read().decode("utf-8", errors="replace")

            print(json.dumps({
                "fetched": True,
                "bucket": bucket,
                "key": key,
                "preview": data[:200]
            }, indent=2))

            # Delete the message
            sqs.delete_message(QueueUrl=args.queue_url, ReceiptHandle=message["ReceiptHandle"])


if __name__ == "__main__":
    main()
