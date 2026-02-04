"""
Demo: Call API Gateway REST API

Makes a request to an API Gateway endpoint.

Usage:
    python call_api.py --url https://abcd1234.execute-api.us-east-1.amazonaws.com/prod/hello
"""
import argparse
import requests


def main():
    parser = argparse.ArgumentParser(description="Call API Gateway endpoint")
    parser.add_argument("--url", required=True, help="API Gateway URL")
    args = parser.parse_args()

    response = requests.get(args.url, timeout=30)

    print(f"Status: {response.status_code}")
    print(f"Response:\n{response.text}")


if __name__ == "__main__":
    main()
