"""
Demo: Deploy Lambda Function from ZIP

Creates or updates a Lambda function using a ZIP file.

Usage:
    python deploy_zip_lambda.py --function-name myfunction --role-arn arn:aws:iam::123456789012:role/lambda-role --region us-east-1
"""
import argparse
import json
import pathlib
import boto3
import botocore.exceptions


def main():
    parser = argparse.ArgumentParser(description="Deploy Lambda function from ZIP")
    parser.add_argument("--function-name", required=True, help="Lambda function name")
    parser.add_argument("--role-arn", required=True, help="IAM role ARN for Lambda")
    parser.add_argument("--zip", default=str(pathlib.Path(__file__).parent / "function.zip"), help="Path to ZIP file")
    parser.add_argument("--handler", default="handler.handler", help="Lambda handler")
    parser.add_argument("--runtime", default="python3.11", help="Lambda runtime")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    lam = session.client("lambda")

    # Read the ZIP file
    with open(args.zip, "rb") as f:
        code = f.read()

    try:
        # Check if function exists
        lam.get_function(FunctionName=args.function_name)

        # Update existing function
        lam.update_function_code(FunctionName=args.function_name, ZipFile=code, Publish=True)
        lam.update_function_configuration(
            FunctionName=args.function_name,
            Handler=args.handler,
            Runtime=args.runtime,
            Environment={"Variables": {"DEMO": "awsdev"}}
        )
        print(json.dumps({"lambda_updated": args.function_name}, indent=2))

    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code") != "ResourceNotFoundException":
            raise

        # Create new function
        lam.create_function(
            FunctionName=args.function_name,
            Runtime=args.runtime,
            Role=args.role_arn,
            Handler=args.handler,
            Code={"ZipFile": code},
            Publish=True,
            Environment={"Variables": {"DEMO": "awsdev"}}
        )
        print(json.dumps({"lambda_created": args.function_name}, indent=2))


if __name__ == "__main__":
    main()
