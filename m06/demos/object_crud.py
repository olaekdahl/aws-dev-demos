"""
Demo: S3 Object CRUD - Complete Object Lifecycle

Walks through the full lifecycle of S3 objects: upload, inspect metadata,
retrieve content, list, and delete -- all in a single orchestrated flow.
"""
import json
from datetime import datetime, timezone

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    json_print, table, generate_name, track_resource,
)

MODULE = "m06"


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


def run(args):
    banner("m06", "S3 Object CRUD - Complete Object Lifecycle")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = session.region_name

    bucket_name = generate_name("crud", getattr(args, "prefix", None))

    # ── Create bucket ──
    info(f"Creating bucket: {bucket_name}")
    try:
        _create_bucket(s3, bucket_name, region)
        success(f"Bucket created: {bucket_name}")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 1: put_object - upload text content ──
    step(1, "put_object - Upload text content")

    key1 = "greeting.txt"
    body1 = "Hello from the S3 Object CRUD demo!"
    s3.put_object(Bucket=bucket_name, Key=key1, Body=body1, ContentType="text/plain")
    kv("Key", key1)
    kv("Content-Type", "text/plain")
    kv("Body length", f"{len(body1)} bytes")
    success(f"Uploaded {key1}")

    # ── Step 2: head_object - show metadata ──
    step(2, "head_object - Inspect object metadata")

    head = s3.head_object(Bucket=bucket_name, Key=key1)
    kv("Content-Type", head["ContentType"])
    kv("Content-Length", head["ContentLength"])
    kv("ETag", head["ETag"])
    kv("Last-Modified", head["LastModified"])
    if head.get("ServerSideEncryption"):
        kv("Encryption", head["ServerSideEncryption"])
    success("Metadata retrieved (no data transferred)")

    # ── Step 3: get_object - retrieve and show content ──
    step(3, "get_object - Retrieve and display content")

    resp = s3.get_object(Bucket=bucket_name, Key=key1)
    content = resp["Body"].read().decode("utf-8")
    kv("Status", resp["ResponseMetadata"]["HTTPStatusCode"])
    kv("Content", content)
    success(f"Retrieved {len(content)} bytes")

    # ── Step 4: list_objects_v2 - show all objects ──
    step(4, "list_objects_v2 - List all objects in bucket")

    listing = s3.list_objects_v2(Bucket=bucket_name)
    objects = listing.get("Contents", [])
    info(f"Found {len(objects)} object(s):")
    for obj in objects:
        kv(f"  {obj['Key']}", f"{obj['Size']} bytes")
    success("Listing complete")

    # ── Step 5: put more objects ──
    step(5, "put_object - Upload additional objects")

    extras = {
        "config.json": (json.dumps({"env": "demo", "version": 1}, indent=2), "application/json"),
        "notes/readme.txt": ("This is a nested key to show prefix-based listing.", "text/plain"),
        "notes/todo.txt": ("Finish the S3 demo.", "text/plain"),
    }

    for key, (body, content_type) in extras.items():
        s3.put_object(Bucket=bucket_name, Key=key, Body=body, ContentType=content_type)
        kv("Uploaded", f"{key} ({len(body)} bytes, {content_type})")

    listing = s3.list_objects_v2(Bucket=bucket_name)
    info(f"\nBucket now contains {listing['KeyCount']} objects:")
    for obj in listing.get("Contents", []):
        kv(f"  {obj['Key']}", f"{obj['Size']} bytes")
    success("Additional objects uploaded")

    # ── Step 6: delete_object - delete one object ──
    step(6, "delete_object - Delete a single object")

    delete_key = "config.json"
    s3.delete_object(Bucket=bucket_name, Key=delete_key)
    kv("Deleted", delete_key)
    success(f"Deleted {delete_key}")

    # ── Step 7: list again to confirm deletion ──
    step(7, "list_objects_v2 - Verify deletion")

    listing = s3.list_objects_v2(Bucket=bucket_name)
    remaining = listing.get("Contents", [])
    info(f"Bucket now contains {len(remaining)} objects:")
    for obj in remaining:
        kv(f"  {obj['Key']}", f"{obj['Size']} bytes")

    if any(o["Key"] == delete_key for o in remaining):
        fail(f"{delete_key} still present!")
    else:
        success(f"Confirmed: {delete_key} is gone")

    info(f"\nBucket {bucket_name} tracked for cleanup (run with --cleanup)")
