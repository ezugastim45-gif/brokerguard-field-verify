"""
Onboarding de brokers para BrokerGuard Field Verify.

Flujo:
  1. Busca el broker por email en la tabla `brokers` (lo crea si no existe).
  2. Marca `activated_at` si estaba solo invitado.
  3. Genera una API key (bfv_...), guarda SOLO el hash SHA-256 en `api_keys`
     y muestra la key en claro UNA vez (kit de bienvenida).

Uso:
  python3 scripts/onboard_broker.py --email broker@x.com --name "Nombre" [--plan beta]
"""

import argparse
import hashlib
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import os  # noqa: E402

import requests  # noqa: E402

BASE = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def _get(path: str, params: dict) -> list:
    r = requests.get(f"{BASE}/{path}", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def _post(path: str, data: dict) -> list:
    r = requests.post(f"{BASE}/{path}", json=data, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def _patch(path: str, params: dict, data: dict) -> list:
    r = requests.patch(f"{BASE}/{path}", params=params, json=data, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def onboard(email: str, name: str, plan: str) -> None:
    # 1. Broker: buscar o crear
    rows = _get("brokers", {"email": f"eq.{email}", "select": "*"})
    if rows:
        broker = rows[0]
        print(f"Broker existente: {broker['id']} ({broker['email']})")
    else:
        broker = _post("brokers", {"email": email, "name": name, "plan": plan})[0]
        print(f"Broker creado: {broker['id']}")

    # 2. Activar si estaba solo invitado
    if not broker.get("activated_at"):
        broker = _patch(
            "brokers", {"id": f"eq.{broker['id']}"}, {"activated_at": "now()"}
        )[0]
        print(f"Broker ACTIVADO: activated_at={broker['activated_at']}")
    else:
        print(f"Ya estaba activado desde {broker['activated_at']}")

    # 3. API key (hash en DB, valor en claro solo aqui)
    api_key = "bfv_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    _post("api_keys", {
        "name": f"field-verify — {name}",
        "key_hash": key_hash,
        "partner_email": email,
        "active": True,
        "rate_limit_per_hour": 1000,
    })

    print("\n" + "=" * 62)
    print("KIT DE BIENVENIDA — BrokerGuard Field Verify")
    print("=" * 62)
    print(f"Broker ID : {broker['id']}")
    print(f"Email     : {email}")
    print(f"Plan      : {broker.get('plan', plan)}")
    print(f"API Key   : {api_key}")
    print("            (GUARDALA AHORA — no se puede recuperar, solo regenerar)")
    print("\nEjemplo de uso:")
    print('  curl -X POST http://76.13.26.65:8005/field-verify/stamp \\')
    print('    -H "Content-Type: application/json" \\')
    print(f'    -H "X-API-Key: {api_key[:12]}..." \\')
    print(f'    -d \'{{"image_base64":"...","lat":19.04,"lon":-98.20,"broker_id":"{broker["id"]}","property_id":"PROP-001"}}\'')
    print("=" * 62)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--plan", default="beta")
    args = p.parse_args()
    try:
        onboard(args.email, args.name, args.plan)
    except requests.HTTPError as e:
        print(f"ERROR HTTP: {e.response.status_code} {e.response.text[:200]}", file=sys.stderr)
        sys.exit(1)
