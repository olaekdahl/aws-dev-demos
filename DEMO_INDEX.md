# Demo Index

## Quick Reference

| Module | Topic | Demos | Cleanup |
|--------|-------|-------|---------|
| [m03](m03/) | Identity & Auth | `whoami` `client-vs-resource` `sigv4` | N/A (read-only) |
| [m04](m04/) | IAM | `assume-role` `detective` `policy-simulator` | `--cleanup` |
| [m05](m05/) | S3 Buckets | `lifecycle` `time-travel` | `--cleanup` |
| [m06](m06/) | S3 Objects | `object-crud` `multipart` `event-pipeline` `presigned` `encryption` | `--cleanup` |
| [m07](m07/) | DynamoDB CRUD | `leaderboard` `conditional` | `--cleanup` |
| [m08](m08/) | DynamoDB Advanced | `gsi` `throughput` `ttl` | `--cleanup` |
| [m09](m09/) | Lambda | `deploy` `cold-start` `errors` | `--cleanup` |
| [m10](m10/) | API Gateway | `test-rest` + SAM apps | `sam delete` |
| [m11](m11/) | Async Patterns | `fanout` `dlq` `fifo` + SAM EventBridge | `--cleanup` / `sam delete` |
| [m12](m12/) | Cognito | `signup-signin` `token-refresh` | `--cleanup` |
| [m13](m13/) | SAM Serverless | URL shortener (SAM app + `test`) | `sam delete` |
| [m14](m14/) | CloudWatch | `metrics` `logs` `dashboard` | `--cleanup` |
| [m15](m15/) | Capstone | Pipeline (SAM app + `test`) | `sam delete` |

## Running Demos

```bash
# Run all demos in a module
python m03/run.py

# Run a specific demo
python m07/run.py --demo leaderboard

# Clean up resources created by a module
python m05/run.py --cleanup

# Use a specific AWS profile and region
python m04/run.py --profile dev --region eu-west-1
```

## SAM Apps

Modules with SAM templates need to be built and deployed separately:

```bash
# Build (use --use-container if local Python != Lambda runtime)
cd m15 && sam build --use-container

# Deploy
sam deploy --guided

# Cleanup
sam delete
```

SAM apps: `m09/sam-event-source`, `m10/sam-rest-api`, `m10/sam-websocket-chat`, `m11/sam-eventbridge`, `m13`, `m15`

## Old-to-New Directory Mapping

| Old Directory | New Location |
|---------------|-------------|
| `m03-aws-auth-and-profiles/` | `m03/demos/whoami.py` |
| `m03-boto3-high-vs-low-s3/` | `m03/demos/client_vs_resource.py` |
| `m03-raw-s3-rest-call/` | `m03/demos/sigv4_signing.py` |
| `m04-assume-role-demo/` | `m04/demos/assume_role.py` |
| `m04-iam-policy-evaluation-debug/` | `m04/demos/access_denied_detective.py`, `m04/demos/policy_simulator.py` |
| `m05-s3-buckets-ops/` | `m05/demos/bucket_lifecycle.py`, `m05/demos/versioning_time_travel.py` |
| `m06-s3-objects-ops/` | `m06/demos/object_crud.py` |
| `m06-s3-multipart-upload/` | `m06/demos/multipart_upload.py` |
| `m06-s3-events-to-sqs/` | `m06/demos/event_pipeline.py` |
| `m07-dynamodb-crud-basics/` | `m07/demos/gaming_leaderboard.py`, `m07/demos/conditional_writes.py` |
| `m08-dynamodb-indexes-design/` | `m08/demos/gsi_access_patterns.py` |
| `m08-dynamodb-throughput-and-waiters/` | `m08/demos/throughput_retry.py`, `m08/demos/ttl_expiring_data.py` |
| `m09-lambda-basics/` | `m09/demos/deploy_and_invoke.py`, `m09/demos/cold_start_measurement.py`, `m09/demos/error_handling.py` |
| `m09-lambda-event-sources/` | `m09/sam-event-source/` |
| `m10-apigw-rest-lambda/` | `m10/sam-rest-api/` |
| `m10-apigw-websocket-chat/` | `m10/sam-websocket-chat/` |
| `m11-async-microservice-patterns/` | `m11/demos/fanout_pattern.py`, `m11/demos/dlq_recovery.py`, `m11/demos/fifo_ordering.py` |
| `m11-eventbridge-integration-events/` | `m11/sam-eventbridge/` |
| `m12-cognito-userpool-auth/` | `m12/demos/signup_signin_flow.py`, `m12/demos/token_refresh.py` |
| `m13-sam-serverless-app/` | `m13/` (URL shortener) |
| `m14-cloudwatch-observability/` | `m14/demos/metrics_and_alarms.py`, `m14/demos/log_insights.py`, `m14/demos/dashboard_builder.py` |
| `m15-end-to-end-capstone/` | `m15/` |
