import json
import time
import base64
from common import create_session, banner, step, success, fail, info, warn, kv, json_print, generate_name, track_resource

def run(args):
    banner("m12", "Cognito Sign-Up & Sign-In Flow")
    session = create_session(args.profile, args.region)
    cognito = session.client("cognito-idp")

    # Step 1: Create User Pool
    step(1, "Creating Cognito User Pool")
    pool_name = generate_name("demo-pool", args.prefix)
    pool = cognito.create_user_pool(
        PoolName=pool_name,
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": False,
            }
        },
        AutoVerifiedAttributes=["email"],
        Schema=[
            {"Name": "email", "Required": True, "Mutable": True, "AttributeDataType": "String"},
        ],
    )
    pool_id = pool["UserPool"]["Id"]
    track_resource("m12", "cognito_user_pool", pool_id)
    kv("User Pool ID", pool_id)
    success("User Pool created")

    # Step 2: Create App Client (no secret for public client)
    step(2, "Creating App Client")
    client = cognito.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName="demo-app-client",
        ExplicitAuthFlows=[
            "ALLOW_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
        ],
        GenerateSecret=False,
    )
    client_id = client["UserPoolClient"]["ClientId"]
    kv("App Client ID", client_id)
    success("App Client created")

    # Step 3: Create test user
    step(3, "Creating test user")
    test_email = "demo@example.com"
    test_password = "DemoPass1!"
    cognito.admin_create_user(
        UserPoolId=pool_id,
        Username=test_email,
        UserAttributes=[
            {"Name": "email", "Value": test_email},
            {"Name": "email_verified", "Value": "true"},
        ],
        TemporaryPassword=test_password,
        MessageAction="SUPPRESS",
    )
    # Set permanent password
    cognito.admin_set_user_password(
        UserPoolId=pool_id,
        Username=test_email,
        Password=test_password,
        Permanent=True,
    )
    kv("Username", test_email)
    kv("Password", test_password)
    success("Test user created and confirmed")

    # Step 4: Sign in
    step(4, "Signing in with USER_PASSWORD_AUTH")
    auth = cognito.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": test_email,
            "PASSWORD": test_password,
        },
    )
    tokens = auth["AuthenticationResult"]
    kv("Access Token", tokens["AccessToken"][:50] + "...")
    kv("ID Token", tokens["IdToken"][:50] + "...")
    kv("Refresh Token", tokens["RefreshToken"][:50] + "...")
    kv("Expires In", f"{tokens['ExpiresIn']}s")
    success("Authentication successful")

    # Step 5: Decode the ID token (without verification, just to show claims)
    step(5, "Decoding JWT claims (ID Token)")
    # Split token and decode payload (middle part)
    payload_b64 = tokens["IdToken"].split(".")[1]
    # Add padding
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    claims = json.loads(base64.b64decode(payload_b64))

    info("Token claims:")
    for key in ["sub", "email", "email_verified", "iss", "aud", "token_use", "auth_time", "exp"]:
        if key in claims:
            kv(f"  {key}", claims[key])

    success("JWT decoded successfully")

    # Step 6: Show how to use with the FastAPI app
    step(6, "Usage with FastAPI /private endpoint")
    info("To test with the FastAPI app:")
    info(f"  export COGNITO_REGION={args.region}")
    info(f"  export COGNITO_USERPOOL_ID={pool_id}")
    info(f"  export COGNITO_APP_CLIENT_ID={client_id}")
    info(f"  uvicorn m12.api.main:app --reload")
    info(f"")
    info(f'  curl -H "Authorization: Bearer {tokens["AccessToken"][:30]}..." http://localhost:8000/private')
