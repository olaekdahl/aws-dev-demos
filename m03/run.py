#!/usr/bin/env python3
"""m03 - Identity & Auth: credential chain, client vs resource, SigV4 signing."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from common.args import build_parser
from common.output import banner

from demos.whoami import run as whoami_demo
from demos.client_vs_resource import run as client_vs_resource_demo
from demos.sigv4_signing import run as sigv4_demo

DEMOS = {
    "whoami": whoami_demo,
    "client-vs-resource": client_vs_resource_demo,
    "sigv4": sigv4_demo,
}

DEMO_INFO = {
    "whoami": "credential chain explorer",
    "client-vs-resource": "client vs resource API comparison",
    "sigv4": "SigV4 signing under the hood",
}


def main():
    parser = build_parser("m03: Identity & Auth", DEMO_INFO)
    args = parser.parse_args()

    if args.cleanup:
        print("m03 demos are read-only -- nothing to clean up.")
        return

    if args.demo:
        DEMOS[args.demo](args)
    else:
        banner("m03", "Identity & Auth")
        for name, fn in DEMOS.items():
            fn(args)


if __name__ == "__main__":
    main()
