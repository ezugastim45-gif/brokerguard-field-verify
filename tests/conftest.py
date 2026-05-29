"""Shared test fixtures for pytest."""

import pytest
from PIL import Image
import io
import base64
from datetime import datetime


@pytest.fixture
def sample_image() -> Image.Image:
    """Creates a 800x600 RGB test image."""
    img = Image.new("RGB", (800, 600), color="blue")
    return img


@pytest.fixture
def sample_image_base64(sample_image: Image.Image) -> str:
    """Returns base64-encoded test image."""
    buffer = io.BytesIO()
    sample_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture
def sample_coordinates() -> dict:
    """Sample GPS coordinates (São Paulo, Brazil)."""
    return {"lat": -23.550520, "lon": -46.633308, "altitude": 760.5}


@pytest.fixture
def mock_osm_tile() -> Image.Image:
    """Returns a mock 256x256 OSM tile."""
    return Image.new("RGB", (256, 256), color="lightgrey")


@pytest.fixture
def sample_timestamp() -> datetime:
    """Returns a fixed timestamp for testing."""
    return datetime(2026, 5, 29, 14, 30, 0)


@pytest.fixture
def sample_qr_code() -> Image.Image:
    """Returns a sample 150x150 QR code."""
    return Image.new("RGB", (150, 150), color="white")


@pytest.fixture
def sample_metadata() -> dict:
    """Sample verification metadata."""
    return {
        "timestamp": "2026-05-29 14:30:00 UTC",
        "lat": -23.550520,
        "lon": -46.633308,
        "altitude": 760.5,
        "address": "23°33'01.9\"S 46°37'59.9\"W",
        "broker_id": "broker-123",
        "property_id": "prop-456",
        "hash": "a" * 64,
        "weather": "22°C, Clear",
        "compass": "NE (45°)",
        "notes": "Test inspection",
        "verification_url": "https://brokerguard.com/verify/aaaa",
    }
