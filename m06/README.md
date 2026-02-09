# m06 - S3 Objects

S3 object operations: CRUD lifecycle, multipart uploads, event notifications, presigned URLs, and server-side encryption.

## Demos

| Name | Description |
|------|-------------|
| `object-crud` | Full object lifecycle -- put, head, get, list, delete |
| `multipart` | Multipart upload with ASCII progress bar |
| `event-pipeline` | Creates S3 + SQS, uploads a file, polls for the event notification |
| `presigned` | Generates presigned PUT/GET URLs, shows URL anatomy and expiration |
| `encryption` | Uploads same object with SSE-S3 and SSE-KMS, compares encryption headers |

## Usage

```bash
# Run all demos
python3 m06/run.py

# Run a specific demo
python3 m06/run.py --demo object-crud
python3 m06/run.py --demo multipart
python3 m06/run.py --demo event-pipeline
python3 m06/run.py --demo presigned
python3 m06/run.py --demo encryption

# Clean up created buckets and queues
python3 m06/run.py --cleanup
```

## AWS Services

- **S3** -- PutObject, GetObject, HeadObject, DeleteObject, CreateMultipartUpload, PresignedUrl
- **SQS** -- CreateQueue, ReceiveMessage (for event notifications)
- **KMS** -- server-side encryption with AWS managed keys
