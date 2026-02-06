"""
Demo: S3 Encryption Comparison

Uploads the same object three ways -- no encryption, SSE-S3 (AES256), and
SSE-KMS (aws/s3 managed key) -- then compares the encryption-related headers
side by side in a table.
"""
from common import (
    create_session, banner, step, success, fail, info, kv,
    table, generate_name, track_resource,
)

MODULE = "m06"


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


def run(args):
    banner("m06", "S3 Encryption Comparison")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = session.region_name

    bucket_name = generate_name("encrypt", getattr(args, "prefix", None))
    body = "Identical content uploaded with different encryption settings."

    # ── Create bucket ──
    info(f"Creating bucket: {bucket_name}")
    try:
        _create_bucket(s3, bucket_name, region)
        success(f"Bucket created: {bucket_name}")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 1: Upload with no explicit encryption ──
    step(1, "Upload with no explicit encryption")

    key_none = "no-encryption.txt"
    s3.put_object(Bucket=bucket_name, Key=key_none, Body=body, ContentType="text/plain")
    kv("Key", key_none)
    info("No ServerSideEncryption parameter specified")
    info("Note: S3 may still apply default bucket encryption (AES256)")
    success(f"Uploaded {key_none}")

    # ── Step 2: Upload with SSE-S3 (AES256) ──
    step(2, "Upload with SSE-S3 (AES256)")

    key_s3 = "sse-s3.txt"
    s3.put_object(
        Bucket=bucket_name,
        Key=key_s3,
        Body=body,
        ContentType="text/plain",
        ServerSideEncryption="AES256",
    )
    kv("Key", key_s3)
    kv("ServerSideEncryption", "AES256")
    info("S3-managed keys -- simplest server-side encryption")
    success(f"Uploaded {key_s3}")

    # ── Step 3: Upload with SSE-KMS (aws/s3 managed key) ──
    step(3, "Upload with SSE-KMS (AWS managed key)")

    key_kms = "sse-kms.txt"
    s3.put_object(
        Bucket=bucket_name,
        Key=key_kms,
        Body=body,
        ContentType="text/plain",
        ServerSideEncryption="aws:kms",
    )
    kv("Key", key_kms)
    kv("ServerSideEncryption", "aws:kms")
    info("Uses the AWS-managed aws/s3 KMS key for encryption")
    success(f"Uploaded {key_kms}")

    # ── Step 4: Head each object and compare encryption headers ──
    step(4, "Compare encryption headers across all three objects")

    keys = {
        "No encryption": key_none,
        "SSE-S3 (AES256)": key_s3,
        "SSE-KMS": key_kms,
    }

    rows = []
    for label, key in keys.items():
        head = s3.head_object(Bucket=bucket_name, Key=key)

        sse = head.get("ServerSideEncryption", "(none)")
        kms_key_id = head.get("SSEKMSKeyId", "(n/a)")
        etag = head.get("ETag", "")
        content_len = head.get("ContentLength", 0)
        bucket_key = "Yes" if head.get("BucketKeyEnabled") else "No"

        # Truncate KMS key ID for table display
        kms_display = kms_key_id
        if kms_key_id and len(kms_key_id) > 22:
            kms_display = "..." + kms_key_id[-20:]

        rows.append([label, sse, kms_display, bucket_key, etag])

        kv(f"\n  {label}", key)
        kv("    ServerSideEncryption", sse)
        kv("    SSEKMSKeyId", kms_key_id)
        kv("    BucketKeyEnabled", bucket_key)
        kv("    ETag", etag)

    info("")
    table(
        ["Method", "SSE Header", "KMS Key ID", "BucketKey", "ETag"],
        rows,
        col_width=22,
    )

    info("Key takeaways:")
    info("  - SSE-S3 (AES256): Simplest; S3 manages keys entirely")
    info("  - SSE-KMS: Supports key policies, auditing via CloudTrail")
    info("  - Default encryption may apply even without explicit headers")
    info("  - ETags may differ when KMS encryption is used")

    success("Encryption comparison complete")
    info(f"\nBucket {bucket_name} tracked for cleanup (run with --cleanup)")
