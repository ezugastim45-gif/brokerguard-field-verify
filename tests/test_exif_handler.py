"""Tests for EXIF handler module."""

import pytest
from src.exif_handler import read_exif, write_exif, _decimal_to_dms, exif_to_dict
from PIL import Image
from datetime import datetime
import piexif
import tempfile
import os


def test_decimal_to_dms_positive():
    """Should convert positive decimal to DMS."""
    dms = _decimal_to_dms(23.550520)
    degrees, minutes, seconds = dms
    assert degrees == (23, 1)
    assert minutes == (33, 1)
    assert seconds[0] > 0  # seconds with precision


def test_decimal_to_dms_negative():
    """Should convert negative decimal to DMS (absolute value)."""
    dms = _decimal_to_dms(-46.633308)
    degrees, minutes, seconds = dms
    assert degrees == (46, 1)
    assert minutes == (37, 1)
    assert seconds[0] > 0


def test_write_and_read_exif(sample_image: Image.Image, sample_timestamp: datetime):
    """Should write EXIF data and read it back."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Write EXIF
        write_exif(
            image=sample_image,
            lat=-23.550520,
            lon=-46.633308,
            altitude=760.5,
            timestamp=sample_timestamp,
            hash_value="test_hash_123",
            broker_id="broker-1",
            property_id="prop-1",
            output_path=output_path,
        )

        # Read back
        exif_data = read_exif(output_path)

        # Verify GPS data exists
        assert "GPS" in exif_data
        assert piexif.GPSIFD.GPSLatitude in exif_data["GPS"]
        assert piexif.GPSIFD.GPSLongitude in exif_data["GPS"]

    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_read_exif_no_file():
    """Should return empty dict for non-existent file."""
    exif_data = read_exif("nonexistent.jpg")
    assert exif_data == {}


def test_exif_to_dict():
    """Should convert EXIF bytes to dict."""
    exif_dict = {"0th": {}, "GPS": {}, "Exif": {}}
    exif_bytes = piexif.dump(exif_dict)
    result = exif_to_dict(exif_bytes)
    assert isinstance(result, dict)
    assert "GPS" in result or "0th" in result


def test_exif_to_dict_invalid():
    """Should return empty dict for invalid EXIF."""
    result = exif_to_dict(b"invalid_data")
    assert result == {}
