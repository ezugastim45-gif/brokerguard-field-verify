# Migración futura: proyecto compartido → proyecto Brokerguard

**Contexto** (01-jul-2026): el proyecto Supabase "Brokerguard"
(`xjlqithpkchwpfszxecr`) está pausado (Free tier = máx. 2 proyectos activos).
Field Verify opera en el proyecto compartido `aacegozyyfyaqkbfkwcg`.
Cuando se reactive Brokerguard (upgrade de plan o pausar otro proyecto),
migrar así:

## Qué migrar

1. Tablas: `field_verifications` (nueva), y decidir si `brokers` / `api_keys`
   se mueven o se quedan compartidas (las usa también el ecosistema BGIE).
2. Storage: bucket `field-verifications` (imágenes + PDFs, organizados
   `images|pdfs/YYYY-MM/{hash}.*`).
3. RPC: `increment_api_key_usage`.

## Pasos

```bash
# 1. Schema en el proyecto destino (Management API o SQL editor):
#    docs/supabase_setup.sql + RPC increment_api_key_usage

# 2. Datos (via pg_dump con el pooler; pedir DATABASE_URL de ambos):
pg_dump "$ORIGEN" --table=field_verifications --data-only > fv_data.sql
psql "$DESTINO" < fv_data.sql

# 3. Storage: copiar objetos con el CLI o script (list + download + upload
#    por bucket). Las URLs públicas cambian de host → regenerar
#    stamped_image_url/pdf_url con UPDATE tras copiar.

# 4. Actualizar .env del deploy (SUPABASE_URL + keys del destino) y
#    bash deploy.sh
```

## Nota de riesgo

Mientras Brokerguard esté pausado, revisar si brokerguard-web (Vercel) depende
de él en runtime — sus llamadas Supabase estarían fallando.
