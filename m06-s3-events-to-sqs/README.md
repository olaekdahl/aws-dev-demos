# m06 – S3 events to SQS

```bash
python create_infra.py --region us-east-1 --prefix awsdev
python put_object.py --bucket <bucket> --key test.txt --text "hello"
python consume_and_fetch.py --queue-url <queueUrl> --region us-east-1
python cleanup.py --bucket <bucket> --queue-url <queueUrl> --yes
```
