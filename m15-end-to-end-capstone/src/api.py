from __future__ import annotations
import os, json, boto3
ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

def handler(event, context):
    item_id = event["pathParameters"]["id"]
    r = ddb.get_item(TableName=TABLE, Key={"id":{"S": item_id}})
    return {"statusCode": 200, "headers":{"content-type":"application/json"}, "body": json.dumps(r.get("Item"))}
