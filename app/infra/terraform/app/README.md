# Application infrastructure (Terraform)

This stack provisions the full AWS infrastructure for the demo application:
- VPC (2 AZ), public + private subnets + NAT
- ALB + HTTPS (ACM cert validated via Route53)
- ECS (Fargate) cluster + services (web, api, worker)
- DynamoDB tables (quizzes, attempts, exports)
- S3 bucket for exports
- S3 bucket for ALB access logs
- SQS queue + DLQ
- CloudWatch log groups
- CloudWatch dashboard
- IAM task roles (least privilege) + GitHub Actions OIDC role (optional)

## First-time deployment

Because ECS tasks require container images, a common approach is:

1) Apply with services disabled (creates ECR repos and everything else)
2) Push images to ECR
3) Apply again with services enabled and image URIs set

### Step 1 — Create infrastructure (without ECS services)

```bash
terraform init  # if using remote backend, pass -backend-config=... (see ../bootstrap)
terraform apply -var='enable_ecs_services=false'
```

### Step 2 — Build & push images (example)

After apply, Terraform outputs ECR repo URLs. Build and push:

```bash
# Example, from repo root:
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.us-west-2.amazonaws.com

docker build -t code-quiz-api:local services/api
docker tag code-quiz-api:local <API_ECR_URL>:v1
docker push <API_ECR_URL>:v1

docker build -t code-quiz-worker:local services/worker
docker tag code-quiz-worker:local <WORKER_ECR_URL>:v1
docker push <WORKER_ECR_URL>:v1

docker build -t code-quiz-web:local services/web
docker tag code-quiz-web:local <WEB_ECR_URL>:v1
docker push <WEB_ECR_URL>:v1
```

### Step 3 — Enable ECS services + set image URIs

```bash
terraform apply \
  -var='enable_ecs_services=true' \
  -var='api_image=<API_ECR_URL>:v1' \
  -var='worker_image=<WORKER_ECR_URL>:v1' \
  -var='web_image=<WEB_ECR_URL>:v1'
```

## GitHub Actions (OIDC)

If you set `github_repo` (owner/repo) Terraform will create:
- GitHub Actions OIDC provider (if missing)
- An IAM role your workflow can assume to run Terraform and deploy

> For real production, replace the attached permissions with least privilege.

