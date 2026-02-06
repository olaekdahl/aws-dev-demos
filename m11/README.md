# m11 - Async Patterns

SNS/SQS fan-out, dead-letter queue recovery, and FIFO ordering guarantees.

## Demos

| Name | Description |
|------|-------------|
| `fanout` | Creates SNS topic + 2 SQS queues, publishes messages, polls both queues in parallel to show fan-out |
| `dlq` | Creates a queue with a DLQ, sends messages that fail processing, demonstrates redrive |
| `fifo` | Creates a FIFO queue, sends messages with group IDs, demonstrates ordering guarantees |

## Usage

```bash
# Run all demos
python m11/run.py

# Run a specific demo
python m11/run.py --demo fanout
python m11/run.py --demo dlq
python m11/run.py --demo fifo

# Clean up created topics and queues
python m11/run.py --cleanup
```

## SAM App

EventBridge integration demo:

```bash
cd m11/sam-eventbridge
sam build --use-container
sam deploy --guided

# Then put a test event
python m11/sam-eventbridge/put_event.py --region us-east-1
```

## AWS Services

- **SNS** -- CreateTopic, Subscribe, Publish
- **SQS** -- CreateQueue (standard + FIFO + DLQ), SendMessage, ReceiveMessage
- **EventBridge** -- PutEvents (SAM app)
