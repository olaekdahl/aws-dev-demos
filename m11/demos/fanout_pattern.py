"""SNS/SQS fan-out pattern: one message delivered to multiple subscribers."""
import json
import time
import threading
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from common import create_session, banner, step, success, info, kv, generate_name, track_resource


def run(args):
    banner("m11", "SNS/SQS Fan-out Pattern")
    session = create_session(args.profile, args.region)
    sns = session.client("sns")
    sqs = session.client("sqs")

    # Step 1: Create SNS topic
    step(1, "Creating SNS topic")
    topic_name = generate_name("fanout-topic", args.prefix)
    topic_arn = sns.create_topic(Name=topic_name)["TopicArn"]
    track_resource("m11", "sns_topic", topic_arn)
    success(f"Topic: {topic_arn}")

    # Step 2: Create 2 SQS queues (orders-svc and analytics-svc)
    step(2, "Creating SQS subscriber queues")
    queue_urls = []
    for svc in ["orders-svc", "analytics-svc"]:
        q_name = generate_name(svc, args.prefix)
        q_url = sqs.create_queue(QueueName=q_name)["QueueUrl"]
        q_arn = sqs.get_queue_attributes(
            QueueUrl=q_url, AttributeNames=["QueueArn"]
        )["Attributes"]["QueueArn"]

        # Allow SNS to publish to queue
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "sns.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": q_arn,
                "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
            }],
        }
        sqs.set_queue_attributes(
            QueueUrl=q_url,
            Attributes={"Policy": json.dumps(policy)},
        )
        sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=q_arn)
        queue_urls.append(q_url)
        track_resource("m11", "sqs_queue", q_url)
        success(f"Queue: {svc} -> subscribed")

    # Step 3: Publish messages
    step(3, "Publishing 5 order events to SNS")
    for i in range(5):
        order = {
            "orderId": f"ORD-{i + 1:03d}",
            "customer": f"customer-{i + 1}",
            "total": round(19.99 + i * 10, 2),
        }
        sns.publish(TopicArn=topic_arn, Message=json.dumps(order))
        info(f"Published: {order['orderId']} (${order['total']})")
    success("All messages published")

    # Step 4: Poll both queues simultaneously using threads
    step(4, "Polling both subscriber queues (fan-out in action)")
    info("Each message should appear in BOTH queues...\n")

    results = {"orders-svc": [], "analytics-svc": []}

    def poll_queue(queue_url, label, result_list):
        deadline = time.time() + 15  # 15 second timeout
        while time.time() < deadline and len(result_list) < 5:
            resp = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=3,
            )
            for msg in resp.get("Messages", []):
                body = json.loads(msg["Body"])
                payload = json.loads(body.get("Message", "{}"))
                result_list.append(payload)
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )

    t1 = threading.Thread(
        target=poll_queue,
        args=(queue_urls[0], "orders-svc", results["orders-svc"]),
    )
    t2 = threading.Thread(
        target=poll_queue,
        args=(queue_urls[1], "analytics-svc", results["analytics-svc"]),
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Step 5: Show results
    step(5, "Fan-out results")
    kv("orders-svc received", f"{len(results['orders-svc'])} messages")
    kv("analytics-svc received", f"{len(results['analytics-svc'])} messages")

    if len(results["orders-svc"]) == 5 and len(results["analytics-svc"]) == 5:
        success("Fan-out confirmed: every message delivered to BOTH subscribers")
    else:
        info("Some messages may still be in transit (SQS is eventually consistent)")
