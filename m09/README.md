# m09 - Lambda

Deploy Lambda functions, measure cold starts, and explore error handling patterns.

## Demos

| Name | Description |
|------|-------------|
| `deploy` | Auto-creates IAM role, packages handler, deploys a word frequency analyzer Lambda, invokes it |
| `cold-start` | Deploys a function and invokes it 10x, parses REPORT lines for Init Duration vs Duration |
| `errors` | Deploys a function that throws different error types (timeout, exception), shows how Lambda reports each |

## Usage

Run all demos:
```bash
python3 m09/run.py
```

Run a specific demo:
```bash
python3 m09/run.py --demo deploy
```
```bash
python3 m09/run.py --demo cold-start
```
```bash
python3 m09/run.py --demo errors
```

Clean up Lambda functions and IAM roles:
```bash
python3 m09/run.py --cleanup
```

## SAM Apps

### Event Source Demo (SQS)

```bash
cd m09/sam-event-source
sam build --use-container
sam deploy --guided
```

### CSV Pipeline (S3 → Lambda → DynamoDB)

Uploads a CSV to S3, triggers Lambda to parse it, and loads rows into DynamoDB.

```bash
cd m09/sam-csv-pipeline
sam build --use-container
sam deploy --guided

# Test with sample CSV
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name sam-csv-pipeline \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 cp sample.csv s3://$BUCKET/
```

See [sam-csv-pipeline/README.md](sam-csv-pipeline/README.md) for full details.

## AWS Services

- **Lambda** -- CreateFunction, Invoke, GetFunctionConfiguration
- **IAM** -- CreateRole, AttachRolePolicy
- **S3** -- Event notifications, GetObject
- **DynamoDB** -- BatchWriteItem
