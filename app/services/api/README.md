# API service

Node.js + Express + TypeScript.

## Endpoints (behind ALB)

- `GET /health`
- `GET /api/quizzes`
- `POST /api/quizzes`
- `GET /api/quizzes/:quizId`
- `POST /api/quizzes/:quizId/attempts` (enqueues grading job to SQS)
- `GET /api/attempts/:attemptId`
- `POST /api/quizzes/:quizId/exports` (enqueues export job to SQS, worker writes JSON to S3)
- `GET /api/exports/:exportId` (returns job status and (if complete) a short-lived presigned download URL)

## Observability

- Structured logs (JSON) to stdout → CloudWatch Logs in ECS.
- AWS X-Ray SDK instrumentation (can be disabled with `XRAY_DISABLED=true`).

