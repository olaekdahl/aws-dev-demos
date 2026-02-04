# DynamoDB Notes Lambda Handler
#
# AWS Lambda function for CRUD operations on a DynamoDB Notes table.
# Designed to be deployed behind API Gateway for a REST API.
#
# Table Schema:
#   - Partition key: UserId (Number)
#   - Sort key: NoteId (Number)
#
# Supported Operations:
#   - GET /notes/{userId}/{noteId} - Retrieve a specific note
#
# Environment Variables:
#   - TABLE_NAME: DynamoDB table name (default: "Notes")
#
# Deployment:
#   1. Create a DynamoDB table with UserId (N) and NoteId (N) keys
#   2. Create Lambda function with this handler
#   3. Attach IAM role with DynamoDB read permissions
#   4. Create API Gateway with Lambda integration

import json
import os
from decimal import Decimal
import boto3


# Initialize DynamoDB resource outside handler for connection reuse
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Decimal types.
    
    DynamoDB returns numbers as Decimal objects for precision.
    Standard json.dumps() doesn't know how to serialize Decimal,
    so we convert them to int or float as appropriate.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if it's a whole number, otherwise float
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Lambda entry point for handling API Gateway requests.
    
    Expected event format (API Gateway proxy integration):
    {
        "pathParameters": {
            "userId": "1",
            "noteId": "101"
        },
        "httpMethod": "GET",
        ...
    }
    
    Args:
        event: API Gateway event dictionary
        context: Lambda context object (runtime info)
        
    Returns:
        API Gateway response with statusCode, headers, and body
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract path parameters
        path_params = event.get('pathParameters', {}) or {}
        user_id = path_params.get('userId')
        note_id = path_params.get('noteId')
        
        # Validate required parameters
        if not user_id or not note_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing required path parameters',
                    'required': ['userId', 'noteId']
                })
            }
        
        # Get the note from DynamoDB
        response = table.get_item(
            Key={
                'UserId': int(user_id),
                'NoteId': int(note_id)
            }
        )
        
        # Check if item exists
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response['Item'], cls=DecimalEncoder)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Note not found',
                    'userId': user_id,
                    'noteId': note_id
                })
            }
            
    except ValueError as e:
        # Handle invalid number format
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Invalid parameter format',
                'message': 'userId and noteId must be valid integers'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
