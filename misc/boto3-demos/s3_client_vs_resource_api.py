#!/usr/bin/env python3
"""
S3 Client vs Resource API Comparison

Demonstrates the difference between boto3's two API styles:
- Client (low-level): Direct service API calls, returns raw responses
- Resource (high-level): Object-oriented interface, more Pythonic

Both achieve the same results, but the resource API is often more readable
while the client API offers more control and access to all service features.

Usage:
    python s3_client_vs_resource_api.py --bucket BUCKET_NAME
    python s3_client_vs_resource_api.py --bucket my-bucket --profile dev
"""

import argparse
import boto3


def list_with_client_api(bucket_name: str, session: boto3.Session) -> list:
    """
    List objects using the Client (low-level) API.
    
    The client API:
    - Mirrors the AWS service API directly
    - Returns raw response dictionaries
    - Requires manual pagination handling
    - Provides access to all service operations
    
    Args:
        bucket_name: Name of the S3 bucket
        session: boto3 Session to use
        
    Returns:
        List of object keys
    """
    # Create a low-level client
    s3_client = session.client('s3')
    
    object_keys = []
    
    # Use paginator for buckets with many objects
    # Without pagination, list_objects_v2 returns max 1000 objects
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name):
        # Response is a dictionary - need to handle missing keys
        contents = page.get('Contents', [])
        for obj in contents:
            object_keys.append(obj['Key'])
            print(f"    {obj['Key']} ({obj['Size']:,} bytes)")
    
    return object_keys


def list_with_resource_api(bucket_name: str, session: boto3.Session) -> list:
    """
    List objects using the Resource (high-level) API.
    
    The resource API:
    - Provides an object-oriented interface
    - Handles pagination automatically
    - Returns resource objects with attributes
    - More Pythonic and readable
    
    Args:
        bucket_name: Name of the S3 bucket
        session: boto3 Session to use
        
    Returns:
        List of object keys
    """
    # Create a high-level resource
    s3_resource = session.resource('s3')
    
    # Get bucket object
    bucket = s3_resource.Bucket(bucket_name)
    
    object_keys = []
    
    # Iteration handles pagination automatically
    for obj in bucket.objects.all():
        object_keys.append(obj.key)
        print(f"    {obj.key} ({obj.size:,} bytes)")
    
    return object_keys


def upload_comparison():
    """
    Print example code comparing upload syntax between client and resource APIs.
    
    This function demonstrates the syntax differences without
    actually uploading (prints code examples for reference).
    """
    print("\n--- Upload Syntax Comparison ---\n")
    
    print("Client API (low-level):")
    print("""
    s3_client = session.client('s3')
    
    # Upload with put_object (for small objects)
    s3_client.put_object(
        Bucket='my-bucket',
        Key='path/to/file.txt',
        Body=b'file contents'
    )
    
    # Upload a file
    s3_client.upload_file(
        Filename='local/file.txt',
        Bucket='my-bucket',
        Key='path/to/file.txt'
    )
    """)
    
    print("Resource API (high-level):")
    print("""
    s3_resource = session.resource('s3')
    
    # Get object reference and upload
    obj = s3_resource.Object('my-bucket', 'path/to/file.txt')
    obj.put(Body=b'file contents')
    
    # Or upload a file directly
    obj.upload_file('local/file.txt')
    
    # Or use bucket reference
    bucket = s3_resource.Bucket('my-bucket')
    bucket.upload_file('local/file.txt', 'path/to/file.txt')
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Compare boto3 client vs resource APIs for S3"
    )
    parser.add_argument(
        "--bucket", "-b",
        required=True,
        help="Name of the S3 bucket to list"
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
    
    print(f"\nComparing Client vs Resource APIs for bucket: {args.bucket}\n")
    
    # Client API demo
    print("=" * 60)
    print("CLIENT API (Low-Level)")
    print("=" * 60)
    print("  - Direct service API calls")
    print("  - Returns dictionary responses")
    print("  - Manual pagination required")
    print("-" * 60)
    client_keys = list_with_client_api(args.bucket, session)
    print(f"\n  Found {len(client_keys)} objects\n")
    
    # Resource API demo
    print("=" * 60)
    print("RESOURCE API (High-Level)")
    print("=" * 60)
    print("  - Object-oriented interface")
    print("  - Automatic pagination")
    print("  - More Pythonic syntax")
    print("-" * 60)
    resource_keys = list_with_resource_api(args.bucket, session)
    print(f"\n  Found {len(resource_keys)} objects\n")
    
    # Show upload syntax comparison
    upload_comparison()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    print("""
  Use RESOURCE API when:
    - Working with common operations (CRUD)
    - Readability is important
    - You want automatic pagination
    
  Use CLIENT API when:
    - You need access to all service operations
    - Working with service-specific features
    - You need fine-grained control over requests
    - The resource API doesn't support an operation
    """)


if __name__ == "__main__":
    main()
