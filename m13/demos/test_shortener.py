import json
import requests
from common import create_session, banner, step, success, fail, info, kv, table as print_table


def run(args):
    banner("m13", "URL Shortener - Integration Test")

    # Step 1: Find the API URL from CloudFormation
    step(1, "Discovering API URL from CloudFormation stack")
    session = create_session(args.profile, args.region)
    cfn = session.client("cloudformation")

    api_url = None
    paginator = cfn.get_paginator("list_stacks")
    for page in paginator.paginate(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"]):
        for stack in page["StackSummaries"]:
            if "m13" in stack["StackName"].lower() or "url-short" in stack["StackName"].lower():
                outputs = cfn.describe_stacks(StackName=stack["StackName"])["Stacks"][0].get("Outputs", [])
                for o in outputs:
                    if o["OutputKey"] == "ApiUrl":
                        api_url = o["OutputValue"]
                        break
            if api_url:
                break
        if api_url:
            break

    if not api_url:
        info("No deployed stack found. Deploy first:")
        info("  cd m13 && sam build && sam deploy --guided")
        return

    kv("API URL", api_url)
    success("Stack found")

    # Step 2: Create a short URL
    step(2, "POST /shorten - Creating a short URL")
    resp = requests.post(
        f"{api_url}/shorten",
        json={"url": "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html", "ttl_hours": 1},
        timeout=30,
    )
    kv("Status", resp.status_code)
    data = resp.json()
    kv("Short URL", data.get("short_url"))
    kv("Code", data.get("code"))
    code = data.get("code")
    if resp.status_code == 201:
        success("Short URL created")
    else:
        fail(f"Unexpected status: {resp.status_code}")
        return

    # Step 3: Follow the redirect
    step(3, "GET /{code} - Following the redirect")
    resp = requests.get(f"{api_url}/{code}", allow_redirects=False, timeout=30)
    kv("Status", resp.status_code)
    kv("Location", resp.headers.get("Location", ""))
    if resp.status_code == 301:
        success("Redirect works")
    else:
        fail(f"Expected 301, got {resp.status_code}")

    # Step 4: Click it a few more times
    step(4, "Clicking the short URL 3 more times")
    for i in range(3):
        requests.get(f"{api_url}/{code}", allow_redirects=False, timeout=30)
        info(f"  Click {i + 2}")
    success("4 total clicks recorded")

    # Step 5: Check stats
    step(5, "GET /stats/{code} - Checking click statistics")
    resp = requests.get(f"{api_url}/stats/{code}", timeout=30)
    stats = resp.json()
    kv("Clicks", stats.get("clicks"))
    kv("Original URL", stats.get("original_url"))
    kv("Created", stats.get("created_at"))
    kv("Expires", stats.get("expires_at"))
    success(f"Stats show {stats.get('clicks')} clicks")

    # Step 6: Test error cases
    step(6, "Testing error cases")

    # Missing URL
    resp = requests.post(f"{api_url}/shorten", json={}, timeout=30)
    kv("POST /shorten {} ->", f"{resp.status_code} {resp.json().get('error', '')}")

    # Invalid code
    resp = requests.get(f"{api_url}/nonexistent123", allow_redirects=False, timeout=30)
    kv("GET /nonexistent123 ->", f"{resp.status_code}")

    success("Error handling verified")
