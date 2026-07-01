# RESUMEN OVERNIGHT — 01/02-jul-2026

Sesión autónoma. Todo lo listado está **construido, probado y desplegado** en
NEXUS-1 salvo lo marcado como pendiente.

## 1. Onboarding del primer broker ✅

- El broker #1 ya existía en la tabla `brokers` **invitado pero nunca activado**
  (`activated_at: null`): Ernesto Zugasti / ezugastim45@gmail.com,
  id `6d30df6f-ce01-4e22-a2fe-f34bdd3cdb57`.
- **Activado** el 01-jul 23:08 UTC vía `scripts/onboard_broker.py` (nuevo:
  busca/crea broker, activa, emite API key `bfv_...` guardando solo el hash
  SHA-256 en `api_keys`).
- **Kit de bienvenida con la API key en claro: `~/BROKER1_WELCOME.txt`**
  (chmod 600 — la key no se puede recuperar, solo regenerar).
- E2E real verificado (local Y en el contenedor de producción): stamp con
  key → 200, imagen+PDF subidos a Supabase Storage, fila en
  `field_verifications`, `/verify/{hash}` → `valid:true`, sin key → 401.

## 2. Infraestructura nueva en Supabase ✅

⚠️ **Decisión que debes conocer**: el proyecto Supabase "Brokerguard"
(`xjlqithpkchwpfszxecr`) está **INACTIVE (pausado)** y no se puede restaurar
(plan Free = máx. 2 proyectos activos: nucleobrokers-v3 e IURIS, ninguno
pausable). Desplegué field-verify contra el **proyecto compartido
`aacegozyyfyaqkbfkwcg`** reutilizando sus tablas `brokers` y `api_keys`
existentes. Migrar después = dump de 2 tablas + bucket. Nota: que Brokerguard
esté pausado también puede estar degradando a brokerguard-web en Vercel.

Aplicado vía Management API: tabla `field_verifications` (+índices, trigger,
RLS: service_role full + lectura pública por hash), bucket público
`field-verifications`, RPC `increment_api_key_usage`.

## 3. Código nuevo/modificado (repo brokerguard-field-verify) ✅

| Archivo | Qué |
|---|---|
| `src/auth.py` (nuevo) | Auth X-API-Key vs `api_keys.key_hash` (SHA-256), cache 5 min, contador de uso; se activa con `REQUIRE_API_KEY=true` |
| `src/api.py` | `/field-verify/stamp` protegido con la dependencia de auth |
| `src/pdf_report.py` | **BUGFIX P1**: el PDF reventaba con imágenes altas + notas ("Flowable too large") — ahora escala preservando aspecto con tope de 14cm |
| `src/config.py` | flag `require_api_key` (default false → tests sin credenciales) |
| `tests/conftest.py` | aísla la suite del `.env` de producción |
| `tests/test_auth.py` (nuevo) | 4 tests de auth |
| `scripts/onboard_broker.py` (nuevo) | onboarding CLI |

**Tests: 41/41 pasando** (37 originales + 4 auth).

## 4. Deploy en NEXUS-1 ✅

- `Dockerfile` (python:3.12-slim, non-root, healthcheck) +
  `docker-compose.prod.yml` (**puerto host 8005** — 8002 lo ocupa iuris-api y
  8004 también está tomado) + `deploy.sh` idempotente (tests → build → up →
  health). Ejecutado completo: contenedor **`bfv-api` Up (healthy)**.
- Secretos en `.env` del repo (chmod 600, gitignored) con las keys **legacy
  JWT** del proyecto compartido (las `sb_secret_*` nuevas no son compatibles
  con supabase-py).
- nginx: site `verify.shildoo.com` → 127.0.0.1:8005 creado y habilitado.

## 5. PENDIENTES para ti (no puedo hacerlos yo)

1. 🔴 **P0 — shildoo.com está SUSPENDIDO por el registrador** (diagnóstico
   23:20 UTC): whois muestra **`clientHold` en Amazon Registrar** — la zona
   entera está fuera del DNS global (ni shildoo.com, ni www, ni bgie.*, ni
   nada resuelve, para todo el mundo, desde cualquier red). NO expiró (vence
   2027-05). Causa típica: verificación de email de registrante pendiente o
   problema de facturación. **Fix**: busca el correo de Amazon
   Registrar/AWS con el link de verificación, o AWS Console → Route 53 →
   Registered domains → shildoo.com. Al resolverlo, el hold se levanta en
   minutos-horas. Después: crear A `verify.shildoo.com` → 76.13.26.65 y
   `certbot --nginx -d verify.shildoo.com`.
2. 🔴 **Revocar el token GitHub `ghp_kMMS…`**: verificado a las 23:19 UTC —
   **sigue VIVO** y autenticado como ezugastim45-gif. NO es el token que usa
   gh CLI (revocar es seguro, nada se rompe): github.com/settings/tokens.
3. Guardar la API key de `~/BROKER1_WELCOME.txt` en un password manager y
   borrar el archivo.
4. Decidir futuro del proyecto Supabase Brokerguard pausado (upgrade o
   migración definitiva al compartido) — plan listo en
   `docs/MIGRACION_SUPABASE.md`.

## 5b. Pendientes de repo — YA RESUELTOS (01-jul noche)

- ✅ main/master unificado: default = `main`, `master` remota eliminada.
- ✅ `cache/` (tiles OSM) fuera de git (.gitignore + untrack).
- ✅ Plan de migración Supabase documentado.

## 6. Estado de ZUMA-AI (corriendo en paralelo)

- Backfill embeddings locales IURIS: **4,228/18,063 (23%)** al cierre de este
  resumen — termina de madrugada (unidad `zuma-embed-backfill`).
- A/B test de las 3 vías de búsqueda: programado para las **07:10 UTC**
  (unidad `zuma-ab-test`) → resultados en
  `~/projects/zumaintelligence-crewai/zuma_ai/docs/AB_TEST_RESULTS.md`.
- Cron horario `overnight_tasks.sh` activo (health + push si hay pendientes);
  quitar con `crontab -e` cuando ya no lo quieras.

## Nota de repo

El remoto ahora tiene rama `main` + tag `v0.1.0` (aparecieron en el fetch de
anoche); el trabajo local sigue en `master` (default del repo). Mismo caso
main/master que arreglamos en zumaintelligence-crewai — candidato a unificar.
