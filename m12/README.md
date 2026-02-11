# m12 - Cognito Auth

Automated Cognito User Pool setup, sign-up/sign-in flow with JWT decoding, and token refresh.

## Demos

| Name | Description |
|------|-------------|
| `signup-signin` | Creates a User Pool + App Client, registers a test user, signs in, decodes JWT claims |
| `token-refresh` | Signs in, uses the refresh token to get new tokens, compares old/new claims |

## Usage

Run all demos:
```bash
python3 m12/run.py
```

Run a specific demo:
```bash
python3 m12/run.py --demo signup-signin
```
```bash
python3 m12/run.py --demo token-refresh
```

Clean up created User Pools:
```bash
python3 m12/run.py --cleanup
```

## FastAPI App

After running the signup-signin demo, you can start the FastAPI app:

```bash
# Set the env vars shown during the demo output, then:
uvicorn m12.api.main:app --reload
```

### Getting a Token

The demo output truncates tokens. To get the full ID token for testing:

```bash
# Replace CLIENT_ID with the App Client ID from the demo output
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id <CLIENT_ID> \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=demo@example.com,PASSWORD=DemoPass1! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/private
```

> **Note:** Use `IdToken` (not `AccessToken`) because the FastAPI app validates the `aud` claim, which only exists in ID tokens.

## AWS Services

- **Cognito** -- CreateUserPool, CreateUserPoolClient, AdminCreateUser, AdminSetUserPassword, InitiateAuth
