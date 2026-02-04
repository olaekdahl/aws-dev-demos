#!/usr/bin/env python3
"""
S3 Get Object Demo

Demonstrates how to download an object from S3 to a local file using the
boto3 resource (high-level) API.

Usage:
    python s3_get_object.py --bucket BUCKET --key KEY --output FILE
    python s3_get_object.py --bucket my-bucket --key data/report.csv --output ./report.csv
    python s3_get_object.py --bucket my-bucket --key images/logo.png --output ./logo.png --profile dev
"""

import argparse
import os
import boto3


def download_object(bucket_name: str, key: str, output_path: str, session: boto3.Session) -> bool:
    """
    Download an object from S3 to a local file.
    
    Args:
        bucket_name: Name of the S3 bucket
        key: S3 object key to download
        output_path: Local file path to save the object
        session: boto3 Session to use for credentials
        
    Returns:
        True if download succeeded, False otherwise
    """
    s3 = session.resource('s3')
    
    try:
        # Get object reference
        obj = s3.Object(bucket_name, key)
        
        # Check if object exists by getting metadata
        obj.load()  # Raises exception if object doesn't exist
        
        print(f"Object found:")
        print(f"  Size: {obj.content_length:,} bytes")
        print(f"  Last modified: {obj.last_modified}")
        print(f"  Content type: {obj.content_type}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Download the file
        print(f"\nDownloading to {output_path}...")
        obj.download_file(output_path)
        
        # Verify download
        local_size = os.path.getsize(output_path)
        print(f"\n✓ Downloaded successfully ({local_size:,} bytes)")
        return True
        
    except s3.meta.client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"✗ Object not found: s3://{bucket_name}/{key}")
        else:
            print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download an object from S3"
    )
    parser.add_argument(
        "--bucket", "-b",
        required=True,
        help="Name of the S3 bucket"
    )
    parser.add_argument(
        "--key", "-k",
        required=True,
        help="S3 object key to download"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Local file path to save the object"
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

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    
    print(f"\nDownloading s3://{args.bucket}/{args.key}\n")
    
    download_object(args.bucket, args.key, args.output, session)


if __name__ == "__main__":
    main()
