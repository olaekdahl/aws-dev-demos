#!/usr/bin/env python3
"""m13 - SAM Serverless: URL Shortener application."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, header

from demos.test_shortener import run as test_demo

DEMOS = {"test": test_demo}
DEMO_INFO = {"test": "integration test against deployed URL shortener"}


def main():
    parser = build_parser("m13: SAM Serverless - URL Shortener", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        info("SAM-deployed stacks should be cleaned up with: sam delete")
        info("  cd m13 && sam delete")
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m13", "SAM Serverless - URL Shortener")
        header("Deploy:")
        info("  cd m13 && sam build && sam deploy --guided")
        header("\nTest:")
        test_demo(args)


if __name__ == "__main__":
    main()
