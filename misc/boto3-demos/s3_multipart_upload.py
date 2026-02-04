#!/usr/bin/env python3
"""
S3 Multipart Upload Demo

Demonstrates how to upload large files to S3 using multipart upload with the
boto3 resource (high-level) API. Multipart uploads are recommended for files
larger than 100 MB and required for files larger than 5 GB.

Key concepts:
- Initiate multipart upload to get an upload ID
- Upload file in chunks (minimum 5 MB per part, except last)
- Complete upload by providing all part ETags
- Abort upload on failure to clean up incomplete parts

Usage:
    python s3_multipart_upload.py --bucket BUCKET --file PATH --key KEY
    python s3_multipart_upload.py --bucket my-bucket --file large.zip --key uploads/large.zip
    python s3_multipart_upload.py --bucket my-bucket --file data.tar.gz --key backups/data.tar.gz --profile prod
"""

import argparse
import os
import boto3


# Minimum part size is 5 MB (required by S3 for all parts except the last)
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB


def multipart_upload(bucket_name: str, file_path: str, key_name: str, session: boto3.Session) -> bool:
    """
    Upload a file to S3 using multipart upload.
    
    This approach is more reliable for large files because:
    - Failed parts can be retried individually
    - Upload can be resumed if interrupted
    - Better network utilization with parallel uploads (not shown here)
    
    Args:
        bucket_name: Name of the S3 bucket
        file_path: Local path to the file to upload
        key_name: S3 object key (destination path in bucket)
        session: boto3 Session to use for credentials
        
    Returns:
        True if upload succeeded, False otherwise
    """
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    
    # Get file size for progress tracking
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    # Step 1: Initiate multipart upload
    # This returns an upload ID that identifies this specific upload session
    multipart_upload = bucket.initiate_multipart_upload(Key=key_name)
    upload_id = multipart_upload.id
    print(f"Initiated multipart upload (ID: {upload_id[:8]}...)")
    
    # Track uploaded parts for completing the upload
    parts = []
    part_number = 1
    bytes_uploaded = 0
    
    try:
        with open(file_path, 'rb') as file:
            while True:
                # Read next chunk
                data = file.read(CHUNK_SIZE)
                if not data:
                    break
                
                # Step 2: Upload each part
                # Each part gets a unique part number (1-based)
                part = multipart_upload.Part(part_number)
                response = part.upload(Body=data)
                
                # Store part info for completing upload later
                # ETag is a hash of the part content used for verification
                parts.append({
                    'PartNumber': part_number,
                    'ETag': response['ETag']
                })
                
                bytes_uploaded += len(data)
                progress = (bytes_uploaded / file_size) * 100
                print(f"  Part {part_number}: {len(data):,} bytes (ETag: {response['ETag'][:10]}...) - {progress:.1f}%")
                
                part_number += 1
        
        # Step 3: Complete the multipart upload
        # S3 assembles all parts into the final object
        multipart_upload.complete(MultipartUpload={'Parts': parts})
        print(f"\n✓ Upload completed successfully!")
        print(f"  Object: s3://{bucket_name}/{key_name}")
        print(f"  Total parts: {len(parts)}")
        return True
        
    except Exception as e:
        # Step 4 (on failure): Abort the upload
        # Important: Incomplete multipart uploads incur storage charges!
        print(f"\n✗ Error occurred: {e}")
        print("  Aborting multipart upload...")
        multipart_upload.abort()
        print("  Upload aborted. No charges for incomplete parts.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Upload large files to S3 using multipart upload"
    )
    parser.add_argument(
        "--bucket", "-b",
        required=True,
        help="Name of the S3 bucket"
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Local file path to upload"
    )
    parser.add_argument(
        "--key", "-k",
        required=True,
        help="S3 object key (destination path)"
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="AWS profile name (optional)"
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region (optional)"
    )
    args = parser.parse_args()

    # Validate file exists
    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    
    print(f"\nUploading {args.file} to s3://{args.bucket}/{args.key}\n")
    
    multipart_upload(args.bucket, args.file, args.key, session)


if __name__ == "__main__":
    main()
