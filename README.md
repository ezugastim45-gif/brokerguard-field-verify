# BrokerGuard Field Verify

**GPS Photo Verification Module with Tamper-Evident Timestamps**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 Misión

Módulo open-source MIT para verificación de campo con:
- ✅ GPS embedding (lat/lon/altitude)
- ✅ Timestamp inmutable con hash SHA-256
- ✅ Overlay de mapa OpenStreetMap (sin APIs de pago)
- ✅ Generación de PDF con evidencia verificable
- ✅ Integración nativa con Supabase
- ✅ Funciona offline (mapas cacheados)

**Alternativa open-source a Tagofy MapCamera** sin vendor lock-in, sin datos a terceros, sin costos recurrentes.

---

## 🚀 Instalación Rápida (3 pasos)

```bash
# 1. Clonar repositorio
git clone https://github.com/ezugastim45-gif/brokerguard-field-verify.git
cd brokerguard-field-verify

# 2. Crear entorno virtual e instalar dependencias
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -e .

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Supabase

# 4. Iniciar servidor
uvicorn src.api:app --reload --port 8002
```

**Servidor corriendo en:** http://localhost:8002  
**Documentación interactiva:** http://localhost:8002/docs

---

## 📡 API Endpoints

### POST /field-verify/stamp

Genera imagen con overlay GPS + timestamp + mapa.

**Request:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANS...",
  "lat": -23.550520,
  "lon": -46.633308,
  "altitude": 760.5,
  "broker_id": "uuid-broker-123",
  "property_id": "PROP-456",
  "notes": "Inspección inicial fachada norte"
}
```

**Response:**
```json
{
  "success": true,
  "stamped_image_base64": "iVBORw0KGgoAAAANS...",
  "hash_sha256": "a3f5d8c2e1b4f7a9...",
  "pdf_url": "https://supabase.co/storage/verifications/abc123.pdf",
  "verification_url": "https://brokerguard.com/verify/a3f5d8c2e1b4f7a9",
  "metadata": {
    "timestamp": "2026-05-29T14:30:00Z",
    "address": "Av. Paulista, 1000 - São Paulo, SP",
    "weather": "22°C, Clear",
    "compass": "NE (45°)"
  }
}
```

### GET /verify/{hash}

Verifica autenticidad de una foto por su hash.

**Response:**
```json
{
  "valid": true,
  "timestamp": "2026-05-29T14:30:00Z",
  "location": {
    "lat": -23.550520,
    "lon": -46.633308,
    "address": "Av. Paulista, 1000"
  },
  "broker_id": "uuid-broker-123",
  "property_id": "PROP-456"
}
```

---

## 🏗️ Arquitectura

```
src/
├── api.py              # FastAPI endpoints
├── geostamp.py         # Motor principal: overlay GPS + timestamp
├── map_renderer.py     # Renderiza tiles de OpenStreetMap
├── verification.py     # Hash SHA-256 y verificación
├── pdf_report.py       # Generador de PDF con ReportLab
├── exif_handler.py     # Lectura/escritura de metadatos EXIF
└── config.py           # Configuración (Supabase, etc.)
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Test específico
pytest tests/test_geostamp.py -v
```

**Requisito FASE 3:** 100% cobertura (mínimo 20 tests).

---

## 🔒 Stack Técnico (Sin APIs de Pago)

| Componente | Tecnología | Licencia | Costo |
|------------|-----------|----------|-------|
| Backend | Python 3.11 + FastAPI | MIT | ✅ Gratis |
| Image Processing | Pillow (PIL Fork) | HPND | ✅ Gratis |
| Maps | OpenStreetMap tiles | ODbL | ✅ Gratis |
| QR Code | python-qrcode | BSD | ✅ Gratis |
| PDF | ReportLab | BSD | ✅ Gratis |
| EXIF | piexif | MIT | ✅ Gratis |
| Storage | Supabase | Apache-2.0 | ✅ Free tier |

**🚫 PROHIBIDO:** Google Maps API, Mapbox, HERE API (tienen costos y vendor lock-in).

---

## 📊 Supabase Schema

```sql
CREATE TABLE field_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  broker_id UUID NOT NULL,
  property_id TEXT NOT NULL,
  lat DECIMAL(10,8) NOT NULL,
  lon DECIMAL(11,8) NOT NULL,
  altitude DECIMAL(8,2),
  address TEXT,
  image_hash VARCHAR(64) UNIQUE NOT NULL,
  stamped_image_url TEXT NOT NULL,
  pdf_url TEXT,
  metadata JSONB,
  verified_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_image_hash ON field_verifications(image_hash);
CREATE INDEX idx_broker_property ON field_verifications(broker_id, property_id);
CREATE INDEX idx_verified_at ON field_verifications(verified_at);
```

---

## 🌍 OpenStreetMap Tiles

**Servidor por defecto:** `https://tile.openstreetmap.org/{z}/{x}/{y}.png`

**Tile Usage Policy:** https://operations.osmfoundation.org/policies/tiles/

**Límites:**
- No más de 2 requests/segundo
- User-Agent requerido: `BrokerGuardFieldVerify/0.1.0`
- Cache local habilitado (24 horas)

**Alternativas self-hosted:**
- OpenMapTiles (https://openmaptiles.org/)
- Mapnik + mod_tile (para alto tráfico)

---

## 📝 Variables de Entorno

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenStreetMap
OSM_TILE_SERVER=https://tile.openstreetmap.org
OSM_USER_AGENT=BrokerGuardFieldVerify/0.1.0
OSM_CACHE_TTL=86400  # 24 horas

# API
API_PORT=8002
API_HOST=0.0.0.0
```

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea tu feature branch: `git checkout -b feature/mi-feature`
3. Commit cambios: `git commit -m 'feat: agregar mi feature'`
4. Push al branch: `git push origin feature/mi-feature`
5. Abre un Pull Request

**Convenciones de commits:** [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

**Úsalo libremente en proyectos comerciales y personales sin royalties.**

---

## 🏆 Roadmap

### ✅ FASE 1 - Auditoría Técnica (COMPLETA)
- [x] Investigación Tagofy MapCamera
- [x] Análisis de competidores open-source
- [x] Definición de features MVP

### 🔄 FASE 2 - Diseño (EN CURSO)
- [x] Arquitectura del proyecto
- [x] Especificación de API
- [x] Schema de base de datos
- [ ] Documentación técnica completa

### 🔜 FASE 3 - Construcción
- [ ] Implementar `geostamp.py`
- [ ] Implementar `map_renderer.py`
- [ ] Implementar API endpoints
- [ ] 20+ tests con 100% cobertura
- [ ] Documentación con screenshots

### 🔜 FASE 4 - Integración BrokerGuard
- [ ] Endpoints en BrokerGuard (puerto 8001)
- [ ] UI para captura de fotos
- [ ] Dashboard de verificaciones

---

## 📞 Soporte

**Issues:** https://github.com/ezugastim45-gif/brokerguard-field-verify/issues  
**Email:** ezugastim45@gmail.com  
**Telegram:** @ZumaBrokers

---

**Made with ❤️ by ZumaIntelligence**
