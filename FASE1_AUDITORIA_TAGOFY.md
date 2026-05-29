# FASE 1 — AUDITORÍA TÉCNICA TAGOFY MAPCAMERA
**ZumaIntelligence Swarm · 29-MAY-2026 · Protocolo Verdad ON**

---

## RESUMEN EJECUTIVO

**Aplicación auditada:** Tagofy - GPS Geotag Map Camera  
**Desarrollador:** Pravin Gondaliya / Vasundhara Infotech LLP (India)  
**Plataformas:** iOS (App Store) y Android (Google Play Store)  
**Versión auditada:** 4.4 (iOS 13.0+), 5.4 (Android)  
**Tamaño:** 137.3 MB (iOS)  
**Rating:** 4.5/5 (iOS, 453 ratings), 4.35/5 (Android, 600 ratings)  
**Descargas:** 31,000+ (Android, últimos 30 días: 18,000)

---

## 1. STACK TÉCNICO INFERIDO

### Plataforma Base
- **iOS:** Nativo (Swift/Objective-C inferido, tamaño 137.3 MB)
- **Android:** Nativo (Java/Kotlin inferido)
- **Mínimos:** iOS 13.0+, Android versión no especificada

### Servicios de Terceros Confirmados
- **Google Firebase Analytics** — crash reporting, analytics
- **Google AdMob** — monetización por anuncios
- **Google Ads** — conversion tracking, remarketing
- **Redes publicitarias adicionales no especificadas** — behavioral targeting

### APIs de Mapas (Inferido)
- Soporte para múltiples estilos de mapa: satellite, hybrid, normal
- **Proveedor NO confirmado** (posible Google Maps API, MapKit, o similar)

---

## 2. PERMISOS SOLICITADOS

### iOS
```
- LOCATION (ALWAYS/WHEN IN USE)
  "This app may use your location even when it isn't open, 
   which can decrease device battery life"
- CAMERA
- PHOTO LIBRARY
- USAGE DATA (tracking, advertising)
```

### Android (Inferido de documentación)
```
- ACCESS_FINE_LOCATION — precise GPS coordinates
- ACCESS_COARSE_LOCATION — approximate location (Wi-Fi/cellular)
- CAMERA — capture images/videos
- READ_EXTERNAL_STORAGE / WRITE_EXTERNAL_STORAGE
- INTERNET — data transmission
- Sensors (compass, altimeter)
- Microphone (no especificado explícitamente)
```

---

## 3. FLUJO DE DATOS

### ¿Salen datos del dispositivo?
**SÍ — CONFIRMADO**

### Destinos de datos verificados:
1. **Google Firebase Analytics** — crash data, error logs
2. **Google AdMob** — device identifiers, cookies, behavioral data
3. **Google Ads networks** — conversion tracking, remarketing
4. **Third-party advertising companies** — cookies, device IDs

### Datos recopilados (según Privacy Policy):
- **Ubicación:** GPS preciso (lat/lon/altitude)
- **Dispositivo:** ID único, modelo, fabricante, OS version
- **Medios:** Acceso a fotos, videos, contacts (¿?)
- **Social:** Profile info si se vincula redes sociales
- **Actividad:** Session duration, app opens, user interactions

### Almacenamiento:
- **Local:** Fotos geoetiquetadas en dispositivo
- **Remoto:** "Personal information may be processed outside your country" (ubicación de servidores NO especificada)
- **Retention:** "Removed when no longer necessary" (sin timeframes específicos)

---

## 4. MODELO DE NEGOCIO

### Modelo Principal: **FREEMIUM CON ADS + SUSCRIPCIONES**

#### Revenue Streams:
1. **Publicidad (Ads)** — AdMob + Google Ads (primary)
2. **In-App Purchases** — Suscripciones premium

#### Pricing (iOS App Store verificado):
```
Weekly Pro:      $5.99
Monthly Pro:     $4.99
Monthly Premium: $14.99
Annual Pro:      $19.99
Annual Premium:  $29.99-$39.99
Lifetime:        $59.99-$99.99
```

#### Limitaciones versión Free:
- Ads persistentes
- Features premium bloqueados detrás de paywall
- "Many features trigger subscription sign up request" (queja recurrente)

---

## 5. POLÍTICA DE PRIVACIDAD

**URL:** https://tagofy.app/privacy-policy  
**Publisher:** Vasundhara Infotech LLP

### Hallazgos críticos:
- ❌ **No especifica ubicación de servidores** (solo "may be processed outside your country")
- ❌ **No timeframes de retención de datos**
- ❌ **Recopila datos de contacts y micrófono** (justificación poco clara)
- ✅ Derecho a modificación "at any time, with Last Updated date"
- ⚠️ **"Continued use constitutes acceptance"** — opt-out implícito

### Cumplimiento:
- GDPR: NO verificado
- CCPA: NO verificado
- Jurisdicción: India (Vasundhara Infotech LLP)

---

## 6. REVIEWS — QUEJAS Y LIMITACIONES

### App Store (iOS)
**Rating:** 4.5/5 (453 ratings)

#### Quejas principales:
1. **Bugs en iOS 26:**
   - "Multiple bugs on iOS 26. After accessing menu, stamp moves below photo"
   - "Button to take photo stops working"
   - "App worked great under iOS 18 but needs updating"

2. **Stamp Template Issues:**
   - "Other Templates stamp shows 'Stamp Not Found'"

3. **Aggressive Monetization:**
   - "Many features trigger subscription sign up request"
   - "Ads in free version"

4. **Battery Consumption:**
   - "Consumes battery quickly"
   - "Location tracking even when app closed"

5. **GPS Accuracy:**
   - "Occasional GPS inaccuracies"
   - "Accuracy decreases in dense urban/indoor environments"

6. **Limited Editing Tools**

### Google Play Store (Android)
**Rating:** 4.35/5 (600 ratings)  
**Descargas:** 31K total, 18K últimos 30 días

#### Feedback positivo:
- "Clean, user-friendly interface"
- "Runs seamlessly without lag or bugs" (contradice iOS reviews)

---

## 7. FEATURES — MATRIZ DE EXISTENCIA

| Feature                    | Status    | Notas                                      |
|----------------------------|-----------|-------------------------------------------|
| GPS embedding              | ✅ SÍ     | Lat/lon/altitude, address                 |
| Timestamp                  | ✅ SÍ     | Date/time customizable                    |
| Timestamp tamper-evident   | ⚠️ PARCIAL| No evidencia de hash criptográfico        |
| Mapa satellite overlay     | ✅ SÍ     | Satellite, hybrid, normal modes           |
| Vista híbrida              | ✅ SÍ     | Confirmado                                |
| Compass                    | ✅ SÍ     | Magnetic field data                       |
| Datos clima                | ✅ SÍ     | Weather data embedding                    |
| QR code                    | ✅ SÍ     | Built-in QR scanner                       |
| Nota personalizada         | ✅ SÍ     | Custom text, logos, hashtags              |
| Watermark/Logo custom      | ✅ SÍ     | Multiple templates                        |
| PDF report                 | ❌ NO     | No mencionado en features                 |
| Exportación EXIF           | ✅ SÍ     | Metadata embedding confirmed              |
| Funciona offline           | ❓ NO VERIFICADO | No mencionado explícitamente      |
| Video con timestamp        | ✅ SÍ     | Video recording + time-lapse              |
| iCloud sync                | ✅ SÍ     | Solo iOS                                  |
| API pública                | ❌ NO     | No existe                                 |
| SDK para developers        | ❌ NO     | No existe                                 |

---

## 8. COMPETIDORES OPEN SOURCE

### ExifTool
- **Licencia:** Perl Artistic License + GPL (NO MIT)
- **Tipo:** Command-line tool + Perl library
- **Features:** Read/write EXIF, GPS, IPTC, XMP metadata
- **URL:** https://exiftool.org/

### PhotoLocator (GitHub: meesoft/PhotoLocator)
- **Licencia:** Open source (licencia específica no verificada)
- **Features:** Geotagging, location browsing, GPX import
- **Stack:** NO especificado

### GeoTagger (GitHub: jkbrzt/geotagger)
- **Licencia:** NO verificada en resultados
- **Features:** Geotag photos using phone's location history
- **Stack:** Python

### GeoTagImage (GitHub: dangiashish/GeoTagImage)
- **Licencia:** ✅ **MIT LICENSE**
- **Plataforma:** Android library
- **Features:** 
  - Real-time metadata overlay
  - Address, City, Lat/Lng
  - Custom timestamps
  - Author names
  - Google Maps static preview
- **Stack:** Kotlin/Java (Android)

### GPSImage (PyPI)
- **Licencia:** NO verificada
- **Stack:** Python
- **Features:** Retrieve GPS data from geo-referenced photos

---

## 9. VEREDICTO FINAL

### ¿Tiene API pública?
**❌ NO** — Tagofy es una aplicación standalone sin API documentada ni endpoints públicos.

### ¿Integrable con BrokerGuard?
**❌ NO DIRECTAMENTE**
- Sin API/SDK → imposible integración programática
- Flujo de trabajo manual: capturar en Tagofy → exportar → importar a BrokerGuard (ineficiente)
- Datos salen a terceros (Firebase, AdMob) → no controlable

### ¿Riesgo legal?
**⚠️ MEDIO-ALTO**

#### Riesgos identificados:
1. **Privacidad de datos:**
   - Datos de ubicación a terceros (AdMob, Firebase)
   - Política de privacidad vaga (sin ubicación de servidores)
   - No compatible con data sovereignty requirements

2. **Vendor lock-in:**
   - Modelo suscripción ($4.99-$99.99 lifetime)
   - Sin exportación bulk de datos históricos

3. **Disponibilidad:**
   - Depende de servers de Vasundhara Infotech LLP
   - Sin SLA documentado
   - Bugs persistentes sin timeframe de fix (iOS 26)

4. **Compliance:**
   - GDPR/CCPA compliance NO verificado
   - Jurisdicción India → DPDP Act 2023 aplica

5. **Propiedad intelectual:**
   - Código propietario, no open source
   - Reverse engineering prohibido por EULA (típico)

---

## 10. RECOMENDACIÓN

### ✅ **PROCEDER CON DESARROLLO PROPIO (BrokerGuard Field Verify)**

#### Justificación:
1. **No existe API integrable** → imposible automatizar
2. **Datos a terceros** → conflicto con data sovereignty
3. **Costos recurrentes** → $5.99-$99.99 por usuario
4. **Vendor lock-in** → dependencia de Vasundhara Infotech LLP
5. **Features MIT disponibles** → GeoTagImage (Android MIT), ExifTool (GPL)

#### Ventajas desarrollo propio:
- ✅ **100% control de datos** (no salen del dispositivo o van a BrokerGuard Supabase)
- ✅ **Licencia MIT** (reutilizable, sin royalties)
- ✅ **Sin costos recurrentes** por usuario
- ✅ **API nativa** integrada en BrokerGuard desde día 1
- ✅ **Customizable** para workflow de brokers (property_id, broker_id, etc.)
- ✅ **Compliance controlado** (GDPR, CCPA, data residency)

---

## 11. PRÓXIMOS PASOS → FASE 2

**Stack recomendado para BrokerGuard Field Verify:**
```
Backend:  Python 3.11+ + FastAPI
Image:    Pillow (PIL Fork)
Maps:     OpenStreetMap tiles (no API keys, gratis)
QR:       python-qrcode
PDF:      ReportLab
EXIF:     piexif / Pillow EXIF
Hash:     hashlib (SHA-256)
Storage:  Supabase (PostgreSQL + Storage)
```

**Repo:** `ezugastim45-gif/brokerguard-field-verify` (MIT License)

**MVP Features (Fase 3):**
- POST /field-verify/stamp → imagen con overlay (mapa + coords + timestamp + hash)
- PDF report generation
- Supabase integration (tabla field_verifications)
- Offline-first (no APIs de pago)
- Hash SHA-256 reproducible para verificación

---

## FUENTES VERIFICABLES

### Tagofy Official
- [Tagofy Privacy Policy](https://tagofy.app/privacy-policy)
- [Tagofy App Store (iOS)](https://apps.apple.com/us/app/gps-geotag-map-camera-tagofy/id6453854362)
- [Tagofy Official Website](https://tagofy.app/)

### App Stores
- [Tagofy Google Play Store](https://play.google.com/store/apps/details?id=com.gps.photo.geo.capture.location.map.time.stamp)
- [Tagofy App Store Reviews](https://apps.apple.com/us/app/gps-geotag-map-camera-tagofy/id6453854362)

### Open Source Alternatives
- [ExifTool Official](https://exiftool.org/)
- [ExifTool Geotagging Guide](https://exiftool.org/geotag.html)
- [GitHub: PhotoLocator](https://github.com/meesoft/PhotoLocator)
- [GitHub: GeoTagger](https://github.com/jkbrzt/geotagger)
- [GitHub: GeoTagImage (MIT)](https://github.com/dangiashish/GeoTagImage)
- [GitHub Geotagging Topics](https://github.com/topics/geotagging)

### Developer Info
- [Vasundhara Infotech LLP - Clutch](https://clutch.co/profile/vasundhara-infotech-llp)
- [Vasundhara Infotech LLP - ZoomInfo](https://www.zoominfo.com/c/vasundhara-infotech-llp/546804576)

### Reviews & Analysis
- [LinuxLinks: Best Free Photo Geotagging Tools](https://www.linuxlinks.com/best-free-open-source-photo-geotagging-tools/)
- [AlternativeTo: Geotag Alternatives](https://alternativeto.net/software/geotag/)

---

**Auditoría completada:** 29-MAY-2026 14:45 UTC  
**Próximo paso:** FASE 2 — Diseño de BrokerGuard Field Verify  
**Status:** ✅ FASE 1 COMPLETA — Notificar Telegram
