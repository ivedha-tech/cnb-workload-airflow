# 🚀 Airflow Kubernetes/Helm Deployment with ServiceNex

## Overview

This guide covers deploying Airflow with ServiceNex telemetry integration on Kubernetes using Helm charts.

**Prerequisites:**
- Kubernetes cluster access
- Helm 3.x installed
- kubectl configured
- Image registry access
- ServiceNex endpoint and API key

---

## 🔑 Step 1 — Create Kubernetes Secret

Create a secret containing ServiceNex credentials:

```bash
kubectl create secret generic servicenex-secrets \
  --from-literal=api_key='YOUR_API_KEY_HERE' \
  --from-literal=download_url='YOUR_IMAGE_URL_HERE' \
  -n airflow
```

**Important:** Replace `YOUR_API_KEY_HERE` and `YOUR_IMAGE_URL_HERE` with actual values provided by your administrator.

---

## ⚙️ Step 2 — Configure Helm Values

Add the following to your `values.yaml`:

```yaml
# Image configuration
images:
  airflow:
    repository: YOUR_REGISTRY/airflow
    tag: 3.1.0-servicenex
    pullPolicy: IfNotPresent

# ServiceNex environment variables (applied to all components)
env:
  - name: SERVICENEX_ENDPOINT
    value: "https://YOUR_SERVICENEX_HOST/api/v1/telemetry"
  - name: INSTALLATION_ID
    value: "airflow-YOUR_ENV"
  - name: ENVIRONMENT
    value: "production"  # or staging, development
  - name: SERVICE_CODE
    value: "Airflow"
  - name: SERVICENEX_API_KEY_FILE
    value: "/run/secrets/servicenex/api_key"
  - name: DOWNLOAD_URL_FILE
    value: "/run/secrets/servicenex/download_url"

# Mount secrets to all components
extraVolumes:
  - name: servicenex-secrets
    secret:
      secretName: servicenex-secrets

extraVolumeMounts:
  - name: servicenex-secrets
    mountPath: /run/secrets/servicenex
    readOnly: true

# Ensure database is initialized before pods start
airflow:
  dbMigrations:
    enabled: true
```

---

## 📝 Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SERVICENEX_ENDPOINT` | ServiceNex API endpoint | `https://servicenex.example.com/api/v1/telemetry` |
| `INSTALLATION_ID` | Unique installation identifier | `airflow-production-cluster` |
| `ENVIRONMENT` | Environment type | `production`, `staging`, `development` |
| `SERVICE_CODE` | Service identifier (always "Airflow") | `Airflow` |
| `SERVICENEX_API_KEY_FILE` | Path to API key secret | `/run/secrets/servicenex/api_key` |
| `DOWNLOAD_URL_FILE` | Path to image URL secret | `/run/secrets/servicenex/download_url` |

### Secret Files

The Kubernetes secret must contain:
- `api_key` - ServiceNex API key
- `download_url` - Docker image URL for tracking

---

## 🚀 Step 3 — Deploy with Helm

```bash
# Add Airflow Helm repository (if not already added)
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Install or upgrade Airflow
helm upgrade --install airflow apache-airflow/airflow \
  -f values.yaml \
  -n airflow \
  --create-namespace
```

---

## 🔍 Step 4 — Verify Deployment

### Check pods are running:

```bash
kubectl get pods -n airflow
```

Expected pods:
- `airflow-scheduler-*`
- `airflow-webserver-*`
- `airflow-worker-*` (if using CeleryExecutor)
- `airflow-triggerer-*`

### Verify ServiceNex notifications:

Check each component's logs for ServiceNex success:

```bash
# Scheduler
kubectl logs -n airflow deployment/airflow-scheduler | grep ServiceNex

# Webserver
kubectl logs -n airflow deployment/airflow-webserver | grep ServiceNex

# Workers
kubectl logs -n airflow deployment/airflow-worker | grep ServiceNex

# Triggerer
kubectl logs -n airflow deployment/airflow-triggerer | grep ServiceNex
```

**Expected output in each:**
```
[ServiceNex] Sending installation notification...
[ServiceNex] ✓ Installation notification succeeded (status: 200)
```

---

## 🔧 Troubleshooting

### Issue: Pods show "ImagePullBackOff"

**Cause:** Cannot pull image from registry

**Solution:**
1. Verify image repository and tag in `values.yaml`
2. Ensure image pull secrets are configured:
   ```yaml
   imagePullSecrets:
     - name: registry-credentials
   ```
3. Create image pull secret if needed:
   ```bash
   kubectl create secret docker-registry registry-credentials \
     --docker-server=YOUR_REGISTRY \
     --docker-username=YOUR_USERNAME \
     --docker-password=YOUR_PASSWORD \
     -n airflow
   ```

---

### Issue: "Configuration not found" in logs

**Cause:** Secret not mounted or empty

**Solution:**
1. Verify secret exists:
   ```bash
   kubectl get secret servicenex-secrets -n airflow
   kubectl describe secret servicenex-secrets -n airflow
   ```
2. Check secret contents:
   ```bash
   kubectl get secret servicenex-secrets -n airflow -o yaml
   ```
3. Verify volume mounts in pod:
   ```bash
   kubectl describe pod airflow-scheduler-xxx -n airflow | grep -A 10 Mounts
   ```

---

### Issue: SSL certificate errors

**Cause:** Corporate environment with self-signed certificates

**Solution:** This is handled automatically by the image. The integration uses `verify=False` which is standard for corporate environments. SSL warnings are suppressed for clean logs.

---

### Issue: Connection timeout or refused

**Cause:** Network policy or firewall blocking ServiceNex endpoint

**Solution:**
1. Test connectivity from pod:
   ```bash
   kubectl exec -it airflow-scheduler-xxx -n airflow -- \
     curl -v https://YOUR_SERVICENEX_HOST/api/v1/telemetry
   ```
2. Check network policies:
   ```bash
   kubectl get networkpolicies -n airflow
   ```
3. Verify egress rules allow HTTPS to ServiceNex endpoint

---

### Issue: Database initialization errors

**Cause:** Database not ready or migrations not run

**Solution:**
1. Ensure `airflow.dbMigrations.enabled: true` in values.yaml
2. Check migration job completed:
   ```bash
   kubectl get jobs -n airflow
   kubectl logs job/airflow-run-airflow-migrations -n airflow
   ```
3. Wait for migrations to complete before pods start

---

## 🔄 Updating Airflow

To update to a new Airflow version with ServiceNex:

1. **Update image tag in `values.yaml`:**
   ```yaml
   images:
     airflow:
       tag: 3.1.0-servicenex-v1  # new version
   ```

2. **Update download_url in secret:**
   ```bash
   kubectl delete secret servicenex-secrets -n airflow
   kubectl create secret generic servicenex-secrets \
     --from-literal=api_key='YOUR_API_KEY' \
     --from-literal=download_url='NEW_IMAGE_URL' \
     -n airflow
   ```

3. **Upgrade Helm release:**
   ```bash
   helm upgrade airflow apache-airflow/airflow \
     -f values.yaml \
     -n airflow
   ```

ServiceNex will automatically detect and report new installations for each component.

---

## 🔒 Security Best Practices

### Secrets Management

- ✅ Use Kubernetes secrets for sensitive data
- ✅ Enable RBAC to restrict secret access
- ✅ Rotate credentials regularly
- ✅ Use external secret managers (Vault, AWS Secrets Manager) for production

### Network Security

- ✅ Use NetworkPolicies to restrict pod-to-pod communication
- ✅ Ensure ServiceNex endpoint uses HTTPS
- ✅ Implement egress controls for outbound connections

### Access Control

- ✅ Limit kubectl access to authorized personnel
- ✅ Use namespace isolation
- ✅ Enable audit logging for secret access

---

## 📚 Additional Configuration

### Custom Installation ID per Component

If you need different installation IDs per component:

```yaml
scheduler:
  env:
    - name: INSTALLATION_ID
      value: "airflow-scheduler-prod"

webserver:
  env:
    - name: INSTALLATION_ID
      value: "airflow-webserver-prod"

workers:
  env:
    - name: INSTALLATION_ID
      value: "airflow-worker-prod"
```

### Environment-Specific Values

Create separate values files:

```
values-production.yaml
values-staging.yaml
values-development.yaml
```

Deploy with:
```bash
helm upgrade airflow apache-airflow/airflow \
  -f values.yaml \
  -f values-production.yaml \
  -n airflow
```

---

## ✅ Validation Checklist

After deployment:

- [ ] All pods are running: `kubectl get pods -n airflow`
- [ ] ServiceNex notifications successful (200 OK) in all component logs
- [ ] Airflow webserver is accessible
- [ ] DAGs are loading correctly
- [ ] ServiceNow/ServiceNex shows installation entries for each component
- [ ] No errors in pod logs: `kubectl logs -n airflow <pod-name>`

---

## 📖 Quick Reference

```bash
# View all Airflow pods
kubectl get pods -n airflow

# Check specific pod logs
kubectl logs -n airflow airflow-scheduler-xxx

# Follow logs in real-time
kubectl logs -n airflow -f airflow-scheduler-xxx

# Describe pod (see events and configuration)
kubectl describe pod -n airflow airflow-scheduler-xxx

# Execute command in pod
kubectl exec -it -n airflow airflow-scheduler-xxx -- bash

# View secrets
kubectl get secrets -n airflow

# Helm status
helm status airflow -n airflow

# Helm values
helm get values airflow -n airflow
```

---

## 🆘 Support

For assistance:
1. Check pod logs: `kubectl logs -n airflow <pod-name>`
2. Check pod events: `kubectl describe pod -n airflow <pod-name>`
3. Verify secret configuration: `kubectl get secret servicenex-secrets -n airflow -o yaml`
4. Contact your platform team for:
   - ServiceNex endpoint URL
   - API keys
   - Image registry access
   - Network policy issues

---

## 📝 Summary

**Deployment Steps:**
1. Create Kubernetes secret with ServiceNex credentials
2. Configure Helm values with environment variables and volume mounts
3. Deploy with Helm
4. Verify ServiceNex notifications in all component logs

**Key Points:**
- ServiceNex runs in **all Airflow components** (scheduler, webserver, workers, triggerer)
- Each component sends an **independent notification**
- Secrets are mounted as **read-only volumes**
- SSL certificate handling is **automatic** for corporate environments
- Multiple installation entries are **expected and correct**
