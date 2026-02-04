#!/usr/bin/env python3
"""
S3 List Objects by Prefix Demo

Demonstrates how to list S3 objects filtered by a prefix using the boto3
resource (high-level) API. Useful for organizing objects into logical groups
like folders or categories.

Usage:
    python s3_list_by_prefix.py --bucket BUCKET_NAME --prefix PREFIX
    python s3_list_by_prefix.py --bucket my-bucket --prefix logs/2024/
    python s3_list_by_prefix.py --bucket my-bucket --prefix images/ --profile dev
"""

import argparse
import boto3


def list_objects_by_prefix(bucket_name: str, prefix: str, session: boto3.Session) -> list:
    """
    List all objects in an S3 bucket that match a given prefix.
    
    Args:
        bucket_name: Name of the S3 bucket
        prefix: Prefix filter (e.g., 'logs/', 'images/2024/')
        session: boto3 Session to use for credentials
        
    Returns:
        List of object keys matching the prefix
    """
    # Use the resource (high-level) API for simpler iteration
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    
    # Filter objects by prefix and collect keys
    object_keys = []
    for obj in bucket.objects.filter(Prefix=prefix):
        object_keys.append(obj.key)
        print(f"  {obj.key} ({obj.size:,} bytes)")
    
    return object_keys


def main():
    parser = argparse.ArgumentParser(
        description="List S3 objects filtered by prefix"
    )
    parser.add_argument(
        "--bucket", "-b",
        required=True,
        help="Name of the S3 bucket"
    )
    parser.add_argument(
        "--prefix", "-p",
        required=True,
        help="Prefix to filter objects (e.g., 'logs/', 'data/2024/')"
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

    # Create session with optional profile/region
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    
    print(f"\nListing objects in s3://{args.bucket}/{args.prefix}\n")
    
    keys = list_objects_by_prefix(args.bucket, args.prefix, session)
    
    print(f"\nFound {len(keys)} object(s) matching prefix '{args.prefix}'")


if __name__ == "__main__":
    main()
