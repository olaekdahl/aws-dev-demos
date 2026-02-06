# m14 - CloudWatch Observability

Publish custom metrics, create alarms, run Logs Insights queries, and build dashboards programmatically.

## Demos

| Name | Description |
|------|-------------|
| `metrics` | Publishes increasing metric values, creates an alarm, waits for ALARM state, shows ASCII chart |
| `logs` | Creates a log group, writes structured JSON entries, runs Logs Insights queries |
| `dashboard` | Creates a CloudWatch dashboard programmatically, displays the console URL |

## Usage

```bash
# Run all demos
python m14/run.py

# Run a specific demo
python m14/run.py --demo metrics
python m14/run.py --demo logs
python m14/run.py --demo dashboard

# Clean up alarms, dashboards, and log groups
python m14/run.py --cleanup
```

## AWS Services

- **CloudWatch** -- PutMetricData, PutMetricAlarm, DescribeAlarms, PutDashboard
- **CloudWatch Logs** -- CreateLogGroup, PutLogEvents, StartQuery, GetQueryResults
