from __future__ import annotations
import json
import os
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]


def handler(event, context):
    code = event["pathParameters"]["code"]

    # Skip non-shortcode paths
    if code in ("shorten", "stats", "favicon.ico"):
        return {"statusCode": 404, "body": "not found"}

    result = ddb.get_item(TableName=TABLE, Key={"code": {"S": code}})
    item = result.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"error": "Short URL not found", "code": code}),
        }

    url = item["url"]["S"]

    # Increment click count atomically
    ddb.update_item(
        TableName=TABLE,
        Key={"code": {"S": code}},
        UpdateExpression="SET clicks = clicks + :inc",
        ExpressionAttributeValues={":inc": {"N": "1"}},
    )

    return {
        "statusCode": 301,
        "headers": {"Location": url},
        "body": "",
    }
