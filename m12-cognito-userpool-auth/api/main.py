from __future__ import annotations
import os
import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

REGION = os.environ.get("COGNITO_REGION")
USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID")
APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

def jwks_url() -> str:
    if not (REGION and USERPOOL_ID):
        raise RuntimeError("Set COGNITO_REGION and COGNITO_USERPOOL_ID")
    return f"https://cognito-idp.{REGION}.amazonaws.com/{USERPOOL_ID}/.well-known/jwks.json"

def verify(token: str) -> dict:
    jwks = PyJWKClient(jwks_url())
    key = jwks.get_signing_key_from_jwt(token).key
    try:
        return jwt.decode(token, key, algorithms=["RS256"], audience=APP_CLIENT_ID, options={"verify_exp": True})
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/public")
def public():
    return {"ok": True}

@app.get("/private")
def private(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    claims = verify(authorization.split(" ", 1)[1].strip())
    return {"ok": True, "claims": claims}
