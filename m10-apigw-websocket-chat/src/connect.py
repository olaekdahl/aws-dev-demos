from __future__ import annotations
import os
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

def handler(event, context):
    cid = event["requestContext"]["connectionId"]
    ddb.put_item(TableName=TABLE, Item={"connectionId":{"S": cid}})
    return {"statusCode": 200, "body": "connected"}
