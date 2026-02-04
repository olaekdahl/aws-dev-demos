# m04 – IAM policy evaluation + AccessDenied debugging

Run safe read-only mode:
```bash
python explain_access_denied.py --profile yourProfile --region us-east-1
```

Optional (to demonstrate denied shape):
```bash
python simulate_access_denied.py --profile yourProfile --region us-east-1
```
