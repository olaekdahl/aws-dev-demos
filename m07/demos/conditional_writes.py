"""
Demo: Optimistic Locking with DynamoDB Conditional Writes

Simulates two concurrent writers using a version attribute to detect conflicts.
Writer A and Writer B both read the same item, then race to update it.  The
loser gets a ConditionalCheckFailedException, re-reads, and retries -- a
classic optimistic concurrency control pattern.
"""
import time
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    table, generate_name, track_resource,
)

# ── ANSI helpers (complement the common palette) ──────────────────

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
RESET = "\033[0m"


def _timeline_entry(ts, actor, action, color=DIM):
    """Print a single line in the event timeline."""
    print(f"  {DIM}{ts}{RESET}  {color}{BOLD}{actor:<10}{RESET}  {action}")


def _wait_for_table(ddb, table_name: str, timeout: int = 60):
    """Poll until the table becomes ACTIVE."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = ddb.describe_table(TableName=table_name)["Table"]["TableStatus"]
        if status == "ACTIVE":
            return
        time.sleep(2)
    raise TimeoutError(f"Table {table_name} did not become ACTIVE within {timeout}s")


def run(args):
    banner("m07", "Optimistic Locking - Conditional Writes")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")

    table_name = generate_name("opt-lock", getattr(args, "prefix", None))

    # ── Step 1: Create table ──────────────────────────────────────
    step(1, "Create DynamoDB table for the locking demo")
    kv("Table", table_name)

    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        info("Waiting for table to become ACTIVE...")
        _wait_for_table(ddb, table_name)
        success(f"Table '{table_name}' is ACTIVE")
    except ClientError as exc:
        fail(f"Could not create table: {exc}")
        return

    track_resource("m07", "dynamodb_table", table_name)

    # ── Step 2: Insert initial item with version=1 ────────────────
    step(2, "Insert a document with version attribute (optimistic lock)")

    item_pk = "CONFIG#app-settings"

    try:
        ddb.put_item(
            TableName=table_name,
            Item={
                "PK":       {"S": item_pk},
                "theme":    {"S": "dark"},
                "language": {"S": "en"},
                "version":  {"N": "1"},
            },
        )
        kv("PK", item_pk)
        kv("theme", "dark")
        kv("language", "en")
        kv("version", "1")
        success("Item inserted with version=1")
    except ClientError as exc:
        fail(f"PutItem failed: {exc}")
        return

    # ── Step 3: Writer A reads the item ───────────────────────────
    step(3, "Writer A reads the item, sees version=1")

    try:
        resp_a = ddb.get_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
        )
        item_a = resp_a["Item"]
        version_a = int(item_a["version"]["N"])
        kv("Writer A sees version", version_a)
        kv("Writer A sees theme", item_a["theme"]["S"])
        success("Writer A has a local copy with version=1")
    except ClientError as exc:
        fail(f"Writer A GetItem failed: {exc}")
        return

    # ── Step 4: Writer B reads the same item ──────────────────────
    step(4, "Writer B reads the item, also sees version=1")

    try:
        resp_b = ddb.get_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
        )
        item_b = resp_b["Item"]
        version_b = int(item_b["version"]["N"])
        kv("Writer B sees version", version_b)
        kv("Writer B sees language", item_b["language"]["S"])
        success("Writer B has a local copy with version=1")
    except ClientError as exc:
        fail(f"Writer B GetItem failed: {exc}")
        return

    info("\nBoth writers now hold stale copies. The race begins...")

    # ── Step 5: Writer A updates (succeeds) ───────────────────────
    step(5, "Writer A updates theme -> 'light' (condition: version=1)")

    writer_a_succeeded = False
    try:
        ddb.update_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
            UpdateExpression="SET theme = :t, version = :new_v",
            ConditionExpression="version = :expected_v",
            ExpressionAttributeValues={
                ":t":          {"S": "light"},
                ":new_v":      {"N": "2"},
                ":expected_v": {"N": str(version_a)},
            },
            ReturnValues="ALL_NEW",
        )
        writer_a_succeeded = True
        kv("theme", "light")
        kv("version", "1 -> 2")
        success(f"{GREEN}Writer A's update SUCCEEDED - version incremented to 2{RESET}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            fail("Writer A was unexpectedly blocked (should have succeeded)")
        else:
            fail(f"Unexpected error: {exc}")
        return

    # ── Step 6: Writer B tries to update (CONFLICT!) ──────────────
    step(6, "Writer B updates language -> 'fr' (condition: version=1) -- CONFLICT!")

    info("Writer B still thinks version=1, but Writer A already bumped it to 2\n")

    writer_b_conflict = False
    try:
        ddb.update_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
            UpdateExpression="SET #lang = :l, version = :new_v",
            ConditionExpression="version = :expected_v",
            ExpressionAttributeNames={
                "#lang": "language",  # language is a reserved word
            },
            ExpressionAttributeValues={
                ":l":          {"S": "fr"},
                ":new_v":      {"N": "2"},
                ":expected_v": {"N": str(version_b)},  # still 1!
            },
        )
        warn("Writer B's update succeeded unexpectedly (no conflict)")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            writer_b_conflict = True
            fail(f"{RED}ConditionalCheckFailedException! "
                 f"Writer B's update was REJECTED{RESET}")
            info("The condition 'version = 1' failed because the current version is 2")
            info("Writer B must re-read and retry")
        else:
            fail(f"Unexpected error: {exc}")
            return

    # ── Step 7: Writer B re-reads and retries (succeeds) ──────────
    step(7, "Writer B re-reads (version=2), retries update -> succeeds")

    try:
        resp_b2 = ddb.get_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
        )
        item_b2 = resp_b2["Item"]
        version_b2 = int(item_b2["version"]["N"])
        kv("Writer B re-reads version", version_b2)
        info(f"Writer B now knows version={version_b2}, retrying with correct condition\n")

        ddb.update_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
            UpdateExpression="SET #lang = :l, version = :new_v",
            ConditionExpression="version = :expected_v",
            ExpressionAttributeNames={
                "#lang": "language",
            },
            ExpressionAttributeValues={
                ":l":          {"S": "fr"},
                ":new_v":      {"N": "3"},
                ":expected_v": {"N": str(version_b2)},
            },
            ReturnValues="ALL_NEW",
        )
        kv("language", "fr")
        kv("version", "2 -> 3")
        success(f"{GREEN}Writer B's retry SUCCEEDED - version incremented to 3{RESET}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            fail("Writer B's retry was also blocked (unexpected)")
        else:
            fail(f"Unexpected error: {exc}")
        return

    # ── Final state ───────────────────────────────────────────────
    info("")
    info("Reading final state of the item:")

    try:
        resp_final = ddb.get_item(
            TableName=table_name,
            Key={"PK": {"S": item_pk}},
        )
        final = resp_final["Item"]
        kv("PK", final["PK"]["S"])
        kv("theme", final["theme"]["S"])
        kv("language", final["language"]["S"])
        kv("version", final["version"]["N"])
    except ClientError as exc:
        fail(f"Final read failed: {exc}")

    # ── Event timeline ────────────────────────────────────────────
    info("")
    info(f"{BOLD}Event Timeline:{RESET}")
    print()
    _timeline_entry("T0", "Item",     "Created with theme=dark, language=en, version=1")
    _timeline_entry("T1", "Writer A", "Reads item -> sees version=1", CYAN)
    _timeline_entry("T2", "Writer B", "Reads item -> sees version=1", CYAN)
    _timeline_entry("T3", "Writer A", f"{GREEN}Updates theme=light, version 1->2 (SUCCESS){RESET}", GREEN)
    _timeline_entry("T4", "Writer B", f"{RED}Tries version=1 condition -> REJECTED{RESET}", RED)
    _timeline_entry("T5", "Writer B", "Re-reads item -> sees version=2", CYAN)
    _timeline_entry("T6", "Writer B", f"{GREEN}Retries with version=2 -> language=fr, version 2->3 (SUCCESS){RESET}", GREEN)
    print()

    info("Key takeaway: ConditionExpression acts as an optimistic lock.")
    info("No item-level locks needed -- conflicts are detected at write time,")
    info("and the loser simply re-reads and retries.")
    info("")

    table(
        ["Concept", "How It Works"],
        [
            ["Optimistic lock", "version attr incremented on write"],
            ["Condition", "version = :expected prevents stale writes"],
            ["Conflict", "ConditionalCheckFailedException"],
            ["Resolution", "Re-read, get new version, retry"],
        ],
        col_width=28,
    )

    success(f"Table '{table_name}' tracked for cleanup (run with --cleanup)")
