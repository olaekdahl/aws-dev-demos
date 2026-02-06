# m13 - SAM Serverless (URL Shortener)

A complete URL shortener deployed with SAM: create short links, follow redirects, and view click stats.

## Deploy

```bash
cd m13
sam build --use-container
sam deploy --guided
```

## Demos

| Name | Description |
|------|-------------|
| `test` | Creates short URLs, follows redirects, checks click stats against the deployed API |

## Usage

```bash
# Test the deployed shortener
python m13/run.py --demo test

# Cleanup
cd m13 && sam delete
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/shorten` | Create a short URL (body: `{"url": "https://..."}`) |
| GET | `/{code}` | Redirect to the original URL (301) |
| GET | `/stats/{code}` | View click count and metadata |

## AWS Services

- **API Gateway** -- REST API
- **Lambda** -- shorten, redirect, stats handlers
- **DynamoDB** -- link storage with TTL for auto-expiring links
