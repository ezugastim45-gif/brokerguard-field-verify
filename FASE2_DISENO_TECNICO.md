# FASE 2 — DISEÑO TÉCNICO · BROKERGUARD FIELD VERIFY
**ZumaIntelligence Swarm · 29-MAY-2026 · MIT License**

---

## 1. ARQUITECTURA DEL SISTEMA

### 1.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Layer                          │   │
│  │  • POST /field-verify/stamp                          │   │
│  │  • GET  /verify/{hash}                               │   │
│  │  • GET  /health                                       │   │
│  └────────────────┬─────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────▼─────────────────────────────────────┐   │
│  │              Business Logic Layer                     │   │
│  │                                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │  geostamp.py │  │ map_renderer │  │verification│ │   │
│  │  │              │  │     .py      │  │    .py     │ │   │
│  │  │ • Overlay    │  │              │  │            │ │   │
│  │  │ • Compose    │  │ • OSM Tiles  │  │ • SHA-256  │ │   │
│  │  │ • Position   │  │ • Cache      │  │ • Verify   │ │   │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │   │
│  │                                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │ pdf_report   │  │ exif_handler │                  │   │
│  │  │    .py       │  │     .py      │                  │   │
│  │  │              │  │              │                  │   │
│  │  │ • Generate   │  │ • Read EXIF  │                  │   │
│  │  │ • Template   │  │ • Write EXIF │                  │   │
│  │  └──────────────┘  └──────────────┘                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              External Services Layer                  │   │
│  │                                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │   Supabase   │  │ OpenStreetMap│  │   Pillow   │ │   │
│  │  │  PostgreSQL  │  │   Tile API   │  │   (PIL)    │ │   │
│  │  │   + Storage  │  │              │  │            │ │   │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Flujo de Datos: POST /field-verify/stamp

```
┌─────────┐
│ Client  │
└────┬────┘
     │ 1. POST /field-verify/stamp
     │    { image_base64, lat, lon, ... }
     ▼
┌─────────────┐
│   API       │
│  (api.py)   │
└──────┬──────┘
       │ 2. Validate input
       │ 3. Decode base64 image
       ▼
┌──────────────┐
│ geostamp.py  │ 4. Create timestamp overlay
│              │ 5. Format GPS coordinates
└──────┬───────┘
       │
       │ 6. Request map tile
       ▼
┌──────────────┐
│map_renderer  │ 7. Fetch OSM tile (or cache)
│    .py       │ 8. Crop to coordinates
└──────┬───────┘
       │
       │ 9. Composite: base + map + text
       ▼
┌──────────────┐
│  Pillow      │ 10. Merge layers
│  (Image)     │ 11. Add overlays
└──────┬───────┘
       │
       │ 12. Compute hash
       ▼
┌──────────────┐
│verification  │ 13. SHA-256(image_bytes)
│    .py       │ 14. Generate verification ID
└──────┬───────┘
       │
       │ 15. Write EXIF metadata
       ▼
┌──────────────┐
│exif_handler  │ 16. Embed GPS, timestamp, hash
│    .py       │
└──────┬───────┘
       │
       │ 17. Generate PDF report
       ▼
┌──────────────┐
│ pdf_report   │ 18. Create PDF with image + data
│    .py       │ 19. QR code with verification URL
└──────┬───────┘
       │
       │ 20. Upload to Supabase
       ▼
┌──────────────┐
│  Supabase    │ 21. Store image in bucket
│  Storage +   │ 22. Insert row in field_verifications
│  PostgreSQL  │
└──────┬───────┘
       │
       │ 23. Return response
       ▼
┌──────────────┐
│   Client     │ { stamped_image_base64, hash, pdf_url, ... }
└──────────────┘
```

---

## 2. ESPECIFICACIONES DE MÓDULOS

### 2.1 `src/api.py` - FastAPI Endpoints

**Responsabilidad:** Exposición de API REST, validación de entrada, orquestación de servicios.

**Endpoints:**

#### POST /field-verify/stamp
```python
class StampRequest(BaseModel):
    image_base64: str  # Base64-encoded image (PNG/JPEG)
    lat: float  # Latitude (-90 to 90)
    lon: float  # Longitude (-180 to 180)
    altitude: Optional[float] = None  # Meters above sea level
    broker_id: str  # UUID of broker
    property_id: str  # Property identifier
    notes: Optional[str] = None  # Optional user notes
    timestamp: Optional[datetime] = None  # If None, use current time

class StampResponse(BaseModel):
    success: bool
    stamped_image_base64: str
    hash_sha256: str
    pdf_url: str
    verification_url: str
    metadata: dict
```

**Validaciones:**
- image_base64: valid base64, max 10MB decoded
- lat: -90 <= lat <= 90
- lon: -180 <= lon <= 180
- broker_id: valid UUID format
- property_id: max 100 chars

**Response time target:** < 3 segundos

#### GET /verify/{hash}
```python
class VerificationResponse(BaseModel):
    valid: bool
    timestamp: datetime
    location: dict  # {lat, lon, address}
    broker_id: str
    property_id: str
    image_url: Optional[str]
    pdf_url: Optional[str]
```

#### GET /health
```python
class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "down"
    version: str
    dependencies: dict  # {supabase: bool, osm: bool}
```

---

### 2.2 `src/geostamp.py` - Motor Principal de Overlay

**Responsabilidad:** Composición de imagen con GPS, timestamp, mapa, texto.

**Funciones principales:**

```python
def create_geostamp(
    image: Image.Image,
    lat: float,
    lon: float,
    altitude: Optional[float],
    timestamp: datetime,
    map_image: Image.Image,
    notes: Optional[str] = None
) -> Image.Image:
    """
    Compone imagen final con overlays.
    
    Layout:
    ┌────────────────────────────────────┐
    │                                    │
    │         [Original Image]           │
    │                                    │
    │                                    │
    ├────────────────────────────────────┤
    │ 📍 Lat: -23.550520, Lon: -46.633308│
    │ 📏 Alt: 760.5m | 🧭 NE (45°)       │
    │ 🕒 2026-05-29 14:30:00 UTC         │
    │ [Mini Map 200x150px]     [QR Code]│
    │ #️⃣ Hash: a3f5d8c2e1b4f7a9...      │
    └────────────────────────────────────┘
    
    Returns: PIL Image
    """
    pass

def format_coordinates(lat: float, lon: float) -> str:
    """
    Formats GPS coordinates in DMS (Degrees Minutes Seconds).
    Example: "23°33'01.9\"S 46°38'00.0\"W"
    """
    pass

def calculate_compass(bearing: float) -> str:
    """
    Converts bearing (0-360°) to compass direction.
    Example: 45° -> "NE", 180° -> "S"
    """
    pass
```

**Parámetros de diseño:**
- Overlay height: 250px (fixed)
- Background color: rgba(0, 0, 0, 0.75) - semi-transparent black
- Text color: white (#FFFFFF)
- Font: DejaVuSans.ttf (included), size 16px
- Mini map size: 200x150px, zoom level 15
- QR code size: 150x150px
- Padding: 10px

---

### 2.3 `src/map_renderer.py` - OpenStreetMap Tiles

**Responsabilidad:** Descarga, cache y renderizado de tiles de OSM.

```python
class OSMTileRenderer:
    """
    Renders OpenStreetMap tiles and crops to specific coordinates.
    Implements local cache with TTL.
    """
    
    def __init__(
        self,
        tile_server: str,
        cache_dir: str,
        cache_ttl: int,
        user_agent: str
    ):
        pass
    
    def get_tile(self, lat: float, lon: float, zoom: int = 15) -> Image.Image:
        """
        Gets map tile centered on coordinates.
        
        1. Calculate tile coordinates (x, y, z)
        2. Check cache (if exists and not expired, return)
        3. Fetch from OSM tile server
        4. Save to cache
        5. Return PIL Image
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level (0-18, default 15 for street-level)
        
        Returns:
            PIL Image (256x256px tile)
        """
        pass
    
    def lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> tuple[int, int]:
        """
        Converts lat/lon to tile coordinates.
        https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
        
        Returns: (x, y)
        """
        pass
    
    def crop_to_center(
        self, 
        tile: Image.Image, 
        lat: float, 
        lon: float, 
        width: int = 200, 
        height: int = 150
    ) -> Image.Image:
        """
        Crops tile to center on exact coordinates with specified dimensions.
        """
        pass
```

**Cache Structure:**
```
cache/
└── osm_tiles/
    ├── 15/
    │   ├── 12345/
    │   │   ├── 67890.png
    │   │   └── 67890.meta.json  # {downloaded_at, expires_at}
    │   └── ...
    └── ...
```

**Rate Limiting:**
- Max 2 requests/second to OSM
- Exponential backoff on 429 errors
- User-Agent: "BrokerGuardFieldVerify/0.1.0"

---

### 2.4 `src/verification.py` - Hash y Verificación

**Responsabilidad:** Generación de hash SHA-256 reproducible, verificación de integridad.

```python
def compute_image_hash(image_bytes: bytes) -> str:
    """
    Computes SHA-256 hash of image bytes.
    
    Args:
        image_bytes: Raw bytes of the stamped image
    
    Returns:
        Hex string (64 chars)
    """
    return hashlib.sha256(image_bytes).hexdigest()

def verify_image_hash(image_bytes: bytes, claimed_hash: str) -> bool:
    """
    Verifies if image matches claimed hash.
    
    Returns:
        True if hash matches, False otherwise
    """
    computed = compute_image_hash(image_bytes)
    return computed == claimed_hash

def generate_verification_url(hash: str, base_url: str) -> str:
    """
    Generates public verification URL.
    
    Example: https://brokerguard.com/verify/a3f5d8c2e1b4f7a9
    """
    return f"{base_url}/verify/{hash}"

def create_qr_code(verification_url: str, size: int = 150) -> Image.Image:
    """
    Creates QR code for verification URL.
    
    Returns:
        PIL Image (size x size px)
    """
    import qrcode
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")
```

**Propiedades del hash:**
- Algoritmo: SHA-256 (industry standard)
- Input: bytes de la imagen PNG final (sin metadata EXIF)
- Output: 64 caracteres hexadecimales
- Reproducible: mismo input → mismo hash

---

### 2.5 `src/pdf_report.py` - Generador de PDF

**Responsabilidad:** Generación de reporte PDF profesional con imagen, datos y QR.

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, Image as RLImage, Paragraph

def generate_pdf_report(
    stamped_image_path: str,
    metadata: dict,
    qr_code_image: Image.Image,
    output_path: str
) -> str:
    """
    Generates professional PDF report.
    
    Layout:
    ┌─────────────────────────────────────┐
    │  BROKERGUARD FIELD VERIFICATION     │
    │  Report ID: [hash]                  │
    ├─────────────────────────────────────┤
    │                                     │
    │      [Stamped Image - 15cm wide]    │
    │                                     │
    ├─────────────────────────────────────┤
    │  VERIFICATION DETAILS               │
    │  ┌───────────────┬────────────────┐ │
    │  │ Timestamp     │ 2026-05-29...  │ │
    │  │ Coordinates   │ -23.55, -46.63 │ │
    │  │ Altitude      │ 760.5m         │ │
    │  │ Broker ID     │ uuid-123       │ │
    │  │ Property ID   │ PROP-456       │ │
    │  │ Hash (SHA256) │ a3f5d8c2...    │ │
    │  └───────────────┴────────────────┘ │
    ├─────────────────────────────────────┤
    │  SCAN TO VERIFY ONLINE              │
    │       [QR Code - 4cm x 4cm]         │
    └─────────────────────────────────────┘
    
    Args:
        stamped_image_path: Path to stamped image
        metadata: Dict with verification data
        qr_code_image: PIL Image of QR code
        output_path: Where to save PDF
    
    Returns:
        Path to generated PDF
    """
    pass
```

**Especificaciones:**
- Page size: A4 (21cm x 29.7cm)
- Margins: 2cm all sides
- Font: Helvetica (built-in)
- Colors: Black text, grey headers (#333333)
- Logo: Optional (if provided in assets/)

---

### 2.6 `src/exif_handler.py` - Metadatos EXIF

**Responsabilidad:** Lectura y escritura de metadatos EXIF en imágenes.

```python
import piexif

def read_exif(image_path: str) -> dict:
    """
    Reads EXIF metadata from image.
    
    Returns:
        Dict with parsed EXIF data
    """
    pass

def write_exif(
    image_path: str,
    lat: float,
    lon: float,
    altitude: Optional[float],
    timestamp: datetime,
    hash: str,
    output_path: str
) -> None:
    """
    Writes GPS and custom EXIF tags to image.
    
    Tags written:
    - GPS IFD: GPSLatitude, GPSLongitude, GPSAltitude, GPSTimeStamp
    - EXIF IFD: DateTimeOriginal, UserComment (hash)
    - Maker Note: Custom data (broker_id, property_id)
    """
    pass

def exif_to_dict(exif_bytes: bytes) -> dict:
    """
    Converts EXIF bytes to readable dict.
    """
    return piexif.load(exif_bytes)
```

**Tags GPS (IFD 1):**
- GPSLatitude (0x0002): Rational[3]
- GPSLongitude (0x0004): Rational[3]
- GPSAltitude (0x0006): Rational
- GPSTimeStamp (0x0007): Rational[3]
- GPSDateStamp (0x001D): ASCII

**Tags Custom:**
- UserComment (0x9286): Hash SHA-256 (ASCII)
- MakerNote (0x927C): JSON serializado con broker_id, property_id

---

### 2.7 `src/config.py` - Configuración

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    supabase_bucket: str = "field-verifications"
    
    # OSM
    osm_tile_server: str = "https://tile.openstreetmap.org"
    osm_user_agent: str = "BrokerGuardFieldVerify/0.1.0"
    osm_cache_dir: str = "./cache/osm_tiles"
    osm_cache_ttl: int = 86400  # 24 hours
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    api_debug: bool = False
    
    # Security
    secret_key: str
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 3. ESQUEMA DE BASE DE DATOS (SUPABASE)

### 3.1 Tabla: `field_verifications`

```sql
CREATE TABLE field_verifications (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- References
  broker_id UUID NOT NULL,
  property_id TEXT NOT NULL,
  
  -- Location
  lat DECIMAL(10,8) NOT NULL CHECK (lat >= -90 AND lat <= 90),
  lon DECIMAL(11,8) NOT NULL CHECK (lon >= -180 AND lon <= 180),
  altitude DECIMAL(8,2),  -- Meters above sea level
  address TEXT,
  
  -- Verification
  image_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hex
  stamped_image_url TEXT NOT NULL,
  pdf_url TEXT,
  
  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,
  -- Example metadata:
  -- {
  --   "weather": "22°C, Clear",
  --   "compass": "NE (45°)",
  --   "notes": "Inspección inicial fachada norte",
  --   "device": "iPhone 14 Pro",
  --   "app_version": "0.1.0"
  -- }
  
  -- Timestamps
  verified_at TIMESTAMPTZ NOT NULL,  -- Timestamp from photo
  created_at TIMESTAMPTZ DEFAULT NOW(),  -- Row creation time
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_image_hash ON field_verifications(image_hash);
CREATE INDEX idx_broker_property ON field_verifications(broker_id, property_id);
CREATE INDEX idx_verified_at ON field_verifications(verified_at DESC);
CREATE INDEX idx_created_at ON field_verifications(created_at DESC);
CREATE INDEX idx_metadata_gin ON field_verifications USING GIN(metadata);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_updated_at
BEFORE UPDATE ON field_verifications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Row-level security (RLS)
ALTER TABLE field_verifications ENABLE ROW LEVEL SECURITY;

-- Policy: Brokers can only see their own verifications
CREATE POLICY broker_select_own ON field_verifications
  FOR SELECT
  USING (broker_id = auth.uid());

-- Policy: Service role can insert/update all
CREATE POLICY service_role_all ON field_verifications
  FOR ALL
  USING (auth.role() = 'service_role');
```

### 3.2 Storage Bucket: `field-verifications`

**Estructura:**
```
field-verifications/
├── images/
│   └── YYYY-MM/
│       └── {hash}.png
└── pdfs/
    └── YYYY-MM/
        └── {hash}.pdf
```

**Políticas:**
```sql
-- Public read access to images and PDFs
CREATE POLICY "Public read access"
ON storage.objects FOR SELECT
USING (bucket_id = 'field-verifications');

-- Service role can insert
CREATE POLICY "Service role insert"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'field-verifications' AND
  auth.role() = 'service_role'
);
```

---

## 4. TESTING STRATEGY

### 4.1 Coverage Target
- **Mínimo:** 100% (FASE 3 requirement)
- **Tests mínimos:** 20+

### 4.2 Test Structure

```
tests/
├── __init__.py
├── conftest.py                  # Fixtures compartidos
├── test_api.py                  # 5 tests (endpoints)
├── test_geostamp.py             # 5 tests (overlay logic)
├── test_map_renderer.py         # 3 tests (OSM tiles)
├── test_verification.py         # 4 tests (hash, QR)
├── test_pdf_report.py           # 2 tests (PDF generation)
├── test_exif_handler.py         # 3 tests (EXIF read/write)
└── integration/
    └── test_full_flow.py        # 2 tests (end-to-end)
```

### 4.3 Fixtures (`conftest.py`)

```python
import pytest
from PIL import Image
import io
import base64

@pytest.fixture
def sample_image() -> Image.Image:
    """Creates a 800x600 RGB test image."""
    img = Image.new('RGB', (800, 600), color='blue')
    return img

@pytest.fixture
def sample_image_base64(sample_image) -> str:
    """Returns base64-encoded test image."""
    buffer = io.BytesIO()
    sample_image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

@pytest.fixture
def sample_coordinates() -> dict:
    return {
        "lat": -23.550520,
        "lon": -46.633308,
        "altitude": 760.5
    }

@pytest.fixture
def mock_osm_tile():
    """Returns a mock 256x256 OSM tile."""
    return Image.new('RGB', (256, 256), color='lightgrey')
```

### 4.4 Test Examples

```python
# tests/test_verification.py
def test_compute_hash_reproducible():
    """Hash should be reproducible for same input."""
    data = b"test image data"
    hash1 = compute_image_hash(data)
    hash2 = compute_image_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex

def test_verify_hash_valid():
    """Should validate correct hash."""
    data = b"test"
    hash = compute_image_hash(data)
    assert verify_image_hash(data, hash) is True

def test_verify_hash_invalid():
    """Should reject incorrect hash."""
    data = b"test"
    wrong_hash = "0" * 64
    assert verify_image_hash(data, wrong_hash) is False
```

---

## 5. DEPENDENCIAS DETALLADAS

### 5.1 Core Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| fastapi | >=0.115.0 | REST API framework | MIT |
| uvicorn[standard] | >=0.32.0 | ASGI server | BSD-3 |
| pillow | >=11.0.0 | Image processing | HPND |
| qrcode[pil] | >=8.0.0 | QR code generation | BSD |
| reportlab | >=4.2.0 | PDF generation | BSD |
| piexif | >=1.1.3 | EXIF metadata | MIT |
| pydantic | >=2.9.0 | Data validation | MIT |
| supabase | >=2.9.0 | Supabase client | MIT |
| httpx | >=0.27.0 | HTTP client (async) | BSD-3 |

### 5.2 Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.3.0 | Testing framework |
| pytest-cov | >=5.0.0 | Coverage reporting |
| pytest-asyncio | >=0.24.0 | Async test support |
| black | >=24.10.0 | Code formatter |
| ruff | >=0.7.0 | Linter |
| mypy | >=1.13.0 | Type checker |

---

## 6. RENDIMIENTO Y ESCALABILIDAD

### 6.1 Performance Targets

| Métrica | Target | Método de medición |
|---------|--------|-------------------|
| Response time (POST /stamp) | < 3s | p95 |
| Concurrent requests | 10 req/s | Load test |
| Max image size | 10 MB | Input validation |
| Memory usage | < 512 MB | Runtime monitoring |
| Disk cache size | < 1 GB | OSM tiles cache |

### 6.2 Optimizaciones

1. **OSM Tile Caching:**
   - TTL: 24 horas
   - Max cache size: 1000 tiles (~256 MB)
   - LRU eviction policy

2. **Image Processing:**
   - Resize images > 4000px width to 4000px (preserve ratio)
   - Use PIL.Image.thumbnail() for efficiency
   - JPEG quality: 85 for stamped images

3. **Async Operations:**
   - OSM tile fetching: async with httpx
   - Supabase uploads: concurrent (image + PDF)
   - PDF generation: sync (ReportLab limitation)

4. **Database:**
   - Indexes on hash, broker_id, verified_at
   - GIN index on metadata JSONB

---

## 7. SEGURIDAD

### 7.1 Validaciones de Entrada

```python
# Input validation with Pydantic
class StampRequest(BaseModel):
    image_base64: constr(min_length=100, max_length=14_000_000)  # ~10MB
    lat: confloat(ge=-90, le=90)
    lon: confloat(ge=-180, le=180)
    altitude: Optional[confloat(ge=-500, le=9000)] = None  # Dead Sea to Everest
    broker_id: UUID4
    property_id: constr(max_length=100)
    notes: Optional[constr(max_length=1000)] = None
```

### 7.2 Protecciones

1. **Rate Limiting:**
   - 10 requests/minute per IP
   - 100 requests/hour per broker_id
   - Implementar con slowapi o FastAPI middleware

2. **Authentication:**
   - Supabase JWT validation
   - Bearer token en header Authorization
   - Scope: `field-verify:write`

3. **CORS:**
   - Allowed origins from env var
   - Credentials: true
   - Methods: GET, POST

4. **Input Sanitization:**
   - HTML escape in notes field
   - File extension validation (PNG, JPEG only)
   - Base64 decode validation

---

## 8. DEPLOYMENT

### 8.1 Environment

- **OS:** Ubuntu 24.04 LTS (NEXUS-1)
- **Python:** 3.11+
- **Port:** 8002
- **Process manager:** systemd or supervisord

### 8.2 Systemd Service

```ini
# /etc/systemd/system/brokerguard-field-verify.service
[Unit]
Description=BrokerGuard Field Verify API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/brokerguard-field-verify
Environment="PATH=/opt/brokerguard-field-verify/venv/bin"
ExecStart=/opt/brokerguard-field-verify/venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 8.3 Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name field-verify.brokerguard.com;
    
    client_max_body_size 12M;
    
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 180s;
    }
}
```

---

## 9. MONITORING Y LOGGING

### 9.1 Health Checks

```python
# GET /health
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 86400,
  "dependencies": {
    "supabase": true,
    "osm": true,
    "cache": true
  }
}
```

### 9.2 Logging

```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# Structured logging
logger.info(json.dumps({
    "event": "stamp_created",
    "broker_id": broker_id,
    "hash": hash,
    "duration_ms": elapsed_time * 1000
}))
```

### 9.3 Metrics (Prometheus)

- `http_requests_total{method, endpoint, status}`
- `http_request_duration_seconds{method, endpoint}`
- `osm_tile_cache_hits_total`
- `osm_tile_cache_misses_total`
- `supabase_upload_duration_seconds`

---

## 10. PRÓXIMOS PASOS → FASE 3

### Definition of Done FASE 2:
- [x] Arquitectura documentada
- [x] Especificaciones de módulos completas
- [x] Schema de base de datos definido
- [x] pyproject.toml con dependencias
- [x] README.md con instalación
- [x] LICENSE MIT
- [x] .gitignore configurado
- [x] Estructura de directorios creada

### FASE 3 Checklist:
- [ ] Implementar `src/geostamp.py`
- [ ] Implementar `src/map_renderer.py`
- [ ] Implementar `src/verification.py`
- [ ] Implementar `src/pdf_report.py`
- [ ] Implementar `src/exif_handler.py`
- [ ] Implementar `src/api.py`
- [ ] Escribir 20+ tests (pytest)
- [ ] Alcanzar 100% cobertura
- [ ] Documentación con screenshots
- [ ] Repo público en GitHub

---

## 11. RESUMEN EJECUTIVO

✅ **Stack 100% open-source y gratis:**
- Python FastAPI + Pillow + OpenStreetMap
- Sin APIs de pago (no Google Maps, Mapbox, HERE)
- Licencia MIT - uso comercial permitido

✅ **Features MVP:**
- POST /field-verify/stamp → imagen con overlay GPS + mapa + timestamp
- Hash SHA-256 reproducible para verificación
- PDF report profesional con QR code
- Integración Supabase (PostgreSQL + Storage)

✅ **Performance targets:**
- < 3 segundos response time
- 10 req/s concurrentes
- Cache local de OSM tiles (24h TTL)

✅ **Testing:**
- 20+ tests con 100% cobertura
- Fixtures compartidos en conftest.py
- Tests unitarios + integración

✅ **Ready for FASE 3 (construcción).**

---

**Documento completado:** 29-MAY-2026  
**Próximo paso:** FASE 3 — Construcción (implementación + tests)  
**Status:** ✅ FASE 2 COMPLETA — Notificar Telegram
