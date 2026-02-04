#!/usr/bin/env bash
set -euo pipefail

cd infra/terraform/app

: "${AWS_REGION:=us-west-2}"
: "${API_IMAGE:?Set API_IMAGE}"
: "${WORKER_IMAGE:?Set WORKER_IMAGE}"
: "${WEB_IMAGE:?Set WEB_IMAGE}"

if [[ -n "${TF_STATE_BUCKET:-}" && -n "${TF_LOCK_TABLE:-}" && -n "${TF_STATE_KEY:-}" ]]; then
  terraform init \
    -backend-config="bucket=${TF_STATE_BUCKET}" \
    -backend-config="key=${TF_STATE_KEY}" \
    -backend-config="region=$AWS_REGION" \
    -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
    -backend-config="encrypt=true"
else
  echo "TF_STATE_BUCKET/TF_LOCK_TABLE/TF_STATE_KEY not set; using local state."
  terraform init -backend=false
fi
terraform apply -auto-approve \
  -var="aws_region=$AWS_REGION" \
  -var="enable_ecs_services=true" \
  -var="api_image=$API_IMAGE" \
  -var="worker_image=$WORKER_IMAGE" \
  -var="web_image=$WEB_IMAGE"
