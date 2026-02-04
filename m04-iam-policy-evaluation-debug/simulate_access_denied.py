"""
Demo: Simulate IAM Access Denied

Tests IAM permissions by attempting an action that might fail.

Usage:
    python simulate_access_denied.py --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3
import botocore.exceptions


def main():
    parser = argparse.ArgumentParser(description="Test IAM ListUsers permission")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    iam = session.client("iam")

    try:
        iam.list_users(MaxItems=5)
        print(json.dumps({"status": "ok", "message": "iam:ListUsers succeeded (you have permission)"}, indent=2))
    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error", {})
        print(json.dumps({
            "status": "expected_failure",
            "code": error.get("Code"),
            "message": error.get("Message"),
            "action": "iam:ListUsers"
        }, indent=2))


if __name__ == "__main__":
    main()
