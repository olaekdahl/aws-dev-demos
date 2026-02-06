"""Dead-letter queue pattern: poison pill detection and message recovery."""
import json
import time
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from common import (
    create_session, banner, step, success, fail, info, warn,
    kv, generate_name, track_resource, progress_bar,
)


def run(args):
    banner("m11", "Dead-Letter Queue & Recovery")
    session = create_session(args.profile, args.region)
    sqs = session.client("sqs")

    # Step 1: Create main queue with DLQ configuration
    step(1, "Creating DLQ and main queue with redrive policy")

    dlq_name = generate_name("dlq", args.prefix)
    dlq_url = sqs.create_queue(QueueName=dlq_name)["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(
        QueueUrl=dlq_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    track_resource("m11", "sqs_queue", dlq_url)
    success(f"DLQ created: {dlq_name}")

    main_name = generate_name("main-queue", args.prefix)
    redrive_policy = json.dumps({
        "deadLetterTargetArn": dlq_arn,
        "maxReceiveCount": "2",
    })
    main_url = sqs.create_queue(
        QueueName=main_name,
        Attributes={
            "VisibilityTimeout": "5",
            "RedrivePolicy": redrive_policy,
        },
    )["QueueUrl"]
    track_resource("m11", "sqs_queue", main_url)
    success(f"Main queue created: {main_name}")
    kv("maxReceiveCount", "2 (messages move to DLQ after 2 failed receives)")
    kv("VisibilityTimeout", "5s (short for demo purposes)")

    # Step 2: Send 3 messages to main queue
    step(2, "Sending 3 messages to main queue")
    for i in range(3):
        body = json.dumps({"taskId": f"TASK-{i + 1:03d}", "payload": f"work-item-{i + 1}"})
        sqs.send_message(QueueUrl=main_url, MessageBody=body)
        info(f"Sent: TASK-{i + 1:03d}")
    success("All 3 messages sent")

    # Step 3: Simulate "failed processing" by receiving messages but NOT deleting them
    step(3, "Simulating failed processing (receive without delete)")
    info("Messages will be received but NOT acknowledged (deleted).")
    info("After 2 receives each, SQS moves them to the DLQ.\n")

    for attempt in range(1, 3):
        kv(f"Attempt {attempt}", "Receiving messages...")
        resp = sqs.receive_message(
            QueueUrl=main_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=3,
        )
        msgs = resp.get("Messages", [])
        for msg in msgs:
            body = json.loads(msg["Body"])
            warn(f"  Received {body['taskId']} -- NOT deleting (simulating failure)")
        if not msgs:
            info("  No messages available yet (may still be invisible)")
        info(f"  Waiting for visibility timeout to expire...")
        time.sleep(6)  # Wait for visibility timeout (5s) + buffer

    success("Both receive attempts complete -- messages should now be in DLQ")

    # Step 4: Wait and then check DLQ for the messages
    step(4, "Checking DLQ for poison-pill messages")
    info("Waiting a moment for SQS to transfer messages...\n")
    time.sleep(5)

    dlq_messages = []
    deadline = time.time() + 15
    while time.time() < deadline and len(dlq_messages) < 3:
        resp = sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=3,
        )
        for msg in resp.get("Messages", []):
            body = json.loads(msg["Body"])
            dlq_messages.append({"body": body, "handle": msg["ReceiptHandle"]})
        progress_bar(len(dlq_messages), 3, label="messages in DLQ")

    print()  # newline after progress bar
    if dlq_messages:
        success(f"Found {len(dlq_messages)} message(s) in DLQ:")
        for m in dlq_messages:
            kv("  Poison pill", m["body"]["taskId"])
    else:
        warn("No messages found in DLQ yet (may need more time)")

    # Step 5: Demonstrate "redrive" - move messages back to main queue
    step(5, "Redriving messages from DLQ back to main queue")
    info("In production you would fix the bug first, then redrive.\n")

    redriven = 0
    for m in dlq_messages:
        sqs.send_message(QueueUrl=main_url, MessageBody=json.dumps(m["body"]))
        sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=m["handle"])
        redriven += 1
        info(f"Redrove: {m['body']['taskId']} -> main queue")

    if redriven:
        success(f"Redrove {redriven} message(s) back to main queue for reprocessing")
    else:
        info("No messages to redrive")

    # Step 6: Verify redriven messages are back in main queue
    step(6, "Verifying redriven messages in main queue")
    time.sleep(2)
    resp = sqs.receive_message(
        QueueUrl=main_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=3,
    )
    recovered = resp.get("Messages", [])
    kv("Messages recovered", len(recovered))
    for msg in recovered:
        body = json.loads(msg["Body"])
        success(f"Recovered: {body['taskId']}")
        sqs.delete_message(QueueUrl=main_url, ReceiptHandle=msg["ReceiptHandle"])

    if recovered:
        success("DLQ recovery cycle complete")
    else:
        info("Messages may still be in transit -- check queue in AWS console")
