# 🧰 Airflow Installation Guide with ServiceNex Telemetry

This guide explains how to install and run the Airflow image that automatically reports installation information to **ServiceNex** via API.

---

## 📁 Prerequisites

You need:
- Docker installed and running.
- The image already built or available (e.g., `airflow-servicenex`).
- Two small text files in the `secrets/` folder:
  - `servicenex_api_key.txt`
  - `download_url.txt`

---

## 🪄 Step 1 — Create the `secrets` folder and files

Create a local folder called `secrets` in the same directory where you’ll run Docker.

```bash
mkdir -p secrets
```

Then create **two files** inside it:

### `secrets/servicenex_api_key.txt`
Contains your ServiceNex API key only.

Example:
```
h4z7q1e9b2n0r5k8t3m6w1y4p9u2d7x5j0l8s3c6v9f1a4g2o7i5o209fmqjrh2b
```

### `secrets/download_url.txt`
Contains the URL where this Airflow image or release is hosted.

Example:
```
us-docker.pkg.dev/prj-workload/workload-airflow/airflow@sha256:x9r3m1t7p4q8z2n6k0c5v1y9b3d7w4a2s8j6u0l5h9e3f1g7o2i4

```

> ⚠️ These files must contain only the value (no quotes, no spaces, no line breaks).

---

## 🚀 Step 2 — Run the container

Now start the Airflow container using this command:

```bash
docker run -d -p 8080:8080 \
  -e SERVICENEX_ENDPOINT="https://<your-servicenex-host>api/v1/telemetry" \
  -e INSTALLATION_ID="airflow-prod-01" \
  -e ENVIRONMENT="production" \
  -e SERVICENEX_API_KEY_FILE="/run/secrets/servicenex_api_key" \
  -e DOWNLOAD_URL_FILE="/run/secrets/download_url" \
  -v "$(pwd)/secrets/servicenex_api_key.txt:/run/secrets/servicenex_api_key:ro" \
  -v "$(pwd)/secrets/download_url.txt:/run/secrets/download_url:ro" \
  --name airflow-servicenex airflow-servicenex standalone
```

Replace the `SERVICENEX_ENDPOINT` value with the real endpoint provided by your environment. Ask your support team for the correct endpoint.

Example for production:
```bash
-e SERVICENEX_ENDPOINT="https://prod.servicenexhost.com/api/v1/telemetry"
```

---

## ⚙️ Environment Variables Reference

| Variable                  | Required | Description                                                       | Example                                           |
| ------------------------- | -------- | ----------------------------------------------------------------- | ------------------------------------------------- |
| `SERVICENEX_ENDPOINT`     | ✅        | API endpoint to send telemetry data                               | `https://<your-servicenex-host>/api/v1/telemetry` |
| `INSTALLATION_ID`         | ✅        | Unique identifier for this installation                           | `airflow-prod-01`                                 |
| `ENVIRONMENT`             | ✅        | Environment type                                                  | `production`                                      |
| `SERVICENEX_API_KEY_FILE` | ✅        | Path to the file containing the API key inside the container      | `/run/secrets/servicenex_api_key`                 |
| `DOWNLOAD_URL_FILE`       | ✅        | Path to the file containing the download URL inside the container | `/run/secrets/download_url`                       |

---

## 🧾 Step 3 — Verify the logs

Check that the ServiceNex call worked correctly:

```bash
docker logs -f airflow-servicenex
```

You should see something like:
```
[ServiceNex] Attempting to notify installation...
[ServiceNex] ✓ Installation reported successfully (status: 200)
```

If there’s a configuration problem:
```
[ServiceNex] Configuration not found - skipping notification
```
means one of the secret files is missing or empty.

---

## 🔒 Security Notes

- Secrets are **mounted as read-only files** (`:ro` flag).  
- They are **never printed** in logs or exposed as environment variables.  
- To rotate credentials, update the secret file and restart the container.  

---

## ✅ Quick Recap

1. Create `secrets/` folder.  
2. Add two files:  
   - `servicenex_api_key.txt` (with the API key)  
   - `download_url.txt` (with the image URL)  
3. Run the `docker run` command above.  
4. Check logs for `[ServiceNex] ✓ Installation reported successfully`.

---

✅ **Done!**  
After following these steps, the Airflow instance will automatically report its installation details to ServiceNex at the first startup.
