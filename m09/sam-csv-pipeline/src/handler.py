"""
Lambda handler for processing CSV files from S3 and loading into DynamoDB.

Triggered by S3 ObjectCreated events for .csv files.
Parses CSV, uses first row as headers, and writes each row to DynamoDB.
"""
import csv
import io
import json
import os
import time
import urllib.parse

import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get("TABLE_NAME", "csv-data-dev")


def lambda_handler(event, context):
    """Process S3 event and load CSV data into DynamoDB."""
    table = dynamodb.Table(TABLE_NAME)
    
    results = []
    
    for record in event.get("Records", []):
        # Extract bucket and key from S3 event
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        
        print(f"Processing s3://{bucket}/{key}")
        
        try:
            # Get the CSV file from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            rows_processed = 0
            
            # Use batch writer for efficient DynamoDB writes
            with table.batch_writer() as batch:
                for row_num, row in enumerate(reader, start=1):
                    # Create item with pk (filename) and sk (row number)
                    item = {
                        "pk": key,  # Partition key is the filename
                        "sk": f"row#{row_num:06d}",  # Sort key is row number
                        "source_bucket": bucket,
                        "uploaded_at": int(time.time()),
                        "ttl": int(time.time()) + 86400 * 7,  # 7 day TTL
                    }
                    
                    # Add all CSV columns to the item
                    for col_name, col_value in row.items():
                        # Clean column name (DynamoDB doesn't like special chars)
                        clean_name = col_name.strip().replace(" ", "_").lower()
                        if clean_name and col_value:
                            item[clean_name] = col_value.strip()
                    
                    batch.put_item(Item=item)
                    rows_processed += 1
            
            result = {
                "bucket": bucket,
                "key": key,
                "rows_processed": rows_processed,
                "status": "success"
            }
            print(f"Successfully processed {rows_processed} rows from {key}")
            
        except Exception as e:
            result = {
                "bucket": bucket,
                "key": key,
                "status": "error",
                "error": str(e)
            }
            print(f"Error processing {key}: {e}")
            raise
        
        results.append(result)
    
    return {
        "statusCode": 200,
        "body": json.dumps({"results": results})
    }
