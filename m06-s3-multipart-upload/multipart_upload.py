"""
Demo: S3 Multipart Upload

Demonstrates multipart upload for large files.

Usage:
    python multipart_upload.py --bucket mybucket --key largefile.bin --size-mb 64 --profile myprofile --region us-east-1
"""
import argparse
import json
import os
import math
import boto3


def main():
    parser = argparse.ArgumentParser(description="Multipart upload to S3")
    parser.add_argument("--bucket", required=True, help="Bucket name")
    parser.add_argument("--key", required=True, help="Object key")
    parser.add_argument("--size-mb", type=int, default=64, help="Total size in MB")
    parser.add_argument("--part-mb", type=int, default=8, help="Part size in MB")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--region", help="AWS region")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3")

    total_bytes = args.size_mb * 1024 * 1024
    part_bytes = args.part_mb * 1024 * 1024
    num_parts = math.ceil(total_bytes / part_bytes)

    # Initiate multipart upload
    upload = s3.create_multipart_upload(Bucket=args.bucket, Key=args.key)
    upload_id = upload["UploadId"]
    print(json.dumps({"multipart_started": True, "upload_id": upload_id, "parts": num_parts}))

    completed_parts = []
    try:
        for part_num in range(1, num_parts + 1):
            # Calculate size of this part
            this_size = min(part_bytes, total_bytes - (part_num - 1) * part_bytes)

            # Generate random data for this part
            data = os.urandom(this_size)

            # Upload the part
            response = s3.upload_part(
                Bucket=args.bucket,
                Key=args.key,
                UploadId=upload_id,
                PartNumber=part_num,
                Body=data
            )

            completed_parts.append({"ETag": response["ETag"], "PartNumber": part_num})
            print(json.dumps({"part_uploaded": part_num, "size": this_size}))

        # Complete the multipart upload
        s3.complete_multipart_upload(
            Bucket=args.bucket,
            Key=args.key,
            UploadId=upload_id,
            MultipartUpload={"Parts": completed_parts}
        )
        print(json.dumps({
            "multipart_completed": True,
            "bucket": args.bucket,
            "key": args.key,
            "total_size": total_bytes
        }, indent=2))

    except Exception as e:
        print(json.dumps({"multipart_failed": True, "error": str(e)}))
        s3.abort_multipart_upload(Bucket=args.bucket, Key=args.key, UploadId=upload_id)
        print(json.dumps({"multipart_aborted": True, "upload_id": upload_id}))
        raise


if __name__ == "__main__":
    main()
