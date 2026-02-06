import time
import random
from datetime import datetime, timedelta, timezone
from common import (
    create_session, banner, step, success, info, warn, kv,
    generate_name, track_resource, table as print_table
)


def run(args):
    banner("m14", "CloudWatch Metrics & Alarms")
    session = create_session(args.profile, args.region)
    cw = session.client("cloudwatch")

    namespace = f"AwsDev/{args.prefix}"
    metric_name = "RequestLatency"
    alarm_name = generate_name("high-latency-alarm", args.prefix)

    # Step 1: Publish a series of metrics
    step(1, "Publishing custom metrics (simulated request latencies)")

    values = []
    now = datetime.now(timezone.utc)
    for i in range(10):
        # Simulate increasing latency (gradual degradation)
        base = 50 + (i * 20)
        value = base + random.randint(-10, 10)
        values.append(value)

        cw.put_metric_data(
            Namespace=namespace,
            MetricData=[{
                "MetricName": metric_name,
                "Timestamp": now - timedelta(minutes=10 - i),
                "Value": float(value),
                "Unit": "Milliseconds",
            }]
        )
        info(f"  t-{10-i:02d}min: {value}ms")

    success(f"Published 10 data points to {namespace}/{metric_name}")

    # Step 2: Display an ASCII chart of the values
    step(2, "Latency trend (ASCII chart)")

    max_val = max(values)
    chart_height = 10
    print()
    for row in range(chart_height, 0, -1):
        threshold = (row / chart_height) * max_val
        line = f"  {threshold:6.0f}ms |"
        for v in values:
            if v >= threshold:
                line += " ##"
            else:
                line += "   "
        print(line)
    print(f"         +{'---' * len(values)}")
    print(f"          " + "".join(f" {i:2d}" for i in range(len(values))))
    print(f"          (minutes ago, 0 = most recent)")
    print()

    # Step 3: Create an alarm
    step(3, "Creating CloudWatch alarm")
    threshold = 150.0

    cw.put_metric_alarm(
        AlarmName=alarm_name,
        Namespace=namespace,
        MetricName=metric_name,
        Statistic="Average",
        Period=60,
        EvaluationPeriods=1,
        Threshold=threshold,
        ComparisonOperator="GreaterThanThreshold",
        TreatMissingData="notBreaching",
        ActionsEnabled=False,  # No SNS notification for demo
    )
    track_resource("m14", "cloudwatch_alarm", alarm_name)

    kv("Alarm Name", alarm_name)
    kv("Threshold", f"Average > {threshold}ms")
    kv("Period", "60 seconds")
    success("Alarm created")

    # Step 4: Check alarm state
    step(4, "Checking alarm state")
    info("(Alarms take 1-2 minutes to evaluate. Showing current state.)")

    alarm = cw.describe_alarms(AlarmNames=[alarm_name])["MetricAlarms"]
    if alarm:
        state = alarm[0]["StateValue"]
        color = "\033[32m" if state == "OK" else "\033[31m" if state == "ALARM" else "\033[33m"
        kv("State", f"{color}{state}\033[0m")
        kv("Reason", alarm[0].get("StateReason", ""))

    # Step 5: Get metric statistics
    step(5, "Retrieving metric statistics")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=15)

    stats = cw.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Average", "Maximum", "Minimum"],
    )

    datapoints = sorted(stats.get("Datapoints", []), key=lambda x: x["Timestamp"])
    if datapoints:
        for dp in datapoints:
            kv(
                f"  {dp['Timestamp'].strftime('%H:%M')}",
                f"avg={dp.get('Average', 0):.0f}ms  max={dp.get('Maximum', 0):.0f}ms  min={dp.get('Minimum', 0):.0f}ms"
            )
    else:
        info("  (Metrics may take a few minutes to appear in statistics)")

    success("Metrics and alarm demo complete")
