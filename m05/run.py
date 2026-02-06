#!/usr/bin/env python3
"""m05 - S3 Buckets: lifecycle policies, versioning & time travel."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from botocore.exceptions import ClientError
from common.args import build_parser
from common.output import banner, step, success, fail, info, warn, kv
from common.session import create_session
from common.cleanup import get_tracked_resources, clear_tracked

from demos.bucket_lifecycle import run as lifecycle_demo
from demos.versioning_time_travel import run as time_travel_demo

DEMOS = {
    "lifecycle": lifecycle_demo,
    "time-travel": time_travel_demo,
}

DEMO_INFO = {
    "lifecycle": "bucket versioning & lifecycle policies with visual timeline",
    "time-travel": "versioning time travel: overwrite, delete, and recover objects",
}


def cleanup(args):
    """Delete all tracked S3 buckets and their contents."""
    resources = get_tracked_resources("m05")

    if not resources:
        info("No tracked m05 resources to clean up.")
        return

    banner("m05", "Cleanup")
    info(f"Found {len(resources)} tracked resource(s) to remove.\n")

    session = create_session(args.profile, args.region)

    for i, resource in enumerate(resources, 1):
        rtype = resource.get("type")
        rid = resource.get("id")
        region = resource.get("region", args.region)

        if rtype != "s3_bucket":
            warn(f"Unknown resource type '{rtype}' -- skipping '{rid}'")
            continue

        step(i, f"Deleting S3 bucket: {rid}")

        # Use the region recorded at creation time
        s3 = session.client("s3", region_name=region)

        # Delete all object versions and delete markers first
        try:
            paginator = s3.get_paginator("list_object_versions")
            pages = paginator.paginate(Bucket=rid)

            deleted_count = 0
            for page in pages:
                objects_to_delete = []

                for version in page.get("Versions", []):
                    objects_to_delete.append({
                        "Key": version["Key"],
                        "VersionId": version["VersionId"],
                    })

                for marker in page.get("DeleteMarkers", []):
                    objects_to_delete.append({
                        "Key": marker["Key"],
                        "VersionId": marker["VersionId"],
                    })

                if objects_to_delete:
                    s3.delete_objects(
                        Bucket=rid,
                        Delete={"Objects": objects_to_delete, "Quiet": True},
                    )
                    deleted_count += len(objects_to_delete)

            if deleted_count > 0:
                kv("  Deleted objects/versions", deleted_count)

        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "NoSuchBucket":
                info(f"  Bucket '{rid}' already gone -- skipping")
                continue
            else:
                fail(f"  Could not empty bucket '{rid}': {exc}")
                continue

        # Now delete the empty bucket
        try:
            s3.delete_bucket(Bucket=rid)
            success(f"Bucket '{rid}' deleted")
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "NoSuchBucket":
                info(f"  Bucket '{rid}' already gone")
            else:
                fail(f"  Could not delete bucket '{rid}': {exc}")
                continue

    clear_tracked("m05")
    success("m05 cleanup complete -- tracking file cleared")


def main():
    parser = build_parser("m05: S3 Buckets", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m05", "S3 Buckets")
        for name, fn in DEMOS.items():
            fn(args)


if __name__ == "__main__":
    main()
