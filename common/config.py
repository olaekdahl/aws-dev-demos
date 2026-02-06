"""Shared configuration defaults for all demos."""
import os

DEFAULTS = {
    "region": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    "prefix": os.environ.get("DEMO_PREFIX", "awsdev"),
    "profile": os.environ.get("AWS_PROFILE"),
}
