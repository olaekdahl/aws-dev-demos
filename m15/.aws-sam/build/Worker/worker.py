from __future__ import annotations
import os
import json
import logging
from datetime import datetime, timezone
import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    results = {"processed": 0, "failed": 0}

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])

            # Handle SNS-wrapped messages
            if "Message" in body:
                body = json.loads(body["Message"])

            s3_records = body.get("Records", [])
            if not s3_records:
                logger.warning(json.dumps({
                    "event": "skip",
                    "reason": "no S3 records in message",
                    "message_id": record.get("messageId"),
                }))
                continue

            for s3_record in s3_records:
                event_name = s3_record.get("eventName", "")
                bucket = s3_record.get("s3", {}).get("bucket", {}).get("name", "unknown")
                key = s3_record.get("s3", {}).get("object", {}).get("key", "unknown")
                size = s3_record.get("s3", {}).get("object", {}).get("size", 0)

                ddb.put_item(
                    TableName=TABLE,
                    Item={
                        "id": {"S": key},
                        "bucket": {"S": bucket},
                        "size": {"N": str(size)},
                        "event": {"S": event_name},
                        "status": {"S": "processed"},
                        "processed_at": {"S": datetime.now(timezone.utc).isoformat()},
                    },
                )

                logger.info(json.dumps({
                    "event": "processed",
                    "key": key,
                    "bucket": bucket,
                    "size": size,
                    "event_name": event_name,
                }))
                results["processed"] += 1

        except Exception as e:
            results["failed"] += 1
            logger.error(json.dumps({
                "event": "processing_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "message_id": record.get("messageId"),
            }))
            raise  # Re-raise so SQS retries (and eventually DLQ)

    logger.info(json.dumps({"event": "batch_complete", **results}))
    return results
