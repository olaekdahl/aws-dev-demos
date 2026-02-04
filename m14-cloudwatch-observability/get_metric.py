"""
Demo: Get CloudWatch Metric Statistics

Retrieves metric statistics from CloudWatch.

Usage:
    python get_metric.py --namespace Demo --metric RequestCount --region us-east-1
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
import boto3


def main():
    parser = argparse.ArgumentParser(description="Get CloudWatch metric statistics")
    parser.add_argument("--namespace", required=True, help="CloudWatch namespace")
    parser.add_argument("--metric", required=True, help="Metric name")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    cloudwatch = session.client("cloudwatch")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=30)

    response = cloudwatch.get_metric_statistics(
        Namespace=args.namespace,
        MetricName=args.metric,
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Sum"]
    )

    datapoints = response.get("Datapoints", [])
    print(json.dumps({"metric_points": len(datapoints)}, indent=2))

    for point in sorted(datapoints, key=lambda x: x["Timestamp"]):
        print(json.dumps({
            "timestamp": point["Timestamp"].isoformat(),
            "sum": point.get("Sum")
        }))


if __name__ == "__main__":
    main()
