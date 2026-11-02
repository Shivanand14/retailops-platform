# SRE Runbook: Pod CrashLoopBackOff

## Alert
**AlertName:** `PodCrashLooping`  
**Severity:** Warning  
**Condition:** `kube_pod_container_status_restarts_total > 0` for 3 minutes  
**Dashboard:** Grafana → RetailOps → Cluster Health

## Impact
- Service degradation or partial outage for affected microservice
- Potential SLO breach if not remediated quickly

## Diagnosis Steps

1. **Identify the failing pod:**
   ```bash
   kubectl get pods -n retailops --field-selector=status.phase=Running
   kubectl get pods -n retailops | grep CrashLoopBackOff
   ```

2. **Check recent restarts:**
   ```bash
   kubectl describe pod <pod-name> -n retailops
   # Look at Last State, Reason, and Exit Code
   ```

3. **View container logs:**
   ```bash
   kubectl logs <pod-name> -n retailops --previous
   kubectl logs <pod-name> -n retailops --tail=100 -f
   ```

4. **Check pod events:**
   ```bash
   kubectl get events -n retailops --sort-by=.lastTimestamp
   ```

5. **Verify resource constraints:**
   ```bash
   kubectl top pods -n retailops
   kubectl describe node <node-name>
   ```

## Common Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Missing env var | `Error: required env var not set` | Add env to Deployment values.yaml |
| Image pull failure | `ErrImagePull` / `ImagePullBackOff` | Verify registry & image tag |
| OOMKilled | Exit code 137 | Increase memory limits in values.yaml |
| CrashLoopBackOff | Non-zero exit code | Fix application code / configmap |

## Remediation

1. **Rollback if regression:**
   ```bash
   helm rollback <release> <revision> -n retailops
   ```

2. **Restart deployment (if config issue fixed):**
   ```bash
   kubectl rollout restart deployment/order-service -n retailops
   ```

3. **Scale up if resource constrained:**
   ```bash
   kubectl scale deployment/order-service --replicas=4 -n retailops
   ```

4. **Verify recovery:**
   ```bash
   kubectl get pods -n retailops -w
   ```

## Prevention

- Ensure all Deployments have Liveness, Readiness, and Startup probes
- Set resource requests/limits on every container
- Enable PodDisruptionBudgets (maxUnavailable: 1)
- Deploy with HorizontalPodAutoscaler for CPU/memory
- Use NetworkPolicies to restrict inter-service traffic

## Escalation

If the pod cannot be recovered within 15 minutes:
1. Page SRE on-call (Slack: #sre-critical)
2. Create incident channel
3. Begin post-mortem draft
