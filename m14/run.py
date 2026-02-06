#!/usr/bin/env python3
"""m14 - CloudWatch Observability: metrics, alarms, logs, dashboards."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, success
from common.cleanup import get_tracked_resources, clear_tracked
from common.session import create_session

from demos.metrics_and_alarms import run as metrics_demo
from demos.log_insights import run as logs_demo
from demos.dashboard_builder import run as dashboard_demo

DEMOS = {
    "metrics": metrics_demo,
    "logs": logs_demo,
    "dashboard": dashboard_demo,
}
DEMO_INFO = {
    "metrics": "publish metrics, create alarms, visualize trends",
    "logs": "structured logging and Logs Insights queries",
    "dashboard": "build a CloudWatch dashboard programmatically",
}


def cleanup(args):
    resources = get_tracked_resources("m14")
    if not resources:
        info("No tracked resources to clean up.")
        return
    session = create_session(args.profile, args.region)
    cw = session.client("cloudwatch")
    logs = session.client("logs")
    for r in resources:
        try:
            if r["type"] == "cloudwatch_alarm":
                cw.delete_alarms(AlarmNames=[r["id"]])
                success(f"Deleted alarm: {r['id']}")
            elif r["type"] == "cloudwatch_dashboard":
                cw.delete_dashboards(DashboardNames=[r["id"]])
                success(f"Deleted dashboard: {r['id']}")
            elif r["type"] == "log_group":
                logs.delete_log_group(logGroupName=r["id"])
                success(f"Deleted log group: {r['id']}")
        except Exception as e:
            info(f"Could not delete {r['id']}: {e}")
    clear_tracked("m14")


def main():
    parser = build_parser("m14: CloudWatch Observability", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        cleanup(args)
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m14", "CloudWatch Observability")
        for fn in DEMOS.values():
            fn(args)


if __name__ == "__main__":
    main()
