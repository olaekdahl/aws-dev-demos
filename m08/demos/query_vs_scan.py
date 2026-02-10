"""
Demo: Query vs Scan - Performance Comparison

Compares DynamoDB Query (uses partition key, efficient) vs Scan (reads entire
table, expensive). Shows when to use each and the RCU cost difference.
"""
import time
from datetime import datetime, timedelta, timezone

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
        if desc["TableStatus"] == "ACTIVE":
            return True
        time.sleep(2)
    return False


def _seed_data(ddb, table_name):
    """Insert sample product data for multiple categories."""
    base_date = datetime.now(timezone.utc) - timedelta(days=60)
    products = [
        # Electronics category
        {"Category": "Electronics", "ProductId": "E001", "Name": "Wireless Mouse", "Price": "29.99", "Stock": "150"},
        {"Category": "Electronics", "ProductId": "E002", "Name": "USB-C Hub", "Price": "49.99", "Stock": "80"},
        {"Category": "Electronics", "ProductId": "E003", "Name": "Bluetooth Keyboard", "Price": "79.99", "Stock": "45"},
        {"Category": "Electronics", "ProductId": "E004", "Name": "Monitor Stand", "Price": "39.99", "Stock": "120"},
        {"Category": "Electronics", "ProductId": "E005", "Name": "Webcam HD", "Price": "89.99", "Stock": "60"},
        # Books category
        {"Category": "Books", "ProductId": "B001", "Name": "Python Cookbook", "Price": "45.00", "Stock": "200"},
        {"Category": "Books", "ProductId": "B002", "Name": "AWS in Action", "Price": "55.00", "Stock": "150"},
        {"Category": "Books", "ProductId": "B003", "Name": "Clean Code", "Price": "40.00", "Stock": "180"},
        {"Category": "Books", "ProductId": "B004", "Name": "System Design", "Price": "50.00", "Stock": "90"},
        # Clothing category
        {"Category": "Clothing", "ProductId": "C001", "Name": "AWS T-Shirt", "Price": "25.00", "Stock": "300"},
        {"Category": "Clothing", "ProductId": "C002", "Name": "Developer Hoodie", "Price": "65.00", "Stock": "100"},
        {"Category": "Clothing", "ProductId": "C003", "Name": "Tech Socks", "Price": "12.00", "Stock": "500"},
        # Home category
        {"Category": "Home", "ProductId": "H001", "Name": "Desk Lamp", "Price": "35.00", "Stock": "75"},
        {"Category": "Home", "ProductId": "H002", "Name": "Cable Organizer", "Price": "15.00", "Stock": "250"},
        {"Category": "Home", "ProductId": "H003", "Name": "Monitor Light Bar", "Price": "55.00", "Stock": "40"},
    ]

    for product in products:
        ddb.put_item(
            TableName=table_name,
            Item={k: {"S": v} for k, v in product.items()}
        )

    return len(products)


def run(args):
    banner("m08", "Query vs Scan - Performance Comparison")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")
    region = session.region_name

    table_name = generate_name("query-scan", getattr(args, "prefix", None))

    # ── Step 1: Create table ──
    step(1, "Create DynamoDB table")

    kv("Table name", table_name)
    kv("Partition key", "Category (String)")
    kv("Sort key", "ProductId (String)")

    try:
        ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "Category", "KeyType": "HASH"},
                {"AttributeName": "ProductId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "Category", "AttributeType": "S"},
                {"AttributeName": "ProductId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except Exception as e:
        fail(f"Failed to create table: {e}")
        return

    info("Waiting for table to become ACTIVE...")
    if not _wait_for_table(ddb, table_name):
        fail("Table did not become ACTIVE in time")
        return

    success("Table created")
    track_resource(MODULE, "dynamodb_table", table_name, region=region)

    # ── Step 2: Seed data ──
    step(2, "Seed sample product data")

    count = _seed_data(ddb, table_name)
    kv("Products inserted", count)
    kv("Categories", "Electronics, Books, Clothing, Home")
    success("Data seeded")

    # ── Step 3: Query operation ──
    step(3, "Query - get all products in 'Electronics' category")

    info("Query uses partition key -> efficient, reads only matching items")
    info("KeyConditionExpression: Category = :cat")

    start = time.perf_counter()
    query_resp = ddb.query(
        TableName=table_name,
        KeyConditionExpression="Category = :cat",
        ExpressionAttributeValues={":cat": {"S": "Electronics"}},
        ReturnConsumedCapacity="TOTAL",
    )
    query_time = (time.perf_counter() - start) * 1000

    kv("Items returned", query_resp["Count"])
    kv("Scanned count", query_resp["ScannedCount"])
    kv("RCUs consumed", query_resp["ConsumedCapacity"]["CapacityUnits"])
    kv("Time", f"{query_time:.1f}ms")
    success("Query completed")

    print()
    info("Query results:")
    headers = ["ProductId", "Name", "Price", "Stock"]
    rows = []
    for item in query_resp["Items"]:
        rows.append([
            item["ProductId"]["S"],
            item["Name"]["S"],
            f"${item['Price']['S']}",
            item["Stock"]["S"],
        ])
    table(headers, rows)

    # ── Step 4: Scan operation ──
    step(4, "Scan - find all products with Price > $40")

    info("Scan reads ENTIRE table, then filters -> expensive!")
    info("FilterExpression: Price > :min (applied AFTER reading)")

    start = time.perf_counter()
    scan_resp = ddb.scan(
        TableName=table_name,
        FilterExpression="Price > :min",
        ExpressionAttributeValues={":min": {"S": "40"}},  # String comparison for demo
        ReturnConsumedCapacity="TOTAL",
    )
    scan_time = (time.perf_counter() - start) * 1000

    kv("Items returned", scan_resp["Count"])
    kv("Scanned count", scan_resp["ScannedCount"])
    kv("RCUs consumed", scan_resp["ConsumedCapacity"]["CapacityUnits"])
    kv("Time", f"{scan_time:.1f}ms")
    warn(f"Scan read {scan_resp['ScannedCount']} items to return {scan_resp['Count']}")
    success("Scan completed")

    print()
    info("Scan results (Price > $40):")
    headers = ["Category", "ProductId", "Name", "Price"]
    rows = []
    for item in scan_resp["Items"]:
        rows.append([
            item["Category"]["S"],
            item["ProductId"]["S"],
            item["Name"]["S"],
            f"${item['Price']['S']}",
        ])
    table(headers, rows)

    # ── Step 5: Comparison summary ──
    step(5, "Query vs Scan comparison")

    query_rcu = query_resp["ConsumedCapacity"]["CapacityUnits"]
    scan_rcu = scan_resp["ConsumedCapacity"]["CapacityUnits"]

    headers = ["Aspect", "Query", "Scan"]
    rows = [
        ["Uses partition key", "Yes (required)", "No"],
        ["Reads from table", "Only matching partition", "Entire table"],
        ["Filter applied", "Before reading (via key)", "After reading all"],
        ["RCUs consumed", f"{query_rcu}", f"{scan_rcu}"],
        ["Time (ms)", f"{query_time:.1f}", f"{scan_time:.1f}"],
        ["Cost at scale", "Efficient", "Expensive"],
        ["Best for", "Known access patterns", "Analytics, one-time jobs"],
    ]
    table(headers, rows)

    print()
    info("Key takeaways:")
    info("  - Query requires a partition key and is O(items in partition)")
    info("  - Scan reads the entire table regardless of filter")
    info("  - FilterExpression reduces returned items but NOT RCUs consumed")
    info("  - Design tables with access patterns in mind -> use Query, not Scan")
    info("  - For non-key attributes, consider GSI to enable Query instead of Scan")

    info(f"\nTable {table_name} tracked for cleanup (run with --cleanup)")
