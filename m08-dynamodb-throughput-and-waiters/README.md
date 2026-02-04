# m08 – DynamoDB throughput + retry

```bash
python create_provisioned_table.py --region us-east-1 --prefix awsdev
python write_with_retry.py --table <table>
python cleanup.py --table <table> --yes
```
