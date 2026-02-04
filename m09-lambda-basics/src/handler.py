from __future__ import annotations
import json
import os
from datetime import datetime, timezone

def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({
            "message": "hello from lambda",
            "now": datetime.now(timezone.utc).isoformat(),
            "env": {"DEMO": os.getenv("DEMO")},
            "event": event,
        })
    }
