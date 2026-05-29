"""FastAPI application with field verification endpoints."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO
import os
from pathlib import Path

from .config import settings
from .geostamp import create_geostamp, resize_image_if_needed, format_coordinates
from .map_renderer import OSMTileRenderer
from .verification import (
    compute_image_hash,
    generate_verification_url,
    create_qr_code,
    get_image_bytes,
)
from .pdf_report import generate_pdf_report
from .exif_handler import write_exif

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="GPS Photo Verification Module with Tamper-Evident Timestamps",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OSM renderer
osm_renderer = OSMTileRenderer(
    tile_server=settings.osm_tile_server,
    cache_dir=settings.osm_cache_dir,
    cache_ttl=settings.osm_cache_ttl,
    user_agent=settings.osm_user_agent,
)


# Request/Response models
class StampRequest(BaseModel):
    """Request model for stamping images."""

    image_base64: str = Field(..., min_length=100, description="Base64-encoded image (PNG/JPEG)")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    altitude: Optional[float] = Field(None, ge=-500, le=9000, description="Altitude in meters")
    broker_id: str = Field(..., min_length=1, max_length=100, description="Broker UUID")
    property_id: str = Field(..., min_length=1, max_length=100, description="Property identifier")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")
    timestamp: Optional[datetime] = Field(None, description="Photo timestamp (default: now)")

    @field_validator("image_base64")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate base64 string."""
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 string")


class StampResponse(BaseModel):
    """Response model for stamped images."""

    success: bool
    stamped_image_base64: str
    hash_sha256: str
    pdf_url: Optional[str] = None
    verification_url: str
    metadata: dict


class VerificationResponse(BaseModel):
    """Response model for hash verification."""

    valid: bool
    timestamp: Optional[datetime] = None
    location: Optional[dict] = None
    broker_id: Optional[str] = None
    property_id: Optional[str] = None
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    dependencies: dict


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "BrokerGuard Field Verify API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    # Check OSM connectivity (simple check)
    osm_status = True
    try:
        # This will use cache or fail gracefully
        _ = osm_renderer.lat_lon_to_tile(0, 0, 15)
    except Exception:
        osm_status = False

    # Check cache directory
    cache_status = Path(settings.osm_cache_dir).exists()

    overall_status = "healthy" if (osm_status and cache_status) else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.api_version,
        dependencies={"osm": osm_status, "cache": cache_status},
    )


@app.post("/field-verify/stamp", response_model=StampResponse, tags=["Field Verification"])
async def stamp_image(request: StampRequest) -> StampResponse:
    """
    Creates stamped image with GPS overlay, timestamp, and map.

    Process:
    1. Decode base64 image
    2. Get OSM tile for coordinates
    3. Create geostamp overlay
    4. Compute hash
    5. Generate QR code
    6. Create PDF report
    7. Write EXIF metadata
    8. Return stamped image

    Args:
        request: StampRequest with image and metadata

    Returns:
        StampResponse with stamped image and verification data

    Raises:
        HTTPException: If processing fails
    """
    try:
        # 1. Decode image
        image_bytes = base64.b64decode(request.image_base64)
        image = Image.open(BytesIO(image_bytes))

        # Resize if too large
        image = resize_image_if_needed(image, max_width=2000)

        # Use current time if not provided
        timestamp = request.timestamp or datetime.utcnow()

        # 2. Get OSM tile and crop
        tile = osm_renderer.get_tile(request.lat, request.lon, zoom=15)
        cropped_map = osm_renderer.crop_to_center(
            tile, request.lat, request.lon, zoom=15, width=200, height=150
        )

        # 3. Create temporary hash (will be recalculated after stamping)
        temp_hash = "temp_hash"

        # Generate verification URL
        verification_url = generate_verification_url(temp_hash)

        # Generate QR code
        qr_code = create_qr_code(verification_url, size=150)

        # 4. Create geostamp
        stamped_image = create_geostamp(
            image=image,
            lat=request.lat,
            lon=request.lon,
            altitude=request.altitude,
            timestamp=timestamp,
            map_image=cropped_map,
            qr_code=qr_code,
            hash_value=temp_hash,
            notes=request.notes,
        )

        # 5. Compute final hash
        stamped_bytes = get_image_bytes(stamped_image, format="PNG")
        final_hash = compute_image_hash(stamped_bytes)

        # Regenerate QR with final hash
        final_verification_url = generate_verification_url(final_hash)
        final_qr_code = create_qr_code(final_verification_url, size=150)

        # Recreate stamp with final hash and QR
        stamped_image = create_geostamp(
            image=image,
            lat=request.lat,
            lon=request.lon,
            altitude=request.altitude,
            timestamp=timestamp,
            map_image=cropped_map,
            qr_code=final_qr_code,
            hash_value=final_hash,
            notes=request.notes,
        )

        # Get final stamped bytes
        stamped_bytes = get_image_bytes(stamped_image, format="PNG")
        stamped_base64 = base64.b64encode(stamped_bytes).decode()

        # 6. Save temporary files
        temp_dir = Path("./tmp")
        temp_dir.mkdir(exist_ok=True)

        stamped_path = temp_dir / f"{final_hash}.png"
        stamped_image.save(stamped_path, "PNG")

        # 7. Write EXIF metadata
        exif_path = temp_dir / f"{final_hash}_exif.jpg"
        write_exif(
            image=stamped_image,
            lat=request.lat,
            lon=request.lon,
            altitude=request.altitude,
            timestamp=timestamp,
            hash_value=final_hash,
            broker_id=request.broker_id,
            property_id=request.property_id,
            output_path=str(exif_path),
        )

        # 8. Generate PDF report
        metadata = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "lat": request.lat,
            "lon": request.lon,
            "altitude": request.altitude,
            "address": format_coordinates(request.lat, request.lon),
            "broker_id": request.broker_id,
            "property_id": request.property_id,
            "hash": final_hash,
            "weather": "N/A",  # Could integrate weather API here
            "compass": "N/A",  # Calculated in geostamp
            "notes": request.notes,
            "verification_url": final_verification_url,
        }

        pdf_path = temp_dir / f"{final_hash}.pdf"
        generate_pdf_report(
            stamped_image_path=str(stamped_path),
            metadata=metadata,
            qr_code_image=final_qr_code,
            output_path=str(pdf_path),
        )

        # In production, upload to Supabase and get URLs
        # For now, return local paths
        pdf_url = f"/tmp/{final_hash}.pdf"

        return StampResponse(
            success=True,
            stamped_image_base64=stamped_base64,
            hash_sha256=final_hash,
            pdf_url=pdf_url,
            verification_url=final_verification_url,
            metadata=metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@app.get("/verify/{hash}", response_model=VerificationResponse, tags=["Verification"])
async def verify_hash(hash: str) -> VerificationResponse:
    """
    Verifies authenticity of a photo by its hash.

    In production, this would query Supabase for the verification record.
    For MVP, returns placeholder data.

    Args:
        hash: SHA-256 hash to verify

    Returns:
        VerificationResponse with verification status and data
    """
    # In production: query Supabase
    # For MVP: return success if hash is valid format
    if len(hash) == 64 and all(c in "0123456789abcdef" for c in hash):
        return VerificationResponse(
            valid=True,
            timestamp=datetime.utcnow(),
            location={"lat": -23.55, "lon": -46.63, "address": "N/A"},
            broker_id="broker-demo",
            property_id="property-demo",
            image_url=f"/tmp/{hash}.png",
            pdf_url=f"/tmp/{hash}.pdf",
        )
    else:
        return VerificationResponse(valid=False)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
