# m14 - CloudWatch Observability

Publish custom metrics, create alarms, run Logs Insights queries, and build dashboards programmatically.

## Demos

| Name | Description |
|------|-------------|
| `metrics` | Publishes increasing metric values, creates an alarm, waits for ALARM state, shows ASCII chart |
| `logs` | Creates a log group, writes structured JSON entries, runs Logs Insights queries |
| `dashboard` | Creates a CloudWatch dashboard programmatically, displays the console URL |

## Usage

Run all demos:
```bash
python3 m14/run.py
```

Run a specific demo:
```bash
python3 m14/run.py --demo metrics
```
```bash
python3 m14/run.py --demo logs
```
```bash
python3 m14/run.py --demo dashboard
```

Clean up alarms, dashboards, and log groups:
```bash
python3 m14/run.py --cleanup
```

## AWS Services

- **CloudWatch** -- PutMetricData, PutMetricAlarm, DescribeAlarms, PutDashboard
- **CloudWatch Logs** -- CreateLogGroup, PutLogEvents, StartQuery, GetQueryResults
