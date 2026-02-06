#!/usr/bin/env python3
"""m15 - End-to-End Capstone: production-ready event pipeline."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner, info, header

from demos.test_capstone import run as test_demo

DEMOS = {"test": test_demo}
DEMO_INFO = {"test": "end-to-end integration test"}


def main():
    parser = build_parser("m15: End-to-End Capstone", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        info("SAM-deployed stacks should be cleaned up with: sam delete")
        info("  cd m15 && sam delete")
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m15", "End-to-End Capstone")
        header("Deploy:")
        info("  cd m15 && sam build && sam deploy --guided")
        header("\nTest:")
        test_demo(args)


if __name__ == "__main__":
    main()
