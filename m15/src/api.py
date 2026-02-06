from __future__ import annotations
import os
import json
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]


def handler(event, context):
    method = event.get("httpMethod", "GET").upper()
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}

    if method == "GET" and "id" in path_params:
        return get_item(path_params["id"])

    if method == "GET" and path.rstrip("/").endswith("/items"):
        return list_items()

    return respond(404, {"error": "Not found"})


def get_item(item_id):
    result = ddb.get_item(TableName=TABLE, Key={"id": {"S": item_id}})
    item = result.get("Item")
    if not item:
        return respond(404, {"error": "Item not found", "id": item_id})
    return respond(200, unmarshal(item))


def list_items():
    result = ddb.scan(TableName=TABLE, Limit=50)
    items = [unmarshal(i) for i in result.get("Items", [])]
    return respond(200, {"items": items, "count": len(items)})


def unmarshal(item):
    """Simple DynamoDB item unmarshaller."""
    out = {}
    for k, v in item.items():
        if "S" in v:
            out[k] = v["S"]
        elif "N" in v:
            out[k] = float(v["N"]) if "." in v["N"] else int(v["N"])
        elif "BOOL" in v:
            out[k] = v["BOOL"]
    return out


def respond(code, body):
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, default=str),
    }
