"""
Demo: S3 Versioning Time Travel

Creates a versioned bucket, uploads the same key multiple times, then
demonstrates 'time travel' by retrieving each version.  Finishes with a
delete-marker round-trip: delete the object, show the marker, then recover
the latest version by removing the marker.
"""
import time
from botocore.exceptions import ClientError
from common import (
    create_session, banner, step, success, fail, info, warn, kv, table,
    generate_name, track_resource,
)


def run(args):
    banner("m05", "Versioning Time Travel")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = args.region or session.region_name

    bucket_name = generate_name("timetravel-bkt", args.prefix)
    object_key = "hello.txt"

    # ── Step 1: Create a versioned bucket ──
    step(1, "Creating a versioned S3 bucket")
    kv("Bucket", bucket_name)
    kv("Region", region)

    try:
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
    except Exception as exc:
        fail(f"Timed out waiting for bucket: {exc}")
        return

    # Enable versioning
    try:
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )
        success("Versioning enabled")
    except ClientError as exc:
        fail(f"Could not enable versioning: {exc}")
        return

    # ── Step 2: Upload three versions of the same object ──
    step(2, "Uploading three versions of the same object")

    versions_content = [
        "Version 1: Hello",
        "Version 2: Hello World",
        "Version 3: Hello World!!!",
    ]
    version_ids = []

    for i, body in enumerate(versions_content, 1):
        try:
            resp = s3.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=body.encode("utf-8"),
            )
            vid = resp["VersionId"]
            version_ids.append(vid)
            kv(f"  Upload {i}", f'"{body}"')
            kv(f"  VersionId", vid)
            info("")
            # Small pause so AWS registers distinct timestamps
            if i < len(versions_content):
                time.sleep(0.5)
        except ClientError as exc:
            fail(f"Upload {i} failed: {exc}")
            return

    success(f"Uploaded {len(version_ids)} versions of '{object_key}'")

    # ── Step 3: List all versions ──
    step(3, "Listing all versions of the object")

    try:
        resp = s3.list_object_versions(Bucket=bucket_name, Prefix=object_key)
        listed_versions = resp.get("Versions", [])

        rows = []
        for v in listed_versions:
            rows.append([
                v["VersionId"][:16] + "...",
                str(v["IsLatest"]),
                str(v["LastModified"].strftime("%H:%M:%S")),
                str(v["Size"]) + " B",
            ])

        table(
            ["VersionId", "IsLatest", "Modified", "Size"],
            rows,
            col_width=20,
        )
        success(f"Found {len(listed_versions)} version(s)")
    except ClientError as exc:
        fail(f"Could not list versions: {exc}")
        return

    # ── Step 4: Time travel -- retrieve each version ──
    step(4, "Time travel -- retrieving each version by VersionId")

    info("We can read ANY past version, even though the object was overwritten:\n")

    for i, vid in enumerate(version_ids, 1):
        try:
            resp = s3.get_object(
                Bucket=bucket_name,
                Key=object_key,
                VersionId=vid,
            )
            content = resp["Body"].read().decode("utf-8")
            kv(f"  Version {i} ({vid[:12]}...)", f'"{content}"')
        except ClientError as exc:
            fail(f"Could not retrieve version {vid}: {exc}")
            return

    info("")
    success("All historical versions are accessible")

    # ── Step 5: Delete the object (creates a delete marker) ──
    step(5, "Deleting the object (creates a delete marker)")

    try:
        del_resp = s3.delete_object(Bucket=bucket_name, Key=object_key)
        delete_marker_vid = del_resp.get("VersionId")
        kv("Delete marker VersionId", delete_marker_vid)
        success("Object deleted -- a delete marker was placed on top")
    except ClientError as exc:
        fail(f"Could not delete object: {exc}")
        return

    # ── Step 6: Demonstrate the object appears gone ──
    step(6, "Attempting to read the 'deleted' object")

    try:
        s3.get_object(Bucket=bucket_name, Key=object_key)
        warn("Object was unexpectedly accessible (no delete marker?)")
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            info("GET returned 'NoSuchKey' -- the object appears deleted to normal reads")
            success("Delete marker is hiding the object as expected")
        else:
            fail(f"Unexpected error: {exc}")
            return

    # ── Step 7: Show versions including the delete marker ──
    step(7, "Listing versions (including the delete marker)")

    try:
        resp = s3.list_object_versions(Bucket=bucket_name, Prefix=object_key)

        # Show delete markers
        markers = resp.get("DeleteMarkers", [])
        if markers:
            for m in markers:
                kv("  Delete Marker", m["VersionId"][:16] + "...")
                kv("    IsLatest", str(m["IsLatest"]))

        # Show remaining versions
        remaining = resp.get("Versions", [])
        info(f"\n  Object versions still stored: {len(remaining)}")
        info("  The data is NOT gone -- only hidden by the delete marker")
    except ClientError as exc:
        fail(f"Could not list versions: {exc}")
        return

    # ── Step 8: Recover by removing the delete marker ──
    step(8, "Recovering the object by removing the delete marker")

    try:
        s3.delete_object(
            Bucket=bucket_name,
            Key=object_key,
            VersionId=delete_marker_vid,
        )
        success(f"Delete marker '{delete_marker_vid[:12]}...' removed")
    except ClientError as exc:
        fail(f"Could not remove delete marker: {exc}")
        return

    # Read back the recovered object
    try:
        resp = s3.get_object(Bucket=bucket_name, Key=object_key)
        recovered = resp["Body"].read().decode("utf-8")
        kv("Recovered content", f'"{recovered}"')
        success("Object is back! The latest version is fully restored")
    except ClientError as exc:
        fail(f"Could not read recovered object: {exc}")
        return

    info("")
    info("Key takeaway: with versioning, 'delete' only adds a marker.")
    info("You can always travel back in time to recover any version.")

    # ── Track for cleanup ──
    track_resource("m05", "s3_bucket", bucket_name, region=region)
    success(f"Bucket '{bucket_name}' tracked for cleanup (run with --cleanup)")
