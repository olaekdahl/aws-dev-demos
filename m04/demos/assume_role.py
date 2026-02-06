"""
Demo: Assume Role - Create, Assume, and Compare Identities

Creates a temporary IAM role, assumes it with STS, and shows the
before/after identity comparison.  Falls back to a user-supplied
--role-arn when IAM permissions are insufficient.
"""
import json
import time
import boto3
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn,
    kv, table, generate_name, track_resource,
)

MODULE = "m04"
READONLY_POLICY_ARN = "arn:aws:iam::aws:policy/ReadOnlyAccess"


def _current_identity(sts_client):
    """Return the caller identity dict."""
    resp = sts_client.get_caller_identity()
    return {
        "Account": resp["Account"],
        "UserId": resp["UserId"],
        "Arn": resp["Arn"],
    }


def _build_trust_policy(account_id):
    """Return a trust policy document allowing the account to assume this role."""
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                "Action": "sts:AssumeRole",
            }
        ],
    })


def _create_temp_role(iam, role_name, account_id):
    """Create a temporary role and attach ReadOnlyAccess."""
    trust_policy = _build_trust_policy(account_id)

    info(f"Creating temporary role: {role_name}")
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=trust_policy,
        Description="Temporary demo role created by aws-dev-demos m04",
        MaxSessionDuration=3600,
    )
    track_resource(MODULE, "iam-role", role_name)

    info(f"Attaching ReadOnlyAccess policy")
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn=READONLY_POLICY_ARN,
    )
    success(f"Role {role_name} created and policy attached")
    return role_name


def _cleanup_role(iam, role_name):
    """Detach policy and delete the temporary role."""
    info(f"Detaching ReadOnlyAccess from {role_name}")
    try:
        iam.detach_role_policy(
            RoleName=role_name,
            PolicyArn=READONLY_POLICY_ARN,
        )
    except ClientError as exc:
        warn(f"Could not detach policy: {exc}")

    info(f"Deleting role {role_name}")
    try:
        iam.delete_role(RoleName=role_name)
        success(f"Role {role_name} deleted")
    except ClientError as exc:
        warn(f"Could not delete role: {exc}")


def run(args):
    banner("m04", "Assume Role - Identity Before & After")

    session = create_session(args.profile, args.region)
    sts = session.client("sts")
    iam = session.client("iam")

    # ── Step 1: Show current identity ────────────────────────────
    step(1, "Current identity (before assuming role)")
    before = _current_identity(sts)
    kv("Account", before["Account"])
    kv("UserId", before["UserId"])
    kv("ARN", before["Arn"])

    # ── Step 2: Obtain a role ARN ────────────────────────────────
    step(2, "Obtaining a role to assume")

    role_arn = getattr(args, "role_arn", None)
    created_role_name = None

    if role_arn:
        info(f"Using user-supplied role ARN: {role_arn}")
    else:
        # Try to create a temporary role
        role_name = generate_name("demo-role", getattr(args, "prefix", None))
        try:
            _create_temp_role(iam, role_name, before["Account"])
            role_arn = f"arn:aws:iam::{before['Account']}:role/{role_name}"
            created_role_name = role_name

            # IAM is eventually consistent -- wait for the role to propagate
            info("Waiting for IAM role to propagate (10 seconds)...")
            time.sleep(10)
            success("Role should be assumable now")

        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("AccessDenied", "UnauthorizedAccess"):
                warn("No permission to create IAM roles.")
                warn("Re-run with --role-arn <ARN> to supply an existing role.")
                fail("Cannot proceed without a role to assume")
                return
            raise

    # ── Step 3: Assume the role ──────────────────────────────────
    step(3, "Assuming the role via sts:AssumeRole")
    kv("Role ARN", role_arn)

    try:
        assume_resp = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="awsdev-demo-session",
            DurationSeconds=900,
        )
    except ClientError as exc:
        fail(f"AssumeRole failed: {exc.response['Error']['Message']}")
        if created_role_name:
            step(5, "Cleanup")
            _cleanup_role(iam, created_role_name)
        return

    creds = assume_resp["Credentials"]
    success("Role assumed successfully")
    kv("AccessKeyId", creds["AccessKeyId"][:8] + "..." )
    kv("Expiration", creds["Expiration"])

    # ── Step 4: Show assumed identity (after) ────────────────────
    step(4, "New identity (after assuming role)")

    assumed_session = boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=session.region_name,
    )
    assumed_sts = assumed_session.client("sts")
    after = _current_identity(assumed_sts)

    kv("Account", after["Account"])
    kv("UserId", after["UserId"])
    kv("ARN", after["Arn"])

    # ── Comparison table ─────────────────────────────────────────
    step(5, "Before / After comparison")
    table(
        ["Field", "Before", "After"],
        [
            ["Account", before["Account"], after["Account"]],
            ["UserId", before["UserId"], after["UserId"]],
            ["ARN", before["Arn"], after["Arn"]],
        ],
        col_width=28,
    )

    same_account = before["Account"] == after["Account"]
    info(f"Same account: {'yes' if same_account else 'no'}")
    info(f"Identity changed: {'yes' if before['Arn'] != after['Arn'] else 'no'}")
    success("Assume role demo complete")

    # ── Step 6: Cleanup ──────────────────────────────────────────
    if created_role_name:
        step(6, "Cleaning up temporary role")
        _cleanup_role(iam, created_role_name)
