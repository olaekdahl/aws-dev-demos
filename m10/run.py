#!/usr/bin/env python3
"""m10 - API Gateway: REST API validation and WebSocket chat via SAM."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, header

from demos.test_rest_api import run as test_rest_demo

DEMOS = {
    "test-rest": test_rest_demo,
}

DEMO_INFO = {
    "test-rest": "test the deployed REST API validation endpoint",
}


def main():
    parser = build_parser("m10: API Gateway", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        info("SAM-deployed stacks should be cleaned up with: sam delete")
        info("  cd m10/sam-rest-api && sam delete")
        info("  cd m10/sam-websocket-chat && sam delete")
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m10", "API Gateway")
        header("SAM Apps (deploy separately):")
        info("  REST API:       cd m10/sam-rest-api && sam build && sam deploy --guided")
        info("  WebSocket Chat: cd m10/sam-websocket-chat && sam build && sam deploy --guided")
        header("\nScript-based demos:")
        for fn in DEMOS.values():
            fn(args)


if __name__ == "__main__":
    main()
