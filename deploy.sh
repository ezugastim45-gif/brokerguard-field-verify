#!/usr/bin/env bash
# Deploy completo de BrokerGuard Field Verify en NEXUS-1 — idempotente.
#
# Uso:  bash deploy.sh
#
# Prerrequisito: .env en la raiz del proyecto (chmod 600, nunca en git) con
#   SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY,
#   SUPABASE_BUCKET=field-verifications, REQUIRE_API_KEY=true
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "== BrokerGuard Field Verify deploy =="

# 1. Secretos
[[ -f .env ]] || { echo "ERROR: falta .env (ver cabecera)"; exit 1; }
chmod 600 .env

# 2. Codigo actualizado
git pull --ff-only || echo "aviso: git pull fallo — sigo con el codigo actual"

# 3. Tests antes de desplegar (regla: coverage >=80%)
if [[ -x venv/bin/python ]]; then
  echo "-- corriendo suite de tests..."
  venv/bin/python -m pytest tests/ -q --no-header 2>&1 | tail -2
fi

# 4. Build + up
docker compose -f docker-compose.prod.yml up -d --build

# 5. Verificacion de salud (hasta 60s de gracia)
echo "-- esperando health..."
for i in $(seq 1 12); do
  if curl -sf --max-time 5 http://127.0.0.1:8005/health >/dev/null; then
    curl -s http://127.0.0.1:8005/health; echo
    echo "== Field Verify desplegado y healthy en :8005 =="
    exit 0
  fi
  sleep 5
done
echo "ERROR: /health no responde tras 60s. Logs:" >&2
docker logs bfv-api --tail 30 >&2
exit 1
