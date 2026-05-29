"""EXIF metadata reading and writing for GPS data."""

import piexif
from PIL import Image
from datetime import datetime
from typing import Optional, Dict, Any
import json


def read_exif(image_path: str) -> Dict[str, Any]:
    """
    Reads EXIF metadata from image.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with parsed EXIF data

    Example:
        >>> exif = read_exif("photo.jpg")
        >>> "GPS" in exif or "0th" in exif
        True
    """
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))
        return exif_dict
    except Exception as e:
        return {}


def _decimal_to_dms(decimal: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """
    Converts decimal degrees to DMS (Degrees, Minutes, Seconds).

    Args:
        decimal: Decimal degrees (e.g., -23.550520)

    Returns:
        Tuple of ((degrees, 1), (minutes, 1), (seconds, 100))
        Seconds are multiplied by 100 for precision

    Example:
        >>> dms = _decimal_to_dms(23.550520)
        >>> dms[0]  # degrees
        (23, 1)
    """
    absolute = abs(decimal)
    degrees = int(absolute)
    minutes_decimal = (absolute - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = int((minutes_decimal - minutes) * 60 * 100)  # * 100 for precision

    return ((degrees, 1), (minutes, 1), (seconds, 100))


def write_exif(
    image: Image.Image,
    lat: float,
    lon: float,
    altitude: Optional[float],
    timestamp: datetime,
    hash_value: str,
    broker_id: str,
    property_id: str,
    output_path: str,
) -> None:
    """
    Writes GPS and custom EXIF tags to image.

    Args:
        image: PIL Image object
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        altitude: Altitude in meters (optional)
        timestamp: Timestamp of photo
        hash_value: SHA-256 hash
        broker_id: Broker UUID
        property_id: Property identifier
        output_path: Where to save image with EXIF

    Example:
        >>> from PIL import Image
        >>> from datetime import datetime
        >>> img = Image.new('RGB', (100, 100))
        >>> write_exif(img, -23.55, -46.63, 760.5, datetime.now(),
        ...            "abc123", "broker-1", "prop-1", "output.jpg")
    """
    # Create EXIF dict
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # GPS coordinates
    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"

    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = _decimal_to_dms(lat)
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = _decimal_to_dms(lon)

    # Altitude
    if altitude is not None:
        altitude_ref = 0 if altitude >= 0 else 1  # 0 = above sea level, 1 = below
        exif_dict["GPS"][piexif.GPSIFD.GPSAltitudeRef] = altitude_ref
        exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (int(abs(altitude) * 100), 100)

    # GPS timestamp
    exif_dict["GPS"][piexif.GPSIFD.GPSDateStamp] = timestamp.strftime("%Y:%m:%d")
    exif_dict["GPS"][piexif.GPSIFD.GPSTimeStamp] = (
        (timestamp.hour, 1),
        (timestamp.minute, 1),
        (timestamp.second, 1),
    )

    # EXIF timestamp
    datetime_str = timestamp.strftime("%Y:%m:%d %H:%M:%S")
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime_str.encode()
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = datetime_str.encode()

    # Custom data in UserComment (hash)
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = f"hash:{hash_value}".encode()

    # MakerNote with broker and property info (JSON)
    maker_note_data = {"broker_id": broker_id, "property_id": property_id, "hash": hash_value}
    exif_dict["Exif"][piexif.ExifIFD.MakerNote] = json.dumps(maker_note_data).encode()

    # Convert to bytes and save
    exif_bytes = piexif.dump(exif_dict)
    image.save(output_path, "JPEG", exif=exif_bytes, quality=95)


def exif_to_dict(exif_bytes: bytes) -> Dict[str, Any]:
    """
    Converts EXIF bytes to readable dict.

    Args:
        exif_bytes: Raw EXIF bytes

    Returns:
        Parsed EXIF dictionary

    Example:
        >>> exif = piexif.dump({"0th": {}, "GPS": {}})
        >>> result = exif_to_dict(exif)
        >>> "GPS" in result or "0th" in result
        True
    """
    try:
        return piexif.load(exif_bytes)
    except Exception:
        return {}
