# boto3 Python Demos

Self-contained Python scripts demonstrating AWS SDK (boto3) patterns for common AWS operations.

## Prerequisites

```bash
pip install boto3 aioboto3
```

Configure AWS credentials via:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAM role (when running on AWS)

## S3 Demos

| Script | Description |
|--------|-------------|
| [s3_list_by_prefix.py](s3_list_by_prefix.py) | List objects filtered by prefix using Resource API |
| [s3_get_object.py](s3_get_object.py) | Download objects from S3 |
| [s3_multipart_upload.py](s3_multipart_upload.py) | Upload large files using multipart upload |
| [s3_client_vs_resource_api.py](s3_client_vs_resource_api.py) | Compare Client (low-level) vs Resource (high-level) APIs |

## DynamoDB Demos

| Script | Description |
|--------|-------------|
| [dynamodb_create_table_sync.py](dynamodb_create_table_sync.py) | Create table and seed data (synchronous) |
| [dynamodb_create_table_async.py](dynamodb_create_table_async.py) | Create table using async aioboto3 |
| [lambda_dynamodb_notes_handler.py](lambda_dynamodb_notes_handler.py) | Lambda handler for DynamoDB CRUD operations |

## EC2 Demos

| Script | Description |
|--------|-------------|
| [ec2_list_instances.py](ec2_list_instances.py) | List EC2 instances with details |

## Usage Pattern

All scripts support `--profile` and `--region` arguments:

```bash
# Use default credentials and region
python s3_list_by_prefix.py --bucket my-bucket --prefix logs/

# Specify AWS profile
python ec2_list_instances.py --profile production

# Specify region
python dynamodb_create_table_sync.py --region us-west-2
```

## Key Concepts Demonstrated

- **Session management**: Creating boto3 sessions with profiles/regions
- **Client vs Resource**: When to use low-level client vs high-level resource APIs
- **Pagination**: Handling large result sets with paginators
- **Waiters**: Waiting for async operations to complete
- **Error handling**: Proper exception handling for AWS operations
- **Async patterns**: Using aioboto3 for async/await workflows
