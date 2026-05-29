"""Tests for geostamp module."""

import pytest
from src.geostamp import (
    format_coordinates,
    calculate_compass,
    calculate_bearing,
    create_geostamp,
    resize_image_if_needed,
)
from PIL import Image
from datetime import datetime


def test_format_coordinates():
    """Should format coordinates in DMS format."""
    result = format_coordinates(-23.550520, -46.633308)
    assert "°" in result
    assert "'" in result
    assert '"' in result
    assert "S" in result  # South
    assert "W" in result  # West


def test_format_coordinates_positive():
    """Should format positive coordinates correctly."""
    result = format_coordinates(51.5074, -0.1278)
    assert "N" in result  # North
    assert "W" in result  # West


def test_calculate_compass():
    """Should calculate compass directions correctly."""
    assert calculate_compass(0) == "N"
    assert calculate_compass(45) == "NE"
    assert calculate_compass(90) == "E"
    assert calculate_compass(135) == "SE"
    assert calculate_compass(180) == "S"
    assert calculate_compass(225) == "SW"
    assert calculate_compass(270) == "W"
    assert calculate_compass(315) == "NW"
    assert calculate_compass(360) == "N"


def test_calculate_bearing():
    """Should calculate bearing from coordinates."""
    bearing = calculate_bearing(0, 0)
    assert 0 <= bearing < 360


def test_create_geostamp(
    sample_image: Image.Image,
    mock_osm_tile: Image.Image,
    sample_qr_code: Image.Image,
    sample_timestamp: datetime,
):
    """Should create stamped image with overlay."""
    result = create_geostamp(
        image=sample_image,
        lat=-23.550520,
        lon=-46.633308,
        altitude=760.5,
        timestamp=sample_timestamp,
        map_image=mock_osm_tile,
        qr_code=sample_qr_code,
        hash_value="a" * 64,
        notes="Test note",
    )

    # Result should be larger (original + overlay)
    assert result.height > sample_image.height
    assert result.width == sample_image.width
    assert result.mode == "RGB"


def test_create_geostamp_without_optional(
    sample_image: Image.Image, sample_timestamp: datetime
):
    """Should create stamp without map, QR, or notes."""
    result = create_geostamp(
        image=sample_image,
        lat=-23.550520,
        lon=-46.633308,
        altitude=None,
        timestamp=sample_timestamp,
        map_image=None,
        qr_code=None,
        hash_value="abc123",
        notes=None,
    )

    assert result.height > sample_image.height
    assert result.width == sample_image.width


def test_resize_image_if_needed():
    """Should resize large images."""
    large_image = Image.new("RGB", (3000, 2000), color="red")
    resized = resize_image_if_needed(large_image, max_width=2000)

    assert resized.width == 2000
    assert resized.height < large_image.height  # Aspect ratio maintained


def test_resize_image_already_small():
    """Should not resize if already under max_width."""
    small_image = Image.new("RGB", (800, 600), color="blue")
    result = resize_image_if_needed(small_image, max_width=2000)

    assert result.width == 800
    assert result.height == 600
