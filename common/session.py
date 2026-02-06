"""Session factory with smart defaults."""
import boto3
from common.config import DEFAULTS


def create_session(profile=None, region=None):
    """Create a boto3 session with fallback to shared defaults."""
    return boto3.Session(
        profile_name=profile or DEFAULTS["profile"],
        region_name=region or DEFAULTS["region"],
    )
