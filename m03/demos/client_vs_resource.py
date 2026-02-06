"""
Demo: Boto3 Client vs Resource API Comparison

Shows the difference between low-level client and high-level resource APIs
with a side-by-side timing comparison.
"""
import time
from common import create_session, banner, step, success, info, kv, table


def run(args):
    banner("m03", "Client vs Resource API Comparison")

    session = create_session(args.profile, args.region)

    # ── Step 1: Low-level Client API ──
    step(1, "Using the low-level Client API (s3.list_buckets)")

    info("client = session.client('s3')")
    info("response = client.list_buckets()")
    info("buckets = response['Buckets']  # raw dict from HTTP response\n")

    s3_client = session.client("s3")

    t0 = time.perf_counter()
    response = s3_client.list_buckets()
    client_time = time.perf_counter() - t0

    client_buckets = response.get("Buckets", [])
    kv("Buckets found", len(client_buckets))
    kv("Time", f"{client_time * 1000:.0f}ms")
    success("Client API returned raw dict with HTTP metadata")

    # ── Step 2: High-level Resource API ──
    step(2, "Using the high-level Resource API (s3.buckets.all)")

    info("s3 = session.resource('s3')")
    info("buckets = list(s3.buckets.all())  # returns OOP Bucket objects\n")

    s3_resource = session.resource("s3")

    t0 = time.perf_counter()
    resource_buckets = list(s3_resource.buckets.all())
    resource_time = time.perf_counter() - t0

    kv("Buckets found", len(resource_buckets))
    kv("Time", f"{resource_time * 1000:.0f}ms")
    success("Resource API returned Bucket objects with methods")

    # ── Step 3: Comparison ──
    step(3, "Comparison")

    table(
        ["Aspect", "Client (low-level)", "Resource (high-level)"],
        [
            ["Return type", "dict", "Python objects"],
            ["Bucket count", str(len(client_buckets)), str(len(resource_buckets))],
            ["Latency", f"{client_time * 1000:.0f}ms", f"{resource_time * 1000:.0f}ms"],
            ["New API support", "Always", "May lag behind"],
            ["Best for", "Fine-grained control", "OOP convenience"],
        ],
        col_width=22,
    )

    info("Tip: Use client for newest APIs and fine-grained control.")
    info("     Use resource for convenient object-oriented patterns.")
