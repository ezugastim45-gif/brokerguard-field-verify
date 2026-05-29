# INTEGRACIÓN BROKERGUARD — FIELD VERIFY

**Versión:** 1.0  
**Última actualización:** 29-MAY-2026

---

## 🎯 Overview

Este documento describe cómo integrar el módulo Field Verify con la aplicación principal BrokerGuard (puerto 8001).

---

## 📐 Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────────┐
│                     BrokerGuard App (8001)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Frontend (React/Next.js)             │ │
│  │  • Capture photo component                             │ │
│  │  • GPS location component                              │ │
│  │  • Field verify dashboard                              │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │ HTTP POST                            │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │                  Backend API (FastAPI)                  │ │
│  │  POST /api/v1/broker/{id}/field-verify                 │ │
│  │  GET  /api/v1/verification/{hash}                      │ │
│  └────────────────────┬───────────────────────────────────┘ │
└───────────────────────┼─────────────────────────────────────┘
                        │ HTTP Request
                        │
┌───────────────────────▼─────────────────────────────────────┐
│           Field Verify Service (8002)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  POST /field-verify/stamp                              │ │
│  │  GET  /verify/{hash}                                    │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │             Supabase Client                             │ │
│  │  • Upload stamped images                               │ │
│  │  • Upload PDF reports                                   │ │
│  │  • Insert verification records                          │ │
│  └────────────────────┬───────────────────────────────────┘ │
└───────────────────────┼─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Supabase                                  │
│  ┌──────────────────────────┬─────────────────────────────┐ │
│  │   PostgreSQL Database    │   Storage (S3-compatible)   │ │
│  │  field_verifications     │   field-verifications/      │ │
│  │  table                   │   ├── images/               │ │
│  │                          │   └── pdfs/                 │ │
│  └──────────────────────────┴─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Setup Supabase

### 1. Crear proyecto en Supabase

1. Ir a https://supabase.com/dashboard
2. Crear nuevo proyecto
3. Anotar:
   - `Project URL` → `SUPABASE_URL`
   - `anon public key` → `SUPABASE_KEY`
   - `service_role key` → `SUPABASE_SERVICE_ROLE_KEY`

### 2. Ejecutar SQL Schema

En Supabase Dashboard > SQL Editor, ejecutar:

```sql
-- Copiar y ejecutar todo el contenido de docs/supabase_setup.sql
```

Esto creará:
- Tabla `field_verifications`
- Indexes para performance
- Row Level Security (RLS) policies
- Trigger para `updated_at`

### 3. Crear Storage Bucket

1. Ir a Storage > Create bucket
2. Nombre: `field-verifications`
3. Public: **No** (acceso autenticado)
4. Permitir file uploads

### 4. Configurar variables de entorno

Crear `.env` en el proyecto Field Verify:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbG...your-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...your-service-role-key
SUPABASE_BUCKET=field-verifications

# API
API_HOST=0.0.0.0
API_PORT=8002
SECRET_KEY=your-secret-key-here

# OpenStreetMap
OSM_TILE_SERVER=https://tile.openstreetmap.org
OSM_USER_AGENT=BrokerGuardFieldVerify/0.1.0
OSM_CACHE_DIR=./cache/osm_tiles
OSM_CACHE_TTL=86400

# CORS (permitir BrokerGuard)
ALLOWED_ORIGINS=http://localhost:8001,https://brokerguard.com
```

---

## 📡 Endpoints de Integración

### BrokerGuard Backend → Field Verify

#### POST /field-verify/stamp

**Request:**
```http
POST http://localhost:8002/field-verify/stamp
Content-Type: application/json

{
  "image_base64": "iVBORw0KGgo...",
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
  "stamped_image_base64": "iVBORw0KGgo...",
  "hash_sha256": "a3f5d8c2e1b4f7a9...",
  "pdf_url": "https://project.supabase.co/storage/v1/.../abc123.pdf",
  "verification_url": "https://brokerguard.com/verify/abc123",
  "metadata": {
    "timestamp": "2026-05-29 14:30:00 UTC",
    "lat": -23.550520,
    "lon": -46.633308,
    "altitude": 760.5,
    "address": "23°33'01.9\"S 46°37'59.9\"W",
    "broker_id": "uuid-broker-123",
    "property_id": "PROP-456",
    "hash": "a3f5d8c2e1b4f7a9...",
    "notes": "Inspección inicial fachada norte"
  }
}
```

#### GET /verify/{hash}

**Request:**
```http
GET http://localhost:8002/verify/a3f5d8c2e1b4f7a9
```

**Response:**
```json
{
  "valid": true,
  "timestamp": "2026-05-29T14:30:00Z",
  "location": {
    "lat": -23.550520,
    "lon": -46.633308,
    "address": "23°33'01.9\"S 46°37'59.9\"W"
  },
  "broker_id": "uuid-broker-123",
  "property_id": "PROP-456",
  "image_url": "https://project.supabase.co/.../abc123.png",
  "pdf_url": "https://project.supabase.co/.../abc123.pdf"
}
```

---

## 💻 Código de Integración (BrokerGuard)

### Python (FastAPI)

```python
# brokerguard/api/field_verify.py
import httpx
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime

router = APIRouter(prefix="/api/v1")
FIELD_VERIFY_URL = "http://localhost:8002"

@router.post("/broker/{broker_id}/field-verify")
async def create_field_verification(
    broker_id: str,
    image: UploadFile = File(...),
    property_id: str,
    lat: float,
    lon: float,
    altitude: float = None,
    notes: str = None
):
    """Creates field verification with stamped image."""
    
    # Read and encode image
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode()
    
    # Call Field Verify service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FIELD_VERIFY_URL}/field-verify/stamp",
            json={
                "image_base64": image_base64,
                "lat": lat,
                "lon": lon,
                "altitude": altitude,
                "broker_id": broker_id,
                "property_id": property_id,
                "notes": notes
            },
            timeout=30.0
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Field verification failed")
    
    return response.json()


@router.get("/verification/{hash}")
async def verify_field_photo(hash: str):
    """Verifies a field photo by hash."""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FIELD_VERIFY_URL}/verify/{hash}",
            timeout=10.0
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return response.json()
```

### TypeScript/JavaScript (Next.js)

```typescript
// lib/fieldVerify.ts
export interface FieldVerifyRequest {
  imageBase64: string;
  lat: number;
  lon: number;
  altitude?: number;
  brokerId: string;
  propertyId: string;
  notes?: string;
}

export interface FieldVerifyResponse {
  success: boolean;
  stampedImageBase64: string;
  hashSha256: string;
  pdfUrl: string;
  verificationUrl: string;
  metadata: Record<string, any>;
}

const FIELD_VERIFY_API = "http://localhost:8002";

export async function createFieldVerification(
  data: FieldVerifyRequest
): Promise<FieldVerifyResponse> {
  const response = await fetch(`${FIELD_VERIFY_API}/field-verify/stamp`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_base64: data.imageBase64,
      lat: data.lat,
      lon: data.lon,
      altitude: data.altitude,
      broker_id: data.brokerId,
      property_id: data.propertyId,
      notes: data.notes,
    }),
  });

  if (!response.ok) {
    throw new Error("Field verification failed");
  }

  return response.json();
}

export async function verifyFieldPhoto(hash: string) {
  const response = await fetch(`${FIELD_VERIFY_API}/verify/${hash}`);
  
  if (!response.ok) {
    throw new Error("Verification failed");
  }

  return response.json();
}
```

---

## 🎨 UI Components (React)

### Photo Capture Component

```tsx
// components/FieldVerifyCapture.tsx
import { useState } from 'react';
import { createFieldVerification } from '@/lib/fieldVerify';

export function FieldVerifyCapture({ brokerId, propertyId }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCapture = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);

    try {
      // Get GPS coordinates
      const position = await getCurrentPosition();
      
      // Convert to base64
      const base64 = await fileToBase64(file);

      // Create verification
      const response = await createFieldVerification({
        imageBase64: base64,
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        altitude: position.coords.altitude,
        brokerId,
        propertyId,
        notes: "Captured from mobile app"
      });

      setResult(response);
    } catch (error) {
      console.error("Verification failed:", error);
      alert("Failed to create verification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="field-verify-capture">
      <input
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleCapture}
        disabled={loading}
      />
      
      {loading && <p>Processing...</p>}
      
      {result && (
        <div className="result">
          <img src={`data:image/png;base64,${result.stampedImageBase64}`} />
          <p>Hash: {result.hashSha256.slice(0, 16)}...</p>
          <a href={result.pdfUrl} target="_blank">Download PDF</a>
          <a href={result.verificationUrl}>Verify Online</a>
        </div>
      )}
    </div>
  );
}

function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject);
  });
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
```

---

## 🔒 Security Considerations

### 1. Authentication

- **Backend to Field Verify:** Usar `SUPABASE_SERVICE_ROLE_KEY` (nunca exponer al frontend)
- **Frontend to BrokerGuard:** JWT auth normal de BrokerGuard
- **Field Verify RLS:** Policies en Supabase controlan acceso

### 2. Rate Limiting

```python
# Agregar en BrokerGuard backend
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/broker/{broker_id}/field-verify")
@limiter.limit("10/minute")  # Max 10 verifications per minute
async def create_field_verification(...):
    ...
```

### 3. Image Validation

```python
# Validar tamaño de imagen
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

if len(image_bytes) > MAX_IMAGE_SIZE:
    raise HTTPException(400, "Image too large")
```

---

## 📊 Monitoring & Logging

### Supabase Dashboard

- **Storage usage:** Storage > Usage
- **Database queries:** Database > Query performance
- **API requests:** Settings > API

### Application Logs

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/broker/{broker_id}/field-verify")
async def create_field_verification(...):
    logger.info(f"Creating verification for broker={broker_id}, property={property_id}")
    
    try:
        result = await field_verify_client.stamp(...)
        logger.info(f"Verification created: hash={result['hash']}")
        return result
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise
```

---

## ✅ Testing Integration

```bash
# 1. Start Field Verify service
cd brokerguard-field-verify
source venv/bin/activate
uvicorn src.api:app --reload --port 8002

# 2. Test direct endpoint
curl -X POST http://localhost:8002/field-verify/stamp \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"iVBORw0KGgo...","lat":-23.55,"lon":-46.63,"broker_id":"test","property_id":"test"}'

# 3. Test from BrokerGuard backend
curl -X POST http://localhost:8001/api/v1/broker/test-123/field-verify \
  -H "Authorization: Bearer YOUR_JWT" \
  -F "image=@test.jpg" \
  -F "property_id=PROP-456" \
  -F "lat=-23.55" \
  -F "lon=-46.63"
```

---

## 🚀 Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  brokerguard:
    image: brokerguard:latest
    ports:
      - "8001:8001"
    environment:
      - FIELD_VERIFY_URL=http://field-verify:8002
    depends_on:
      - field-verify

  field-verify:
    build: ./brokerguard-field-verify
    ports:
      - "8002:8002"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    volumes:
      - ./cache:/app/cache
```

### Systemd Services

```ini
# /etc/systemd/system/field-verify.service
[Unit]
Description=BrokerGuard Field Verify Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/brokerguard-field-verify
Environment="PATH=/opt/brokerguard-field-verify/venv/bin"
EnvironmentFile=/opt/brokerguard-field-verify/.env
ExecStart=/opt/brokerguard-field-verify/venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8002
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📞 Support

**Issues:** https://github.com/ezugastim45-gif/brokerguard-field-verify/issues  
**Email:** ezugastim45@gmail.com

---

**Made with ❤️ by ZumaIntelligence**
