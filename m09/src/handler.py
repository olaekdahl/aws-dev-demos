"""Word frequency analyzer Lambda handler."""
from __future__ import annotations
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone


def handler(event, context):
    """Analyze word frequency in text. Accepts {"text": "..."} payload."""
    text = event.get(
        "text",
        "The quick brown fox jumps over the lazy dog. The fox was very quick.",
    )

    # Normalize and split
    words = re.findall(r"\b[a-z]+\b", text.lower())
    counter = Counter(words)
    top_10 = counter.most_common(10)

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({
            "total_words": len(words),
            "unique_words": len(counter),
            "top_10": [{"word": w, "count": c} for w, c in top_10],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "env": {"DEMO": os.getenv("DEMO")},
        }),
    }
