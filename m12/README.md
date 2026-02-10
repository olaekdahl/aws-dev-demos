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

## AWS Services

- **Cognito** -- CreateUserPool, CreateUserPoolClient, AdminCreateUser, AdminSetUserPassword, InitiateAuth
