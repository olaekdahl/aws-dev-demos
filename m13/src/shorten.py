from __future__ import annotations
import json
import os
import string
import random
import time
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]
CHARS = string.ascii_letters + string.digits


def generate_code(length=6):
    return "".join(random.choices(CHARS, k=length))


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON"})

    url = body.get("url")
    if not url or not url.startswith(("http://", "https://")):
        return response(400, {"error": "Missing or invalid 'url' field. Must start with http:// or https://"})

    ttl_hours = body.get("ttl_hours", 24)
    code = generate_code()
    expires_at = int(time.time()) + (ttl_hours * 3600)

    ddb.put_item(
        TableName=TABLE,
        Item={
            "code": {"S": code},
            "url": {"S": url},
            "clicks": {"N": "0"},
            "created_at": {"N": str(int(time.time()))},
            "expires_at": {"N": str(expires_at)},
        },
    )

    api_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    short_url = f"{api_url}/{code}"

    return response(201, {
        "short_url": short_url,
        "code": code,
        "original_url": url,
        "expires_in_hours": ttl_hours,
    })


def response(code, body):
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }
