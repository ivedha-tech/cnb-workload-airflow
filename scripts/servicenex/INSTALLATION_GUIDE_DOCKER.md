# 🧰 Airflow Installation Guide with ServiceNex Telemetry

## Overview

This guide covers installing Airflow with ServiceNex telemetry integration for CNB's environment. ServiceNex automatically reports installation details when Airflow containers start.

**Authentication Method:** GCP Service Account  

---
## 📦 Before You Start

### 1. GCP Service Account Authentication (For Image Pull)

If pulling from GCP Artifact Registry, you need to authenticate Docker first.

**Steps:**

1. **Obtain Service Account key** (JSON file) from your GCP administrator

2. **Authenticate Docker:**
   ```bash
   cat service-account-key.json | docker login -u _json_key \
     --password-stdin us-docker.pkg.dev
   ```
   
   Expected output: `Login Succeeded`

3. **Pull the image:**
   ```bash
   docker pull us-docker.pkg.dev/prj-workload/workload-airflow/airflow:3.0.2-vX
   ```

---

## 🪄 Step 1 — Create Secrets Folder and Files

ServiceNex requires two secret files for authentication and tracking.

### Create the secrets folder:

```bash
mkdir -p secrets
cd secrets
```

### Create `servicenex_api_key.txt`

Contains your ServiceNex API key (provided by your admin).

```bash
echo "your-api-key-here" > servicenex_api_key.txt
```

Example content:
```
h4z7q1e9b2n0r5k8t3m6w1y4p9u2d7x5j0l8s3c6v9f1a4g2o7i5o209fmqjrh2b
```

### Create `download_url.txt`

Contains the Docker image URL for tracking purposes.

```bash
echo "us-docker.pkg.dev/prj-workload/workload-airflow/airflow:3.0.2-vX" > download_url.txt
```

### Verify files:

```bash
ls -la
cat servicenex_api_key.txt  # Should show your API key
cat download_url.txt         # Should show image URL
```

> ⚠️ **Important:** Files must contain only the value (no quotes, no spaces, no line breaks)

---

## 🚀 Step 2 — Run the Container

Navigate back to your working directory and run:

```bash
docker run -d -p 8080:8080 \
  -e SERVICENEX_ENDPOINT="https://<your-servicenex-host>api/v1/telemetry" \
  -e INSTALLATION_ID="airflow-prod-01" \
  -e ENVIRONMENT="production" \
  -e SERVICE_CODE="Airflow" \
  -e SERVICENEX_API_KEY_FILE="/run/secrets/servicenex_api_key" \
  -e DOWNLOAD_URL_FILE="/run/secrets/download_url" \
  -v "$(pwd)/secrets/servicenex_api_key.txt:/run/secrets/servicenex_api_key:ro" \
  -v "$(pwd)/secrets/download_url.txt:/run/secrets/download_url:ro" \
  --name airflow-servicenex \
  us-docker.pkg.dev/prj-workload/workload-airflow/airflow:3.0.2-v4 \
  standalone
```

### Command Breakdown:

- `-d` - Run in detached mode (background)
- `-p 8080:8080` - Expose Airflow webserver on port 8080
- `-e SERVICENEX_ENDPOINT` - ServiceNex API endpoint
- `-e INSTALLATION_ID` - Unique identifier for this installation
- `-e ENVIRONMENT` - Environment type (production, staging, development)
- `-e SERVICE_CODE` - Service identifier (always "Airflow")
- `-v` - Mount secret files as read-only volumes

---

## ⚙️ Environment Variables Reference

| Variable                  | Required | Description                                | Example                                           |
| ------------------------- | -------- | ------------------------------------------ | ------------------------------------------------- |
| `SERVICENEX_ENDPOINT`     | ✅        | API endpoint to send telemetry data        | `https://<your-servicenex-host>/api/v1/telemetry` |
| `INSTALLATION_ID`         | ✅        | Unique identifier for this installation    | `airflow-prod-01`                                 |
| `ENVIRONMENT`             | ✅        | Environment type                           | `production`, `staging`, `development`            |
| `SERVICE_CODE`            | ✅        | Service identifier                         | `Airflow`                                         |
| `SERVICENEX_API_KEY_FILE` | ✅        | Path to API key file inside container      | `/run/secrets/servicenex_api_key`                 |
| `DOWNLOAD_URL_FILE`       | ✅        | Path to download URL file inside container | `/run/secrets/download_url`                       |

---

## 🧾 Step 3 — Verify Installation

### Check container is running:

```bash
docker ps | grep airflow-servicenex
```

Expected output shows container running.

### Check ServiceNex notification:

```bash
docker logs airflow-servicenex 2>&1 | grep ServiceNex
```

**Expected output:**
```
[ServiceNex] Sending installation notification...
[ServiceNex] ✓ Installation notification succeeded (status: 200)
```

### Check Airflow is accessible:

```bash
curl http://<airflow-url>/api/v2/monitor/health
```

Default credentials:
- Username: `admin`
- Password: Check logs with `docker logs airflow-servicenex | grep password`

---

## ✅ Validation Checklist

After installation, verify:

- [ ] Container is running: `docker ps | grep airflow`
- [ ] ServiceNex notification succeeded (200 OK): `docker logs airflow-servicenex | grep ServiceNex`
- [ ] Airflow webserver is accessible
- [ ] ServiceNow shows new installation entry (if applicable)

---

## 🔧 Troubleshooting

### Issue: "unauthorized: authentication required" (Image Pull)

**Cause:** Docker not authenticated to GCP Artifact Registry  

**Solution:**
```bash
cat service-account-key.json | docker login -u _json_key \
  --password-stdin us-docker.pkg.dev
```

---

### Issue: "Configuration not found - skipping notification"

**Cause:** Secret files missing or empty  

**Solution:**
1. Verify files exist:
   ```bash
   ls -la secrets/
   ```
2. Check file contents:
   ```bash
   cat secrets/servicenex_api_key.txt
   cat secrets/download_url.txt
   ```
3. Ensure no extra spaces or newlines
4. Restart container after fixing

---

### Issue: "SSL certificate verification failed"

**Cause:** Corporate environment with self-signed certificates  

**Solution:** This is handled automatically by the image. If you still see warnings, they are informational only and can be ignored. The integration uses `verify=False` which is standard for corporate environments.

---

### Issue: "Connection refused" or "Timeout"

**Cause:** ServiceNex endpoint unreachable or firewall blocking  

**Solution:**
1. Verify endpoint URL is correct
2. Test connectivity:
   ```bash
   docker exec airflow-servicenex curl -v https://<your-servicenex-host>/api/v1/telemetry
   ```
3. Check firewall rules allow outbound HTTPS to ServiceNex
4. Contact network team if blocked

---

### Issue: Container crashes or won't start

**Cause:** Various (check logs for details)  

**Solution:**
```bash
docker logs airflow-servicenex
```

Common issues:
- Port 8080 already in use → Use different port: `-p 8081:8080`
- Insufficient memory → Increase Docker memory allocation
- Database initialization failed → Wait 30-60 seconds, check logs again

---

## 🔒 Security Notes

- **Secrets are mounted as read-only files** (`:ro` flag)
- **Never printed in logs** or exposed as environment variables
- **API keys are never logged** - only success/failure status
- **To rotate credentials:** Update secret files and restart container
- **Service Account keys:** Store securely, do not commit to version control

---

## 🔄 Updating Airflow

To update to a new version:

1. **Pull new image:**
   ```bash
   docker pull us-docker.pkg.dev/prj-workload/workload-airflow/airflow:3.0.2-vX
   ```

2. **Stop and remove old container:**
   ```bash
   docker stop airflow-servicenex
   docker rm airflow-servicenex
   ```

3. **Update `download_url.txt` with new image tag**

4. **Run new container** (same command as Step 2, with new image tag)

ServiceNex will automatically detect and report the new installation.

---
## ✅ Quick Recap

1. **Authenticate Docker** with Service Account (if pulling from GCP)
2. **Create `secrets/` folder** with two files:
   - `servicenex_api_key.txt` (API key)
   - `download_url.txt` (image URL)
3. **Run container** with `docker run` command
4. **Verify logs** show ServiceNex success (200 OK)
5. **Access Airflow**

---

✅ **Done!**  

After following these steps, Airflow will automatically report installation details to ServiceNex on startup. The integration runs once per container start and does not affect Airflow's normal operation.

---
