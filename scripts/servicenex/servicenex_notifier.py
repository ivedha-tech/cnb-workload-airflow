"""
ServiceNex Installation Notifier Plugin

This script notifies ServiceNex when an Airflow installation is completed and the container starts.
Configuration via environment variables:
- SERVICENEX_ENDPOINT: API endpoint URL
- INSTALLATION_ID: Unique installation identifier
- ENVIRONMENT: Environment name (production, staging, etc.)
"""

import os
import json
import socket
import requests
from datetime import datetime
from pathlib import Path




def read_secret(var_env: str, var_file_env: str):
    val = os.getenv(var_env)
    if val:
        return val
    path = os.getenv(var_file_env)
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None




def get_airflow_version():
    """Get current Airflow version"""
    try:
        from airflow import __version__
        return __version__
    except ImportError:
        return os.environ.get('AIRFLOW_VERSION', '3.0.2')




def get_servicenex_config():
    return {
        "endpoint": os.getenv("SERVICENEX_ENDPOINT"),
        "api_key": read_secret("SERVICENEX_API_KEY", "SERVICENEX_API_KEY_FILE"),
        "download_url": read_secret("DOWNLOAD_URL", "DOWNLOAD_URL_FILE"),
        "installation_id": os.getenv("INSTALLATION_ID", socket.gethostname()),
        "environment": os.getenv("ENVIRONMENT", "production")
    }




def load_release_info():
    file_path = Path(__file__).parent / "release_info.json"
    if not file_path.exists():
        print(f"[ServiceNex] release_info.json not found {file_path}")
        return {"features": [], "bugFixes": [], "dependencies": []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ServiceNex] Error reading release_info.json: {e}")
        return {"features": [], "bugFixes": [], "dependencies": []}


release_info = load_release_info()


def notify_servicenex_installation():
    """Notify ServiceNex about this Airflow installation"""

    config = get_servicenex_config()

    if not config:
        print("[ServiceNex] Configuration not found - skipping notification")
        return False


    payload = {
        "installationId": config['installation_id'],
        "serviceCode": os.environ.get('SERVICE_CODE', 'Airflow'),
        "version": get_airflow_version(),
        "hostname": socket.gethostname(),
        "environment": config['environment'],
        "deployedAt": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "releaseType": os.environ.get('RELEASE_TYPE', 'minor'),
        "downloadUrl": config['download_url'] or 'https://airflow.apache.org/docs/apache-airflow/3.0.2/',
        "documentationUrl": os.environ.get('DOCUMENTATION_URL', 'https://airflow.apache.org/docs/'),
        "summary": f"Airflow {get_airflow_version()} installation detected on {socket.gethostname()}",
        "details": f"Airflow installation completed. Airflow initialized at {datetime.utcnow().replace(microsecond=0).isoformat()}",
        "features": release_info.get("features", []),
        "bugFixes": release_info.get("bugFixes", []),
        "dependencies": release_info.get("dependencies", [])
    }

    # Safe logging (no sensitive data)
    print("[ServiceNex] Sending installation notification...")


    try:
        response = requests.post(
            config['endpoint'],
            headers={
                'X-API-Key': config['api_key'],
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"[ServiceNex] ✓ Installation notification succeeded (status: {response.status_code})")
            return True
        else:
            print(f"[ServiceNex] ✗ Installation notification failed (status: {response.status_code})")
            return False


    except Exception:
        print("[ServiceNex] ✗ Installation notification error")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ServiceNex Notifier - Direct Test")
    print("=" * 60)
    result = notify_servicenex_installation()
    print("=" * 60)
    if result:
        print("✓ SUCCESS")
    else:
        print("✗ FAILED")
    print("=" * 60)
