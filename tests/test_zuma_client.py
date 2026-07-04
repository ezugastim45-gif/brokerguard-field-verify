"""Tests for the NB AI assistant client (src/zuma_client.py).

Garantias que cubren el desacople de productos:
  1. Fail-closed: sin ZUMA_AI_URL el cliente truena limpio y el endpoint da 503.
  2. Solo texto acotado sale hacia la IA — una foto base64 no cabe en el payload.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src import zuma_client
from src.api import app
from src.config import settings
from src.zuma_client import ZumaAIUnavailable, build_payload

client = TestClient(app)

FAKE_RESULT = {"answer": "ok", "model": "qwen2.5:7b", "latency_ms": 42}


class TestBuildPayload:
    def test_only_question_key(self):
        """El payload tiene UN solo campo de texto — nada mas puede viajar."""
        payload = build_payload("hola", plan="p", context="c")
        assert set(payload.keys()) == {"question"}
        assert isinstance(payload["question"], str)

    def test_composes_plan_and_context(self):
        payload = build_payload("pregunta", plan="mi plan", context="mi contexto")
        assert "pregunta" in payload["question"]
        assert "Plan: mi plan" in payload["question"]
        assert "Contexto: mi contexto" in payload["question"]

    def test_truncates_to_contract_max(self, sample_image_base64):
        """Una imagen base64 (~600KB) NO cabe: se trunca al contrato de 2000."""
        payload = build_payload("q", context=sample_image_base64)
        assert len(payload["question"]) <= zuma_client.MAX_QUESTION_LEN


class TestAsk:
    def test_fail_closed_without_url(self, monkeypatch):
        """URL vacia (default) = ZumaAIUnavailable sin intentar red."""
        monkeypatch.setattr(settings, "zuma_ai_url", "")
        with pytest.raises(ZumaAIUnavailable, match="fail-closed"):
            zuma_client.ask("pregunta")

    def test_network_error_raises_unavailable(self, monkeypatch):
        monkeypatch.setattr(settings, "zuma_ai_url", "http://127.0.0.1:1/ask")
        with patch("src.zuma_client.httpx.post", side_effect=httpx.ConnectError("boom")):
            with pytest.raises(ZumaAIUnavailable, match="inalcanzable"):
                zuma_client.ask("pregunta")

    def test_non_200_raises_unavailable(self, monkeypatch):
        monkeypatch.setattr(settings, "zuma_ai_url", "http://zuma-nb.test/ask")
        response = MagicMock(status_code=401)
        with patch("src.zuma_client.httpx.post", return_value=response):
            with pytest.raises(ZumaAIUnavailable, match="401"):
                zuma_client.ask("pregunta")

    def test_success_sends_key_header(self, monkeypatch):
        monkeypatch.setattr(settings, "zuma_ai_url", "http://zuma-nb.test/ask")
        monkeypatch.setattr(settings, "zuma_ai_key", "test-nb-key")
        response = MagicMock(status_code=200)
        response.json.return_value = FAKE_RESULT
        with patch("src.zuma_client.httpx.post", return_value=response) as mock_post:
            assert zuma_client.ask("pregunta") == FAKE_RESULT
        kwargs = mock_post.call_args.kwargs
        assert kwargs["headers"]["X-Zuma-Key"] == "test-nb-key"
        assert set(kwargs["json"].keys()) == {"question"}


class TestAssistantEndpoint:
    def test_unconfigured_returns_503(self, monkeypatch):
        """Fail-closed de punta a punta: sin URL el endpoint responde 503."""
        monkeypatch.setattr(settings, "zuma_ai_url", "")
        resp = client.post("/assistant/ask", json={"question": "hola mundo"})
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()

    def test_core_intact_when_unconfigured(self, monkeypatch):
        """La IA caida no arrastra al core de verificacion."""
        monkeypatch.setattr(settings, "zuma_ai_url", "")
        assert client.get("/health").status_code == 200

    def test_success_passthrough(self, monkeypatch):
        monkeypatch.setattr(settings, "zuma_ai_url", "http://zuma-nb.test/ask")
        with patch("src.zuma_client.ask", return_value=FAKE_RESULT):
            resp = client.post("/assistant/ask", json={"question": "hola mundo"})
        assert resp.status_code == 200
        assert resp.json() == FAKE_RESULT

    def test_rejects_oversized_question(self):
        """Pydantic corta preguntas fuera de contrato antes de llegar al cliente."""
        resp = client.post("/assistant/ask", json={"question": "x" * 3000})
        assert resp.status_code == 422
