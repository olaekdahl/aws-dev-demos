import json
import time
from datetime import datetime, timezone
from common import (
    create_session, banner, step, success, info, warn, kv,
    generate_name, track_resource
)


def run(args):
    banner("m14", "CloudWatch Logs Insights")
    session = create_session(args.profile, args.region)
    logs = session.client("logs")

    log_group = f"/awsdev/{args.prefix}/demo-app"

    # Step 1: Create log group
    step(1, "Creating log group")
    try:
        logs.create_log_group(logGroupName=log_group)
        success(f"Created: {log_group}")
    except logs.exceptions.ResourceAlreadyExistsException:
        info(f"Already exists: {log_group}")
    track_resource("m14", "log_group", log_group)

    # Set retention
    logs.put_retention_policy(logGroupName=log_group, retentionInDays=1)

    # Step 2: Create log stream and write structured JSON logs
    step(2, "Writing structured JSON log entries")
    stream_name = f"demo-{int(time.time())}"
    logs.create_log_stream(logGroupName=log_group, logStreamName=stream_name)

    # Generate realistic application logs
    log_entries = [
        {"level": "INFO", "message": "Application started", "service": "api", "latency_ms": 0},
        {"level": "INFO", "message": "GET /users", "service": "api", "latency_ms": 45, "status": 200},
        {"level": "INFO", "message": "GET /users/1", "service": "api", "latency_ms": 23, "status": 200},
        {"level": "WARN", "message": "Slow query detected", "service": "db", "latency_ms": 850, "query": "SELECT * FROM orders"},
        {"level": "ERROR", "message": "Connection timeout", "service": "cache", "latency_ms": 5000, "error": "Redis timeout"},
        {"level": "INFO", "message": "POST /orders", "service": "api", "latency_ms": 120, "status": 201},
        {"level": "INFO", "message": "Order processed", "service": "worker", "latency_ms": 340, "order_id": "ORD-001"},
        {"level": "ERROR", "message": "Payment failed", "service": "payments", "latency_ms": 2100, "error": "Card declined"},
        {"level": "INFO", "message": "GET /health", "service": "api", "latency_ms": 5, "status": 200},
        {"level": "INFO", "message": "Cache miss", "service": "cache", "latency_ms": 150},
    ]

    now = int(time.time() * 1000)
    events = []
    for i, entry in enumerate(log_entries):
        events.append({
            "timestamp": now + (i * 100),
            "message": json.dumps(entry),
        })
        info(f"  [{entry['level']:5s}] {entry['service']:8s} | {entry['message']}")

    logs.put_log_events(logGroupName=log_group, logStreamName=stream_name, logEvents=events)
    success(f"Wrote {len(events)} log entries")

    # Step 3: Wait for logs to be queryable
    step(3, "Waiting for logs to be indexed (5 seconds)")
    time.sleep(5)

    # Step 4: Run Logs Insights queries
    queries = [
        ("Count by log level", "stats count(*) by level"),
        ("Errors only", 'filter level = "ERROR" | fields message, service, error'),
        ("Average latency by service", "stats avg(latency_ms) as avg_latency by service | sort avg_latency desc"),
        ("Slow requests (>100ms)", "filter latency_ms > 100 | fields message, service, latency_ms | sort latency_ms desc"),
    ]

    for idx, (description, query) in enumerate(queries, start=4):
        step(idx, f"Query: {description}")
        info(f"  {query}\n")

        start = logs.start_query(
            logGroupName=log_group,
            startTime=int((time.time() - 300) * 1000),
            endTime=int((time.time() + 60) * 1000),
            queryString=f"fields @timestamp, @message | parse @message '{{json_msg}}' | {query}",
        )
        query_id = start["queryId"]

        # Poll for results
        for _ in range(10):
            result = logs.get_query_results(queryId=query_id)
            if result["status"] == "Complete":
                break
            time.sleep(1)

        results = result.get("results", [])
        if results:
            for row in results[:5]:
                fields = {f["field"]: f["value"] for f in row if not f["field"].startswith("@")}
                if fields:
                    info(f"  {fields}")
            if len(results) > 5:
                info(f"  ... and {len(results) - 5} more rows")
            success(f"{len(results)} results")
        else:
            warn("No results (logs may need more time to index)")
