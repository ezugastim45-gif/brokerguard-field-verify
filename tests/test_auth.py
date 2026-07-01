"""Tests for API key authentication (src/auth.py)."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src import auth
from src.config import settings


@pytest.fixture(autouse=True)
def clear_cache():
    auth._CACHE.clear()
    yield
    auth._CACHE.clear()


class TestVerifyApiKey:
    def test_disabled_returns_none(self, monkeypatch):
        """Con REQUIRE_API_KEY=false (default) la dependencia no exige nada."""
        monkeypatch.setattr(settings, "require_api_key", False)
        assert auth.verify_api_key(x_api_key=None) is None

    def test_missing_key_401(self, monkeypatch):
        monkeypatch.setattr(settings, "require_api_key", True)
        with pytest.raises(HTTPException) as exc:
            auth.verify_api_key(x_api_key=None)
        assert exc.value.status_code == 401

    def test_invalid_key_401(self, monkeypatch):
        monkeypatch.setattr(settings, "require_api_key", True)
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        with patch("src.supabase_client.supabase_client") as mock_sc:
            mock_sc.client = mock_client
            with pytest.raises(HTTPException) as exc:
                auth.verify_api_key(x_api_key="clave-invalida")
        assert exc.value.status_code == 401

    def test_valid_key_returns_info_and_caches(self, monkeypatch):
        monkeypatch.setattr(settings, "require_api_key", True)
        key_info = {"id": "abc", "name": "test", "partner_email": "t@t.com", "active": True}
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [key_info]
        with patch("src.supabase_client.supabase_client") as mock_sc:
            mock_sc.client = mock_client
            result = auth.verify_api_key(x_api_key="clave-valida")
        assert result == key_info
        # Segunda llamada sale del cache (sin tocar la DB)
        key_hash = hashlib.sha256(b"clave-valida").hexdigest()
        assert key_hash in auth._CACHE
