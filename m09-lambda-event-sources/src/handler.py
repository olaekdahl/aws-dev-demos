from __future__ import annotations
import json

def handler(event, context):
    for r in event.get("Records", []):
        print(json.dumps({"event":"received", "body": r.get("body")}))
    return {"ok": True}
