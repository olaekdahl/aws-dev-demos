"""Shared utilities for AWS dev demos."""
from common.config import DEFAULTS
from common.session import create_session
from common.naming import generate_name
from common.output import (
    banner, step, success, fail, info, warn, header, kv,
    json_print, table, progress_bar,
)
from common.cleanup import track_resource, get_tracked_resources, clear_tracked
from common.args import build_parser
