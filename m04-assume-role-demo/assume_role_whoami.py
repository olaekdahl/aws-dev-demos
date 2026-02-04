"""
Demo: Assume IAM Role and Get Identity

Shows how to assume an IAM role and use temporary credentials.

Usage:
    python assume_role_whoami.py --role-arn arn:aws:iam::123456789012:role/MyRole --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Assume IAM role and get caller identity")
    parser.add_argument("--role-arn", required=True, help="ARN of the role to assume")
    parser.add_argument("--session-name", default="demo-assume-role", help="Session name for assumed role")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    # Create initial session
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    sts = session.client("sts")

    # Assume the role
    response = sts.assume_role(RoleArn=args.role_arn, RoleSessionName=args.session_name)
    credentials = response["Credentials"]

    # Create new session with assumed role credentials
    assumed_session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=args.region,
    )

    # Get identity with assumed role
    assumed_sts = assumed_session.client("sts")
    identity = assumed_sts.get_caller_identity()

    result = {
        "AssumedRole": args.role_arn,
        "Account": identity["Account"],
        "Arn": identity["Arn"],
        "UserId": identity["UserId"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
