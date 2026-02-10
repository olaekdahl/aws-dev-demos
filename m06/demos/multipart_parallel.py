"""
Demo: S3 Parallel Multipart Upload

Demonstrates parallel multipart upload using boto3's TransferConfig to
automatically handle chunking and concurrent uploads via the high-level
upload_file API.
"""
import os
import tempfile

import boto3.s3.transfer

from common import (
    create_session, banner, step, success, fail, info, kv,
    generate_name, track_resource,
)

MODULE = "m06"
FILE_SIZE = 32 * 1024 * 1024        # 32 MB
CHUNK_SIZE = 5 * 1024 * 1024        # 5 MB (minimum for multipart)
MAX_CONCURRENCY = 4


def _create_bucket(s3, bucket_name, region):
    """Create an S3 bucket, handling the us-east-1 LocationConstraint quirk."""
    params = {"Bucket": bucket_name}
    if region and region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**params)


class ProgressCallback:
    """Callback to track upload progress."""

    def __init__(self, total_size):
        self.total_size = total_size
        self.uploaded = 0

    def __call__(self, bytes_transferred):
        self.uploaded += bytes_transferred
        pct = (self.uploaded / self.total_size) * 100
        bar_len = 40
        filled = int(bar_len * self.uploaded // self.total_size)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r  [{bar}] {pct:5.1f}%", end="", flush=True)


def run(args):
    banner("m06", "S3 Parallel Multipart Upload")

    session = create_session(args.profile, args.region)
    s3_client = session.client("s3")
    s3_resource = session.resource("s3")
    region = session.region_name

    bucket_name = generate_name("parallel-mp", getattr(args, "prefix", None))
    object_key = "parallel-upload.bin"

    # ── Create bucket ──
    info(f"Creating bucket: {bucket_name}")
    try:
        _create_bucket(s3_client, bucket_name, region)
        success(f"Bucket created: {bucket_name}")
    except Exception as e:
        fail(f"Failed to create bucket: {e}")
        return

    track_resource(MODULE, "s3_bucket", bucket_name, region=region)

    # ── Step 1: Create a temporary file ──
    step(1, "Create temporary file for upload")

    kv("File size", f"{FILE_SIZE // (1024 * 1024)} MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp_path = tmp.name
        tmp.write(os.urandom(FILE_SIZE))

    kv("Temp file", tmp_path)
    success("Temporary file created")

    # ── Step 2: Configure parallel multipart upload ──
    step(2, "Configure TransferConfig for parallel upload")

    config = boto3.s3.transfer.TransferConfig(
        multipart_threshold=5 * 1024 * 1024,   # Use multipart for files > 5 MB
        multipart_chunksize=CHUNK_SIZE,         # 5 MB chunks
        max_concurrency=MAX_CONCURRENCY,        # 4 parallel threads
        use_threads=True,                       # Enable threading
    )

    kv("Multipart threshold", "5 MB")
    kv("Chunk size", f"{CHUNK_SIZE // (1024 * 1024)} MB")
    kv("Max concurrency", MAX_CONCURRENCY)
    kv("Threading", "enabled")
    success("TransferConfig ready")

    # ── Step 3: Upload with progress tracking ──
    step(3, "Upload file with parallel multipart")

    try:
        progress = ProgressCallback(FILE_SIZE)

        s3_resource.Bucket(bucket_name).upload_file(
            Filename=tmp_path,
            Key=object_key,
            Config=config,
            Callback=progress,
        )
        print()  # newline after progress bar
        success("Parallel multipart upload completed")
    except Exception as e:
        print()
        fail(f"Upload failed: {e}")
        os.unlink(tmp_path)
        return
    finally:
        os.unlink(tmp_path)

    # ── Step 4: Verify the uploaded object ──
    step(4, "Verify uploaded object")

    head = s3_client.head_object(Bucket=bucket_name, Key=object_key)
    kv("Content-Length", f"{head['ContentLength']:,} bytes")
    kv("ETag", head["ETag"])
    kv("Last-Modified", head["LastModified"])

    if "-" in head["ETag"]:
        info("Note: ETag contains '-' indicating multipart upload was used")

    expected = FILE_SIZE
    actual = head["ContentLength"]
    if actual == expected:
        success(f"Size matches: {actual:,} bytes == {expected:,} bytes expected")
    else:
        fail(f"Size mismatch: {actual:,} bytes != {expected:,} bytes expected")

    info(f"\nBucket {bucket_name} tracked for cleanup (run with --cleanup)")
