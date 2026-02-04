# m11 – EventBridge integration events (SAM)

Deploy:
```bash
sam build
sam deploy --guided
```

Send event:
```bash
python put_event.py --region us-east-1 --detail '{"orderId":"123"}'
```
