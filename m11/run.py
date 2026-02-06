#!/usr/bin/env python3
"""m11 - Async Patterns: SNS/SQS fan-out, dead-letter queues, FIFO ordering."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, success, header
from common.cleanup import get_tracked_resources, clear_tracked
from common.session import create_session

from demos.fanout_pattern import run as fanout_demo
from demos.dlq_recovery import run as dlq_demo
from demos.fifo_ordering import run as fifo_demo

DEMOS = {
    "fanout": fanout_demo,
    "dlq": dlq_demo,
    "fifo": fifo_demo,
}

DEMO_INFO = {
    "fanout": "SNS/SQS fan-out with parallel consumers",
    "dlq": "dead-letter queue and poison pill recovery",
    "fifo": "FIFO ordering guarantees with message groups",
}


def cleanup(args):
    """Delete all SNS topics and SQS queues tracked by m11 demos."""
    resources = get_tracked_resources("m11")
    if not resources:
        info("No tracked resources to clean up.")
        return
    session = create_session(args.profile, args.region)
    sns = session.client("sns")
    sqs = session.client("sqs")
    for r in resources:
        try:
            if r["type"] == "sns_topic":
                # Unsubscribe all subscriptions first
                subs = sns.list_subscriptions_by_topic(
                    TopicArn=r["id"]
                ).get("Subscriptions", [])
                for s in subs:
                    if s["SubscriptionArn"] != "PendingConfirmation":
                        sns.unsubscribe(SubscriptionArn=s["SubscriptionArn"])
                sns.delete_topic(TopicArn=r["id"])
                success(f"Deleted topic: {r['id']}")
            elif r["type"] == "sqs_queue":
                sqs.delete_queue(QueueUrl=r["id"])
                success(f"Deleted queue: {r['id']}")
        except Exception as e:
            info(f"Could not delete {r['id']}: {e}")
    clear_tracked("m11")


def main():
    parser = build_parser("m11: Async Patterns", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m11", "Async Patterns")
        for fn in DEMOS.values():
            fn(args)
        header("\nSAM App (deploy separately):")
        info("  EventBridge: cd m11/sam-eventbridge && sam build && sam deploy --guided")
        info("  Then:        python m11/sam-eventbridge/put_event.py --region us-east-1")


if __name__ == "__main__":
    main()
