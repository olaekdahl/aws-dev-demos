from __future__ import annotations
import json

def handler(event, context):
    qs = event.get("queryStringParameters") or {}
    name = qs.get("name", "world")
    return {"statusCode": 200, "headers": {"content-type":"application/json"}, "body": json.dumps({"message": f"hello {name}"})}
