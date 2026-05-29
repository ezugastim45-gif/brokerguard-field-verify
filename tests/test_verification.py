"""Tests for verification module."""

import pytest
from src.verification import (
    compute_image_hash,
    verify_image_hash,
    generate_verification_url,
    create_qr_code,
    get_image_bytes,
)
from PIL import Image


def test_compute_hash_reproducible():
    """Hash should be reproducible for same input."""
    data = b"test image data"
    hash1 = compute_image_hash(data)
    hash2 = compute_image_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


def test_compute_hash_different_inputs():
    """Different inputs should produce different hashes."""
    hash1 = compute_image_hash(b"test1")
    hash2 = compute_image_hash(b"test2")
    assert hash1 != hash2


def test_verify_hash_valid():
    """Should validate correct hash."""
    data = b"test data"
    hash_value = compute_image_hash(data)
    assert verify_image_hash(data, hash_value) is True


def test_verify_hash_invalid():
    """Should reject incorrect hash."""
    data = b"test data"
    wrong_hash = "0" * 64
    assert verify_image_hash(data, wrong_hash) is False


def test_generate_verification_url():
    """Should generate correct verification URL."""
    hash_value = "abc123"
    url = generate_verification_url(hash_value)
    assert url == "https://brokerguard.com/verify/abc123"


def test_generate_verification_url_custom_base():
    """Should use custom base URL."""
    hash_value = "abc123"
    url = generate_verification_url(hash_value, base_url="https://custom.com")
    assert url == "https://custom.com/verify/abc123"


def test_create_qr_code():
    """Should create QR code with correct size."""
    url = "https://brokerguard.com/verify/abc123"
    qr = create_qr_code(url, size=150)
    assert qr.size == (150, 150)
    assert qr.mode in ["RGB", "L", "1"]


def test_get_image_bytes():
    """Should convert PIL image to bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = get_image_bytes(img, format="PNG")
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    # Verify it's a valid PNG
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"
