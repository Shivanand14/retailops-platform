# 🛍️ RetailOps Platform — Cloud-Native Microservices with SRE & Observability

> A production-grade, multi-microservice e-commerce order-processing platform deployed on local Kubernetes,
> designed to showcase **Docker, Kubernetes, Linux, SRE, Observability, and Grafana** expertise.

[![CI/CD Pipeline](https://github.com/Shivanand14/retailops-platform/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Shivanand14/retailops-platform/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28-blue.svg)](https://kubernetes.io)
[![Grafana](https://img.shields.io/badge/Grafana-10-orange.svg)](https://grafana.com)

---

## 👨‍💻 Author

**Shivanand Sanglage**  
Enterprise Integration Architect & AI Product Owner | Kubernetes | Docker | Linux | SRE | Observability | Grafana

- GitHub: [@Shivanand14](https://github.com/Shivanand14)
- LinkedIn: [Shivanand Sanglage](https://linkedin.com/in/shivanand-sanglage)
- Email: shivanand.sanglage@example.com

---

## 📖 About This Project

**RetailOps Platform** is a microservices-based order processing system built for the telecom/e-commerce domain (OSS/BSS automation). It demonstrates how AI agents and SRE practices can autonomously intercept, repair, and reflow broken order notifications after system incidents are resolved.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Microservices** | Order, Payment, Inventory, and User services built with FastAPI |
| **Containerization** | Multi-stage Dockerfiles, non-root users, distroless-like runtime images |
| **Orchestration** | Helm charts with HPA, PDB, NetworkPolicy, Liveness/Readiness/Startup probes |
| **SRE Practices** | SLOs/SLIs, error budgets, alerting, runbooks, chaos engineering |
| **Observability** | Prometheus metrics, Grafana dashboards (RED/SLO), Loki logs, Tempo traces, Alertmanager |
| **CI/CD** | GitHub Actions: lint, test, build, push to GHCR, deploy dry-run |
| **Chaos Engineering** | Python chaos-monkey + LitmusChaos pod-delete experiments |
| **Load Testing** | Locust-based synthetic traffic generation |

---

## 🏗️ Architecture

```text
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Client    │────▶│   NGINX Ingress  │────▶│   API Gateway   │
└─────────────┘      └──────────────────┘      └────────┬────────┘
                                                        │
        ┌─────────────┐  ┌─────────────┐  ┌────────────▼────────────┐
        │  Order Svc  │  │ Payment Svc │  │   Inventory / User Svc  │
        └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────┘
               │                │                        │
        ┌──────▼──────┐  ┌──────▼──────┐  ┌─────────────▼──────────┐
        │ PostgreSQL  │  │   Redis     │  │    RabbitMQ / Kafka    │
        └─────────────┘  └─────────────┘  └─────────────────────────┘
                                                        │
        ┌───────────────────────────────────────────────┴─────────────┐
        │              OBSERVABILITY STACK (monitoring namespace)     │
        │  Prometheus  │  Grafana  │  Loki  │  Tempo  │  Alertmanager │
        └─────────────────────────────────────────────────────────────┘
```

### Data Flow (End-to-End)

```
1. Client sends order request → NGINX Ingress → API Gateway
2. API Gateway → Order Service (creates order, emits metrics)
3. Order Service → Payment Service (process payment)
4. Order Service → Inventory Service (check stock)
5. Order Service → User Service (validate customer)
6. All services emit Prometheus metrics → scraped by Prometheus
7. Logs → Loki | Traces → Tempo
8. Alerts → Alertmanager → Slack/Email
9. Visualize → Grafana dashboards (RED method, SLO, Error Budget)
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Linux (WSL2 on Windows, or native Linux)
- `kubectl` CLI
- `helm` CLI
- `kind` (Kubernetes IN Docker)
- Python 3.11+ (for local development)
- `git`

### Step 1: Clone the Repository

```bash
git clone https://github.com/Shivanand14/retailops-platform.git
cd retailops-platform
```

### Step 2: Create Local Kubernetes Cluster

```bash
# Create a kind cluster with ingress port mappings
kind create cluster --config kind-config.yaml

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

### Step 3: Deploy Observability Stack

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.nodeSelector."kubernetes\.io/os"=linux \
  --set grafana.enabled=true \
  --set alertmanager.enabled=true

# Apply Prometheus alerting rules
kubectl apply -f observability/prometheus/rules.yaml -n monitoring

# Apply Grafana datasources
kubectl apply -f observability/grafana/datasources.yaml -n monitoring
```

### Step 4: Deploy Application Services

```bash
# Create namespace
kubectl create namespace retailops

# Deploy all microservices via Helm
for svc in order-service payment-service inventory-service user-service; do
  helm upgrade --install "${svc}" deployments/helm/${svc} \
    --namespace retailops \
    --set image.repository=localhost:5000/retailops/${svc}
done

# Verify all pods are running
kubectl get pods -n retailops
kubectl get svc -n retailops
```

### Step 5: Access the Services

```bash
# Port-forward Order Service (local testing)
kubectl port-forward svc/order-service 8080:80 -n retailops

# Test health endpoint
curl http://localhost:8080/healthz

# Test metrics endpoint
curl http://localhost:8080/metrics

# Create an order (POST)
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-1001",
    "items": [
      {"product_id": "PROD-001", "quantity": 2, "unit_price": 49.99},
      {"product_id": "PROD-002", "quantity": 1, "unit_price": 199.99}
    ]
  }'

# Port-forward Grafana (separate terminal)
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
# Open: http://localhost:3000
# Login: admin / prom-operator
```

---

## 🔄 End-to-End Flow with Commands

### Flow 1: Normal Order Processing

```bash
# 1. Generate synthetic traffic with Locust
pip install locust
locust -f tests/load/locustfile.py --host http://localhost:8080
# Open http://localhost:8089 in browser, start swarm

# 2. Watch services scale (HPA)
kubectl get hpa -n retailops -w

# 3. View metrics in Grafana
# Open http://localhost:3000 → Dashboards → RetailOps Service RED Metrics

# 4. Check logs via Loki (Grafana Explore)
# Select Loki datasource, query: {service="order-service"}
```

### Flow 2: Chaos Engineering (Pod Failure Simulation)

```bash
# 1. Make chaos script executable
chmod +x chaos/chaos-monkey.py

# 2. Run chaos monkey (kills random pods every 30s for 5 minutes)
python chaos/chaos-monkey.py --namespace retailops --interval 30 --duration 300

# 3. Observe self-healing in another terminal
kubectl get pods -n retailops -w

# 4. Check Alertmanager alerts
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
# Open http://localhost:9093

# 5. View crash loop alerts in Grafana
# Dashboard: RetailOps Cluster Health → PodCrashLooping alert
```

### Flow 3: SLO & Error Budget Monitoring

```bash
# 1. Access Grafana SLO Dashboard
# http://localhost:3000 → Dashboards → RetailOps SLO & Error Budget

# 2. Check alert rules
kubectl get prometheusrules -n monitoring

# 3. Verify Alertmanager configuration
kubectl get secret alertmanager-retailops -n monitoring -o yaml
```

### Flow 4: Manual Auto-Reflow (via FastAPI Backend)

```bash
# Trigger incident resolution via API
curl -X POST http://localhost:8000/incident-resolved \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2026-00987",
    "resolution_message": "Inventory System Timeout cleared. Database restored.",
    "order_ids": ["ORD-2026-10442", "ORD-2026-10451"]
  }'

# Check fallout queue status
curl http://localhost:8000/fallout-queue

# Get specific order
curl http://localhost:8000/order/ORD-2026-10442
```

---

## 📊 Grafana Dashboards

| Dashboard | Purpose | Panels |
|-----------|---------|--------|
| **Service RED Metrics** | Rate, Errors, Duration per service | Request Rate, Error Rate, p95 Latency, Time-series graphs |
| **SLO & Error Budget** | Availability SLO, Error Budget Remaining, Burn Rate | SLO compliance, 1h/6h/24h burn rate, 30-day trend |

**Access:** `http://localhost:3000` (after port-forward)  
**Credentials:** `admin` / `prom-operator`

---

## 🛠️ SRE Runbooks

Located in `docs/runbooks/`:

| Runbook | Alert | Scenario |
|---------|-------|----------|
| `pod-crashloop.md` | `PodCrashLooping` | Pod restarting continuously — diagnosis, remediation, escalation |

---

## 🧪 Testing & CI/CD

### Run Locally

```bash
# Install Python dependencies
pip install -r services/order-service/requirements.txt

# Run order service locally
cd services/order-service
python app/main.py

# Test endpoints
curl http://localhost:8080/healthz
curl http://localhost:8080/metrics
```

### GitHub Actions CI/CD

The `.github/workflows/ci-cd.yml` pipeline runs on every push/PR:

1. **lint-test** — flake8, black, pytest per service (matrix)
2. **build-push** — Docker build & push to GitHub Container Registry (GHCR)
3. **deploy-dry-run** — Helm lint + template validation on PRs
4. **deploy-prod** — Production deploy on `main` branch (requires `KUBE_CONFIG_DATA` secret)

### Load Testing

```bash
# Install Locust
pip install -r tests/load/requirements.txt

# Run load test
locust -f tests/load/locustfile.py --host http://localhost:8080 --headless -u 50 -r 10 --run-time 5m

# View results at http://localhost:8089
```

---

## 📁 Project Structure

```
retailops-platform/
├── .github/workflows/ci-cd.yml        # GitHub Actions CI/CD pipeline
├── .gitignore
├── README.md                          # This file
├── kind-config.yaml                   # Local kind cluster config
├── scripts/deploy-all.sh              # One-command deploy script
│
├── services/                          # Python microservice source code
│   ├── order-service/
│   │   ├── app/main.py                # Order CRUD + Prometheus metrics
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   ├── payment-service/
│   │   ├── app/main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   ├── inventory-service/
│   │   ├── app/main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   └── user-service/
│       ├── app/main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── .dockerignore
│
├── deployments/helm/                  # Helm charts (4 services)
│   ├── order-service/
│   ├── payment-service/
│   ├── inventory-service/
│   └── user-service/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml        # HPA, probes, security context
│           ├── service.yaml
│           ├── hpa.yaml               # HorizontalPodAutoscaler
│           ├── pdb.yaml               # PodDisruptionBudget
│           ├── networkpolicy.yaml     # Network isolation
│           └── _helpers.tpl
│
├── observability/
│   ├── grafana/
│   │   ├── datasources.yaml           # Prometheus, Loki, Tempo
│   │   └── dashboards/
│   │       ├── service-red-dashboard.json
│   │       └── slo-dashboard.json
│   ├── prometheus/
│   │   └── rules.yaml                 # SLO + infra alerting rules
│   └── alertmanager/
│       └── alertmanager.yaml          # Alert routing (Slack/Email)
│
├── chaos/
│   ├── chaos-monkey.py                # Python chaos injector
│   └── litmus/
│       └── pod-chaos-experiment.yaml  # LitmusChaos experiment
│
├── tests/load/
│   ├── locustfile.py                  # Load test scenarios
│   └── requirements.txt
│
└── docs/
    ├── architecture.mmd               # Mermaid architecture diagram
    └── runbooks/
        └── pod-crashloop.md           # SRE runbook
```

---

## 🧹 Cleanup

```bash
# Delete all Helm releases
for svc in order-service payment-service inventory-service user-service; do
  helm uninstall "${svc}" -n retailops
done

# Delete monitoring stack
helm uninstall kube-prometheus-stack -n monitoring

# Delete kind cluster
kind delete cluster --name retailops
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

**Author:** Shivanand Sanglage  
**GitHub:** [@Shivanand14](https://github.com/Shivanand14)

---

## 🏷️ Tags

`kubernetes` `docker` `linux` `sre` `observability` `grafana` `prometheus` `helm` `fastapi` `microservices` `chaos-engineering` `slo` `ci-cd` `oss-bss` `telecom`
