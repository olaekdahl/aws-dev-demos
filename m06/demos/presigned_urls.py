"""
Demo: S3 Presigned URLs - PUT and GET

Generates presigned PUT and GET URLs, demonstrates uploading and downloading
via plain HTTP requests (no AWS credentials needed at request time), and
dissects the URL anatomy to show the SigV4 query parameters.
"""
from urllib.parse import urlparse, parse_qs

import requests

from common import (
    create_session, banner, step, success, fail, info, kv,
    generate_name, track_resource,
)

MODULE = "m06"
EXPIRY_SECONDS = 300  # 5 minutes


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


def run(args):
    banner("m06", "S3 Presigned URLs - PUT and GET")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = session.region_name

    bucket_name = generate_name("presigned", getattr(args, "prefix", None))
    object_key = "shared-document.txt"
    upload_body = "This content was uploaded via a presigned PUT URL -- no SDK needed!"

    # ── Create bucket ──
    info(f"Creating bucket: {bucket_name}")
    try:
        _create_bucket(s3, bucket_name, region)
        success(f"Bucket created: {bucket_name}")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 1: Generate a presigned PUT URL ──
    step(1, "Generate a presigned PUT URL (5-minute expiry)")

    put_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket_name, "Key": object_key, "ContentType": "text/plain"},
        ExpiresIn=EXPIRY_SECONDS,
    )

    kv("Object key", object_key)
    kv("Expires in", f"{EXPIRY_SECONDS} seconds")
    kv("URL length", f"{len(put_url)} characters")
    info(f"PUT URL: {put_url[:120]}...")
    success("Presigned PUT URL generated")

    # ── Step 2: Upload via the presigned URL using requests ──
    step(2, "Upload via presigned PUT URL (plain HTTP, no AWS creds)")

    info("Using the 'requests' library -- no boto3 / no AWS credentials")
    resp = requests.put(put_url, data=upload_body, headers={"Content-Type": "text/plain"}, timeout=30)
    kv("HTTP method", "PUT")
    kv("Status", f"{resp.status_code} {resp.reason}")
    kv("Uploaded bytes", len(upload_body))

    if resp.status_code in (200, 204):
        success("Object uploaded via presigned URL")
    else:
        fail(f"Upload failed: {resp.status_code} {resp.text[:200]}")
        return

    # ── Step 3: Generate a presigned GET URL ──
    step(3, "Generate a presigned GET URL (5-minute expiry)")

    get_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=EXPIRY_SECONDS,
    )

    kv("Expires in", f"{EXPIRY_SECONDS} seconds")
    kv("URL length", f"{len(get_url)} characters")
    info(f"GET URL: {get_url[:120]}...")
    success("Presigned GET URL generated")

    # ── Step 4: Download via the presigned URL ──
    step(4, "Download via presigned GET URL (plain HTTP, no AWS creds)")

    resp = requests.get(get_url, timeout=30)
    kv("HTTP method", "GET")
    kv("Status", f"{resp.status_code} {resp.reason}")
    kv("Downloaded bytes", len(resp.content))
    kv("Content", resp.text)

    if resp.status_code == 200 and resp.text == upload_body:
        success("Content matches -- round-trip successful")
    elif resp.status_code == 200:
        success("Downloaded successfully (content may differ due to encoding)")
    else:
        fail(f"Download failed: {resp.status_code}")

    # ── Step 5: Show URL anatomy ──
    step(5, "URL anatomy - SigV4 query parameters")

    info("Presigned URLs embed authentication in the query string.")
    info("Anyone with this URL can perform the operation until it expires.\n")

    parsed = urlparse(get_url)
    params = parse_qs(parsed.query)

    kv("Scheme", parsed.scheme)
    kv("Host", parsed.hostname)
    kv("Path", parsed.path)
    info("\nQuery parameters:")

    # Display auth-related parameters in a structured way
    auth_params = [
        ("X-Amz-Algorithm", "Signing algorithm"),
        ("X-Amz-Credential", "Access key + scope"),
        ("X-Amz-Date", "Request timestamp"),
        ("X-Amz-Expires", "Validity window (seconds)"),
        ("X-Amz-SignedHeaders", "Headers included in signature"),
        ("X-Amz-Signature", "The computed signature"),
        ("X-Amz-Security-Token", "Session token (if using temp creds)"),
    ]

    for param_name, description in auth_params:
        value = params.get(param_name, [None])[0]
        if value:
            # Truncate long values for readability
            display = value if len(value) <= 64 else value[:60] + "..."
            kv(f"  {param_name}", display)
            info(f"    ({description})")

    success("URL anatomy displayed")
    info(f"\nBucket {bucket_name} tracked for cleanup (run with --cleanup)")
