from __future__ import annotations
import json
import os
from datetime import datetime, timezone
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]


def handler(event, context):
    code = event["pathParameters"]["code"]

    result = ddb.get_item(TableName=TABLE, Key={"code": {"S": code}})
    item = result.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"error": "Short URL not found"}),
        }

    created_at = int(item.get("created_at", {}).get("N", "0"))
    expires_at = int(item.get("expires_at", {}).get("N", "0"))

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({
            "code": code,
            "original_url": item["url"]["S"],
            "clicks": int(item["clicks"]["N"]),
            "created_at": datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat() if created_at else None,
            "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat() if expires_at else None,
        }),
    }
