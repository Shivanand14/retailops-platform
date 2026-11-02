# RetailOps Platform — Cloud-Native Microservices with SRE & Observability

A production-grade, multi-microservice e-commerce platform deployed on local Kubernetes,
designed to showcase **Docker, Kubernetes, Linux, SRE, Observability, and Grafana** expertise.

## Architecture

```text
Client → NGINX Ingress → API Gateway → {Order, Payment, Inventory, User} Services
                                            ↓
                                  PostgreSQL / Redis / RabbitMQ

Observability: Prometheus → Grafana | Loki | Tempo | Alertmanager
```

## Skill Coverage

| Domain | What's Included |
|--------|-----------------|
| **Docker** | Multi-stage Dockerfiles, non-root users, image scanning, local registry |
| **Kubernetes** | Helm charts, HPA, PDB, NetworkPolicies, probes, RBAC, Ingress |
| **Linux** | systemd units, Bash automation, journald, ss/tcpdump, resource tuning |
| **SRE** | SLOs/SLIs, error budgets, alerting, runbooks, chaos engineering |
| **Observability** | Prometheus metrics, Grafana dashboards, Loki logs, Tempo traces |
| **Grafana** | Dashboard-as-code, alerting, annotations, Explore (metrics/logs/traces) |

## Quick Start

```bash
# 1. Create local Kubernetes cluster
kind create cluster --config kind-config.yaml

# 2. Deploy observability stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# 3. Deploy application services
./scripts/deploy-all.sh

# 4. Access Grafana
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
# Login: admin / prom-operator

# 5. Run chaos engineering
python chaos/chaos-monkey.py --interval 30 --duration 300
```

## Repository Structure

```
retailops-platform/
├── kind-config.yaml
├── deployments/helm/{order,payment,inventory,user}-service/
├── observability/{grafana,prometheus,alertmanager}/
├── chaos/{chaos-monkey.py,litmus/}
├── scripts/deploy-all.sh
└── docs/{architecture.mmd,runbooks/}
```
