"""
Demo: S3 Multipart Upload with Progress Bar

Demonstrates multipart upload by splitting a 32 MB payload into 8 MB parts,
uploading each with an ASCII progress bar, then verifying the assembled object.
"""
import os

from common import (
    create_session, banner, step, success, fail, info, kv,
    progress_bar, generate_name, track_resource,
)

MODULE = "m06"
TOTAL_SIZE = 32 * 1024 * 1024    # 32 MB
PART_SIZE = 8 * 1024 * 1024      # 8 MB


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


def run(args):
    banner("m06", "S3 Multipart Upload with Progress Bar")

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    region = session.region_name

    bucket_name = generate_name("multipart", getattr(args, "prefix", None))
    object_key = "large-payload.bin"

    # ── Create bucket ──
    info(f"Creating bucket: {bucket_name}")
    try:
        _create_bucket(s3, bucket_name, region)
        success(f"Bucket created: {bucket_name}")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 1: Initiate multipart upload ──
    step(1, "Initiate multipart upload")

    kv("Object key", object_key)
    kv("Total size", f"{TOTAL_SIZE // (1024 * 1024)} MB")
    kv("Part size", f"{PART_SIZE // (1024 * 1024)} MB")

    num_parts = TOTAL_SIZE // PART_SIZE
    kv("Number of parts", num_parts)

    mpu = s3.create_multipart_upload(Bucket=bucket_name, Key=object_key)
    upload_id = mpu["UploadId"]
    kv("Upload ID", upload_id)
    success("Multipart upload initiated")

    # ── Step 2: Upload parts with progress ──
    step(2, "Upload parts with progress bar")

    parts = []
    try:
        for i in range(1, num_parts + 1):
            data = os.urandom(PART_SIZE)
            resp = s3.upload_part(
                Bucket=bucket_name,
                Key=object_key,
                PartNumber=i,
                UploadId=upload_id,
                Body=data,
            )
            parts.append({"PartNumber": i, "ETag": resp["ETag"]})
            progress_bar(i, num_parts, label=f"Part {i}/{num_parts}")
    except Exception as e:
        fail(f"Part upload failed: {e}")
        info("Aborting multipart upload...")
        s3.abort_multipart_upload(Bucket=bucket_name, Key=object_key, UploadId=upload_id)
        fail("Multipart upload aborted")
        return

    success(f"All {num_parts} parts uploaded")

    # ── Step 3: Complete multipart upload ──
    step(3, "Complete multipart upload")

    result = s3.complete_multipart_upload(
        Bucket=bucket_name,
        Key=object_key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )
    kv("Location", result.get("Location", "(none)"))
    kv("ETag", result["ETag"])
    info("Note: multipart ETags contain a dash followed by the part count")
    success("Multipart upload completed")

    # ── Step 4: Verify with head_object ──
    step(4, "Verify assembled object with head_object")

    head = s3.head_object(Bucket=bucket_name, Key=object_key)
    kv("Content-Length", f"{head['ContentLength']:,} bytes")
    kv("ETag", head["ETag"])
    kv("Last-Modified", head["LastModified"])

    expected = TOTAL_SIZE
    actual = head["ContentLength"]
    if actual == expected:
        success(f"Size matches: {actual:,} bytes == {expected:,} bytes expected")
    else:
        fail(f"Size mismatch: {actual:,} bytes != {expected:,} bytes expected")

    info(f"\nBucket {bucket_name} tracked for cleanup (run with --cleanup)")
