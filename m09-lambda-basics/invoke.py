"""
Demo: Invoke Lambda Function

Invokes a Lambda function and prints the response.

Usage:
    python invoke.py --function-name myfunction --region us-east-1
    python invoke.py --function-name myfunction --payload '{"key": "value"}' --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Invoke Lambda function")
    parser.add_argument("--function-name", required=True, help="Lambda function name")
    parser.add_argument("--payload", default="{}", help="JSON payload to send")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    lam = session.client("lambda")

    response = lam.invoke(
        FunctionName=args.function_name,
        InvocationType="RequestResponse",
        Payload=args.payload.encode("utf-8")
    )

    body = response["Payload"].read().decode("utf-8", errors="replace")

    print(json.dumps({"invoked": True, "status_code": response.get("StatusCode")}, indent=2))
    print("\nResponse:")
    print(body)


if __name__ == "__main__":
    main()
