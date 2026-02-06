"""
Demo: Access Denied Detective - Permission Matrix Tester

Makes real AWS API calls across multiple services, catches AccessDenied
errors, and displays a visual matrix showing which actions are allowed
or denied for the current identity.
"""
from botocore.exceptions import ClientError, EndpointConnectionError
from common import (
    create_session, banner, step, success, fail, info, warn, kv, table,
)

# ANSI color codes for inline cell coloring
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"

# Each entry: (display_name, service, method, kwargs)
ACTIONS = [
    ("sts:GetCallerIdentity",   "sts",      "get_caller_identity",  {}),
    ("s3:ListAllMyBuckets",     "s3",       "list_buckets",         {}),
    ("iam:ListUsers",           "iam",      "list_users",           {}),
    ("ec2:DescribeInstances",   "ec2",      "describe_instances",   {}),
    ("dynamodb:ListTables",     "dynamodb", "list_tables",          {}),
    ("lambda:ListFunctions",    "lambda",   "list_functions",       {}),
    ("sqs:ListQueues",          "sqs",      "list_queues",          {}),
    ("sns:ListTopics",          "sns",      "list_topics",          {}),
]

# Error codes that indicate permission denial
DENIED_CODES = {
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedAccess",
    "AuthorizationError",
    "UnauthorizedOperation",
    "ForbiddenException",
}


def _test_action(session, service, method, kwargs):
    """Try a single API call and return (status, detail).

    Returns one of:
        ("ALLOWED", "")
        ("DENIED",  error_message)
        ("ERROR",   error_message)
    """
    try:
        client = session.client(service)
        getattr(client, method)(**kwargs)
        return "ALLOWED", ""
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        msg = exc.response["Error"]["Message"]
        if code in DENIED_CODES:
            return "DENIED", msg
        return "ERROR", f"{code}: {msg}"
    except EndpointConnectionError as exc:
        return "ERROR", f"Endpoint not available: {exc}"
    except Exception as exc:
        return "ERROR", str(exc)


def _colored_status(status):
    """Return a colored status string for terminal display."""
    if status == "ALLOWED":
        return f"{_GREEN}ALLOWED{_RESET}"
    elif status == "DENIED":
        return f"{_RED}DENIED{_RESET}"
    return f"{_YELLOW}{status}{_RESET}"


def run(args):
    banner("m04", "Access Denied Detective - Permission Matrix")

    session = create_session(args.profile, args.region)

    # ── Step 1: Identify ourselves ───────────────────────────────
    step(1, "Identifying current principal")
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        kv("Account", identity["Account"])
        kv("ARN", identity["Arn"])
        success("Identity confirmed")
    except ClientError:
        warn("Could not call sts:GetCallerIdentity -- credentials may be invalid")

    # ── Step 2: Test each action ─────────────────────────────────
    step(2, "Testing permissions across AWS services")
    info(f"Running {len(ACTIONS)} checks...\n")

    results = []
    allowed_count = 0
    denied_count = 0
    error_count = 0

    for display_name, service, method, kwargs in ACTIONS:
        status, detail = _test_action(session, service, method, kwargs)
        results.append((display_name, status, detail))

        if status == "ALLOWED":
            allowed_count += 1
        elif status == "DENIED":
            denied_count += 1
        else:
            error_count += 1

        # Live feedback per action
        colored = _colored_status(status)
        info(f"  {display_name:<30s} {colored}")

    # ── Step 3: Summary table ────────────────────────────────────
    step(3, "Permission matrix results")

    rows = []
    for display_name, status, detail in results:
        status_cell = _colored_status(status)
        rows.append([display_name, status_cell, detail[:40] if detail else ""])

    table(
        ["Action", "Status", "Detail"],
        rows,
        col_width=32,
    )

    # ── Step 4: Summary statistics ───────────────────────────────
    step(4, "Summary")
    kv("Total actions tested", len(ACTIONS))
    kv("Allowed", f"{_GREEN}{allowed_count}{_RESET}")
    kv("Denied", f"{_RED}{denied_count}{_RESET}")
    if error_count:
        kv("Errors", f"{_YELLOW}{error_count}{_RESET}")

    if denied_count == 0:
        success("All tested actions are allowed for this identity")
    elif allowed_count == 0:
        fail("All tested actions were denied -- check your IAM policies")
    else:
        info(f"{allowed_count} of {len(ACTIONS)} actions allowed, "
             f"{denied_count} denied")
        info("Use the Policy Simulator demo (policy-simulator) to test "
             "without making real calls")
