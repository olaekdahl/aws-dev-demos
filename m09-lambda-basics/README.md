# m09 – Lambda basics (zip deploy)

```bash
python build_zip.py
python deploy_zip_lambda.py --function-name awsdev-hello --role-arn arn:aws:iam::<acct>:role/<lambdaRole> --region us-east-1
python invoke.py --function-name awsdev-hello --payload '{"name":"Ola"}' --region us-east-1
```
