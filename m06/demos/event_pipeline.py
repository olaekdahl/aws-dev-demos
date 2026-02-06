"""
Demo: S3 Event Pipeline - S3 Events to SQS

Creates an S3 bucket and an SQS queue, wires up S3 event notifications to
the queue, uploads a test object, then polls for and displays the resulting
event notification. Fully self-contained -- no external setup required.
"""
import json
import time

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    json_print, generate_name, track_resource,
)

MODULE = "m06"

# How long to wait for S3 event notification propagation
NOTIFICATION_PROPAGATION_DELAY = 5   # seconds
POLL_TIMEOUT = 30                     # seconds
POLL_INTERVAL = 2                     # seconds


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


def run(args):
    banner("m06", "S3 Event Pipeline - S3 Events to SQS")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    sqs = session.client("sqs")
    region = session.region_name

    bucket_name = generate_name("events", getattr(args, "prefix", None))
    queue_name = generate_name("events-q", getattr(args, "prefix", None))

    # ── Step 1: Create S3 bucket ──
    step(1, "Create S3 bucket")

    try:
        _create_bucket(s3, bucket_name, region)
        kv("Bucket", bucket_name)
        success("Bucket created")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 2: Create SQS queue and get ARN ──
    step(2, "Create SQS queue")

    try:
        q_resp = sqs.create_queue(QueueName=queue_name)
        queue_url = q_resp["QueueUrl"]
        kv("Queue URL", queue_url)

        attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
        queue_arn = attrs["Attributes"]["QueueArn"]
        kv("Queue ARN", queue_arn)
        success("SQS queue created")
    except Exception as e:
        fail(f"Failed to create SQS queue: {e}")
        return

    track_resource(MODULE, "sqs_queue", queue_url, queue_name=queue_name, region=region)

    # ── Step 3: Set queue policy allowing S3 to send messages ──
    step(3, "Set SQS queue policy for S3 access")

    account_id = queue_arn.split(":")[4]
    bucket_arn = f"arn:aws:s3:::{bucket_name}"

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowS3SendMessage",
                "Effect": "Allow",
                "Principal": {"Service": "s3.amazonaws.com"},
                "Action": "SQS:SendMessage",
                "Resource": queue_arn,
                "Condition": {
                    "ArnEquals": {"aws:SourceArn": bucket_arn}
                },
            }
        ],
    }

    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={"Policy": json.dumps(policy)},
    )
    info("Policy grants s3.amazonaws.com -> SQS:SendMessage")
    kv("Condition", f"aws:SourceArn == {bucket_arn}")
    success("Queue policy applied")

    # ── Step 4: Configure S3 event notification -> SQS ──
    step(4, "Configure S3 event notification to SQS")

    notification_config = {
        "QueueConfigurations": [
            {
                "QueueArn": queue_arn,
                "Events": ["s3:ObjectCreated:*"],
            }
        ]
    }

    s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration=notification_config,
    )
    kv("Event type", "s3:ObjectCreated:*")
    kv("Target", queue_arn)
    success("Event notification configured")

    info(f"Waiting {NOTIFICATION_PROPAGATION_DELAY}s for notification config to propagate...")
    time.sleep(NOTIFICATION_PROPAGATION_DELAY)

    # ── Step 5: Upload a test object to trigger the event ──
    step(5, "Upload a test object to trigger the event")

    test_key = "event-test.txt"
    test_body = "This upload should trigger an S3 event notification to SQS."
    s3.put_object(Bucket=bucket_name, Key=test_key, Body=test_body, ContentType="text/plain")
    kv("Key", test_key)
    kv("Size", f"{len(test_body)} bytes")
    success(f"Uploaded {test_key}")

    # ── Step 6: Poll SQS for the event notification ──
    step(6, "Poll SQS for the event notification")

    info(f"Polling (timeout: {POLL_TIMEOUT}s)...")

    event_message = None
    deadline = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        resp = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=min(5, max(1, int(deadline - time.time()))),
        )
        messages = resp.get("Messages", [])
        if messages:
            event_message = messages[0]
            # Delete the message from the queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=event_message["ReceiptHandle"],
            )
            success("Event notification received!")
            break
        info(f"  No messages yet, retrying... ({int(deadline - time.time())}s remaining)")

    if not event_message:
        warn("Timed out waiting for the event notification.")
        info("This can happen if notification config propagation takes longer than usual.")
        info("Try running the demo again -- the configuration may need more time.")
        return

    # ── Step 7: Display the S3 event details ──
    step(7, "Display S3 event details")

    body = json.loads(event_message["Body"])

    # S3 notifications may be wrapped in an SNS envelope or sent directly
    if "Records" in body:
        records = body["Records"]
    elif "Message" in body:
        records = json.loads(body["Message"]).get("Records", [])
    else:
        info("Raw message body:")
        json_print(body)
        return

    for record in records:
        kv("Event name", record.get("eventName"))
        kv("Event time", record.get("eventTime"))
        kv("Region", record.get("awsRegion"))
        kv("Source IP", record.get("requestParameters", {}).get("sourceIPAddress"))

        s3_info = record.get("s3", {})
        kv("Bucket", s3_info.get("bucket", {}).get("name"))
        kv("Object key", s3_info.get("object", {}).get("key"))
        kv("Object size", s3_info.get("object", {}).get("size"))
        kv("Object eTag", s3_info.get("object", {}).get("eTag"))

    info("\nFull event record:")
    json_print(records[0] if len(records) == 1 else records)

    success("S3 -> SQS event pipeline demonstrated successfully")
    info(f"\nResources tracked for cleanup (run with --cleanup)")
