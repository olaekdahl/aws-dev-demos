from __future__ import annotations
import os, json
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

def handler(event, context):
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    api = boto3.client("apigatewaymanagementapi", endpoint_url=f"https://{domain}/{stage}")

    body = json.loads(event.get("body") or "{}")
    msg = body.get("message", "")

    conns = ddb.scan(TableName=TABLE).get("Items", [])
    for c in conns:
        cid = c["connectionId"]["S"]
        try:
            api.post_to_connection(ConnectionId=cid, Data=json.dumps({"message": msg}).encode("utf-8"))
        except Exception:
            ddb.delete_item(TableName=TABLE, Key={"connectionId":{"S": cid}})
    return {"statusCode": 200, "body": "sent"}
