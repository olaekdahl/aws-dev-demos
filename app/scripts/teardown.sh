#!/usr/bin/env bash
set -euo pipefail

# Tears down the entire AWS deployment:
# - Empties S3 buckets created by the app (exports + ALB logs)
# - terraform destroy for the app stack (remote state)
# - Purges the remote state bucket (incl. versions) and destroys bootstrap

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

require aws
require terraform
require jq

: "${AWS_REGION:=us-west-2}"
: "${PROJECT_NAME:=code-quiz}"
: "${DOMAIN_NAME:=code-quiz.io}"
: "${GITHUB_BRANCH:=main}"
: "${GITHUB_REPO:=placeholder/placeholder}"
: "${TF_STATE_KEY:=${PROJECT_NAME}/app.tfstate}"

purge_versioned_bucket() {
  local bucket="$1"
  echo "==> Purging versioned bucket: s3://${bucket}"

  # Remove current objects (best-effort)
  aws s3 rm "s3://${bucket}" --recursive >/dev/null 2>&1 || true

  local key_marker=""
  local version_marker=""

  while true; do
    local resp
    if [[ -z "$key_marker" ]]; then
      resp=$(aws s3api list-object-versions --bucket "$bucket" --output json)
    else
      resp=$(aws s3api list-object-versions --bucket "$bucket" --key-marker "$key_marker" --version-id-marker "$version_marker" --output json)
    fi

    local objs
    objs=$(echo "$resp" | jq -c '[.Versions[]?, .DeleteMarkers[]? | {Key:.Key, VersionId:.VersionId}]')
    local count
    count=$(echo "$objs" | jq 'length')

    if [[ "$count" -gt 0 ]]; then
      echo "    Deleting ${count} object versions/delete-markers..."
      echo "{\"Objects\":${objs},\"Quiet\":true}" > /tmp/s3-delete.json
      aws s3api delete-objects --bucket "$bucket" --delete file:///tmp/s3-delete.json >/dev/null
    fi

    local truncated
    truncated=$(echo "$resp" | jq -r '.IsTruncated')
    if [[ "$truncated" != "true" ]]; then
      break
    fi
    key_marker=$(echo "$resp" | jq -r '.NextKeyMarker')
    version_marker=$(echo "$resp" | jq -r '.NextVersionIdMarker')
  done
}

echo "==> Verifying AWS identity..."
aws sts get-caller-identity >/dev/null

# Discover backend config from bootstrap outputs unless explicitly provided.
TF_STATE_BUCKET="${TF_STATE_BUCKET:-}"
TF_LOCK_TABLE="${TF_LOCK_TABLE:-}"

if [[ -z "$TF_STATE_BUCKET" || -z "$TF_LOCK_TABLE" ]]; then
  if terraform -chdir=infra/terraform/bootstrap output -raw tfstate_bucket_name >/dev/null 2>&1; then
    TF_STATE_BUCKET=$(terraform -chdir=infra/terraform/bootstrap output -raw tfstate_bucket_name)
    TF_LOCK_TABLE=$(terraform -chdir=infra/terraform/bootstrap output -raw terraform_lock_table_name)
  else
    echo "Could not read bootstrap outputs. Set TF_STATE_BUCKET and TF_LOCK_TABLE (and optionally TF_STATE_KEY) and try again." >&2
    exit 1
  fi
fi

echo "==> Using backend bucket: ${TF_STATE_BUCKET}"
echo "==> Using lock table:    ${TF_LOCK_TABLE}"
echo "==> Using state key:     ${TF_STATE_KEY}"

echo "==> Terraform app init (remote backend)..."
terraform -chdir=infra/terraform/app init -upgrade \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=${TF_STATE_KEY}" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
  -backend-config="encrypt=true"

# Empty buckets that otherwise prevent destroy.
EXPORTS_BUCKET=$(terraform -chdir=infra/terraform/app output -raw s3_exports_bucket 2>/dev/null || true)
ALB_LOGS_BUCKET=$(terraform -chdir=infra/terraform/app output -raw s3_alb_logs_bucket 2>/dev/null || true)

if [[ -n "$EXPORTS_BUCKET" ]]; then
  purge_versioned_bucket "$EXPORTS_BUCKET"
fi

if [[ -n "$ALB_LOGS_BUCKET" ]]; then
  purge_versioned_bucket "$ALB_LOGS_BUCKET"
fi

echo "==> Destroying app stack..."
terraform -chdir=infra/terraform/app destroy -auto-approve \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}" \
  -var="domain_name=${DOMAIN_NAME}" \
  -var="github_repo=${GITHUB_REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -var="enable_ecs_services=true" \
  -var="api_image=public.ecr.aws/docker/library/node:20-alpine" \
  -var="worker_image=public.ecr.aws/docker/library/node:20-alpine" \
  -var="web_image=public.ecr.aws/docker/library/nginx:alpine"

echo "==> Purging Terraform state bucket (so bootstrap can be destroyed)..."
purge_versioned_bucket "$TF_STATE_BUCKET"

echo "==> Destroying bootstrap stack..."
terraform -chdir=infra/terraform/bootstrap init -upgrade
terraform -chdir=infra/terraform/bootstrap destroy -auto-approve \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}"

echo "==> Teardown complete."
