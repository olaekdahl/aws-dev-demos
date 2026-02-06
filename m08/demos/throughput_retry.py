"""
Demo: Throughput & Retry - Exponential Backoff Under Throttling

Creates a provisioned-capacity DynamoDB table with intentionally low throughput
(1 WCU) and writes 50 items to trigger throttling.  Demonstrates exponential
backoff with jitter and shows real-time progress with colored counters.
"""
import time
import random
from botocore.exceptions import ClientError

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    table, progress_bar, generate_name, track_resource,
)

MODULE = "m08"

# Retry configuration
MAX_RETRIES = 8
BASE_DELAY = 0.25       # seconds
MAX_DELAY = 8.0         # seconds cap
JITTER_LOW = 0.6        # multiplier range low
JITTER_HIGH = 1.4       # multiplier range high
TOTAL_ITEMS = 50


def _wait_for_table_active(ddb, table_name, max_wait=120):
    """Poll until the table reaches ACTIVE status."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        desc = ddb.describe_table(TableName=table_name)["Table"]
        if desc["TableStatus"] == "ACTIVE":
            return True
        time.sleep(2)
    return False


def _write_with_backoff(ddb, table_name, item_id, stats):
    """Write a single item with exponential backoff + jitter on throttle."""
    item = {
        "PK": {"S": f"ITEM#{item_id:04d}"},
        "SK": {"S": "DATA"},
        "Payload": {"S": f"Demo payload for item {item_id}"},
        "Timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
    }

    t0 = time.perf_counter()

    for attempt in range(MAX_RETRIES + 1):
        try:
            ddb.put_item(TableName=table_name, Item=item)
            latency = time.perf_counter() - t0
            stats["latencies"].append(latency)
            return True
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("ProvisionedThroughputExceededException", "ThrottlingException"):
                stats["retries"] += 1
                if attempt == MAX_RETRIES:
                    stats["failures"] += 1
                    return False
                # Exponential backoff with jitter
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                jitter = random.uniform(JITTER_LOW, JITTER_HIGH)
                delay *= jitter
                time.sleep(delay)
            else:
                # Non-throttle error -- do not retry
                stats["failures"] += 1
                return False

    stats["failures"] += 1
    return False


def run(args):
    banner("m08", "Throughput & Retry - Exponential Backoff Under Throttling")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")

    table_name = generate_name("throttle", getattr(args, "prefix", None))

    # ── Step 1: Create provisioned table with very low throughput ──
    step(1, "Create provisioned table with 1 RCU / 1 WCU (intentionally low)")

    kv("Table", table_name)
    kv("Read capacity", "1 RCU")
    kv("Write capacity", "1 WCU")
    info("This low throughput will cause DynamoDB to throttle rapid writes.")

    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 1,
                "WriteCapacityUnits": 1,
            },
        )
    except ClientError as exc:
        fail(f"Could not create table: {exc}")
        return

    info("Waiting for table to become ACTIVE...")
    if not _wait_for_table_active(ddb, table_name):
        fail("Table did not reach ACTIVE status in time.")
        return
    success(f"Table '{table_name}' is ACTIVE")
    track_resource(MODULE, "dynamodb_table", table_name)

    # ── Step 2: Explain what will happen ──
    step(2, "Explain the retry strategy")

    info("We will write 50 items as fast as possible to a 1-WCU table.")
    info("DynamoDB will throttle us when we exceed provisioned capacity.")
    info("")
    info("Retry strategy: exponential backoff with jitter")
    kv("Max retries", MAX_RETRIES)
    kv("Base delay", f"{BASE_DELAY}s")
    kv("Max delay cap", f"{MAX_DELAY}s")
    kv("Jitter range", f"{JITTER_LOW}x - {JITTER_HIGH}x")
    info("")
    info("Formula: delay = min(base * 2^attempt, max_cap) * random(0.6, 1.4)")
    info("Jitter prevents thundering-herd when many clients retry together.")

    # ── Step 3: Write items with real-time progress ──
    step(3, f"Write {TOTAL_ITEMS} items with exponential backoff")

    stats = {
        "retries": 0,
        "failures": 0,
        "latencies": [],
    }

    t_start = time.perf_counter()

    for i in range(1, TOTAL_ITEMS + 1):
        retries_before = stats["retries"]
        ok = _write_with_backoff(ddb, table_name, i, stats)

        retries_this = stats["retries"] - retries_before
        label = f"({stats['retries']} retries, {stats['failures']} failures)"
        if retries_this > 0:
            label = f"\033[33m{label}\033[0m"  # yellow on throttle
        progress_bar(i, TOTAL_ITEMS, label=label)

    total_time = time.perf_counter() - t_start

    # ── Step 4: Final statistics ──
    step(4, "Final statistics")

    successful = TOTAL_ITEMS - stats["failures"]
    avg_latency = (
        sum(stats["latencies"]) / len(stats["latencies"])
        if stats["latencies"]
        else 0
    )
    max_latency = max(stats["latencies"]) if stats["latencies"] else 0
    min_latency = min(stats["latencies"]) if stats["latencies"] else 0

    kv("Total items attempted", TOTAL_ITEMS)
    kv("Successful writes", successful)
    kv("Failed writes", stats["failures"])
    kv("Total retries", stats["retries"])
    kv("Total elapsed time", f"{total_time:.1f}s")
    kv("Avg latency per item", f"{avg_latency * 1000:.0f}ms")
    kv("Min latency", f"{min_latency * 1000:.0f}ms")
    kv("Max latency", f"{max_latency * 1000:.0f}ms")

    if stats["retries"] > 0:
        info("")
        info("Retries occurred because the 1-WCU table could not keep up")
        info("with the write rate. Each throttled request backed off with")
        info("increasing delay + jitter before retrying.")
    else:
        info("")
        info("No retries were needed -- DynamoDB burst capacity may have")
        info("absorbed the writes. Try running again quickly to exhaust")
        info("the burst budget.")

    if stats["failures"] > 0:
        warn(f"{stats['failures']} item(s) failed after {MAX_RETRIES} retries each.")
    else:
        success(f"All {successful} items written successfully")

    # Summary table
    table(
        ["Metric", "Value"],
        [
            ["Items written", str(successful)],
            ["Total retries", str(stats["retries"])],
            ["Retries / item", f"{stats['retries'] / TOTAL_ITEMS:.2f}"],
            ["Avg latency", f"{avg_latency * 1000:.0f}ms"],
            ["Total time", f"{total_time:.1f}s"],
        ],
        col_width=20,
    )

    info(f"Table '{table_name}' tracked for cleanup (run with --cleanup)")
