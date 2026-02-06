"""
Demo: GSI Access Patterns - Unlock Alternate Query Dimensions

Shows how a Global Secondary Index (GSI) enables an entirely different access
pattern on the same DynamoDB table.  The base table is keyed by CustomerId +
OrderId, but the GSI re-indexes by Status + OrderDate so you can efficiently
query "all SHIPPED orders sorted by date" without scanning.
"""
import time
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    table, generate_name, track_resource,
)

MODULE = "m08"


def _wait_for_table(ddb, table_name, max_wait=120):
    """Poll until the table reaches ACTIVE status."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        desc = ddb.describe_table(TableName=table_name)["Table"]
        status = desc["TableStatus"]
        if status == "ACTIVE":
            # Also check that all GSIs are ACTIVE
            gsis = desc.get("GlobalSecondaryIndexes", [])
            if all(g["IndexStatus"] == "ACTIVE" for g in gsis):
                return True
        time.sleep(2)
    return False


def _seed_orders(ddb, table_name):
    """Insert sample order data across multiple customers and statuses."""
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    orders = [
        # Customer C001
        {"CustomerId": "C001", "OrderId": "O1001", "Status": "DELIVERED",
         "OrderDate": (base_date + timedelta(days=1)).isoformat(),
         "Total": "29.99", "Item": "USB-C Cable"},
        {"CustomerId": "C001", "OrderId": "O1002", "Status": "SHIPPED",
         "OrderDate": (base_date + timedelta(days=10)).isoformat(),
         "Total": "149.00", "Item": "Wireless Mouse"},
        {"CustomerId": "C001", "OrderId": "O1003", "Status": "PENDING",
         "OrderDate": (base_date + timedelta(days=25)).isoformat(),
         "Total": "59.95", "Item": "Keyboard"},
        # Customer C002
        {"CustomerId": "C002", "OrderId": "O2001", "Status": "SHIPPED",
         "OrderDate": (base_date + timedelta(days=5)).isoformat(),
         "Total": "399.99", "Item": "Monitor"},
        {"CustomerId": "C002", "OrderId": "O2002", "Status": "CANCELLED",
         "OrderDate": (base_date + timedelta(days=15)).isoformat(),
         "Total": "12.50", "Item": "HDMI Cable"},
        {"CustomerId": "C002", "OrderId": "O2003", "Status": "PENDING",
         "OrderDate": (base_date + timedelta(days=28)).isoformat(),
         "Total": "89.00", "Item": "Webcam"},
        # Customer C003
        {"CustomerId": "C003", "OrderId": "O3001", "Status": "DELIVERED",
         "OrderDate": (base_date + timedelta(days=2)).isoformat(),
         "Total": "249.99", "Item": "Headphones"},
        {"CustomerId": "C003", "OrderId": "O3002", "Status": "SHIPPED",
         "OrderDate": (base_date + timedelta(days=20)).isoformat(),
         "Total": "74.50", "Item": "USB Hub"},
        {"CustomerId": "C003", "OrderId": "O3003", "Status": "PENDING",
         "OrderDate": (base_date + timedelta(days=29)).isoformat(),
         "Total": "199.00", "Item": "Docking Station"},
        # Customer C004
        {"CustomerId": "C004", "OrderId": "O4001", "Status": "CANCELLED",
         "OrderDate": (base_date + timedelta(days=8)).isoformat(),
         "Total": "34.99", "Item": "Mouse Pad"},
        {"CustomerId": "C004", "OrderId": "O4002", "Status": "DELIVERED",
         "OrderDate": (base_date + timedelta(days=12)).isoformat(),
         "Total": "549.00", "Item": "Mechanical Keyboard"},
        {"CustomerId": "C004", "OrderId": "O4003", "Status": "SHIPPED",
         "OrderDate": (base_date + timedelta(days=22)).isoformat(),
         "Total": "119.99", "Item": "Speakers"},
    ]

    for order in orders:
        ddb.put_item(
            TableName=table_name,
            Item={
                "CustomerId": {"S": order["CustomerId"]},
                "OrderId": {"S": order["OrderId"]},
                "Status": {"S": order["Status"]},
                "OrderDate": {"S": order["OrderDate"]},
                "Total": {"S": order["Total"]},
                "Item": {"S": order["Item"]},
                "GSI1PK": {"S": order["Status"]},
                "GSI1SK": {"S": order["OrderDate"]},
            },
        )

    return orders


def run(args):
    banner("m08", "GSI Access Patterns - Unlock Alternate Query Dimensions")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")

    table_name = generate_name("orders-gsi", getattr(args, "prefix", None))

    # ── Step 1: Create table with GSI ──
    step(1, "Create table with Global Secondary Index")

    info("Base table key:  PK = CustomerId, SK = OrderId")
    info("GSI key:         GSI1PK = Status, GSI1SK = OrderDate")
    info(f"Table name:      {table_name}")

    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "CustomerId", "KeyType": "HASH"},
                {"AttributeName": "OrderId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "CustomerId", "AttributeType": "S"},
                {"AttributeName": "OrderId", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1-StatusDate",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except ClientError as exc:
        fail(f"Could not create table: {exc}")
        return

    info("Waiting for table and GSI to become ACTIVE...")
    if not _wait_for_table(ddb, table_name):
        fail("Table did not reach ACTIVE status in time.")
        return
    success(f"Table '{table_name}' is ACTIVE with GSI 'GSI1-StatusDate'")
    track_resource(MODULE, "dynamodb_table", table_name)

    # ── Step 2: Seed order data ──
    step(2, "Seed order data across multiple customers and statuses")

    orders = _seed_orders(ddb, table_name)

    status_counts = {}
    customer_counts = {}
    for o in orders:
        status_counts[o["Status"]] = status_counts.get(o["Status"], 0) + 1
        customer_counts[o["CustomerId"]] = customer_counts.get(o["CustomerId"], 0) + 1

    kv("Total orders", len(orders))
    for status, count in sorted(status_counts.items()):
        kv(f"  {status}", count)
    for cust, count in sorted(customer_counts.items()):
        kv(f"  {cust}", f"{count} orders")
    success("Order data seeded")

    # ── Step 3: Query base table - all orders for customer C001 ──
    step(3, 'Query base table - "All orders for customer C001"')

    info("Query: PK = C001  (natural access pattern)")
    resp = ddb.query(
        TableName=table_name,
        KeyConditionExpression="CustomerId = :cid",
        ExpressionAttributeValues={":cid": {"S": "C001"}},
    )
    items = resp["Items"]

    rows = []
    for item in items:
        rows.append([
            item["OrderId"]["S"],
            item["Status"]["S"],
            item["Item"]["S"],
            f"${item['Total']['S']}",
        ])

    table(["OrderId", "Status", "Item", "Total"], rows, col_width=20)
    success(f"Found {len(items)} orders for C001 -- direct query, no scan needed")

    # ── Step 4: Try to query by status on base table - IMPOSSIBLE ──
    step(4, 'Query base table by Status - IMPOSSIBLE without full scan')

    info("Want: 'All SHIPPED orders sorted by date'")
    info("Problem: Status is NOT part of the base table key schema.")
    info("The only option would be a full-table Scan with FilterExpression.")
    warn("Scan reads EVERY item in the table and filters client-side.")
    warn("At scale (millions of items), this is slow and expensive.")
    info("")

    info("Demonstrating the Scan approach for comparison...")
    resp = ddb.scan(
        TableName=table_name,
        FilterExpression="#s = :status",
        ExpressionAttributeNames={"#s": "Status"},
        ExpressionAttributeValues={":status": {"S": "SHIPPED"}},
    )
    scanned_count = resp["ScannedCount"]
    returned_count = resp["Count"]
    kv("Items scanned (read from disk)", scanned_count)
    kv("Items returned (after filter)", returned_count)
    kv("Wasted reads", scanned_count - returned_count)
    warn(f"Scan read {scanned_count} items to return {returned_count} -- wasteful!")

    # ── Step 5: Query GSI - all SHIPPED orders sorted by date ──
    step(5, 'Query GSI - "All SHIPPED orders sorted by date" -- EASY')

    info("Query GSI1-StatusDate: GSI1PK = SHIPPED")
    resp = ddb.query(
        TableName=table_name,
        IndexName="GSI1-StatusDate",
        KeyConditionExpression="GSI1PK = :status",
        ExpressionAttributeValues={":status": {"S": "SHIPPED"}},
    )
    items = resp["Items"]

    rows = []
    for item in items:
        rows.append([
            item["CustomerId"]["S"],
            item["OrderId"]["S"],
            item["Item"]["S"],
            item["OrderDate"]["S"][:10],
            f"${item['Total']['S']}",
        ])

    table(["Customer", "OrderId", "Item", "Date", "Total"], rows, col_width=16)
    kv("Items scanned", resp["ScannedCount"])
    kv("Items returned", resp["Count"])
    success(f"Found {len(items)} SHIPPED orders -- direct query, sorted by date!")

    # ── Step 6: Query GSI - all PENDING orders ──
    step(6, 'Query GSI - "All PENDING orders" to find what needs attention')

    resp = ddb.query(
        TableName=table_name,
        IndexName="GSI1-StatusDate",
        KeyConditionExpression="GSI1PK = :status",
        ExpressionAttributeValues={":status": {"S": "PENDING"}},
    )
    items = resp["Items"]

    rows = []
    for item in items:
        rows.append([
            item["CustomerId"]["S"],
            item["OrderId"]["S"],
            item["Item"]["S"],
            item["OrderDate"]["S"][:10],
            f"${item['Total']['S']}",
        ])

    table(["Customer", "OrderId", "Item", "Date", "Total"], rows, col_width=16)
    success(f"Found {len(items)} PENDING orders that need attention")

    # ── Visual comparison ──
    info("")
    info("=" * 58)
    info("  COMPARISON: With vs Without GSI")
    info("=" * 58)
    info("")
    info("  WITHOUT GSI (base table only):")
    info("    'All orders for C001'     -> Query PK=C001     [OK]")
    info("    'All SHIPPED orders'      -> Full table Scan   [SLOW]")
    info("    'PENDING orders by date'  -> Full table Scan   [SLOW]")
    info("")
    info("  WITH GSI (GSI1PK=Status, GSI1SK=OrderDate):")
    info("    'All orders for C001'     -> Query PK=C001     [OK]")
    info("    'All SHIPPED orders'      -> Query GSI1PK      [FAST]")
    info("    'PENDING orders by date'  -> Query GSI1PK      [FAST]")
    info("")
    info("  The GSI costs extra storage and write capacity,")
    info("  but turns expensive Scans into efficient Queries.")
    info("")

    info(f"Table '{table_name}' tracked for cleanup (run with --cleanup)")
