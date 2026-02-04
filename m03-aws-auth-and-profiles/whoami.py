"""
Demo: AWS Authentication & Profiles - Who Am I?

Shows how to use STS get_caller_identity() to verify AWS credentials.

Usage:
    python whoami.py --profile myprofile --region us-east-1
    python whoami.py  # uses default credentials
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Get AWS caller identity")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    # Create session with optional profile and region
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sts = session.client("sts")

    # Get caller identity
    identity = sts.get_caller_identity()

    result = {
        "Account": identity.get("Account"),
        "Arn": identity.get("Arn"),
        "UserId": identity.get("UserId"),
        "Region": args.region or session.region_name,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
