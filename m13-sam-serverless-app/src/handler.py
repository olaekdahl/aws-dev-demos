from __future__ import annotations
import json, os, boto3
ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

def handler(event, context):
    method = event["httpMethod"].upper()
    item_id = event["pathParameters"]["id"]
    if method == "GET":
        r = ddb.get_item(TableName=TABLE, Key={"id":{"S": item_id}})
        return {"statusCode": 200, "body": json.dumps(r.get("Item"))}
    if method == "PUT":
        body = json.loads(event.get("body") or "{}")
        ddb.put_item(TableName=TABLE, Item={"id":{"S": item_id}, "data":{"S": json.dumps(body)}})
        return {"statusCode": 200, "body": json.dumps({"ok": True})}
    return {"statusCode": 405, "body": "method not allowed"}
