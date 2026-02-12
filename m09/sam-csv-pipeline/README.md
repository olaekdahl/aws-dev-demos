# S3 CSV to DynamoDB Pipeline

A SAM application that processes CSV files uploaded to S3 and loads the data into DynamoDB.

## Architecture

```
+-------------+      +-------------+      +-------------+
|     S3      | ---> |   Lambda    | ---> |  DynamoDB   |
|   (.csv)    |      |             |      |             |
+-------------+      +-------------+      +-------------+
    Upload             Parse CSV           Store Rows
```

## How It Works

1. Upload a `.csv` file to the S3 bucket
2. S3 triggers the Lambda function
3. Lambda downloads the CSV, parses it using the first row as headers
4. Each row is written to DynamoDB with:
   - `pk`: filename (partition key)
   - `sk`: `row#000001` (sort key)
   - All CSV columns as attributes
   - 7-day TTL for automatic cleanup

## Deploy

```bash
cd m09/sam-csv-pipeline
sam build --use-container
sam deploy --guided
```

## Test

After deployment, upload the sample CSV:

```bash
# Get the bucket name from stack outputs
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name sam-app \
  --region us-west-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

# Upload sample CSV
aws s3 cp sample.csv s3://$BUCKET/

# Check Lambda logs
sam logs -n CsvProcessorFunction --stack-name sam-app --tail

# Query DynamoDB
TABLE=$(aws cloudformation describe-stacks \
  --stack-name sam-app \
  --region us-west-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`TableName`].OutputValue' \
  --output text)

aws dynamodb scan --table-name $TABLE --region us-west-1
```

## Cleanup

```bash
# Empty the bucket first
aws s3 rm s3://$BUCKET --recursive

# Delete the stack
sam delete --stack-name sam-app
```

## CSV Format

- First row must be headers
- Headers become DynamoDB attribute names (lowercased, spaces replaced with underscores)
- Empty values are skipped
