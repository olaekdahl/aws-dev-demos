# m10 - API Gateway

REST API with request validation and WebSocket chat -- both deployed via SAM.

## SAM Apps

### REST API (request validation)

```bash
cd m10/sam-rest-api
sam build --use-container
sam deploy --guided
```

### WebSocket Chat

```bash
cd m10/sam-websocket-chat
sam build --use-container
sam deploy --guided
```

## Demos

| Name | Description |
|------|-------------|
| `test-rest` | Auto-discovers the deployed stack URL, sends valid/invalid requests, shows responses |

## Usage

```bash
# Test the REST API (after deploying sam-rest-api)
python m10/run.py --demo test-rest

# Cleanup -- use sam delete for each app
cd m10/sam-rest-api && sam delete
cd m10/sam-websocket-chat && sam delete
```

## AWS Services

- **API Gateway** -- REST API, WebSocket API
- **Lambda** -- request validation handler, WebSocket connect/disconnect/send handlers
- **DynamoDB** -- WebSocket connection tracking
