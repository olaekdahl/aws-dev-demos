"""Resource name generation with prefix + short UUID."""
import uuid
from common.config import DEFAULTS


def generate_name(suffix: str, prefix: str | None = None) -> str:
    """Generate a unique AWS resource name like 'awsdev-bucket-a1b2c3'."""
    prefix = prefix or DEFAULTS["prefix"]
    return f"{prefix}-{suffix}-{uuid.uuid4().hex[:6]}".lower()
