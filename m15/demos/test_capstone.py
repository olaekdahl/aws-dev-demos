import json
import time
import requests
from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    json_print, table as print_table
)


def run(args):
    banner("m15", "Capstone - End-to-End Test")
    session = create_session(args.profile, args.region)
    cfn = session.client("cloudformation")

    # Step 1: Discover stack
    step(1, "Discovering deployed stack")
    stack_outputs = {}
    paginator = cfn.get_paginator("list_stacks")
    for page in paginator.paginate(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"]):
        for stack in page["StackSummaries"]:
            if "m15" in stack["StackName"].lower() or "capstone" in stack["StackName"].lower():
                outputs = cfn.describe_stacks(StackName=stack["StackName"])["Stacks"][0].get("Outputs", [])
                stack_outputs = {o["OutputKey"]: o["OutputValue"] for o in outputs}
                break
        if stack_outputs:
            break

    if not stack_outputs:
        info("No deployed stack found. Deploy first:")
        info("  cd m15 && sam build && sam deploy --guided")
        return

    for k, v in stack_outputs.items():
        kv(k, v)
    success("Stack found")

    bucket = stack_outputs.get("BucketName")
    api_url = stack_outputs.get("ApiUrl")
    dlq_url = stack_outputs.get("DLQUrl")

    if not all([bucket, api_url]):
        fail("Missing required stack outputs")
        return

    s3 = session.client("s3")
    sqs = session.client("sqs")

    # Step 2: Upload test files
    step(2, "Uploading test files to S3")
    test_files = {
        "report-2024-q1.txt": "Q1 Revenue: $1.2M, Growth: 15%",
        "report-2024-q2.txt": "Q2 Revenue: $1.5M, Growth: 25%",
        "data/metrics.json": json.dumps({"requests": 50000, "errors": 12}),
    }

    for key, content in test_files.items():
        s3.put_object(Bucket=bucket, Key=key, Body=content.encode())
        info(f"  Uploaded: {key} ({len(content)} bytes)")
    success(f"Uploaded {len(test_files)} files")

    # Step 3: Wait for processing
    step(3, "Waiting for Lambda to process events (15s)")
    for i in range(15):
        time.sleep(1)
        print(f"\r  {'.' * (i + 1)}", end="", flush=True)
    print()

    # Step 4: Verify via API
    step(4, "Checking processed items via API")

    # List all items
    resp = requests.get(f"{api_url}/items", timeout=30)
    kv("GET /items status", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        kv("Items processed", data.get("count", 0))
        for item in data.get("items", []):
            info(f"  {item.get('id', '?'):30s} status={item.get('status', '?')}")

    # Get specific item
    resp = requests.get(f"{api_url}/items/report-2024-q1.txt", timeout=30)
    if resp.status_code == 200:
        success(f"Item lookup works: {resp.json().get('id')}")

    # Test 404
    resp = requests.get(f"{api_url}/items/nonexistent", timeout=30)
    kv("GET /items/nonexistent", f"{resp.status_code} (expected 404)")

    # Step 5: Check DLQ
    step(5, "Checking Dead Letter Queue")
    if dlq_url:
        attrs = sqs.get_queue_attributes(
            QueueUrl=dlq_url,
            AttributeNames=["ApproximateNumberOfMessagesVisible"]
        )
        dlq_count = int(attrs["Attributes"].get("ApproximateNumberOfMessagesVisible", "0"))
        if dlq_count == 0:
            success("DLQ is empty - all messages processed successfully")
        else:
            warn(f"DLQ has {dlq_count} message(s) - some processing failed")

    # Step 6: Summary
    step(6, "Architecture summary")
    info("")
    info("  S3 Bucket  -->  SQS Queue  -->  Lambda Worker  -->  DynamoDB")
    info("                     |")
    info("                     +--> DLQ (after 3 failures)")
    info("                          |")
    info("                          +--> CloudWatch Alarm")
    info("")
    info("  API Gateway  -->  Lambda API  -->  DynamoDB (read)")
    info("")
    success("Capstone end-to-end test complete")
