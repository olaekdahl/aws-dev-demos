"""
Demo: REST API Validation Test

Auto-discovers the deployed SAM REST API stack and sends various test
requests to exercise the /health and /validate endpoints.
"""
import json
import urllib.request
import urllib.error
from common import create_session, banner, step, success, fail, info, warn, kv, table


def _find_api_url(session):
    """Scan CloudFormation stacks for the REST API's ApiUrl output."""
    cfn = session.client("cloudformation")
    paginator = cfn.get_paginator("list_stacks")
    for page in paginator.paginate(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"]):
        for summary in page.get("StackSummaries", []):
            name = summary["StackName"]
            if "rest" not in name.lower() and "api" not in name.lower():
                continue
            desc = cfn.describe_stacks(StackName=name)
            for stack in desc.get("Stacks", []):
                for out in stack.get("Outputs", []):
                    if out["OutputKey"] == "ApiUrl":
                        return out["OutputValue"], name
    return None, None


def _http(url, method="GET", body=None, raw_body=None):
    """Minimal HTTP helper using stdlib only (no requests dependency)."""
    headers = {"content-type": "application/json"}
    data = None
    if raw_body is not None:
        data = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    elif body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    except Exception as exc:
        return 0, {"error": str(exc)}


def run(args):
    banner("m10", "REST API Validation Test")

    # ── Step 1: Discover the API URL ──
    step(1, "Discovering API URL from CloudFormation stack")
    session = create_session(args.profile, args.region)
    api_url, stack_name = _find_api_url(session)

    if not api_url:
        warn("No deployed REST API stack found.")
        info("Deploy the SAM app first:")
        info("  cd m10/sam-rest-api && sam build && sam deploy --guided")
        return

    kv("Stack", stack_name)
    kv("API URL", api_url)
    success("Stack discovered")

    results = []

    # ── Step 2: GET /health ──
    step(2, "Testing GET /health")
    status, body = _http(f"{api_url}/health")
    kv("Status", status)
    kv("Body", json.dumps(body, indent=2))
    passed = status == 200 and body.get("status") == "healthy"
    (success if passed else fail)("Health check")
    results.append(["GET /health", status, "PASS" if passed else "FAIL"])

    # ── Step 3: POST /validate with valid data ──
    step(3, "Testing POST /validate with valid data")
    payload = {"name": "Ada", "email": "ada@example.com", "age": 30}
    status, body = _http(f"{api_url}/validate", method="POST", body=payload)
    kv("Status", status)
    kv("Body", json.dumps(body, indent=2))
    passed = status == 200 and body.get("valid") is True
    (success if passed else fail)("Valid payload accepted")
    results.append(["POST valid", status, "PASS" if passed else "FAIL"])

    # ── Step 4: POST /validate with missing fields ──
    step(4, "Testing POST /validate with missing fields")
    payload = {"name": "Ada"}
    status, body = _http(f"{api_url}/validate", method="POST", body=payload)
    kv("Status", status)
    kv("Body", json.dumps(body, indent=2))
    passed = status == 422 and "validation_errors" in body
    (success if passed else fail)("Missing fields rejected with 422")
    results.append(["POST missing fields", status, "PASS" if passed else "FAIL"])

    # ── Step 5: POST /validate with invalid data ──
    step(5, "Testing POST /validate with invalid data")
    payload = {"name": "Ada", "email": "not-an-email", "age": -5}
    status, body = _http(f"{api_url}/validate", method="POST", body=payload)
    kv("Status", status)
    kv("Body", json.dumps(body, indent=2))
    passed = status == 422 and "validation_errors" in body
    (success if passed else fail)("Invalid data rejected with 422")
    results.append(["POST invalid data", status, "PASS" if passed else "FAIL"])

    # ── Step 6: POST /validate with invalid JSON ──
    step(6, "Testing POST /validate with invalid JSON")
    status, body = _http(f"{api_url}/validate", method="POST", raw_body="not json")
    kv("Status", status)
    kv("Body", json.dumps(body, indent=2))
    passed = status == 400 and "Invalid JSON" in body.get("error", "")
    (success if passed else fail)("Bad JSON rejected with 400")
    results.append(["POST bad JSON", status, "PASS" if passed else "FAIL"])

    # ── Summary table ──
    info("")
    table(["Test Case", "HTTP Status", "Result"], results, col_width=22)

    total = len(results)
    passed_count = sum(1 for r in results if r[2] == "PASS")
    if passed_count == total:
        success(f"All {total} tests passed")
    else:
        warn(f"{passed_count}/{total} tests passed")
