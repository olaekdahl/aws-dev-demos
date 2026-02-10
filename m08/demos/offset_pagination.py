"""
Demo: Offset Pagination - Mimicking SQL OFFSET in DynamoDB

DynamoDB doesn't have OFFSET like SQL. It uses cursor-based pagination with
ExclusiveStartKey. This demo shows strategies to access specific "pages":

1. Sequential page navigation (cursor-based)
2. Page token caching (for random page access)
3. Skip-to-page by traversing (expensive but sometimes needed)
"""
import time
import json
import base64
from datetime import datetime, timezone

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


def _seed_data(ddb, table_name, num_items=50):
    """Insert sample order data for pagination demo."""
    now = datetime.now(timezone.utc)
    
    for i in range(1, num_items + 1):
        order_id = f"ORD-{i:04d}"
        ddb.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": "ORDERS"},
                "SK": {"S": order_id},
                "OrderId": {"S": order_id},
                "Customer": {"S": f"Customer-{(i % 10) + 1}"},
                "Amount": {"N": str(10 + (i * 5))},
                "Status": {"S": "completed" if i % 3 else "pending"},
                "CreatedAt": {"S": now.isoformat()},
            }
        )
    
    return num_items


def _encode_page_token(last_key):
    """Encode LastEvaluatedKey as a URL-safe string token."""
    if not last_key:
        return None
    return base64.urlsafe_b64encode(json.dumps(last_key).encode()).decode()


def _decode_page_token(token):
    """Decode a page token back to ExclusiveStartKey."""
    if not token:
        return None
    return json.loads(base64.urlsafe_b64decode(token.encode()).decode())


def run(args):
    banner("m08", "Offset Pagination - Mimicking SQL OFFSET")

    session = create_session(args.profile, args.region)
    ddb = session.client("dynamodb")
    region = session.region_name

    table_name = generate_name("pagination", getattr(args, "prefix", None))
    page_size = 5  # Items per page

    # ── Step 1: Create table ──
    step(1, "Create DynamoDB table")

    kv("Table name", table_name)
    kv("Partition key", "PK (String)")
    kv("Sort key", "SK (String)")

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
    step(2, "Seed sample order data")

    total_items = 50
    count = _seed_data(ddb, table_name, total_items)
    kv("Orders inserted", count)
    kv("Page size", page_size)
    kv("Expected pages", (total_items + page_size - 1) // page_size)
    success("Data seeded")

    # ── Step 3: Basic cursor pagination ──
    step(3, "Strategy 1: Sequential cursor-based pagination")

    info("DynamoDB uses LastEvaluatedKey/ExclusiveStartKey for pagination")
    info("This is efficient for forward navigation but NO random access")
    print()

    # Fetch first 3 pages sequentially
    last_key = None
    page_tokens = {1: None}  # Page 1 starts with no token
    
    for page_num in range(1, 4):
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "ORDERS"}},
            "Limit": page_size,
        }
        if last_key:
            query_params["ExclusiveStartKey"] = last_key

        response = ddb.query(**query_params)
        items = response["Items"]
        last_key = response.get("LastEvaluatedKey")
        
        # Cache the token for next page
        if last_key:
            page_tokens[page_num + 1] = last_key

        info(f"Page {page_num}: {len(items)} items")
        for item in items:
            info(f"  - {item['OrderId']['S']}: ${item['Amount']['N']} ({item['Status']['S']})")
    
    print()
    warn("Problem: To reach page 5, you must read pages 1-4 first!")

    # ── Step 4: Page token caching ──
    step(4, "Strategy 2: Cache page tokens for random access")

    info("Pre-compute and cache tokens for each page boundary")
    info("Trade-off: Initial scan cost vs. random page access later")
    print()

    # Build complete page token cache
    page_tokens = {1: None}
    last_key = None
    page_num = 1
    
    info("Building page token cache...")
    while True:
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "ORDERS"}},
            "Limit": page_size,
        }
        if last_key:
            query_params["ExclusiveStartKey"] = last_key

        response = ddb.query(**query_params)
        last_key = response.get("LastEvaluatedKey")
        
        if last_key:
            page_num += 1
            page_tokens[page_num] = last_key
        else:
            break
    
    total_pages = page_num
    kv("Total pages cached", total_pages)
    print()

    # Show encoded tokens (as you'd store in a cache/database)
    info("Sample cached page tokens (base64 encoded for storage):")
    for pg in [1, 3, 5, 10]:
        if pg in page_tokens:
            token = _encode_page_token(page_tokens[pg])
            display_token = token[:30] + "..." if token and len(token) > 30 else (token or "(start)")
            info(f"  Page {pg}: {display_token}")

    # ── Step 5: Jump directly to page ──
    step(5, "Jump directly to page 7 using cached token")

    target_page = 7
    if target_page in page_tokens:
        info(f"Using cached token to go directly to page {target_page}")
        
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "ORDERS"}},
            "Limit": page_size,
        }
        if page_tokens[target_page]:
            query_params["ExclusiveStartKey"] = page_tokens[target_page]

        response = ddb.query(**query_params)
        items = response["Items"]

        print()
        headers = ["OrderId", "Customer", "Amount", "Status"]
        rows = [[
            item["OrderId"]["S"],
            item["Customer"]["S"],
            f"${item['Amount']['N']}",
            item["Status"]["S"],
        ] for item in items]
        table(headers, rows)

        success(f"Page {target_page} retrieved with single query (no scanning previous pages)")
    else:
        warn(f"Page {target_page} not in cache")

    # ── Step 6: Skip-to-page without cache ──
    step(6, "Strategy 3: Skip to page N (without cache)")

    info("Sometimes you need random page access without pre-caching")
    info("Solution: Query with high Limit, then skip items client-side")
    warn("This reads all items up to target page - expensive!")
    print()

    target_page = 8
    offset = (target_page - 1) * page_size  # Items to skip
    
    kv("Target page", target_page)
    kv("Items to skip", offset)
    kv("Items to fetch", page_size)

    # Fetch enough items to reach target page plus the page itself
    start = time.perf_counter()
    items_to_fetch = offset + page_size
    
    all_items = []
    last_key = None
    
    while len(all_items) < items_to_fetch:
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "ORDERS"}},
            "Limit": min(page_size * 3, items_to_fetch - len(all_items)),  # Batch reads
            "ReturnConsumedCapacity": "TOTAL",
        }
        if last_key:
            query_params["ExclusiveStartKey"] = last_key

        response = ddb.query(**query_params)
        all_items.extend(response["Items"])
        last_key = response.get("LastEvaluatedKey")
        
        if not last_key:
            break
    
    elapsed = (time.perf_counter() - start) * 1000
    
    # Get the target page items
    page_items = all_items[offset:offset + page_size]
    
    print()
    info(f"Page {target_page} items:")
    headers = ["OrderId", "Customer", "Amount", "Status"]
    rows = [[
        item["OrderId"]["S"],
        item["Customer"]["S"],
        f"${item['Amount']['N']}",
        item["Status"]["S"],
    ] for item in page_items]
    table(headers, rows)

    kv("Total items read", len(all_items))
    kv("Items displayed", len(page_items))
    kv("Time", f"{elapsed:.1f}ms")
    warn(f"To show {len(page_items)} items, we read {len(all_items)} from DynamoDB")

    # ── Step 7: Comparison summary ──
    step(7, "Pagination strategies comparison")

    headers = ["Strategy", "Random Access", "Cost", "Complexity", "Use Case"]
    rows = [
        ["Cursor (Sequential)", "No", "Low", "Simple", "Infinite scroll, forward-only"],
        ["Token Cache", "Yes", "Initial scan", "Medium", "Known dataset, admin UIs"],
        ["Skip-to-Page", "Yes", "High (reads)", "Simple", "Small datasets, rare use"],
        ["GSI + Query", "Partial", "Medium", "Medium", "If can design key for offset"],
    ]
    table(headers, rows)

    print()
    info("Key takeaways:")
    info("  - DynamoDB pagination is cursor-based, not offset-based")
    info("  - For random page access, cache page tokens or accept read cost")
    info("  - SQL OFFSET scans too - DynamoDB just makes the cost explicit")
    info("  - Consider if you really need random pages (often infinite scroll works)")
    info("  - For analytics/exports, use parallel scan with Segments")

    print()
    info("Pro tips for pagination:")
    info("  1. Encode LastEvaluatedKey as opaque token for clients")
    info("  2. Set reasonable page sizes (10-100 items)")
    info("  3. Include 'hasNextPage' and 'nextToken' in API responses")
    info("  4. For large exports, use parallel scan with TotalSegments")

    info(f"\nTable {table_name} tracked for cleanup (run with --cleanup)")
