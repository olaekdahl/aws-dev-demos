#!/usr/bin/env python3
"""
EC2 List Instances Demo

Demonstrates how to list EC2 instances with their key attributes using
the boto3 client API.

Usage:
    python ec2_list_instances.py
    python ec2_list_instances.py --profile dev --region us-west-2
"""

import argparse
import boto3


def list_instances(session: boto3.Session):
    """
    List all EC2 instances in the account/region with key details.
    
    Args:
        session: boto3 Session to use for credentials
    """
    ec2 = session.client('ec2')
    
    # Describe all instances
    response = ec2.describe_instances()
    
    instance_count = 0
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_count += 1
            
            # Extract instance name from tags (if present)
            name = "N/A"
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            print(f"\nInstance: {instance['InstanceId']}")
            print(f"  Name:           {name}")
            print(f"  State:          {instance['State']['Name']}")
            print(f"  Type:           {instance['InstanceType']}")
            print(f"  Platform:       {instance.get('PlatformDetails', 'N/A')}")
            print(f"  Private IP:     {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"  Public IP:      {instance.get('PublicIpAddress', 'N/A')}")
            print(f"  VPC:            {instance.get('VpcId', 'N/A')}")
            print(f"  Subnet:         {instance.get('SubnetId', 'N/A')}")
            print(f"  Launch Time:    {instance.get('LaunchTime', 'N/A')}")
    
    print(f"\n{'=' * 50}")
    print(f"Total instances: {instance_count}")


def main():
    parser = argparse.ArgumentParser(
        description="List EC2 instances with details"
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
    
    region = session.region_name or "default region"
    print(f"\nListing EC2 instances in {region}...")
    print("=" * 50)
    
    list_instances(session)


if __name__ == "__main__":
    main()
