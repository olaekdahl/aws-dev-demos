# m08 - DynamoDB Advanced

Global Secondary Indexes, throughput management with exponential backoff, and TTL auto-expiring data.

## Demos

| Name | Description |
|------|-------------|
| `gsi` | Creates a table with a GSI, seeds data, shows how the GSI enables an alternate access pattern |
| `throughput` | Writes against a provisioned table with exponential backoff, shows real-time colored counters for successes/retries/throttles |
| `ttl` | Creates a table with TTL enabled, inserts items with various expiry times, polls to show items disappearing |

## Usage

Run all demos:
```bash
python3 m08/run.py
```

Run a specific demo:
```bash
python3 m08/run.py --demo gsi
```
```bash
python3 m08/run.py --demo throughput
```
```bash
python3 m08/run.py --demo ttl
```

Clean up created tables:
```bash
python3 m08/run.py --cleanup
```

## AWS Services

- **DynamoDB** -- CreateTable (with GSI, TTL, provisioned throughput), Query, Scan, UpdateTimeToLive
