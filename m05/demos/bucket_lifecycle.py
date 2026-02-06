"""
Demo: S3 Bucket Lifecycle - Versioning, Lifecycle Policies & Visual Timeline

Creates a bucket, enables versioning, sets lifecycle rules (transition to
Glacier after 90 days, expire after 365 days), and displays the configuration
as an ASCII timeline.
"""
import time
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    generate_name, track_resource,
)


def run(args):
    banner("m05", "Bucket Lifecycle - Versioning & Lifecycle Policies")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = args.region or session.region_name

    bucket_name = generate_name("lifecycle-bkt", args.prefix)

    # ── Step 1: Create the bucket ──
    step(1, "Creating S3 bucket")
    kv("Bucket", bucket_name)
    kv("Region", region)

    try:
        # us-east-1 does not accept a LocationConstraint
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        success(f"Bucket '{bucket_name}' created")
    except ClientError as exc:
        fail(f"Could not create bucket: {exc}")
        return

    # Wait for the bucket to exist
    info("Waiting for bucket to be available...")
    waiter = s3.get_waiter("bucket_exists")
    try:
        waiter.wait(Bucket=bucket_name, WaiterConfig={"Delay": 2, "MaxAttempts": 15})
        success("Bucket is available")
    except Exception as exc:
        fail(f"Timed out waiting for bucket: {exc}")
        return

    # ── Step 2: Enable versioning ──
    step(2, "Enabling bucket versioning")

    try:
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )

        # Confirm versioning is enabled
        response = s3.get_bucket_versioning(Bucket=bucket_name)
        status = response.get("Status", "Not set")
        kv("Versioning status", status)

        if status == "Enabled":
            success("Versioning is enabled")
        else:
            warn(f"Versioning status is '{status}' -- expected 'Enabled'")
    except ClientError as exc:
        fail(f"Could not enable versioning: {exc}")
        return

    # ── Step 3: Set lifecycle configuration ──
    step(3, "Setting lifecycle rules")

    lifecycle_rules = [
        {
            "ID": "TransitionToGlacier",
            "Filter": {"Prefix": ""},
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER",
                },
            ],
        },
        {
            "ID": "ExpireAfterOneYear",
            "Filter": {"Prefix": ""},
            "Status": "Enabled",
            "Expiration": {
                "Days": 365,
            },
        },
    ]

    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={"Rules": lifecycle_rules},
        )
        success("Lifecycle configuration applied")
    except ClientError as exc:
        fail(f"Could not set lifecycle configuration: {exc}")
        return

    # ── Step 4: Display the lifecycle configuration ──
    step(4, "Displaying lifecycle configuration")

    try:
        response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        rules = response.get("Rules", [])

        for rule in rules:
            kv("Rule ID", rule["ID"])
            kv("  Status", rule["Status"])
            if "Transitions" in rule:
                for t in rule["Transitions"]:
                    kv("  Transition", f"Day {t['Days']} -> {t['StorageClass']}")
            if "Expiration" in rule:
                exp = rule["Expiration"]
                if "Days" in exp:
                    kv("  Expiration", f"Day {exp['Days']}")
            info("")

        success(f"Bucket has {len(rules)} lifecycle rule(s)")
    except ClientError as exc:
        fail(f"Could not read lifecycle configuration: {exc}")
        return

    # ── Step 5: Visual timeline ──
    step(5, "Lifecycle timeline")

    info("Object lifecycle from upload to expiration:\n")
    print("  Day 0          Day 90              Day 365")
    print("  |-- STANDARD --|-- GLACIER ---------|-- EXPIRED")
    print()
    info("  - Objects are created in STANDARD storage class")
    info("  - After 90 days, objects transition to GLACIER (cheaper, slower retrieval)")
    info("  - After 365 days, objects are permanently deleted")
    info("")

    # ── Track for cleanup ──
    track_resource("m05", "s3_bucket", bucket_name, region=region)
    success(f"Bucket '{bucket_name}' tracked for cleanup (run with --cleanup)")
