"""
Demo: Delete S3 Bucket and All Contents

Deletes all objects (including versions and delete markers) then deletes the bucket.

Usage:
    python delete_bucket_and_contents.py --bucket mybucket --yes --profile myprofile --region us-east-1
"""
import argparse
import json
import boto3


def main():
    parser = argparse.ArgumentParser(description="Delete S3 bucket and all contents")
    parser.add_argument("--bucket", required=True, help="Bucket name to delete")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to delete without --yes flag")

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    # Delete all object versions and delete markers
    paginator = s3.get_paginator("list_object_versions")
    total_deleted = 0

    for page in paginator.paginate(Bucket=args.bucket):
        objects_to_delete = []

        # Collect versions
        for version in page.get("Versions", []):
            objects_to_delete.append({"Key": version["Key"], "VersionId": version["VersionId"]})

        # Collect delete markers
        for marker in page.get("DeleteMarkers", []):
            objects_to_delete.append({"Key": marker["Key"], "VersionId": marker["VersionId"]})

        if objects_to_delete:
            s3.delete_objects(Bucket=args.bucket, Delete={"Objects": objects_to_delete, "Quiet": True})
            total_deleted += len(objects_to_delete)
            print(json.dumps({"deleted_versions": len(objects_to_delete)}))

    # Delete the bucket
    s3.delete_bucket(Bucket=args.bucket)
    print(json.dumps({"bucket_deleted": args.bucket, "total_objects_deleted": total_deleted}, indent=2))


if __name__ == "__main__":
    main()
