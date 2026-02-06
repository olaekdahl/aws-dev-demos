# AWS Dev Class – Python Demos

Hands-on Python demos for AWS services, organized by module. Each module is self-contained with smart defaults — no required CLI parameters.

## AWS Services Used

| Icon | Service | Description |
|:----:|---------|-------------|
| <img src="icons/Identity-and-Access-Management.svg" width="40"> | **AWS IAM** | Identity and access management |
| <img src="icons/Simple-Storage-Service.svg" width="40"> | **Amazon S3** | Object storage for exports, artifacts, and file uploads |
| <img src="icons/DynamoDB.svg" width="40"> | **Amazon DynamoDB** | NoSQL database for quizzes, attempts, and exports |
| <img src="icons/Lambda.svg" width="40"> | **AWS Lambda** | Serverless compute for event-driven functions |
| <img src="icons/API-Gateway.svg" width="40"> | **Amazon API Gateway** | REST and WebSocket API management |
| <img src="icons/Simple-Queue-Service.svg" width="40"> | **Amazon SQS** | Message queuing for async job processing |
| <img src="icons/EventBridge.svg" width="40"> | **Amazon EventBridge** | Serverless event bus |
| <img src="icons/Cognito.svg" width="40"> | **Amazon Cognito** | User authentication and authorization |
| <img src="icons/CloudWatch.svg" width="40"> | **Amazon CloudWatch** | Monitoring, logging, and metrics |
| <img src="icons/CloudFormation.svg" width="40"> | **AWS CloudFormation** | Infrastructure as Code (SAM) |
| <img src="icons/Elastic-Container-Service.svg" width="40"> | **Amazon ECS** | Container orchestration service |
| <img src="icons/Fargate.svg" width="40"> | **AWS Fargate** | Serverless compute for containers |
| <img src="icons/Elastic-Container-Registry.svg" width="40"> | **Amazon ECR** | Docker container registry |
| <img src="icons/Virtual-Private-Cloud.svg" width="40"> | **Amazon VPC** | Isolated cloud network |
| <img src="icons/Elastic-Load-Balancing.svg" width="40"> | **Elastic Load Balancing** | Application load balancer for traffic distribution |
| <img src="icons/Route-53.svg" width="40"> | **Amazon Route 53** | DNS and domain management |
| <img src="icons/Certificate-Manager.svg" width="40"> | **AWS Certificate Manager** | SSL/TLS certificate provisioning |
| <img src="icons/X-Ray.svg" width="40"> | **AWS X-Ray** | Distributed tracing and debugging |
| <img src="icons/Step-Functions.svg" width="40"> | **AWS Step Functions** | Workflow orchestration |

## Modules

| Module | Topic | Demos |
|--------|-------|-------|
| **m03** | Identity & Auth | `whoami` · `client-vs-resource` · `sigv4` |
| **m04** | IAM | `assume-role` · `access-denied` · `policy-sim` |
| **m05** | S3 Buckets | `lifecycle` · `versioning` |
| **m06** | S3 Objects | `crud` · `multipart` · `events` · `presigned` · `encryption` |
| **m07** | DynamoDB CRUD | `leaderboard` · `conditional-writes` |
| **m08** | DynamoDB Advanced | `gsi` · `throughput` · `ttl` |
| **m09** | Lambda | `deploy` · `cold-start` · `errors` |
| **m10** | API Gateway | `test-rest` · SAM REST API · SAM WebSocket chat |
| **m11** | Async Patterns | `fanout` · `dlq` · `fifo` · SAM EventBridge |
| **m12** | Cognito | `signup-signin` · `token-refresh` |
| **m13** | SAM Serverless | URL shortener (`shorten` · `redirect` · `stats`) |
| **m14** | CloudWatch | `metrics` · `log-insights` · `dashboard` |
| **m15** | Capstone | End-to-end S3 → SQS → Lambda pipeline |

## Quickstart

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # mac/linux
# .\.venv\Scripts\Activate.ps1   # windows powershell

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Run any module
python m03/run.py                # run all m03 demos
python m07/run.py --demo leaderboard   # run a specific demo
python m05/run.py --cleanup      # tear down tracked resources
```

### CLI Options (all optional)

| Flag | Default | Description |
|------|---------|-------------|
| `--demo NAME` | *(all)* | Run a specific demo by name |
| `--cleanup` | — | Delete all tracked resources for this module |
| `--profile NAME` | `$AWS_PROFILE` | AWS profile to use |
| `--region NAME` | `us-east-1` | AWS region |
| `--prefix NAME` | `awsdev` | Prefix for auto-generated resource names |

### Why `pip install -e .`?

Scripts in subdirectories import shared utilities from the `common/` package at the project root. Installing in **editable mode** (`-e`) registers the `common` package so it's importable from anywhere. Changes take effect immediately — no reinstall needed.

## Safety

- Demos that create AWS resources track them automatically for cleanup
- Run `python mXX/run.py --cleanup` to tear down resources for any module
- Resource names are auto-generated with a random suffix to avoid conflicts
