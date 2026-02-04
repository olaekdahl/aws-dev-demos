#!/usr/bin/env python3
"""
DynamoDB Create Table and Seed Data Demo (Synchronous)

Demonstrates how to:
- Create a DynamoDB table with partition and sort key
- Wait for table creation to complete
- Seed the table with sample data
- Query data using key conditions

This uses the synchronous boto3 API. See dynamodb_create_table_async.py
for the async aioboto3 version.

Usage:
    python dynamodb_create_table_sync.py
    python dynamodb_create_table_sync.py --profile dev --region us-west-2
"""

import argparse
import boto3
from botocore.exceptions import ClientError


TABLE_NAME = "Notes"


def create_table(dynamodb) -> bool:
    """
    Create the Notes DynamoDB table if it doesn't exist.
    
    Table schema:
    - Partition key: UserId (Number)
    - Sort key: NoteId (Number)
    
    Args:
        dynamodb: boto3 DynamoDB resource
        
    Returns:
        True if table was created, False if it already exists
    """
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'UserId',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'NoteId',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'UserId',
                    'AttributeType': 'N'  # Number type
                },
                {
                    'AttributeName': 'NoteId',
                    'AttributeType': 'N'  # Number type
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand capacity (no provisioning needed)
        )
        
        print(f"Creating table '{TABLE_NAME}'...")
        
        # Wait until the table exists (polls every 20 seconds)
        table.wait_until_exists()
        
        print(f"✓ Table '{TABLE_NAME}' created successfully!")
        print(f"  Status: {table.table_status}")
        print(f"  ARN: {table.table_arn}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{TABLE_NAME}' already exists.")
            return False
        raise


def seed_table(dynamodb):
    """
    Seed the Notes table with sample data.
    
    Creates multiple notes for different users demonstrating:
    - Basic attributes (Note, FavoriteColor)
    - Boolean-like strings (Favorite)
    - List attributes (Tags)
    - Map attributes (Metadata)
    
    Args:
        dynamodb: boto3 DynamoDB resource
    """
    table = dynamodb.Table(TABLE_NAME)
    
    # Sample data with various attribute types
    sample_notes = [
        {
            'UserId': 1,
            'NoteId': 101,
            'Note': 'My first note - learning DynamoDB!',
            'FavoriteColor': 'Blue',
            'Favorite': 'True',
            'Tags': ['personal', 'learning'],
            'Metadata': {
                'Author': 'User1',
                'CreatedDate': '2024-01-15'
            }
        },
        {
            'UserId': 1,
            'NoteId': 102,
            'Note': 'Meeting notes from today',
            'FavoriteColor': 'Green',
            'Favorite': 'False',
            'Tags': ['work', 'meetings'],
            'Metadata': {
                'Author': 'User1',
                'CreatedDate': '2024-01-16'
            }
        },
        {
            'UserId': 1,
            'NoteId': 103,
            'Note': 'Shopping list for the weekend',
            'FavoriteColor': 'Blue',
            'Favorite': 'True',
            'Tags': ['personal', 'shopping'],
            'Metadata': {
                'Author': 'User1',
                'CreatedDate': '2024-01-17'
            }
        },
        {
            'UserId': 2,
            'NoteId': 201,
            'Note': 'Project ideas brainstorm',
            'FavoriteColor': 'Red',
            'Favorite': 'True',
            'Tags': ['work', 'projects'],
            'Metadata': {
                'Author': 'User2',
                'CreatedDate': '2024-01-15'
            }
        },
        {
            'UserId': 2,
            'NoteId': 202,
            'Note': 'Team collaboration notes',
            'FavoriteColor': 'Red',
            'Favorite': 'False',
            'Tags': ['work', 'collaboration'],
            'Metadata': {
                'Author': 'User2',
                'CreatedDate': '2024-01-16'
            }
        }
    ]
    
    print(f"\nSeeding table with {len(sample_notes)} items...")
    
    for note in sample_notes:
        table.put_item(Item=note)
        print(f"  ✓ Added note {note['NoteId']} for user {note['UserId']}")
    
    print("\n✓ Seeding complete!")


def query_user_notes(dynamodb, user_id: int):
    """
    Query all notes for a specific user.
    
    Uses the partition key (UserId) to retrieve all notes for a user.
    Results are automatically sorted by the sort key (NoteId).
    
    Args:
        dynamodb: boto3 DynamoDB resource
        user_id: The user ID to query
    """
    table = dynamodb.Table(TABLE_NAME)
    
    print(f"\nQuerying notes for UserId={user_id}...")
    print("-" * 50)
    
    # Query by partition key
    response = table.query(
        KeyConditionExpression='UserId = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    
    for item in response['Items']:
        print(f"\nNote {item['NoteId']}:")
        print(f"  Content: {item['Note']}")
        print(f"  Tags: {', '.join(item.get('Tags', []))}")
        print(f"  Favorite: {item.get('Favorite', 'N/A')}")
    
    print(f"\n{'=' * 50}")
    print(f"Found {len(response['Items'])} notes for user {user_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Create and seed a DynamoDB Notes table"
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
    dynamodb = session.resource('dynamodb')
    
    print(f"\n{'=' * 50}")
    print("DynamoDB Table Creation and Seeding Demo")
    print(f"{'=' * 50}")
    
    # Create table (if needed)
    create_table(dynamodb)
    
    # Seed with sample data
    seed_table(dynamodb)
    
    # Query and display data
    query_user_notes(dynamodb, user_id=1)


if __name__ == "__main__":
    main()
