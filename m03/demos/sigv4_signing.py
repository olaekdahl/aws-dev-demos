"""
Demo: SigV4 Signing - Under the Hood

Manually signs an HTTP request to S3 using AWS Signature Version 4,
showing each cryptographic step visually.
"""
import datetime as dt
import hashlib
import hmac

import requests
from botocore.credentials import ReadOnlyCredentials
from botocore.session import Session as BotocoreSession

from common import banner, step, success, info, kv, header


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def run(args):
    banner("m03", "SigV4 Signing - Under the Hood")

    # ── Step 1: Get credentials ──
    step(1, "Resolving AWS credentials")

    bc = BotocoreSession()
    if args.profile:
        bc.set_config_variable("profile", args.profile)
    region = args.region
    bc.set_config_variable("region", region)

    creds = bc.get_credentials()
    frozen: ReadOnlyCredentials = creds.get_frozen_credentials()

    kv("Access Key", frozen.access_key[:8] + "..." + frozen.access_key[-4:])
    kv("Has Session Token", "yes" if frozen.token else "no")
    success("Credentials resolved")

    # ── Step 2: Build canonical request ──
    step(2, "Building the Canonical Request")

    method = "GET"
    service = "s3"
    host = "s3.amazonaws.com"
    endpoint = f"https://{host}/"

    t = dt.datetime.utcnow()
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(b"").hexdigest()

    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join([
        method,                              # HTTP method
        "/",                                 # Canonical URI
        "",                                  # Canonical query string (empty)
        f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n",
        signed_headers,                      # Signed headers
        payload_hash,                        # Hash of payload
    ])

    info("Canonical request components:")
    kv("  HTTP Method", method)
    kv("  URI", "/")
    kv("  Query String", "(empty)")
    kv("  Headers", f"host:{host}, x-amz-content-sha256:..., x-amz-date:{amz_date}")
    kv("  Payload Hash", payload_hash[:32] + "...")
    kv("  Request Hash", hashlib.sha256(canonical_request.encode()).hexdigest()[:32] + "...")

    # ── Step 3: Build string to sign ──
    step(3, "Creating the String to Sign")

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    request_hash = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()

    string_to_sign = "\n".join([algorithm, amz_date, credential_scope, request_hash])

    kv("Algorithm", algorithm)
    kv("Timestamp", amz_date)
    kv("Credential Scope", credential_scope)
    kv("Request Hash", request_hash[:32] + "...")

    # ── Step 4: Derive signing key ──
    step(4, "Deriving the Signing Key (4-step HMAC chain)")

    info("kDate    = HMAC-SHA256('AWS4' + SecretKey, date)")
    info("kRegion  = HMAC-SHA256(kDate, region)")
    info("kService = HMAC-SHA256(kRegion, service)")
    info("kSigning = HMAC-SHA256(kService, 'aws4_request')")

    signing_key = _get_signature_key(frozen.secret_key, date_stamp, region, service)
    kv("\n  Signing Key", signing_key.hex()[:32] + "...")

    # ── Step 5: Calculate signature ──
    step(5, "Calculating the final signature")

    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    kv("Signature", signature)

    auth_header = (
        f"{algorithm} Credential={frozen.access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    info(f"\nAuthorization header:")
    info(f"  {auth_header[:80]}...")

    # ── Step 6: Make the request ──
    step(6, "Sending the signed request to S3")

    headers = {
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": auth_header,
    }
    if frozen.token:
        headers["x-amz-security-token"] = frozen.token

    kv("Endpoint", endpoint)
    response = requests.get(endpoint, headers=headers, timeout=30)

    kv("Status", f"{response.status_code} {response.reason}")

    if response.status_code == 200:
        # Count buckets in XML response
        count = response.text.count("<Bucket>")
        success(f"Received XML response with {count} bucket(s)")
        info("(Response is XML because we called the REST API directly)")
    else:
        info(f"Response: {response.text[:500]}")
