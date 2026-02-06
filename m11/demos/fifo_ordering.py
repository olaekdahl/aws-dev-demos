"""FIFO queue ordering guarantees with message groups."""
import json
import time
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from common import (
    create_session, banner, step, success, info, warn,
    kv, table, generate_name, track_resource,
)


def run(args):
    banner("m11", "SQS FIFO Ordering Guarantees")
    session = create_session(args.profile, args.region)
    sqs = session.client("sqs")

    # Step 1: Create a FIFO queue (name must end in .fifo)
    step(1, "Creating FIFO queue")
    base_name = generate_name("fifo", args.prefix)
    fifo_name = f"{base_name}.fifo"
    q_url = sqs.create_queue(
        QueueName=fifo_name,
        Attributes={
            "FifoQueue": "true",
            "ContentBasedDeduplication": "true",
        },
    )["QueueUrl"]
    track_resource("m11", "sqs_queue", q_url)
    success(f"FIFO queue created: {fifo_name}")
    kv("FifoQueue", "true")
    kv("ContentBasedDeduplication", "true (no need for manual dedup IDs)")

    # Step 2: Send messages with different MessageGroupIds
    step(2, "Sending messages with two message groups")
    info("Group A: sequential pipeline steps (must stay in order)")
    info("Group B: alphabetical items (must stay in order)\n")

    group_a_messages = [
        {"step": "step-1", "action": "validate-input"},
        {"step": "step-2", "action": "process-data"},
        {"step": "step-3", "action": "generate-report"},
    ]
    group_b_messages = [
        {"step": "alpha", "action": "initialize"},
        {"step": "beta", "action": "execute"},
        {"step": "gamma", "action": "finalize"},
    ]

    for msg in group_a_messages:
        sqs.send_message(
            QueueUrl=q_url,
            MessageBody=json.dumps(msg),
            MessageGroupId="group-A",
        )
        info(f"Sent to group-A: {msg['step']} ({msg['action']})")

    for msg in group_b_messages:
        sqs.send_message(
            QueueUrl=q_url,
            MessageBody=json.dumps(msg),
            MessageGroupId="group-B",
        )
        info(f"Sent to group-B: {msg['step']} ({msg['action']})")

    success("All 6 messages sent (3 per group)")

    # Step 3: Receive all messages
    step(3, "Receiving all messages from FIFO queue")
    time.sleep(2)  # Brief pause to ensure delivery

    received = []
    deadline = time.time() + 15
    while time.time() < deadline and len(received) < 6:
        resp = sqs.receive_message(
            QueueUrl=q_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=3,
            AttributeNames=["MessageGroupId", "SequenceNumber"],
        )
        for msg in resp.get("Messages", []):
            body = json.loads(msg["Body"])
            attrs = msg.get("Attributes", {})
            received.append({
                "group": attrs.get("MessageGroupId", "?"),
                "step": body["step"],
                "action": body["action"],
                "sequence": attrs.get("SequenceNumber", "?"),
            })
            sqs.delete_message(QueueUrl=q_url, ReceiptHandle=msg["ReceiptHandle"])

    kv("Total received", len(received))

    # Step 4: Show that within each group, order is preserved
    step(4, "Verifying ordering within each message group")

    group_a_received = [m for m in received if m["group"] == "group-A"]
    group_b_received = [m for m in received if m["group"] == "group-B"]

    info("Group A (pipeline steps):")
    rows_a = []
    for i, m in enumerate(group_a_received):
        rows_a.append([str(i + 1), m["step"], m["action"], m["sequence"]])
    if rows_a:
        table(["Order", "Step", "Action", "Sequence#"], rows_a)

    a_ordered = [m["step"] for m in group_a_received] == ["step-1", "step-2", "step-3"]
    if a_ordered:
        success("Group A: order preserved (step-1 -> step-2 -> step-3)")
    elif group_a_received:
        warn("Group A: unexpected order detected")
    else:
        warn("Group A: no messages received yet")

    info("Group B (alphabetical items):")
    rows_b = []
    for i, m in enumerate(group_b_received):
        rows_b.append([str(i + 1), m["step"], m["action"], m["sequence"]])
    if rows_b:
        table(["Order", "Step", "Action", "Sequence#"], rows_b)

    b_ordered = [m["step"] for m in group_b_received] == ["alpha", "beta", "gamma"]
    if b_ordered:
        success("Group B: order preserved (alpha -> beta -> gamma)")
    elif group_b_received:
        warn("Group B: unexpected order detected")
    else:
        warn("Group B: no messages received yet")

    # Step 5: Explain parallel processing across groups
    step(5, "Key takeaway: parallelism across groups")
    info("FIFO guarantees ordering WITHIN a MessageGroupId.")
    info("Different groups (group-A, group-B) CAN be processed in parallel.")
    info("This means you get both ordering guarantees AND throughput:")
    kv("Per-group ordering", "strict FIFO within each MessageGroupId")
    kv("Cross-group parallelism", "different groups processed independently")
    info("")
    info("Use case: order processing where each customer's orders")
    info("must be sequential, but different customers run in parallel.")
    success("FIFO ordering demo complete")
