#!/usr/bin/env python3
"""
DynamoDB Create Table Demo (Async with aioboto3)

Demonstrates async/await patterns for DynamoDB operations using aioboto3.
Useful for high-throughput applications or when integrating with async frameworks
like FastAPI, aiohttp, or asyncio-based applications.

Prerequisites:
    pip install aioboto3

Usage:
    python dynamodb_create_table_async.py
    
Note: This demo uses hardcoded region. For production, use environment
variables or AWS config files.
"""

import asyncio

try:
    import aioboto3
except ImportError:
    print("Error: aioboto3 is required for this demo")
    print("Install with: pip install aioboto3")
    exit(1)


TABLE_NAME = "NotesAsync"
REGION = "us-west-1"


async def create_dynamodb_table():
    """
    Create a DynamoDB table asynchronously using aioboto3.
    
    Key differences from sync boto3:
    - Use 'async with' for resource/client context managers
    - Use 'await' for all API calls
    - Use async waiters for table creation
    
    Returns:
        Table status after creation
    """
    print(f"Creating DynamoDB table '{TABLE_NAME}' in {REGION}...")
    print("-" * 50)
    
    # Create an async session
    session = aioboto3.Session()
    
    # Use async context manager for the resource
    async with session.resource('dynamodb', region_name=REGION) as dynamodb:
        
        # Create the table asynchronously
        table = await dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'ID',
                    'KeyType': 'HASH'  # Partition key only (simple primary key)
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'ID',
                    'AttributeType': 'S'  # String type
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        print(f"Table creation initiated...")
        
        # Wait for the table to be created using async waiter
        # The waiter polls the table status until it becomes ACTIVE
        waiter = table.meta.client.get_waiter('table_exists')
        await waiter.wait(TableName=TABLE_NAME)
        
        # Reload table attributes after waiting
        await table.reload()
        
        print(f"\n✓ Table created successfully!")
        print(f"  Table name: {table.table_name}")
        print(f"  Status: {table.table_status}")
        print(f"  Item count: {table.item_count}")
        print(f"  ARN: {table.table_arn}")
        
        return table.table_status


async def cleanup_table():
    """
    Delete the demo table (optional cleanup).
    """
    print(f"\nDeleting table '{TABLE_NAME}'...")
    
    session = aioboto3.Session()
    
    async with session.resource('dynamodb', region_name=REGION) as dynamodb:
        table = await dynamodb.Table(TABLE_NAME)
        await table.delete()
        
        # Wait for deletion
        waiter = table.meta.client.get_waiter('table_not_exists')
        await waiter.wait(TableName=TABLE_NAME)
        
        print(f"✓ Table '{TABLE_NAME}' deleted.")


async def main():
    """
    Main async entry point demonstrating async DynamoDB operations.
    
    Shows the pattern for running async boto3 operations:
    1. Define async functions with async def
    2. Use await for all API calls
    3. Run with asyncio.run() from sync code
    """
    print("=" * 50)
    print("Async DynamoDB Demo with aioboto3")
    print("=" * 50)
    
    try:
        await create_dynamodb_table()
        
        print("\n" + "=" * 50)
        print("TIP: Use 'async for' for paginated operations:")
        print("""
    async with session.resource('dynamodb') as dynamodb:
        table = await dynamodb.Table('MyTable')
        async for item in table.scan():
            process(item)
        """)
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    # Run the async main function
    # asyncio.run() creates an event loop, runs the coroutine, then closes the loop
    asyncio.run(main())
