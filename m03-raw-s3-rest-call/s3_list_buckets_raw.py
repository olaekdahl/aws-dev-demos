"""
Demo: Raw S3 REST API Call with SigV4 Signing

Shows how AWS Signature Version 4 signing works under the hood.
This manually signs and executes an HTTP request to S3.

Usage:
    python s3_list_buckets_raw.py --profile myprofile --region us-east-1
"""
import argparse
import datetime as dt
import hashlib
import hmac
import requests
from botocore.credentials import ReadOnlyCredentials
from botocore.session import Session as BotocoreSession


def sign(key: bytes, msg: str) -> bytes:
    """HMAC-SHA256 signing helper."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    """Derive the signing key for AWS SigV4."""
    k_date = sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    return sign(k_service, "aws4_request")


def main():
    parser = argparse.ArgumentParser(description="Raw S3 REST call with SigV4 signing")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    # Get credentials from botocore
    bc_session = BotocoreSession()
    if args.profile:
        bc_session.set_config_variable("profile", args.profile)
    if args.region:
        bc_session.set_config_variable("region", args.region)

    creds = bc_session.get_credentials()
    frozen: ReadOnlyCredentials = creds.get_frozen_credentials()

    # Request parameters
    method = "GET"
    service = "s3"
    region = args.region
    host = "s3.amazonaws.com"
    endpoint = f"https://{host}/"

    # Create timestamp
    t = dt.datetime.utcnow()
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    # Create canonical request
    canonical_request = "\n".join([
        method,
        "/",
        "",
        f"host:{host}\n" + f"x-amz-date:{amz_date}\n",
        "host;x-amz-date",
        hashlib.sha256(b"").hexdigest(),
    ])

    # Create string to sign
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join([
        algorithm,
        amz_date,
        credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    # Calculate signature
    signing_key = get_signature_key(frozen.secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # Create authorization header
    authorization_header = (
        f"{algorithm} Credential={frozen.access_key}/{credential_scope}, "
        f"SignedHeaders=host;x-amz-date, Signature={signature}"
    )

    headers = {"x-amz-date": amz_date, "Authorization": authorization_header}
    if frozen.token:
        headers["x-amz-security-token"] = frozen.token

    print(f"Making SigV4 signed request to {endpoint}")
    print(f"Credential scope: {credential_scope}")

    response = requests.get(endpoint, headers=headers, timeout=30)
    print(f"\nHTTP {response.status_code} {response.reason}")
    print(response.text[:4000])


if __name__ == "__main__":
    main()
