#!/usr/bin/env bash
set -euo pipefail
: "${AWS_REGION:?Set AWS_REGION}"
: "${EKS_CLUSTER_NAME:?Set EKS_CLUSTER_NAME}"
: "${ECR_REGISTRY:?Set ECR_REGISTRY}"
: "${IMAGE_TAG:?Set IMAGE_TAG to a built commit SHA}"
cd "$(dirname "$0")/.."
aws eks update-kubeconfig --region "$AWS_REGION" --name "$EKS_CLUSTER_NAME"
python3 scripts/render.py > /tmp/launchpad-rendered.yaml
kubectl apply -f /tmp/launchpad-rendered.yaml
for service in tasks summary frontend; do
  kubectl -n launchpad rollout status "deployment/$service" --timeout=240s
done
# Failure reports a failed release; automatic multi-service rollback is intentionally omitted.
kubectl -n launchpad get pods
