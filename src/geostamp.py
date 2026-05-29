"""Main geostamp overlay engine - combines image, GPS, timestamp, and map."""

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import Optional, Tuple
import math


def format_coordinates(lat: float, lon: float) -> str:
    """
    Formats GPS coordinates in DMS (Degrees Minutes Seconds).

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)

    Returns:
        Formatted string like "23°33'01.9\"S 46°38'00.0\"W"

    Example:
        >>> format_coordinates(-23.550520, -46.633308)
        '23°33\\'01.9"S 46°37\\'59.9"W'
    """

    def decimal_to_dms(decimal: float, is_latitude: bool) -> str:
        absolute = abs(decimal)
        degrees = int(absolute)
        minutes_decimal = (absolute - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60

        # Determine direction
        if is_latitude:
            direction = "N" if decimal >= 0 else "S"
        else:
            direction = "E" if decimal >= 0 else "W"

        return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"

    lat_str = decimal_to_dms(lat, True)
    lon_str = decimal_to_dms(lon, False)

    return f"{lat_str} {lon_str}"


def calculate_compass(bearing: float) -> str:
    """
    Converts bearing (0-360°) to compass direction.

    Args:
        bearing: Bearing in degrees (0-360)

    Returns:
        Compass direction (N, NE, E, SE, S, SW, W, NW)

    Example:
        >>> calculate_compass(0)
        'N'
        >>> calculate_compass(45)
        'NE'
        >>> calculate_compass(180)
        'S'
    """
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((bearing + 22.5) / 45) % 8
    return directions[index]


def calculate_bearing(lat: float, lon: float) -> float:
    """
    Calculate bearing from coordinates (simplified).
    For demo purposes, we derive from longitude.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Bearing in degrees (0-360)
    """
    # Simplified: derive bearing from longitude
    # In real implementation, would use device compass or calculate from movement
    bearing = (lon + 180) % 360
    return bearing


def create_geostamp(
    image: Image.Image,
    lat: float,
    lon: float,
    altitude: Optional[float],
    timestamp: datetime,
    map_image: Optional[Image.Image],
    qr_code: Optional[Image.Image],
    hash_value: str,
    notes: Optional[str] = None,
) -> Image.Image:
    """
    Composes final image with GPS, timestamp, map, and overlays.

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
    │ 📝 Notes: ...                      │
    └────────────────────────────────────┘

    Args:
        image: Original PIL Image
        lat: Latitude
        lon: Longitude
        altitude: Altitude in meters (optional)
        timestamp: Photo timestamp
        map_image: Cropped OSM tile (200x150)
        qr_code: QR code image (150x150)
        hash_value: SHA-256 hash (first 16 chars shown)
        notes: Optional user notes

    Returns:
        PIL Image with overlay
    """
    # Calculate overlay height
    overlay_height = 270  # Increased to fit all elements

    # Create new image with space for overlay
    width = image.width
    new_height = image.height + overlay_height
    result = Image.new("RGB", (width, new_height), color="white")

    # Paste original image at top
    result.paste(image, (0, 0))

    # Create overlay rectangle (semi-transparent black)
    overlay = Image.new("RGBA", (width, overlay_height), color=(0, 0, 0, 200))
    overlay_draw = ImageDraw.Draw(overlay)

    # Try to load font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Text color
    text_color = (255, 255, 255)  # White

    # Starting Y position for text
    y_pos = 10
    x_padding = 15

    # Line 1: Coordinates
    coords_text = f"📍 {format_coordinates(lat, lon)}"
    overlay_draw.text((x_padding, y_pos), coords_text, fill=text_color, font=font)
    y_pos += 25

    # Line 2: Altitude and Compass
    bearing = calculate_bearing(lat, lon)
    compass = calculate_compass(bearing)
    alt_text = f"📏 Alt: {altitude:.1f}m" if altitude else "📏 Alt: N/A"
    compass_text = f"🧭 {compass} ({bearing:.0f}°)"
    line2_text = f"{alt_text}  |  {compass_text}"
    overlay_draw.text((x_padding, y_pos), line2_text, fill=text_color, font=font)
    y_pos += 25

    # Line 3: Timestamp
    timestamp_text = f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    overlay_draw.text((x_padding, y_pos), timestamp_text, fill=text_color, font=font)
    y_pos += 30

    # Line 4: Hash (first 32 chars)
    hash_short = hash_value[:32] + "..." if len(hash_value) > 32 else hash_value
    hash_text = f"#️⃣ Hash: {hash_short}"
    overlay_draw.text((x_padding, y_pos), hash_text, fill=text_color, font=font_small)
    y_pos += 25

    # Line 5: Notes (if provided)
    if notes:
        notes_short = notes[:60] + "..." if len(notes) > 60 else notes
        notes_text = f"📝 {notes_short}"
        overlay_draw.text((x_padding, y_pos), notes_text, fill=text_color, font=font_small)

    # Paste overlay onto result
    result_rgba = result.convert("RGBA")
    result_rgba.paste(overlay, (0, image.height), overlay)
    result = result_rgba.convert("RGB")

    # Add map image (bottom left)
    if map_image:
        map_x = x_padding
        map_y = image.height + overlay_height - map_image.height - 10
        # Draw white border around map
        map_with_border = Image.new(
            "RGB", (map_image.width + 4, map_image.height + 4), color="white"
        )
        map_with_border.paste(map_image, (2, 2))
        result.paste(map_with_border, (map_x, map_y))

    # Add QR code (bottom right)
    if qr_code:
        qr_x = width - qr_code.width - x_padding
        qr_y = image.height + overlay_height - qr_code.height - 10
        # Draw white border around QR
        qr_with_border = Image.new("RGB", (qr_code.width + 4, qr_code.height + 4), color="white")
        qr_with_border.paste(qr_code, (2, 2))
        result.paste(qr_with_border, (qr_x, qr_y))

    return result


def resize_image_if_needed(image: Image.Image, max_width: int = 2000) -> Image.Image:
    """
    Resizes image if width exceeds max_width, maintaining aspect ratio.

    Args:
        image: PIL Image
        max_width: Maximum width in pixels

    Returns:
        Resized image (or original if already smaller)

    Example:
        >>> img = Image.new('RGB', (3000, 2000))
        >>> resized = resize_image_if_needed(img, 2000)
        >>> resized.width
        2000
    """
    if image.width <= max_width:
        return image

    ratio = max_width / image.width
    new_height = int(image.height * ratio)
    return image.resize((max_width, new_height), Image.Resampling.LANCZOS)
