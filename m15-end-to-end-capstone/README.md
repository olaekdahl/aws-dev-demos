# m15 – End-to-end capstone (SAM)

Deploy:
```bash
sam build
sam deploy --guided
```

Test:
```bash
python upload.py --bucket <bucket> --key demo.txt --text "hello" --region us-east-1
python call_api.py --url https://.../Prod/items/demo.txt
```
