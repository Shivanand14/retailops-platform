#!/usr/bin/env bash
#
# deploy-all.sh — Deploy RetailOps Platform to local kind cluster.
#
# Prerequisites:
#   - kind cluster running (kind create cluster --config kind-config.yaml)
#   - helm installed
#   - local container registry running on localhost:5000
#

set -euo pipefail

NAMESPACE="retailops"
HELM_DIR="deployments/helm"
REGISTRY="localhost:5000"

echo "==> Creating namespace ${NAMESPACE}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Deploying monitoring stack (kube-prometheus-stack)"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update >/dev/null 2>&1 || true
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.nodeSelector."kubernetes\.io/os"=linux \
  --set grafana.enabled=true \
  --set alertmanager.enabled=true

echo "==> Applying Prometheus alerting rules"
kubectl apply -f observability/prometheus/rules.yaml -n monitoring || true

echo "==> Applying Grafana datasources"
kubectl apply -f observability/grafana/datasources.yaml -n monitoring || true

echo "==> Deploying application services"
for svc in order-service payment-service inventory-service user-service; do
  echo "    Installing ${svc}..."
  helm upgrade --install "${svc}" "${HELM_DIR}/${svc}" \
    --namespace "${NAMESPACE}" \
    --set image.repository="${REGISTRY}/retailops/${svc}"
done

echo "==> Verifying deployments"
kubectl get pods -n "${NAMESPACE}"

echo "==> Deploy complete."
echo "    Access Grafana: kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring"
