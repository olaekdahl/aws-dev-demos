#!/usr/bin/env bash
set -euo pipefail

# Stand up initial environment:
# - Creates remote state (bootstrap)
# - Provisions core infrastructure (app) with enable_ecs_services=false
# - Configures GitHub Actions secrets/vars via gh CLI (idempotent)

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

require aws
require terraform
require gh
require jq

: "${AWS_REGION:=us-west-2}"
: "${PROJECT_NAME:=code-quiz}"
: "${DOMAIN_NAME:=code-quiz.io}"
: "${GITHUB_BRANCH:=main}"
: "${TF_STATE_KEY:=${PROJECT_NAME}/app.tfstate}"

echo "==> Using region:       ${AWS_REGION}"
echo "==> Using project name: ${PROJECT_NAME}"
echo "==> Using domain:       ${DOMAIN_NAME}"
echo "==> TF state key:       ${TF_STATE_KEY}"

echo "==> Verifying AWS identity..."
aws sts get-caller-identity >/dev/null

echo "==> Verifying GitHub CLI authentication..."
gh auth status -h github.com >/dev/null

REPO="${GITHUB_REPO:-}"
if [[ -z "$REPO" ]]; then
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
fi
echo "==> GitHub repo: ${REPO}"

echo "==> Terraform bootstrap (remote state)..."
terraform -chdir=infra/terraform/bootstrap init -upgrade
terraform -chdir=infra/terraform/bootstrap apply -auto-approve \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}"

TF_STATE_BUCKET=$(terraform -chdir=infra/terraform/bootstrap output -raw tfstate_bucket_name)
TF_LOCK_TABLE=$(terraform -chdir=infra/terraform/bootstrap output -raw terraform_lock_table_name)

echo "==> Terraform app init (remote backend)..."
terraform -chdir=infra/terraform/app init -upgrade \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=${TF_STATE_KEY}" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
  -backend-config="encrypt=true"

echo "==> Terraform app apply (core infra; ECS services disabled)..."
terraform -chdir=infra/terraform/app apply -auto-approve \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}" \
  -var="domain_name=${DOMAIN_NAME}" \
  -var="github_repo=${REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -var="enable_ecs_services=false"

ROLE_ARN=$(terraform -chdir=infra/terraform/app output -raw github_actions_role_arn)

echo "==> Configuring GitHub repository variables/secrets (idempotent)..."
gh variable set AWS_REGION --body "${AWS_REGION}"

gh secret set AWS_ROLE_ARN --body "${ROLE_ARN}"
gh secret set TF_STATE_BUCKET --body "${TF_STATE_BUCKET}"
gh secret set TF_LOCK_TABLE --body "${TF_LOCK_TABLE}"
gh secret set TF_STATE_KEY --body "${TF_STATE_KEY}"

echo "==> Done. Next steps:"
echo "  1) Push images (local): ./scripts/push-images.sh <tag>"
echo "  2) Deploy ECS tasks (local): TF_STATE_BUCKET=... TF_LOCK_TABLE=... TF_STATE_KEY=... ./scripts/terraform-apply.sh"
echo "  3) Or push to main and let GitHub Actions deploy automatically."
echo
echo "Site URL (once deployed): $(terraform -chdir=infra/terraform/app output -raw site_url)"
echo "CloudWatch dashboard:     $(terraform -chdir=infra/terraform/app output -raw cloudwatch_dashboard_url)"
