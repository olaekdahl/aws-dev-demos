# m15 - End-to-End Capstone

Production-ready event pipeline: S3 uploads trigger SQS messages, processed by a Lambda worker that stores results in DynamoDB. Includes a DLQ, CloudWatch alarm, and REST API for querying results.

## Deploy

```bash
cd m15
sam build --use-container
sam deploy --guided
```

## Demos

| Name | Description |
|------|-------------|
| `test` | End-to-end integration test: uploads files, verifies processing via API, tests DLQ path |

## Usage

Test the deployed pipeline:
```bash
python3 m15/run.py --demo test
```

Cleanup:
```bash
cd m15 && sam delete
```

## Architecture

```
S3 Bucket → SQS Queue → Lambda Worker → DynamoDB Table
                ↓ (failures)
           Dead Letter Queue → CloudWatch Alarm
```

## AWS Services

- **S3** -- file upload trigger
- **SQS** -- standard queue with DLQ and redrive policy
- **Lambda** -- worker (processes S3 events) and API (query results)
- **DynamoDB** -- results storage
- **API Gateway** -- GET /items, GET /items/{id}
- **CloudWatch** -- DLQ depth alarm, log groups with retention
