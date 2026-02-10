#!/usr/bin/env python3
"""m06 - S3 Objects: CRUD, multipart, events, presigned URLs, encryption."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common import (
    create_session, banner, step, success, fail, info, warn, kv,
    get_tracked_resources, clear_tracked, build_parser,
)

from demos.object_crud import run as object_crud_demo
from demos.multipart_upload import run as multipart_upload_demo
from demos.multipart_parallel import run as multipart_parallel_demo
from demos.event_pipeline import run as event_pipeline_demo
from demos.presigned_urls import run as presigned_urls_demo
from demos.encryption_comparison import run as encryption_comparison_demo

MODULE = "m06"

DEMOS = {
    "object-crud": object_crud_demo,
    "multipart": multipart_upload_demo,
    "multipart-parallel": multipart_parallel_demo,
    "event-pipeline": event_pipeline_demo,
    "presigned": presigned_urls_demo,
    "encryption": encryption_comparison_demo,
}

DEMO_INFO = {
    "object-crud": "S3 object lifecycle (put, head, get, list, delete)",
    "multipart": "multipart upload with progress bar",
    "multipart-parallel": "parallel multipart upload using TransferConfig",
    "event-pipeline": "S3 event notifications to SQS",
    "presigned": "presigned PUT and GET URLs",
    "encryption": "SSE-S3 vs SSE-KMS encryption comparison",
}


def _cleanup_s3_bucket(s3, bucket_name):
    """Empty and delete an S3 bucket, handling both versioned and unversioned objects."""
    try:
        # Delete all object versions (covers versioned buckets)
        paginator = s3.get_paginator("list_object_versions")
        delete_markers = []
        versions = []

        for page in paginator.paginate(Bucket=bucket_name):
            for v in page.get("Versions", []):
                versions.append({"Key": v["Key"], "VersionId": v["VersionId"]})
            for dm in page.get("DeleteMarkers", []):
                delete_markers.append({"Key": dm["Key"], "VersionId": dm["VersionId"]})

        all_objects = versions + delete_markers

        if all_objects:
            # delete_objects supports max 1000 per call
            for i in range(0, len(all_objects), 1000):
                batch = all_objects[i:i + 1000]
                s3.delete_objects(Bucket=bucket_name, Delete={"Objects": batch})
            info(f"  Deleted {len(all_objects)} object version(s)/marker(s)")
        else:
            # Try plain object listing (unversioned bucket)
            paginator = s3.get_paginator("list_objects_v2")
            objects = []
            for page in paginator.paginate(Bucket=bucket_name):
                for obj in page.get("Contents", []):
                    objects.append({"Key": obj["Key"]})
            if objects:
                for i in range(0, len(objects), 1000):
                    batch = objects[i:i + 1000]
                    s3.delete_objects(Bucket=bucket_name, Delete={"Objects": batch})
                info(f"  Deleted {len(objects)} object(s)")

        s3.delete_bucket(Bucket=bucket_name)
        success(f"  Bucket deleted: {bucket_name}")

    except s3.exceptions.NoSuchBucket:
        info(f"  Bucket already gone: {bucket_name}")
    except Exception as e:
        fail(f"  Failed to delete bucket {bucket_name}: {e}")


def _cleanup_sqs_queue(sqs, queue_url, queue_name):
    """Delete an SQS queue."""
    try:
        sqs.delete_queue(QueueUrl=queue_url)
        success(f"  Queue deleted: {queue_name}")
    except Exception as e:
        if "NonExistentQueue" in str(e) or "AWS.SimpleQueueService.NonExistentQueue" in str(e):
            info(f"  Queue already gone: {queue_name}")
        else:
            fail(f"  Failed to delete queue {queue_name}: {e}")


def cleanup(args):
    """Delete all tracked m06 resources."""
    banner("m06", "Cleanup")

    resources = get_tracked_resources(MODULE)
    if not resources:
        info("No tracked resources to clean up.")
        return

    session = create_session(args.profile, args.region)
    s3 = session.client("s3")
    sqs = session.client("sqs")

    info(f"Found {len(resources)} tracked resource(s)\n")

    for r in resources:
        rtype = r["type"]
        rid = r["id"]

        if rtype == "s3_bucket":
            kv("Cleaning up S3 bucket", rid)
            _cleanup_s3_bucket(s3, rid)

        elif rtype == "sqs_queue":
            queue_name = r.get("queue_name", rid)
            kv("Cleaning up SQS queue", queue_name)
            _cleanup_sqs_queue(sqs, rid, queue_name)

        else:
            warn(f"Unknown resource type: {rtype} ({rid})")

    clear_tracked(MODULE)
    success("\nAll m06 resources cleaned up")


def main():
    parser = build_parser("m06: S3 Objects", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m06", "S3 Objects")
        for name, fn in DEMOS.items():
            fn(args)


if __name__ == "__main__":
    main()
