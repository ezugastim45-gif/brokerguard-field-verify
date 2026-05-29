"""Tests for map renderer module."""

import pytest
from src.map_renderer import OSMTileRenderer
from PIL import Image
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_cache_dir():
    """Creates temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_lat_lon_to_tile(temp_cache_dir: str):
    """Should convert lat/lon to tile coordinates."""
    renderer = OSMTileRenderer(cache_dir=temp_cache_dir)
    x, y = renderer.lat_lon_to_tile(51.5074, -0.1278, 15)

    assert isinstance(x, int)
    assert isinstance(y, int)
    assert x >= 0
    assert y >= 0


def test_lat_lon_to_tile_zoom_levels(temp_cache_dir: str):
    """Should work with different zoom levels."""
    renderer = OSMTileRenderer(cache_dir=temp_cache_dir)

    for zoom in [10, 12, 15, 18]:
        x, y = renderer.lat_lon_to_tile(0, 0, zoom)
        assert isinstance(x, int)
        assert isinstance(y, int)


def test_crop_to_center(temp_cache_dir: str, mock_osm_tile: Image.Image):
    """Should crop tile to specified dimensions."""
    renderer = OSMTileRenderer(cache_dir=temp_cache_dir)
    cropped = renderer.crop_to_center(
        tile=mock_osm_tile, lat=51.5074, lon=-0.1278, zoom=15, width=200, height=150
    )

    assert cropped.size == (200, 150)


def test_get_tile_creates_cache_dir(temp_cache_dir: str):
    """Should create cache directory if it doesn't exist."""
    cache_path = Path(temp_cache_dir) / "new_cache"
    renderer = OSMTileRenderer(cache_dir=str(cache_path))

    assert cache_path.exists()


def test_cache_path_structure(temp_cache_dir: str):
    """Should generate correct cache path structure."""
    renderer = OSMTileRenderer(cache_dir=temp_cache_dir)
    cache_path = renderer._get_cache_path(15, 12345, 67890)

    assert str(cache_path).endswith("15/12345/67890.png")
    assert "15" in str(cache_path)
    assert "12345" in str(cache_path)


def test_metadata_path_structure(temp_cache_dir: str):
    """Should generate correct metadata path."""
    renderer = OSMTileRenderer(cache_dir=temp_cache_dir)
    meta_path = renderer._get_metadata_path(15, 12345, 67890)

    assert str(meta_path).endswith("15/12345/67890.meta.json")
