"""
Demo: Lambda Error Handling Patterns

Deploys a purpose-built Lambda that responds to different "action"
payloads to demonstrate how Lambda surfaces successes, exceptions,
timeouts, and large payloads.  Each scenario is invoked and the raw
response metadata is displayed for comparison.
"""
import io
import json
import textwrap
import time
import zipfile

from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn,
    kv, table, generate_name, track_resource, get_tracked_resources,
)

MODULE = "m09"
LAMBDA_BASIC_ROLE_ARN = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# Inline handler that exercises different error paths
ERROR_HANDLER_CODE = textwrap.dedent("""\
    import json
    import time

    def handler(event, context):
        action = event.get("action", "succeed")

        if action == "succeed":
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Success!", "action": action}),
            }

        elif action == "timeout":
            # Function timeout is set to 5 s -- sleep longer to trigger it
            time.sleep(30)
            return {"statusCode": 200, "body": "should not reach here"}

        elif action == "exception":
            raise ValueError("Intentional demo exception from Lambda handler")

        elif action == "oom":
            # Allocate more memory than function limit (128 MB) to trigger OOM
            chunks = []
            while True:
                chunks.append("x" * (10 * 1024 * 1024))  # 10 MB per chunk

        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Unknown action: {action}"}),
            }
""")


def _build_trust_policy():
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            },
        ],
    })


def _find_or_create_role(iam, prefix):
    """Reuse a tracked role or create a new one. Returns (arn, name, newly_created)."""
    for r in get_tracked_resources(MODULE):
        if r["type"] == "iam_role":
            try:
                resp = iam.get_role(RoleName=r["id"])
                info(f"Reusing tracked IAM role: {r['id']}")
                return resp["Role"]["Arn"], r["id"], False
            except ClientError:
                pass

    role_name = generate_name("lambda-role", prefix)
    info(f"Creating IAM role: {role_name}")
    resp = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=_build_trust_policy(),
        Description="Lambda execution role created by aws-dev-demos m09",
    )
    role_arn = resp["Role"]["Arn"]
    iam.attach_role_policy(RoleName=role_name, PolicyArn=LAMBDA_BASIC_ROLE_ARN)
    success(f"Role '{role_name}' created")
    track_resource(MODULE, "iam_role", role_name)
    return role_arn, role_name, True


def _build_inline_zip(code_str):
    """Create an in-memory ZIP from an inline handler string."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("handler.py", code_str)
    buf.seek(0)
    return buf.read()


def _wait_for_function(lam, function_name, max_wait=30):
    for _ in range(max_wait):
        resp = lam.get_function_configuration(FunctionName=function_name)
        if resp.get("State") == "Active":
            return True
        time.sleep(1)
    return False


def run(args):
    banner("m09", "Lambda Error Handling Patterns")

    session = create_session(args.profile, args.region)
    iam = session.client("iam")
    lam = session.client("lambda")

    # ── Step 1: Deploy the error-scenario function ───────────────
    step(1, "Deploying error-scenario Lambda")

    try:
        role_arn, role_name, newly_created = _find_or_create_role(iam, args.prefix)
        kv("Role ARN", role_arn)
    except ClientError as exc:
        fail(f"Could not prepare IAM role: {exc}")
        return

    if newly_created:
        info("Waiting 10 s for IAM role to propagate...")
        time.sleep(10)

    zip_bytes = _build_inline_zip(ERROR_HANDLER_CODE)
    function_name = generate_name("err-demo", args.prefix)
    kv("Function", function_name)

    try:
        lam.create_function(
            FunctionName=function_name,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=5,
            MemorySize=128,
            Environment={"Variables": {"DEMO": "error-handling"}},
        )
        success(f"Function '{function_name}' created (timeout=5s)")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceConflictException":
            info("Function already exists -- updating code")
            lam.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
        else:
            fail(f"Could not create function: {exc}")
            return

    track_resource(MODULE, "lambda_function", function_name)

    if not _wait_for_function(lam, function_name):
        warn("Function did not reach Active state within timeout")

    success("Function is Active")

    # ── Step 2: Invoke each scenario ─────────────────────────────
    scenarios = [
        ("succeed", "Normal success response"),
        ("timeout", "Exceeds 5 s timeout"),
        ("exception", "Raises ValueError"),
        ("oom", "Exceeds 128 MB memory limit"),
    ]

    scenario_results = []

    for idx, (action, description) in enumerate(scenarios, start=2):
        step(idx, f"Scenario: {action} -- {description}")
        payload = json.dumps({"action": action})

        try:
            resp = lam.invoke(
                FunctionName=function_name,
                Payload=payload,
            )
            status_code = resp["StatusCode"]
            function_error = resp.get("FunctionError", "")
            resp_payload = json.loads(resp["Payload"].read())

            kv("StatusCode", status_code)
            if function_error:
                kv("FunctionError", function_error)

            # Display the response payload (truncate if very large)
            payload_str = json.dumps(resp_payload, indent=2, default=str)
            if len(payload_str) > 500:
                kv("Response (truncated)", payload_str[:500] + "...")
            else:
                kv("Response", payload_str)

            scenario_results.append({
                "action": action,
                "status_code": status_code,
                "function_error": function_error or "-",
                "outcome": "Error" if function_error else "Success",
            })

        except ClientError as exc:
            warn(f"API error for '{action}': {exc}")
            scenario_results.append({
                "action": action,
                "status_code": "N/A",
                "function_error": str(exc)[:40],
                "outcome": "API Error",
            })

    # ── Comparison table ─────────────────────────────────────────
    step(idx + 1, "Error handling comparison")

    headers = ["Action", "StatusCode", "FunctionError", "Outcome"]
    rows = [
        [r["action"], str(r["status_code"]), r["function_error"], r["outcome"]]
        for r in scenario_results
    ]
    table(headers, rows, col_width=18)

    info("Key takeaways:")
    info("  - Successful invocations return StatusCode 200 with no FunctionError")
    info("  - Timeouts return StatusCode 200 but FunctionError='Unhandled'")
    info("  - Unhandled exceptions return StatusCode 200 with FunctionError='Unhandled'")
    info("  - Lambda always returns HTTP 200; check FunctionError for actual errors")

    success("Error handling demo complete")
