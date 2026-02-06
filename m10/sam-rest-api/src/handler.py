from __future__ import annotations
import json
from datetime import datetime, timezone

REQUIRED_FIELDS = ["name", "email", "age"]


def handler(event, context):
    method = event.get("httpMethod", "GET").upper()
    path = event.get("path", "")

    if method == "GET" and path.endswith("/health"):
        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})
        }

    if method == "POST" and path.endswith("/validate"):
        # Parse body
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body")

        # Validate required fields
        errors = []
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append({"field": field, "error": "required"})

        # Validate types
        if "age" in body:
            if not isinstance(body["age"], (int, float)) or body["age"] < 0 or body["age"] > 150:
                errors.append({"field": "age", "error": "must be a number between 0 and 150"})

        if "email" in body:
            if not isinstance(body["email"], str) or "@" not in body["email"]:
                errors.append({"field": "email", "error": "must be a valid email address"})

        if errors:
            return error_response(422, "Validation failed", errors)

        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"valid": True, "data": body, "validated_at": datetime.now(timezone.utc).isoformat()})
        }

    return error_response(404, f"Not found: {method} {path}")


def error_response(code, message, errors=None):
    body = {"error": message, "statusCode": code}
    if errors:
        body["validation_errors"] = errors
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body)
    }
