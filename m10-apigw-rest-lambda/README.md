# m10 – API Gateway REST + Lambda (SAM)

Deploy:
```bash
sam build
sam deploy --guided
```

Test:
```bash
python call_api.py --url https://<id>.execute-api.<region>.amazonaws.com/Prod/hello?name=Ola
```
