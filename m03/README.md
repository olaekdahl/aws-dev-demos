# m03 - Identity & Auth

Explore the AWS credential chain, compare boto3's client vs resource APIs, and manually sign an HTTP request with SigV4.

## Demos

| Name | Description |
|------|-------------|
| `whoami` | Credential chain explorer -- shows env vars, config files, profiles, and calls STS GetCallerIdentity |
| `client-vs-resource` | Side-by-side timing comparison of boto3 client vs resource APIs |
| `sigv4` | Manually signs an S3 request using AWS Signature Version 4, showing each cryptographic step |

## Usage

Run all demos:
```bash
python3 m03/run.py
```

Run a specific demo:
```bash
python3 m03/run.py --demo whoami
```
```bash
python3 m03/run.py --demo client-vs-resource
```
```bash
python3 m03/run.py --demo sigv4
```

## AWS Services

- **STS** -- GetCallerIdentity
- **S3** -- ListBuckets (via client, resource, and raw REST)

## Notes

- All demos are read-only -- no resources are created
- No cleanup needed
