# m09 – Lambda event source (SQS) via SAM

Deploy:
```bash
sam build
sam deploy --guided
```

Send:
```bash
python send_messages.py --queue-url <url> --region us-east-1
```
