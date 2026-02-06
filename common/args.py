"""Shared argument parser for all module run.py entry points."""
import argparse
from common.config import DEFAULTS


def build_parser(module_description: str, demos: dict | None = None) -> argparse.ArgumentParser:
    """Build a standard argument parser for a module run.py.

    Args:
        module_description: Short description shown in --help.
        demos: Optional dict of {name: description} for the --demo choices help text.
    """
    parser = argparse.ArgumentParser(description=module_description)

    if demos:
        names = list(demos.keys())
        help_lines = ", ".join(f"{k} ({v})" for k, v in demos.items())
        parser.add_argument(
            "--demo",
            choices=names,
            help=f"Run a specific demo: {help_lines}",
        )
    else:
        parser.add_argument("--demo", help="Run a specific demo by name")

    parser.add_argument("--cleanup", action="store_true", help="Tear down all tracked resources")
    parser.add_argument("--profile", default=DEFAULTS["profile"], help="AWS CLI profile")
    parser.add_argument("--region", default=DEFAULTS["region"], help="AWS region (default: %(default)s)")
    parser.add_argument("--prefix", default=DEFAULTS["prefix"], help="Resource name prefix (default: %(default)s)")
    return parser
