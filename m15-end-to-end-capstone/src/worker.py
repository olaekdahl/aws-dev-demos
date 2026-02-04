from __future__ import annotations
import os, json, boto3
ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

def handler(event, context):
    for r in event.get("Records", []):
        body = json.loads(r["body"])
        if "Message" in body:
            body = json.loads(body["Message"])
        rec = body["Records"][0]
        key = rec["s3"]["object"]["key"]
        ddb.put_item(TableName=TABLE, Item={"id":{"S": key}, "status":{"S":"processed"}})
        print(json.dumps({"event":"processed", "key": key}))
    return {"ok": True}
