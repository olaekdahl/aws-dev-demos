"""
Demo: Publish Messages to SNS Topic

Publishes messages to an SNS topic for fan-out to subscribers.

Usage:
    python publish.py --topic-arn arn:aws:sns:... --region us-east-1
    python publish.py --topic-arn arn:aws:sns:... --count 10 --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Publish messages to SNS topic")
    parser.add_argument("--topic-arn", required=True, help="SNS topic ARN")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--count", type=int, default=5, help="Number of messages to publish")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sns = session.client("sns")

    for i in range(args.count):
        sns.publish(TopicArn=args.topic_arn, Message=json.dumps({"i": i}))

    print(json.dumps({"published": True, "count": args.count}, indent=2))


if __name__ == "__main__":
    main()
