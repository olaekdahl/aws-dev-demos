"""
Demo: Cold Start Measurement

Deploys the word-frequency Lambda and invokes it multiple times in
sequence to measure cold-start vs. warm invocation performance.  Parses
the REPORT line from CloudWatch log tail to extract Init Duration
(cold start), Duration, and Billed Duration.
"""
import base64
import io
import json
import pathlib
import re
import time
import zipfile

from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn,
    kv, table, generate_name, track_resource, get_tracked_resources,
)

MODULE = "m09"
LAMBDA_BASIC_ROLE_ARN = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
NUM_INVOCATIONS = 10


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


def _build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for py_file in SRC_DIR.glob("*.py"):
            zf.write(py_file, py_file.name)
    buf.seek(0)
    return buf.read()


def _wait_for_function(lam, function_name, max_wait=30):
    for _ in range(max_wait):
        resp = lam.get_function_configuration(FunctionName=function_name)
        if resp.get("State") == "Active":
            return True
        time.sleep(1)
    return False


def _parse_report_line(log_bytes):
    """Parse the REPORT line from Lambda log tail.

    Returns dict with keys: duration_ms, billed_ms, init_ms (or None).
    """
    text = log_bytes.decode("utf-8", errors="replace")

    result = {"duration_ms": None, "billed_ms": None, "init_ms": None}

    # Find the REPORT line
    for line in text.splitlines():
        if "REPORT" not in line:
            continue

        m = re.search(r"Duration:\s*([\d.]+)\s*ms", line)
        if m:
            result["duration_ms"] = float(m.group(1))

        m = re.search(r"Billed Duration:\s*([\d.]+)\s*ms", line)
        if m:
            result["billed_ms"] = float(m.group(1))

        m = re.search(r"Init Duration:\s*([\d.]+)\s*ms", line)
        if m:
            result["init_ms"] = float(m.group(1))

        break

    return result


def run(args):
    banner("m09", "Cold Start Measurement")

    session = create_session(args.profile, args.region)
    iam = session.client("iam")
    lam = session.client("lambda")

    # ── Step 1: Deploy function ──────────────────────────────────
    step(1, "Deploying Lambda function for cold-start test")

    try:
        role_arn, role_name, newly_created = _find_or_create_role(iam, args.prefix)
        kv("Role ARN", role_arn)
    except ClientError as exc:
        fail(f"Could not prepare IAM role: {exc}")
        return

    if newly_created:
        info("Waiting 10 s for IAM role to propagate...")
        time.sleep(10)

    zip_bytes = _build_zip()
    function_name = generate_name("cold-start", args.prefix)
    kv("Function", function_name)

    try:
        lam.create_function(
            FunctionName=function_name,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=15,
            MemorySize=128,
            Environment={"Variables": {"DEMO": "cold-start"}},
        )
        success(f"Function '{function_name}' created")
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

    success("Function is Active and ready for invocations")

    # ── Step 2: Invoke N times and collect metrics ───────────────
    step(2, f"Invoking function {NUM_INVOCATIONS} times in sequence")

    payload = json.dumps({
        "text": "the quick brown fox jumps over the lazy dog",
    })

    results = []
    for i in range(1, NUM_INVOCATIONS + 1):
        info(f"  Invocation {i}/{NUM_INVOCATIONS}...")
        try:
            resp = lam.invoke(
                FunctionName=function_name,
                Payload=payload,
                LogType="Tail",
            )
            log_bytes = base64.b64decode(resp.get("LogResult", ""))
            report = _parse_report_line(log_bytes)
            is_cold = report["init_ms"] is not None
            results.append({
                "invocation": i,
                "cold": is_cold,
                "init_ms": report["init_ms"],
                "duration_ms": report["duration_ms"],
                "billed_ms": report["billed_ms"],
            })
        except ClientError as exc:
            warn(f"  Invocation {i} failed: {exc}")
            results.append({
                "invocation": i,
                "cold": None,
                "init_ms": None,
                "duration_ms": None,
                "billed_ms": None,
            })

    # ── Step 3: Display results table ────────────────────────────
    step(3, "Invocation results")

    headers = ["#", "Cold/Warm", "Init Duration", "Duration", "Billed"]
    rows = []
    for r in results:
        label = "COLD" if r["cold"] else ("WARM" if r["cold"] is not None else "N/A")
        init = f"{r['init_ms']:.1f} ms" if r["init_ms"] is not None else "-"
        dur = f"{r['duration_ms']:.1f} ms" if r["duration_ms"] is not None else "-"
        billed = f"{r['billed_ms']:.0f} ms" if r["billed_ms"] is not None else "-"
        rows.append([str(r["invocation"]), label, init, dur, billed])

    table(headers, rows, col_width=16)

    # ── Step 4: Summary statistics ───────────────────────────────
    step(4, "Summary statistics")

    cold_runs = [r for r in results if r["cold"] is True]
    warm_runs = [r for r in results if r["cold"] is False]

    kv("Total invocations", len(results))
    kv("Cold starts", len(cold_runs))
    kv("Warm invocations", len(warm_runs))

    if cold_runs:
        cold_durations = [r["duration_ms"] for r in cold_runs if r["duration_ms"]]
        cold_inits = [r["init_ms"] for r in cold_runs if r["init_ms"]]
        if cold_inits:
            kv("Avg cold init duration", f"{sum(cold_inits) / len(cold_inits):.1f} ms")
        if cold_durations:
            kv("Avg cold exec duration", f"{sum(cold_durations) / len(cold_durations):.1f} ms")

    if warm_runs:
        warm_durations = [r["duration_ms"] for r in warm_runs if r["duration_ms"]]
        if warm_durations:
            avg = sum(warm_durations) / len(warm_durations)
            kv("Avg warm exec duration", f"{avg:.1f} ms")
            mn = min(warm_durations)
            mx = max(warm_durations)
            kv("Warm range", f"{mn:.1f} ms - {mx:.1f} ms")

    if cold_runs and warm_runs:
        cold_avg = sum(r["duration_ms"] for r in cold_runs if r["duration_ms"]) / max(len(cold_runs), 1)
        warm_avg = sum(r["duration_ms"] for r in warm_runs if r["duration_ms"]) / max(len(warm_runs), 1)
        if warm_avg > 0:
            info(f"Cold start is ~{cold_avg / warm_avg:.1f}x slower than warm")

    success("Cold start measurement complete")
