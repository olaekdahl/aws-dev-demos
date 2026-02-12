# SQS Event Source Demo

A SAM application demonstrating Lambda event source mapping with SQS.

## Architecture

```
+-------------+      +-------------+
|    SQS      | ---> |   Lambda    |
|   Queue     |      |   Worker    |
+-------------+      +-------------+
  Send Message        Process Batch
```

## How It Works

1. Messages are sent to the SQS queue
2. Lambda polls the queue automatically (event source mapping)
3. Messages are delivered in batches (up to 5 messages per invocation)
4. Lambda logs each message body

## Deploy

```bash
cd m09/sam-event-source
sam build --use-container
sam deploy --guided sam-event-source
```

## Test

After deployment, send a test message:

```bash
# Get the queue URL from stack outputs
QUEUE_URL=$(aws cloudformation describe-stacks \
  --stack-name sam-event-source \
  --query 'Stacks[0].Outputs[?OutputKey==`QueueUrl`].OutputValue' \
  --output text)

# Send a test message
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"hello": "world"}'

# Send multiple messages
for i in {1..5}; do
  aws sqs send-message \
    --queue-url $QUEUE_URL \
    --message-body "{\"message\": $i}"
done

# Check Lambda logs
sam logs -n WorkerFunction --stack-name sam-event-source --tail
```

## Cleanup

```bash
sam delete --stack-name sam-event-source
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| BatchSize | 5 | Max messages per Lambda invocation |
| VisibilityTimeout | 30s | Time before failed message reappears |
| Runtime | Python 3.12 | Lambda runtime |
| Timeout | 10s | Lambda execution timeout |
