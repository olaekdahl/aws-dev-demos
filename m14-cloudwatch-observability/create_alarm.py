"""
Demo: Create CloudWatch Alarm

Creates a CloudWatch alarm for a custom metric.

Usage:
    python create_alarm.py --namespace Demo --metric RequestCount --alarm-name HighRequests --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Create CloudWatch alarm")
    parser.add_argument("--namespace", required=True, help="CloudWatch namespace")
    parser.add_argument("--metric", required=True, help="Metric name")
    parser.add_argument("--alarm-name", required=True, help="Alarm name")
    parser.add_argument("--threshold", type=float, default=1, help="Alarm threshold")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    cloudwatch = session.client("cloudwatch")

    cloudwatch.put_metric_alarm(
        AlarmName=args.alarm_name,
        Namespace=args.namespace,
        MetricName=args.metric,
        Statistic="Sum",
        Period=60,
        EvaluationPeriods=1,
        Threshold=args.threshold,
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        TreatMissingData="notBreaching"
    )

    print(json.dumps({"alarm_created": args.alarm_name, "threshold": args.threshold}, indent=2))


if __name__ == "__main__":
    main()
