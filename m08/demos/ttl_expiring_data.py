"""
Demo: TTL Expiring Data - Auto-Expiring Items with Time to Live

Creates a DynamoDB table with TTL enabled on the "expires_at" attribute, inserts
items with various expiry times (past, near-future, far-future), and shows how
to filter out expired items in queries.

Important: DynamoDB TTL deletion is asynchronous.  Expired items are typically
removed within 48 hours but may still appear in scans/queries until then.
"""
import time
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    table, generate_name, track_resource,
)

MODULE = "m08"


def _wait_for_table_active(ddb, table_name, max_wait=120):
    """Poll until the table reaches ACTIVE status."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        desc = ddb.describe_table(TableName=table_name)["Table"]
        if desc["TableStatus"] == "ACTIVE":
            return True
        time.sleep(2)
    return False


def _ts(dt):
    """Convert datetime to Unix epoch integer (what DynamoDB TTL expects)."""
    return int(dt.timestamp())


def _format_ttl_status(expires_epoch, now_epoch):
    """Return a human-readable TTL status string."""
    diff = expires_epoch - now_epoch
    if diff < 0:
        mins_ago = abs(diff) // 60
        if mins_ago < 60:
            return f"EXPIRED ({mins_ago}m ago)"
        hours_ago = mins_ago // 60
        return f"EXPIRED ({hours_ago}h ago)"
    elif diff < 3600:
        return f"expires in {diff // 60}m"
    else:
        return f"expires in {diff // 3600}h"


def run(args):
    banner("m08", "TTL Expiring Data - Auto-Expiring Items")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")

    table_name = generate_name("ttl-demo", getattr(args, "prefix", None))

    # ── Step 1: Create table with TTL enabled ──
    step(1, 'Create table with TTL enabled on "expires_at" attribute')

    kv("Table", table_name)
    kv("TTL attribute", "expires_at")
    info("DynamoDB TTL uses a Unix epoch timestamp (number) to decide")
    info("when an item should be automatically deleted.")

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
            BillingMode="PAY_PER_REQUEST",
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

    # Enable TTL on the table
    info("Enabling TTL on attribute 'expires_at'...")
    try:
        ddb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                "Enabled": True,
                "AttributeName": "expires_at",
            },
        )
        success("TTL enabled on 'expires_at' attribute")
    except ClientError as exc:
        fail(f"Could not enable TTL: {exc}")
        return

    # Verify TTL setting
    resp = ddb.describe_time_to_live(TableName=table_name)
    ttl_desc = resp["TimeToLiveDescription"]
    kv("TTL status", ttl_desc.get("TimeToLiveStatus", "N/A"))
    kv("TTL attribute", ttl_desc.get("AttributeName", "N/A"))

    # ── Step 2: Insert items with various expiry times ──
    step(2, "Insert items with different TTL values")

    now = datetime.now(timezone.utc)
    now_epoch = _ts(now)

    items = [
        {
            "PK": "SESSION#user-alice",
            "SK": "TOKEN#001",
            "description": "Alice session (expired 2h ago)",
            "expires_at": _ts(now - timedelta(hours=2)),
        },
        {
            "PK": "SESSION#user-bob",
            "SK": "TOKEN#002",
            "description": "Bob session (expired 30min ago)",
            "expires_at": _ts(now - timedelta(minutes=30)),
        },
        {
            "PK": "SESSION#user-charlie",
            "SK": "TOKEN#003",
            "description": "Charlie session (expires in 5min)",
            "expires_at": _ts(now + timedelta(minutes=5)),
        },
        {
            "PK": "SESSION#user-diana",
            "SK": "TOKEN#004",
            "description": "Diana session (expires in 5min)",
            "expires_at": _ts(now + timedelta(minutes=5)),
        },
        {
            "PK": "SESSION#user-eve",
            "SK": "TOKEN#005",
            "description": "Eve session (expires in 1h)",
            "expires_at": _ts(now + timedelta(hours=1)),
        },
    ]

    for item in items:
        ddb.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": item["PK"]},
                "SK": {"S": item["SK"]},
                "description": {"S": item["description"]},
                "expires_at": {"N": str(item["expires_at"])},
            },
        )
        ttl_status = _format_ttl_status(item["expires_at"], now_epoch)
        kv(item["description"], ttl_status)

    success(f"Inserted {len(items)} items with varying TTL values")

    # ── Step 3: Scan and show all items with TTL status ──
    step(3, "Scan table - show all items with TTL status")

    resp = ddb.scan(TableName=table_name)
    scan_items = resp["Items"]

    rows = []
    for item in sorted(scan_items, key=lambda x: int(x["expires_at"]["N"])):
        pk = item["PK"]["S"]
        exp_epoch = int(item["expires_at"]["N"])
        exp_dt = datetime.fromtimestamp(exp_epoch, tz=timezone.utc)
        status = _format_ttl_status(exp_epoch, now_epoch)
        user = pk.split("#")[1] if "#" in pk else pk
        rows.append([user, exp_dt.strftime("%H:%M:%S UTC"), status])

    table(["User", "Expires At", "Status"], rows, col_width=22)

    kv("Total items in table", len(scan_items))
    info("Note: ALL items still appear -- including expired ones.")

    # ── Step 4: Explain TTL async deletion ──
    step(4, "Understanding DynamoDB TTL behavior")

    info("DynamoDB TTL deletion is ASYNCHRONOUS and EVENTUALLY CONSISTENT.")
    info("")
    info("Key facts about TTL:")
    info("  - DynamoDB checks for expired items in the background.")
    info("  - Expired items are typically deleted within 48 hours.")
    info("  - There is no SLA on exact deletion time.")
    info("  - Expired items MAY still appear in Scans and Queries.")
    info("  - TTL deletes do NOT consume Write Capacity Units.")
    info("  - TTL deletions are recorded in DynamoDB Streams (if enabled).")
    info("")
    warn("Do NOT rely on TTL for time-critical deletion.")
    warn("Your application should treat TTL as a cleanup mechanism,")
    warn("not a real-time expiration enforcer.")

    # ── Step 5: Filter expired items in queries ──
    step(5, "Filter out expired items using FilterExpression")

    info("Since expired items may still be in the table, your application")
    info("should filter them out at query time.")
    info("")
    info("FilterExpression: expires_at > :now")
    info(f"  :now = {now_epoch} (current Unix epoch)")
    info("")

    resp = ddb.scan(
        TableName=table_name,
        FilterExpression="expires_at > :now",
        ExpressionAttributeValues={":now": {"N": str(now_epoch)}},
    )
    valid_items = resp["Items"]

    rows = []
    for item in sorted(valid_items, key=lambda x: int(x["expires_at"]["N"])):
        pk = item["PK"]["S"]
        exp_epoch = int(item["expires_at"]["N"])
        exp_dt = datetime.fromtimestamp(exp_epoch, tz=timezone.utc)
        status = _format_ttl_status(exp_epoch, now_epoch)
        user = pk.split("#")[1] if "#" in pk else pk
        rows.append([user, exp_dt.strftime("%H:%M:%S UTC"), status])

    table(["User", "Expires At", "Status"], rows, col_width=22)

    kv("Items returned (valid)", len(valid_items))
    kv("Items filtered out (expired)", len(scan_items) - len(valid_items))
    success("FilterExpression excluded expired items from the result set")

    info("")
    info("Best practice: Always include a filter for TTL in your queries")
    info("so your application never serves stale/expired data, even if")
    info("DynamoDB has not yet deleted the items in the background.")
    info("")

    info(f"Table '{table_name}' tracked for cleanup (run with --cleanup)")
