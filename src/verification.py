"""Image hash verification and QR code generation."""

import hashlib
from PIL import Image
import qrcode
from io import BytesIO


def compute_image_hash(image_bytes: bytes) -> str:
    """
    Computes SHA-256 hash of image bytes.

    Args:
        image_bytes: Raw bytes of the image

    Returns:
        Hex string (64 characters)

    Example:
        >>> data = b"test image data"
        >>> hash_value = compute_image_hash(data)
        >>> len(hash_value)
        64
    """
    return hashlib.sha256(image_bytes).hexdigest()


def verify_image_hash(image_bytes: bytes, claimed_hash: str) -> bool:
    """
    Verifies if image matches claimed hash.

    Args:
        image_bytes: Raw bytes of the image
        claimed_hash: The hash to verify against

    Returns:
        True if hash matches, False otherwise

    Example:
        >>> data = b"test"
        >>> hash_val = compute_image_hash(data)
        >>> verify_image_hash(data, hash_val)
        True
        >>> verify_image_hash(data, "wrong_hash")
        False
    """
    computed = compute_image_hash(image_bytes)
    return computed == claimed_hash


def generate_verification_url(hash_value: str, base_url: str = "https://brokerguard.com") -> str:
    """
    Generates public verification URL.

    Args:
        hash_value: SHA-256 hash of the image
        base_url: Base URL for the verification service

    Returns:
        Full verification URL

    Example:
        >>> url = generate_verification_url("abc123")
        >>> url
        'https://brokerguard.com/verify/abc123'
    """
    return f"{base_url}/verify/{hash_value}"


def create_qr_code(verification_url: str, size: int = 150) -> Image.Image:
    """
    Creates QR code for verification URL.

    Args:
        verification_url: URL to encode in QR code
        size: Size of QR code in pixels

    Returns:
        PIL Image of QR code

    Example:
        >>> url = "https://brokerguard.com/verify/abc123"
        >>> qr = create_qr_code(url, 150)
        >>> qr.size
        (150, 150)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Resize to exact size
    if qr_image.size != (size, size):
        qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)

    return qr_image


def get_image_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Converts PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Image as bytes

    Example:
        >>> img = Image.new('RGB', (100, 100), color='red')
        >>> img_bytes = get_image_bytes(img)
        >>> len(img_bytes) > 0
        True
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()
