#!/usr/bin/env bash
set -euo pipefail

# Run the registration before Airflow (does not abort the container if it fails)
if command -v python >/dev/null 2>&1; then
  python /opt/airflow/scripts/servicenex_notifier.py || echo "[ServiceNex] Register script failed (non-blocking)."
else
  echo "[ServiceNex] Python not found? Skipping registration."
fi

# Delegate to the official entrypoint of the Airflow image
exec /usr/bin/dumb-init -- /entrypoint "$@"
