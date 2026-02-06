"""
Demo: IAM Policy Simulator - Test Permissions Without Real API Calls

Uses iam:SimulatePrincipalPolicy to evaluate whether the current
identity is allowed or denied for a set of actions, without actually
invoking those APIs.
"""
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn, kv, table,
)

# ANSI color codes for inline cell coloring
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"

# Actions to simulate -- same set as the detective demo for easy comparison
DEFAULT_ACTIONS = [
    "s3:ListAllMyBuckets",
    "s3:GetObject",
    "iam:ListUsers",
    "iam:CreateUser",
    "iam:DeleteUser",
    "sts:GetCallerIdentity",
    "ec2:DescribeInstances",
    "ec2:RunInstances",
    "ec2:TerminateInstances",
    "dynamodb:ListTables",
    "dynamodb:CreateTable",
    "lambda:ListFunctions",
    "lambda:CreateFunction",
    "sqs:ListQueues",
    "sns:ListTopics",
]


def _get_principal_arn(session):
    """Return the ARN of the current principal.

    For IAM users this returns the user ARN.  For assumed roles it
    returns the role ARN (not the assumed-role session ARN) so that
    SimulatePrincipalPolicy works correctly.
    """
    sts = session.client("sts")
    identity = sts.get_caller_identity()
    arn = identity["Arn"]

    # assumed-role ARNs look like:
    #   arn:aws:sts::123456789012:assumed-role/RoleName/SessionName
    # SimulatePrincipalPolicy needs the IAM role ARN instead:
    #   arn:aws:iam::123456789012:role/RoleName
    if ":assumed-role/" in arn:
        parts = arn.split(":")
        account = parts[4]
        role_name = parts[5].split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}", identity
    return arn, identity


def _colored_decision(decision):
    """Return a colored decision string."""
    if decision == "allowed":
        return f"{_GREEN}ALLOWED{_RESET}"
    elif decision == "implicitDeny":
        return f"{_RED}IMPLICIT DENY{_RESET}"
    elif decision == "explicitDeny":
        return f"{_RED}EXPLICIT DENY{_RESET}"
    return f"{_YELLOW}{decision}{_RESET}"


def run(args):
    banner("m04", "IAM Policy Simulator")

    session = create_session(args.profile, args.region)

    # ── Step 1: Identify the principal ───────────────────────────
    step(1, "Resolving current principal for simulation")

    try:
        principal_arn, identity = _get_principal_arn(session)
    except ClientError as exc:
        fail(f"Could not determine identity: {exc.response['Error']['Message']}")
        return

    kv("Account", identity["Account"])
    kv("Caller ARN", identity["Arn"])
    kv("Simulation ARN", principal_arn)
    success("Principal resolved")

    # ── Step 2: Run the simulation ───────────────────────────────
    step(2, f"Simulating {len(DEFAULT_ACTIONS)} actions via iam:SimulatePrincipalPolicy")

    iam = session.client("iam")

    try:
        paginator = iam.get_paginator("simulate_principal_policy")
        eval_results = []
        for page in paginator.paginate(
            PolicySourceArn=principal_arn,
            ActionNames=DEFAULT_ACTIONS,
        ):
            eval_results.extend(page.get("EvaluationResults", []))
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        msg = exc.response["Error"]["Message"]
        if code in ("AccessDenied", "AccessDeniedException"):
            fail("iam:SimulatePrincipalPolicy is not allowed for this identity")
            warn(f"Detail: {msg}")
            info("Your IAM policy must include iam:SimulatePrincipalPolicy permission")
            info("Try the Access Denied Detective demo (detective) for real-call testing")
            return
        raise

    success(f"Simulation completed for {len(eval_results)} actions")

    # ── Step 3: Display results ──────────────────────────────────
    step(3, "Simulation results")

    allowed_count = 0
    denied_count = 0
    rows = []

    for result in eval_results:
        action = result["EvalActionName"]
        decision = result["EvalDecision"]
        resource = result.get("EvalResourceName", "*")

        colored = _colored_decision(decision)
        rows.append([action, colored, resource])

        if decision == "allowed":
            allowed_count += 1
        else:
            denied_count += 1

    table(
        ["Action", "Decision", "Resource"],
        rows,
        col_width=28,
    )

    # ── Step 4: Summary ──────────────────────────────────────────
    step(4, "Summary")

    kv("Total actions simulated", len(eval_results))
    kv("Allowed", f"{_GREEN}{allowed_count}{_RESET}")
    kv("Denied", f"{_RED}{denied_count}{_RESET}")

    if denied_count == 0:
        success("All simulated actions are allowed for this principal")
    elif allowed_count == 0:
        fail("All simulated actions were denied")
    else:
        info(f"{allowed_count} of {len(eval_results)} actions allowed, "
             f"{denied_count} denied")

    info("\nNote: Simulation does not account for resource-level policies,")
    info("SCPs, permission boundaries, or session policies.  Use this as")
    info("a first-pass check; verify with real calls when in doubt.")
