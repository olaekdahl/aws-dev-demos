"""
Demo: Cleanup SNS/SQS Infrastructure

Deletes the SNS topic and SQS queues created by create_infra.py.

Usage:
    python cleanup.py --topic-arn arn:aws:sns:... --queue-urls https://sqs... https://sqs... --yes --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Cleanup SNS/SQS infrastructure")
    parser.add_argument("--topic-arn", required=True, help="SNS topic ARN to delete")
    parser.add_argument("--queue-urls", nargs="+", required=True, help="SQS queue URLs to delete")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to delete without --yes flag")

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sns = session.client("sns")
    sqs = session.client("sqs")

    # Unsubscribe all subscriptions from the topic
    subscriptions = sns.list_subscriptions_by_topic(TopicArn=args.topic_arn).get("Subscriptions", [])
    for sub in subscriptions:
        arn = sub.get("SubscriptionArn")
        if arn and arn != "PendingConfirmation":
            sns.unsubscribe(SubscriptionArn=arn)

    # Delete the topic
    sns.delete_topic(TopicArn=args.topic_arn)

    # Delete the queues
    for queue_url in args.queue_urls:
        sqs.delete_queue(QueueUrl=queue_url)

    print(json.dumps({
        "cleanup_done": True,
        "topic_deleted": args.topic_arn,
        "queues_deleted": len(args.queue_urls)
    }, indent=2))


if __name__ == "__main__":
    main()
