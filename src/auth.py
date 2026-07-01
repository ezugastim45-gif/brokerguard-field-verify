"""API key authentication against the api_keys table (Supabase).

Disabled by default (REQUIRE_API_KEY=false) so local dev and the test suite
keep working without credentials. In production the deploy sets
REQUIRE_API_KEY=true and every POST must send X-API-Key; the key is stored
hashed (SHA-256) in api_keys.key_hash, never in plain text.
"""

import hashlib
import time
from typing import Optional

from fastapi import Header, HTTPException, status

from .config import settings

# Cache en memoria para no consultar Supabase en cada request
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300  # seconds


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> Optional[dict]:
    """FastAPI dependency: valida X-API-Key contra api_keys (active=true)."""
    if not settings.require_api_key:
        return None

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    key_hash = _hash_key(x_api_key)

    cached = _CACHE.get(key_hash)
    if cached and cached[0] > time.time():
        return cached[1]

    from .supabase_client import supabase_client

    try:
        response = (
            supabase_client.client.table("api_keys")
            .select("id,name,partner_email,active")
            .eq("key_hash", key_hash)
            .eq("active", True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth backend unavailable: {e}",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    key_info = rows[0]
    _CACHE[key_hash] = (time.time() + _CACHE_TTL, key_info)

    # Contador de uso best-effort (no bloquea la request si falla)
    try:
        supabase_client.client.rpc(
            "increment_api_key_usage", {"p_key_hash": key_hash}
        ).execute()
    except Exception:
        pass

    return key_info
