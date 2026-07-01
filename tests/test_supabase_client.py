"""Tests for src/supabase_client.py (mocked Supabase client)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.supabase_client import SupabaseClient


@pytest.fixture
def client():
    with patch("src.supabase_client.create_client") as mock_create:
        mock_create.return_value = MagicMock()
        c = SupabaseClient()
    return c


class TestGenerateStoragePath:
    def test_image_path(self, client):
        ts = datetime(2026, 7, 1, 12, 0)
        assert client.generate_storage_path("abc123", "png", ts) == "images/2026-07/abc123.png"

    def test_pdf_path(self, client):
        ts = datetime(2026, 7, 1, 12, 0)
        assert client.generate_storage_path("abc123", "pdf", ts) == "pdfs/2026-07/abc123.pdf"

    def test_other_extension_goes_to_files(self, client):
        ts = datetime(2026, 12, 31, 23, 59)
        assert client.generate_storage_path("h", "zip", ts) == "files/2026-12/h.zip"


class TestUploadFile:
    def test_upload_returns_public_url(self, client, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"fake-image-data")
        storage = client.client.storage.from_.return_value
        storage.get_public_url.return_value = "https://x.supabase.co/storage/v1/object/public/b/p.png"

        url = client.upload_file(str(f), "images/2026-07/p.png")

        assert url.startswith("https://")
        storage.upload.assert_called_once()
        _, kwargs = storage.upload.call_args
        assert kwargs["path"] == "images/2026-07/p.png"
        assert kwargs["file"] == b"fake-image-data"

    def test_upload_missing_file_raises(self, client):
        with pytest.raises(FileNotFoundError):
            client.upload_file("/no/existe.png", "images/x.png")


class TestInsertVerification:
    def _args(self):
        return dict(
            broker_id="b-1", property_id="p-1", lat=19.04, lon=-98.21,
            altitude=2135.0, address="Puebla", image_hash="h" * 64,
            stamped_image_url="https://x/img.png", pdf_url="https://x/r.pdf",
            verified_at=datetime(2026, 7, 1, 12, 0), metadata={"k": "v"},
        )

    def test_insert_returns_record(self, client):
        record = {"id": "uuid-1", "image_hash": "h" * 64}
        client.client.table.return_value.insert.return_value.execute.return_value.data = [record]
        assert client.insert_verification(**self._args()) == record
        # verified_at debe serializarse a ISO
        payload = client.client.table.return_value.insert.call_args[0][0]
        assert payload["verified_at"] == "2026-07-01T12:00:00"

    def test_insert_empty_response_raises(self, client):
        client.client.table.return_value.insert.return_value.execute.return_value.data = []
        with pytest.raises(Exception, match="Failed to insert"):
            client.insert_verification(**self._args())


class TestGetters:
    def test_get_by_hash_found(self, client):
        row = {"image_hash": "abc"}
        client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [row]
        assert client.get_verification_by_hash("abc") == row

    def test_get_by_hash_not_found(self, client):
        client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        assert client.get_verification_by_hash("nope") is None

    def test_get_by_broker_returns_list(self, client):
        rows = [{"id": 1}, {"id": 2}]
        chain = client.client.table.return_value.select.return_value.eq.return_value
        chain.order.return_value.limit.return_value.offset.return_value.execute.return_value.data = rows
        assert client.get_verifications_by_broker("b-1") == rows

    def test_get_by_property_empty(self, client):
        chain = client.client.table.return_value.select.return_value.eq.return_value
        chain.order.return_value.limit.return_value.execute.return_value.data = None
        assert client.get_verifications_by_property("p-1") == []
