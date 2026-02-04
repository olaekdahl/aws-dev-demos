# m12 – Cognito User Pool auth + JWT validation (FastAPI)

See `cognito_setup.md`, then run the API locally:

```bash
cd api
pip install -r requirements.txt
set COGNITO_REGION=us-east-1
set COGNITO_USERPOOL_ID=...
set COGNITO_APP_CLIENT_ID=...
uvicorn main:app --reload --port 8000
```
