# AWS Dev Class – Python Demos

This repo contains complete Python demos mapped to the module flow.

## AWS Services Used

| Icon | Service | Description |
|:----:|---------|-------------|
| <img src="icons/Simple-Storage-Service.svg" width="40"> | **Amazon S3** | Object storage for exports, artifacts, and file uploads |
| <img src="icons/DynamoDB.svg" width="40"> | **Amazon DynamoDB** | NoSQL database for quizzes, attempts, and exports |
| <img src="icons/Lambda.svg" width="40"> | **AWS Lambda** | Serverless compute for event-driven functions |
| <img src="icons/Simple-Queue-Service.svg" width="40"> | **Amazon SQS** | Message queuing for async job processing |
| <img src="icons/API-Gateway.svg" width="40"> | **Amazon API Gateway** | REST and WebSocket API management |
| <img src="icons/Elastic-Container-Service.svg" width="40"> | **Amazon ECS** | Container orchestration service |
| <img src="icons/Fargate.svg" width="40"> | **AWS Fargate** | Serverless compute for containers |
| <img src="icons/Elastic-Container-Registry.svg" width="40"> | **Amazon ECR** | Docker container registry |
| <img src="icons/Virtual-Private-Cloud.svg" width="40"> | **Amazon VPC** | Isolated cloud network |
| <img src="icons/Elastic-Load-Balancing.svg" width="40"> | **Elastic Load Balancing** | Application load balancer for traffic distribution |
| <img src="icons/Route-53.svg" width="40"> | **Amazon Route 53** | DNS and domain management |
| <img src="icons/Certificate-Manager.svg" width="40"> | **AWS Certificate Manager** | SSL/TLS certificate provisioning |
| <img src="icons/Identity-and-Access-Management.svg" width="40"> | **AWS IAM** | Identity and access management |
| <img src="icons/Cognito.svg" width="40"> | **Amazon Cognito** | User authentication and authorization |
| <img src="icons/CloudWatch.svg" width="40"> | **Amazon CloudWatch** | Monitoring, logging, and metrics |
| <img src="icons/X-Ray.svg" width="40"> | **AWS X-Ray** | Distributed tracing and debugging |
| <img src="icons/EventBridge.svg" width="40"> | **Amazon EventBridge** | Serverless event bus |
| <img src="icons/Step-Functions.svg" width="40"> | **AWS Step Functions** | Workflow orchestration |
| <img src="icons/CloudFormation.svg" width="40"> | **AWS CloudFormation** | Infrastructure as Code (SAM) |

## Prereqs

- Python 3.11+
- AWS CLI configured (or env vars set)
- An AWS account where you can create resources

## Setup

```bash
python3 -m venv .venv
# mac/linux
source .venv/bin/activate
# windows powershell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -e .
```

### Why `pip install -e .`?

Scripts in subdirectories (e.g., `m03-aws-auth-and-profiles/whoami.py`) import shared utilities from the `common/` package at the project root. By default, Python can't resolve these imports when running scripts from subdirectories.

Installing the project in **editable mode** (`-e`) registers the `common` package in your virtual environment, making it importable from anywhere. "Editable" means changes to the `common/` code take effect immediately—no reinstall needed.

## Safety

Many scripts create AWS resources. Most deletes require `--yes`.

Generated: 2026-02-03
