# Code Quiz: AWS ECS Example (React + Node.js + TypeScript)

This repository reference implementation for a simple **quiz platform** deployed on **AWS ECS (Fargate)** behind an **Application Load Balancer (ALB)** with **Route 53**, **DynamoDB**, **S3**, **SQS**, **CloudWatch Logs/Metrics**, and **AWS X-Ray** tracing.

It is designed to be:

- **Multi-AZ / redundant** (ALB + ECS services across private subnets in at least 2 AZs)
- **Observable** (structured logs to CloudWatch, embedded custom metrics, X-Ray tracing via daemon sidecar)
- **Secure by default** (private subnets for tasks, least-privilege IAM roles, S3 block public access)
- **CI/CD ready** (GitHub Actions pipeline using AWS OIDC to build/push images and run Terraform)

---

## AWS Services Used

| Icon | Service | Purpose |
|:----:|---------|---------|
| <img src="../icons/Elastic-Container-Service.svg" width="40"> | **Amazon ECS** | Container orchestration for api, web, and worker services |
| <img src="../icons/Fargate.svg" width="40"> | **AWS Fargate** | Serverless compute engine for containers |
| <img src="../icons/Elastic-Container-Registry.svg" width="40"> | **Amazon ECR** | Private Docker container registry |
| <img src="../icons/Elastic-Load-Balancing.svg" width="40"> | **Application Load Balancer** | HTTPS traffic distribution to ECS services |
| <img src="../icons/Virtual-Private-Cloud.svg" width="40"> | **Amazon VPC** | Isolated network with public/private subnets across 2 AZs |
| <img src="../icons/Route-53.svg" width="40"> | **Amazon Route 53** | DNS management for `code-quiz.io` domain |
| <img src="../icons/Certificate-Manager.svg" width="40"> | **AWS Certificate Manager** | SSL/TLS certificates for HTTPS |
| <img src="../icons/DynamoDB.svg" width="40"> | **Amazon DynamoDB** | NoSQL database for quizzes, attempts, and exports |
| <img src="../icons/Simple-Storage-Service.svg" width="40"> | **Amazon S3** | Object storage for quiz exports and ALB access logs |
| <img src="../icons/Simple-Queue-Service.svg" width="40"> | **Amazon SQS** | Message queue for async grading and export jobs |
| <img src="../icons/Identity-and-Access-Management.svg" width="40"> | **AWS IAM** | Least-privilege task roles and GitHub OIDC |
| <img src="../icons/CloudWatch.svg" width="40"> | **Amazon CloudWatch** | Logs, metrics, alarms, and dashboards |
| <img src="../icons/X-Ray.svg" width="40"> | **AWS X-Ray** | Distributed tracing via daemon sidecar |
| <img src="../icons/Cognito.svg" width="40"> | **Amazon Cognito** | User authentication and authorization |

---

## Architecture (high level)

- **ALB (HTTPS)** terminates TLS using an ACM certificate for `code-quiz.io` and routes:
  - `/*` → **web** (React build served by NGINX container)
  - `/api/*` → **api** (Node/Express service)
- **api** writes quiz data to **DynamoDB**, stores export artifacts in **S3**, and enqueues async jobs to **SQS**
- **worker** consumes **SQS** jobs to:
  - Grade quiz attempts asynchronously
  - Export quizzes to S3 (JSON export)
- **CloudWatch** receives logs from all containers via `awslogs`
- **AWS X-Ray** is enabled for **api** and **worker** via:
  - `aws-xray-sdk-core` instrumentation in Node
  - `aws-xray-daemon` sidecar container in ECS task definitions

---

## Repository layout

- `services/web` — React + TypeScript (Vite), containerized with NGINX
- `services/api` — Node.js + Express + TypeScript REST API
- `services/worker` — Node.js + TypeScript background worker consuming SQS
- `infra/terraform/bootstrap` — one-time Terraform for remote state (optional but recommended)
- `infra/terraform/app` — main infrastructure (VPC, ALB, ECS, DDB, S3, SQS, Route53, etc.)
- `.github/workflows` — CI and deploy workflows

---

## Prerequisites

- AWS account with a Route 53 hosted zone for `code-quiz.io`
- Terraform >= 1.6
- Docker
- Node.js >= 20 (for local development)
 - (Recommended) GitHub CLI (`gh`) + `jq` if you want to use the one-command bootstrap scripts

---

## Local development (Docker Compose)

This repo includes a local stack using:

- DynamoDB Local
- LocalStack (S3 + SQS)
- API + Worker + Web containers

```bash
cd services
docker compose up --build
```

Then open:

- Web: http://localhost:8080
- API health: http://localhost:3000/health

> Note: Local X-Ray is disabled by default.

---

## Deploy to AWS (Terraform + GitHub Actions)

### Deployment Scripts Overview

The `scripts/` directory contains helper scripts for deployment:

| Script | Purpose |
|--------|---------|
| `standup.sh` | One-time setup: bootstrap infrastructure + configure GitHub |
| `push-images.sh` | Build and push Docker images to ECR |
| `terraform-apply.sh` | Apply Terraform to deploy/update ECS services |
| `teardown.sh` | Destroy all AWS resources |

### Quick Start (Recommended)

If you have `aws`, `terraform`, `gh`, and `jq` installed and are authenticated to both AWS and GitHub:

#### Step 1: Initial Setup

```bash
./scripts/standup.sh
```

This will:
- Create a remote state bucket + DynamoDB lock table (bootstrap)
- Provision the core AWS infrastructure with ECS services **disabled**
- Configure GitHub Actions secrets and variables automatically

#### Step 2: Push Container Images

```bash
AWS_REGION=us-east-1 ./scripts/push-images.sh [tag]
```

This builds and pushes the `web`, `api`, and `worker` Docker images to ECR.
The script also writes the image URIs to `.env.images` for use in the next step.

#### Step 3: Deploy ECS Services

**Option A — Manual deployment:**

```bash
# Source the image URIs from push-images.sh
source .env.images

# Optional: Set remote state config (if using S3 backend)
export TF_STATE_BUCKET=<bucket-name>
export TF_LOCK_TABLE=<table-name>
export TF_STATE_KEY=code-quiz/app.tfstate

# Deploy
AWS_REGION=us-east-1 ./scripts/terraform-apply.sh
```

Or as a one-liner after pushing images:

```bash
source .env.images && AWS_REGION=us-east-1 ./scripts/terraform-apply.sh
```

**Option B — Automated via GitHub Actions:**

Simply push to the `main` branch. The CI/CD workflow will:
1. Build and push images to ECR
2. Run `terraform apply` with the new image tags
3. Deploy updated ECS task definitions

### Cleanup

To remove all AWS resources:

```bash
./scripts/teardown.sh
```

---

### Manual Deployment (Step-by-Step)

If you prefer not to use the helper scripts:

#### 1) Bootstrap remote state

```bash
cd infra/terraform/bootstrap
terraform init
terraform apply -var="aws_region=us-west-2" -var="project_name=code-quiz"
```

This creates:
- S3 bucket for Terraform state
- DynamoDB table for state locking

#### 2) Deploy the application stack

```bash
cd ../app
terraform init \
  -backend-config="bucket=<TF_STATE_BUCKET>" \
  -backend-config="key=code-quiz/app.tfstate" \
  -backend-config="region=us-west-2" \
  -backend-config="dynamodb_table=<TF_LOCK_TABLE>" \
  -backend-config="encrypt=true"

terraform apply \
  -var="aws_region=us-west-2" \
  -var="project_name=code-quiz" \
  -var="domain_name=code-quiz.io" \
  -var="github_repo=<owner/repo>" \
  -var="enable_ecs_services=false"
```

#### 3) Build and push Docker images

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com

# Build and push each service
docker build -t <ecr-repo>/web:latest ./services/web
docker push <ecr-repo>/web:latest
# Repeat for api and worker
```

#### 4) Enable ECS services

```bash
terraform apply -var="enable_ecs_services=true" ...
```

---

### CI/CD with GitHub Actions

This repo provides a workflow that uses **AWS OIDC** to assume an IAM role created by Terraform.

The `standup.sh` script automatically configures these, but if setting up manually:

**GitHub Repository Variables:**
- `AWS_REGION` — Target AWS region (e.g., `us-west-2`)

**GitHub Repository Secrets:**
- `AWS_ROLE_ARN` — IAM role ARN for GitHub Actions to assume
- `TF_STATE_BUCKET` — S3 bucket for Terraform state
- `TF_LOCK_TABLE` — DynamoDB table for state locking
- `TF_STATE_KEY` — State file key (e.g., `code-quiz/app.tfstate`)

Once configured, push to `main` to trigger the deploy workflow.

Detailed instructions are in `infra/terraform/app/README.md`.

---

## Security notes

This is a reference implementation:

- The GitHub Actions role can be configured with broad permissions for simplicity; tighten it for real use.
- Consider adding AWS WAF, Shield Advanced, and stricter security headers for internet-facing production.

## Observability notes

- **Structured JSON access logs**:
  - `web` (NGINX) writes JSON access logs to stdout (captured in CloudWatch Logs).
  - `api` uses `pino-http` (JSON) for request logging.
- **ALB access logs** are enabled and delivered to an S3 bucket created by Terraform.
- A **CloudWatch dashboard** is created automatically (see the Terraform output `cloudwatch_dashboard_url`).

---
