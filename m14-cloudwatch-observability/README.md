# m14 – CloudWatch metrics + alarms

```bash
python put_metric.py --namespace AwsDev/Demo --metric DemoCounter --value 1 --region us-east-1
python get_metric.py --namespace AwsDev/Demo --metric DemoCounter --region us-east-1
python create_alarm.py --namespace AwsDev/Demo --metric DemoCounter --alarm-name AwsDevDemoAlarm --region us-east-1
```
