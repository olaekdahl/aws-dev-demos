# m05 - S3 Buckets

Create S3 buckets with lifecycle policies and explore versioning with time-travel recovery.

## Demos

| Name | Description |
|------|-------------|
| `lifecycle` | Creates a versioned bucket, sets lifecycle rules (Glacier transition, expiration), displays visual timeline |
| `time-travel` | Uploads multiple versions of the same key, retrieves each version, deletes and recovers via delete marker removal |

## Usage

```bash
# Run all demos
python3 m05/run.py

# Run a specific demo
python3 m05/run.py --demo lifecycle
python3 m05/run.py --demo time-travel

# Clean up created buckets
python3 m05/run.py --cleanup
```

## AWS Services

- **S3** -- CreateBucket, PutBucketVersioning, PutBucketLifecycleConfiguration, PutObject, GetObject, ListObjectVersions, DeleteObject
