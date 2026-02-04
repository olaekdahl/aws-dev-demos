# m10 – API Gateway WebSocket chat (SAM)

Deploy:
```bash
sam build
sam deploy --guided
```

Send this JSON over the socket:
```json
{"action":"sendMessage","message":"hello"}
```
