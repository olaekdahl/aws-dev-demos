"""
Demo: Put CloudWatch Custom Metric

Publishes a custom metric to CloudWatch.

Usage:
    python put_metric.py --namespace Demo --metric RequestCount --value 1 --region us-east-1
"""
import argparse
import json
from datetime import datetime, timezone
import boto3


def main():
    parser = argparse.ArgumentParser(description="Put CloudWatch custom metric")
    parser.add_argument("--namespace", required=True, help="CloudWatch namespace")
    parser.add_argument("--metric", required=True, help="Metric name")
    parser.add_argument("--value", type=float, required=True, help="Metric value")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    cloudwatch = session.client("cloudwatch")

    cloudwatch.put_metric_data(
        Namespace=args.namespace,
        MetricData=[{
            "MetricName": args.metric,
            "Timestamp": datetime.now(timezone.utc),
            "Value": args.value,
            "Unit": "Count"
        }]
    )

    print(json.dumps({
        "metric_put": True,
        "namespace": args.namespace,
        "metric": args.metric,
        "value": args.value
    }, indent=2))


if __name__ == "__main__":
    main()
