"""
Demo: Who Am I? - Credential Chain Explorer

Shows which credential provider is active and displays your AWS identity
with details about the credential resolution chain.
"""
import os
import pathlib
from botocore.session import Session as BotocoreSession
from common import create_session, banner, step, success, info, kv, json_print


def run(args):
    banner("m03", "Who Am I? - Credential Chain Explorer")

    # ── Step 1: Inspect credential sources ──
    step(1, "Inspecting credential sources")

    env_vars = {
        "AWS_ACCESS_KEY_ID": "***" if os.environ.get("AWS_ACCESS_KEY_ID") else None,
        "AWS_SECRET_ACCESS_KEY": "***" if os.environ.get("AWS_SECRET_ACCESS_KEY") else None,
        "AWS_SESSION_TOKEN": "***" if os.environ.get("AWS_SESSION_TOKEN") else None,
        "AWS_PROFILE": os.environ.get("AWS_PROFILE"),
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION"),
    }

    info("Environment variables:")
    for var, val in env_vars.items():
        status = f"\033[32m{val}\033[0m" if val else "\033[2mnot set\033[0m"
        kv(f"  {var}", status)

    # Check config files
    config_paths = {
        "~/.aws/credentials": pathlib.Path.home() / ".aws" / "credentials",
        "~/.aws/config": pathlib.Path.home() / ".aws" / "config",
    }
    info("\nConfig files:")
    for label, path in config_paths.items():
        exists = path.exists()
        status = f"\033[32mfound\033[0m" if exists else "\033[2mnot found\033[0m"
        kv(f"  {label}", status)

    # Show available profiles
    bc = BotocoreSession()
    profiles = list(bc.full_config.get("profiles", {}).keys())
    if profiles:
        info(f"\nAvailable profiles: {', '.join(profiles)}")
    active_profile = args.profile or os.environ.get("AWS_PROFILE") or "(default chain)"
    kv("\n  Active profile", active_profile)

    # ── Step 2: Call STS to verify identity ──
    step(2, "Calling sts:GetCallerIdentity")

    session = create_session(args.profile, args.region)
    sts = session.client("sts")
    identity = sts.get_caller_identity()

    kv("Account", identity["Account"])
    kv("UserId", identity["UserId"])
    kv("ARN", identity["Arn"])
    kv("Region", session.region_name)

    # Parse the ARN to show identity type
    arn = identity["Arn"]
    if ":assumed-role/" in arn:
        info("\nYou are using temporary credentials from an assumed role.")
    elif ":user/" in arn:
        info("\nYou are using IAM user credentials.")
    elif ":root" in arn:
        info("\nYou are using root account credentials (not recommended).")

    success("Identity verified")
