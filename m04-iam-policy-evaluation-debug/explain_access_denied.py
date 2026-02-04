"""
Demo: Explain Access Denied Errors

Shows how to diagnose permission issues and optionally check CloudTrail.

Usage:
    python explain_access_denied.py --profile myprofile --region us-east-1
    python explain_access_denied.py --lookup-cloudtrail --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3
import botocore.exceptions


def main():
    parser = argparse.ArgumentParser(description="Test S3 access and diagnose errors")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--lookup-cloudtrail", action="store_true", help="Look up recent CloudTrail events")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    # Try to list buckets
    try:
        s3.list_buckets()
        print(json.dumps({"status": "ok", "message": "s3:ListAllMyBuckets succeeded"}, indent=2))
    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error", {})
        print(json.dumps({
            "status": "access_denied",
            "code": error.get("Code"),
            "message": error.get("Message"),
            "operation": "s3:ListAllMyBuckets"
        }, indent=2))

    # Optionally look up CloudTrail events
    if args.lookup_cloudtrail:
        ct = session.client("cloudtrail")
        try:
            events = ct.lookup_events(
                LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": "ListBuckets"}],
                MaxResults=5
            )
            print(json.dumps({
                "cloudtrail_lookup": "success",
                "event_count": len(events.get("Events", []))
            }, indent=2))
        except botocore.exceptions.ClientError as e:
            print(json.dumps({"cloudtrail_lookup": "failed", "error": str(e)}, indent=2))


if __name__ == "__main__":
    main()
