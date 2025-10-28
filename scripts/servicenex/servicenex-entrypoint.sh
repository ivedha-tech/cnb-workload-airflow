#!/usr/bin/env bash
set -euo pipefail

# Rodar o registro antes do Airflow (não aborta o container se falhar)
if command -v python >/dev/null 2>&1; then
  python /opt/airflow/scripts/servicenex_notifier.py || echo "[ServiceNex] Register script failed (non-blocking)."
else
  echo "[ServiceNex] Python not found? Skipping registration."
fi

# Delegar para o entrypoint oficial da imagem do Airflow
exec /usr/bin/dumb-init -- /entrypoint "$@"
