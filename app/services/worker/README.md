# Worker service

Background worker (Node.js + TypeScript) consuming SQS jobs.

## Jobs

- `GRADE_ATTEMPT` — reads quiz + attempt from DynamoDB, computes score, updates attempt status
- `EXPORT_QUIZ` — exports quiz JSON to S3 and updates export job in DynamoDB

## Observability

- Structured logs to stdout → CloudWatch Logs.
- AWS X-Ray daemon sidecar + SDK in worker process (can be disabled with `XRAY_DISABLED=true`).

