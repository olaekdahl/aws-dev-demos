#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:=us-west-2}"
: "${PROJECT_NAME:=code-quiz}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

API_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}/api"
WORKER_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}/worker"
WEB_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}/web"

TAG="${1:-local}"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building and pushing images with tag: $TAG"

docker build -t "${API_REPO}:${TAG}" services/api
docker push "${API_REPO}:${TAG}"

docker build -t "${WORKER_REPO}:${TAG}" services/worker
docker push "${WORKER_REPO}:${TAG}"

docker build -t "${WEB_REPO}:${TAG}" services/web
docker push "${WEB_REPO}:${TAG}"

echo "Done."
