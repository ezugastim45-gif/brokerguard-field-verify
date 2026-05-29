"""OpenStreetMap tile rendering and caching."""

import math
import time
import os
import json
from pathlib import Path
from PIL import Image
import httpx
from typing import Tuple, Optional


class OSMTileRenderer:
    """
    Renders OpenStreetMap tiles and crops to specific coordinates.
    Implements local cache with TTL.
    """

    def __init__(
        self,
        tile_server: str = "https://tile.openstreetmap.org",
        cache_dir: str = "./cache/osm_tiles",
        cache_ttl: int = 86400,
        user_agent: str = "BrokerGuardFieldVerify/0.1.0",
    ):
        """
        Initialize OSM tile renderer.

        Args:
            tile_server: OSM tile server URL
            cache_dir: Directory for tile cache
            cache_ttl: Cache time-to-live in seconds
            user_agent: User agent for OSM requests
        """
        self.tile_server = tile_server.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl
        self.user_agent = user_agent
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """
        Converts lat/lon to tile coordinates.
        Based on: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            zoom: Zoom level (0-18)

        Returns:
            Tuple of (x, y) tile coordinates

        Example:
            >>> renderer = OSMTileRenderer()
            >>> x, y = renderer.lat_lon_to_tile(51.5074, -0.1278, 15)
            >>> isinstance(x, int) and isinstance(y, int)
            True
        """
        n = 2.0**zoom
        x = int((lon + 180.0) / 360.0 * n)
        lat_rad = math.radians(lat)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)

    def _get_cache_path(self, zoom: int, x: int, y: int) -> Path:
        """Returns cache file path for tile."""
        return self.cache_dir / str(zoom) / str(x) / f"{y}.png"

    def _get_metadata_path(self, zoom: int, x: int, y: int) -> Path:
        """Returns metadata file path for tile."""
        return self.cache_dir / str(zoom) / str(x) / f"{y}.meta.json"

    def _is_cache_valid(self, zoom: int, x: int, y: int) -> bool:
        """Checks if cached tile is still valid (not expired)."""
        cache_path = self._get_cache_path(zoom, x, y)
        meta_path = self._get_metadata_path(zoom, x, y)

        if not cache_path.exists() or not meta_path.exists():
            return False

        try:
            with open(meta_path, "r") as f:
                metadata = json.load(f)
            expires_at = metadata.get("expires_at", 0)
            return time.time() < expires_at
        except Exception:
            return False

    def _save_tile_to_cache(self, zoom: int, x: int, y: int, tile_image: Image.Image) -> None:
        """Saves tile to cache with metadata."""
        cache_path = self._get_cache_path(zoom, x, y)
        meta_path = self._get_metadata_path(zoom, x, y)

        # Create directories
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Save image
        tile_image.save(cache_path, "PNG")

        # Save metadata
        metadata = {
            "downloaded_at": time.time(),
            "expires_at": time.time() + self.cache_ttl,
        }
        with open(meta_path, "w") as f:
            json.dump(metadata, f)

    def _fetch_tile_from_server(self, zoom: int, x: int, y: int) -> Optional[Image.Image]:
        """
        Fetches tile from OSM server.
        Respects rate limiting (2 req/s).
        """
        url = f"{self.tile_server}/{zoom}/{x}/{y}.png"

        try:
            # Rate limiting: sleep 0.5s between requests
            time.sleep(0.5)

            response = httpx.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=10.0,
                follow_redirects=True,
            )

            if response.status_code == 200:
                from io import BytesIO

                tile_image = Image.open(BytesIO(response.content))
                return tile_image
            else:
                print(f"Failed to fetch tile: {url} (status {response.status_code})")
                return None

        except Exception as e:
            print(f"Error fetching tile {url}: {e}")
            return None

    def get_tile(self, lat: float, lon: float, zoom: int = 15) -> Image.Image:
        """
        Gets map tile centered on coordinates.

        Process:
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

        Example:
            >>> renderer = OSMTileRenderer()
            >>> tile = renderer.get_tile(51.5074, -0.1278, 15)
            >>> tile.size
            (256, 256)
        """
        x, y = self.lat_lon_to_tile(lat, lon, zoom)

        # Check cache
        if self._is_cache_valid(zoom, x, y):
            cache_path = self._get_cache_path(zoom, x, y)
            return Image.open(cache_path)

        # Fetch from server
        tile_image = self._fetch_tile_from_server(zoom, x, y)

        if tile_image is None:
            # Return blank tile on error
            return Image.new("RGB", (256, 256), color="lightgrey")

        # Save to cache
        self._save_tile_to_cache(zoom, x, y, tile_image)

        return tile_image

    def crop_to_center(
        self, tile: Image.Image, lat: float, lon: float, zoom: int, width: int = 200, height: int = 150
    ) -> Image.Image:
        """
        Crops tile to center on exact coordinates with specified dimensions.

        Args:
            tile: 256x256 OSM tile
            lat: Latitude
            lon: Longitude
            zoom: Zoom level used for the tile
            width: Desired width
            height: Desired height

        Returns:
            Cropped PIL Image

        Example:
            >>> renderer = OSMTileRenderer()
            >>> tile = Image.new('RGB', (256, 256), color='blue')
            >>> cropped = renderer.crop_to_center(tile, 51.5074, -0.1278, 15, 200, 150)
            >>> cropped.size
            (200, 150)
        """
        # Calculate pixel position within tile
        n = 2.0**zoom
        x_tile, y_tile = self.lat_lon_to_tile(lat, lon, zoom)

        # Calculate exact pixel position
        lon_deg = (lon + 180.0) / 360.0 * n
        lat_rad = math.radians(lat)
        lat_deg = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

        x_pixel = (lon_deg - x_tile) * 256
        y_pixel = (lat_deg - y_tile) * 256

        # Calculate crop box (centered on coordinates)
        left = int(x_pixel - width / 2)
        top = int(y_pixel - height / 2)
        right = left + width
        bottom = top + height

        # Ensure crop box is within tile bounds
        left = max(0, min(left, 256 - width))
        top = max(0, min(top, 256 - height))
        right = left + width
        bottom = top + height

        # Crop and return
        cropped = tile.crop((left, top, right, bottom))
        return cropped
