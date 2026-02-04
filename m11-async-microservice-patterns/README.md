# m11 – Async microservice patterns (SNS -> SQS fanout)

```bash
python create_infra.py --region us-east-1 --prefix awsdev
python publish.py --topic-arn <arn> --region us-east-1 --count 5
python consume.py --queue-url <queue1Url> --region us-east-1
python consume.py --queue-url <queue2Url> --region us-east-1
python cleanup.py --topic-arn <arn> --queue-urls <q1> <q2> --region us-east-1 --yes
```
