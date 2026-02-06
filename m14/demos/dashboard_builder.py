import json
from common import (
    create_session, banner, step, success, info, kv,
    generate_name, track_resource
)


def run(args):
    banner("m14", "CloudWatch Dashboard Builder")
    session = create_session(args.profile, args.region)
    cw = session.client("cloudwatch")

    dashboard_name = generate_name("demo-dashboard", args.prefix)
    namespace = f"AwsDev/{args.prefix}"

    # Step 1: Define dashboard widgets
    step(1, "Defining dashboard layout")

    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0, "y": 0, "width": 12, "height": 6,
                "properties": {
                    "title": "Request Latency",
                    "metrics": [
                        [namespace, "RequestLatency", {"stat": "Average", "period": 60}],
                        [namespace, "RequestLatency", {"stat": "p99", "period": 60}],
                    ],
                    "view": "timeSeries",
                    "region": args.region,
                },
            },
            {
                "type": "metric",
                "x": 12, "y": 0, "width": 12, "height": 6,
                "properties": {
                    "title": "Request Count",
                    "metrics": [
                        [namespace, "RequestLatency", {"stat": "SampleCount", "period": 60}],
                    ],
                    "view": "timeSeries",
                    "region": args.region,
                },
            },
            {
                "type": "text",
                "x": 0, "y": 6, "width": 24, "height": 2,
                "properties": {
                    "markdown": "## AWS Dev Demo Dashboard\nThis dashboard was created programmatically using the CloudWatch API."
                },
            },
            {
                "type": "alarm",
                "x": 0, "y": 8, "width": 12, "height": 6,
                "properties": {
                    "title": "Alarm Status",
                    "alarms": [],  # Will be populated if alarms exist
                },
            },
        ],
    }

    info("Layout:")
    info("  +------------+------------+")
    info("  | Latency    | Req Count  |")
    info("  | (avg/p99)  | (timeline) |")
    info("  +------------+------------+")
    info("  | Markdown text banner     |")
    info("  +--------------------------+")
    info("  | Alarm Status             |")
    info("  +--------------------------+")

    # Check for existing alarms to add to dashboard
    alarms = cw.describe_alarms(AlarmNamePrefix=args.prefix)["MetricAlarms"]
    if alarms:
        alarm_arns = [a["AlarmArn"] for a in alarms[:5]]
        dashboard_body["widgets"][3]["properties"]["alarms"] = alarm_arns
        info(f"\n  Found {len(alarms)} existing alarm(s) to include")

    # Step 2: Create the dashboard
    step(2, "Creating CloudWatch dashboard")

    cw.put_dashboard(
        DashboardName=dashboard_name,
        DashboardBody=json.dumps(dashboard_body),
    )
    track_resource("m14", "cloudwatch_dashboard", dashboard_name)

    kv("Dashboard Name", dashboard_name)
    console_url = f"https://{args.region}.console.aws.amazon.com/cloudwatch/home?region={args.region}#dashboards:name={dashboard_name}"
    kv("Console URL", console_url)
    success("Dashboard created - open the URL above in your browser")
