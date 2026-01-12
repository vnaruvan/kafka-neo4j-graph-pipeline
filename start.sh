#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-graph-pipeline}"
RELEASE="${RELEASE:-neo4j}"
CHART="${CHART:-neo4j/neo4j}"

cd "$(dirname "$0")"

command -v kubectl >/dev/null
command -v helm >/dev/null
command -v envsubst >/dev/null

if [[ -z "${NEO4J_PASSWORD:-}" ]]; then
  read -r -s -p "NEO4J_PASSWORD: " NEO4J_PASSWORD
  echo
  export NEO4J_PASSWORD
fi

kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || kubectl create ns "$NAMESPACE"

kubectl apply -n "$NAMESPACE" -f k8s/zookeeper-setup.yaml
kubectl apply -n "$NAMESPACE" -f k8s/kafka-setup.yaml

helm repo add neo4j https://helm.neo4j.com/neo4j >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1 || true

helm upgrade --install "$RELEASE" "$CHART" -n "$NAMESPACE" -f helm/neo4j-values.yaml --set neo4j.password="$NEO4J_PASSWORD"

envsubst < k8s/kafka-neo4j-connector.yaml | kubectl apply -n "$NAMESPACE" -f -

kubectl get pods -n "$NAMESPACE"
kubectl get svc -n "$NAMESPACE"
