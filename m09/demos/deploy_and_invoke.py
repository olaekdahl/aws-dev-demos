"""
Demo: Deploy and Invoke - Word Frequency Analyzer

Creates an IAM execution role, packages the handler from src/ into a ZIP,
deploys the Lambda function, invokes it with sample text, and displays
the word-frequency results.
"""
import io
import json
import pathlib
import time
import zipfile

from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn,
    kv, json_print, table, generate_name, track_resource,
    get_tracked_resources,
)

MODULE = "m09"
LAMBDA_BASIC_ROLE_ARN = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"


def _build_trust_policy():
    """Return a trust policy allowing Lambda to assume the role."""
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
    """Reuse an existing tracked role or create a new one.

    Returns the role ARN.
    """
    # Check if we already have a tracked IAM role from a previous run
    for r in get_tracked_resources(MODULE):
        if r["type"] == "iam_role":
            try:
                resp = iam.get_role(RoleName=r["id"])
                info(f"Reusing tracked IAM role: {r['id']}")
                return resp["Role"]["Arn"], r["id"], False
            except ClientError:
                pass  # role was deleted externally, create a new one

    role_name = generate_name("lambda-role", prefix)
    info(f"Creating IAM role: {role_name}")

    resp = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=_build_trust_policy(),
        Description="Lambda execution role created by aws-dev-demos m09",
    )
    role_arn = resp["Role"]["Arn"]

    iam.attach_role_policy(RoleName=role_name, PolicyArn=LAMBDA_BASIC_ROLE_ARN)
    success(f"Role '{role_name}' created and AWSLambdaBasicExecutionRole attached")
    track_resource(MODULE, "iam_role", role_name)

    return role_arn, role_name, True


def _build_zip():
    """Package the contents of src/ into an in-memory ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for py_file in SRC_DIR.glob("*.py"):
            zf.write(py_file, py_file.name)
    buf.seek(0)
    return buf.read()


def _wait_for_function(lam, function_name, max_wait=30):
    """Poll until the function state is Active."""
    for _ in range(max_wait):
        resp = lam.get_function_configuration(FunctionName=function_name)
        state = resp.get("State", "Unknown")
        if state == "Active":
            return True
        time.sleep(1)
    return False


def run(args):
    banner("m09", "Deploy & Invoke - Word Frequency Analyzer")

    session = create_session(args.profile, args.region)
    iam = session.client("iam")
    lam = session.client("lambda")

    # ── Step 1: IAM role ─────────────────────────────────────────
    step(1, "Preparing IAM execution role for Lambda")
    try:
        role_arn, role_name, newly_created = _find_or_create_role(iam, args.prefix)
        kv("Role ARN", role_arn)
    except ClientError as exc:
        fail(f"Could not create IAM role: {exc}")
        return

    if newly_created:
        info("Waiting 10 s for IAM role to propagate...")
        time.sleep(10)
        success("Role propagation wait complete")

    # ── Step 2: Build deployment ZIP ─────────────────────────────
    step(2, "Packaging handler from src/ into ZIP")
    zip_bytes = _build_zip()
    kv("Package size", f"{len(zip_bytes):,} bytes")
    success("ZIP package built")

    # ── Step 3: Create or update Lambda function ─────────────────
    function_name = generate_name("word-freq", args.prefix)
    step(3, f"Creating Lambda function: {function_name}")

    try:
        lam.create_function(
            FunctionName=function_name,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=15,
            MemorySize=128,
            Environment={"Variables": {"DEMO": "word-frequency"}},
        )
        success(f"Function '{function_name}' created")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceConflictException":
            info("Function already exists -- updating code")
            lam.update_function_code(
                FunctionName=function_name, ZipFile=zip_bytes,
            )
            success("Function code updated")
        else:
            fail(f"Could not create function: {exc}")
            return

    track_resource(MODULE, "lambda_function", function_name)

    # ── Step 4: Wait for function to be Active ───────────────────
    step(4, "Waiting for function to become Active")
    if _wait_for_function(lam, function_name):
        success("Function is Active")
    else:
        warn("Function did not reach Active state within timeout")

    # ── Step 5: Invoke with sample text ──────────────────────────
    step(5, "Invoking function with sample text")
    payload = {
        "text": (
            "to be or not to be that is the question "
            "whether tis nobler in the mind to suffer"
        ),
    }
    kv("Input text", payload["text"])

    try:
        resp = lam.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload),
        )
        status_code = resp["StatusCode"]
        kv("StatusCode", status_code)

        result = json.loads(resp["Payload"].read())
        body = json.loads(result.get("body", "{}"))
    except ClientError as exc:
        fail(f"Invocation failed: {exc}")
        return

    # ── Step 6: Display results ──────────────────────────────────
    step(6, "Word frequency results")
    kv("Total words", body.get("total_words"))
    kv("Unique words", body.get("unique_words"))
    kv("Timestamp", body.get("timestamp"))

    rows = [
        [entry["word"], str(entry["count"])]
        for entry in body.get("top_10", [])
    ]
    table(["Word", "Count"], rows, col_width=16)
    success("Deploy & invoke demo complete")
