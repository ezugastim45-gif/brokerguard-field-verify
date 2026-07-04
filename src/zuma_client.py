"""Client for the dedicated NB AI assistant (zuma-ai-nb, host :8005).

Fail-closed: sin ZUMA_AI_URL configurada se levanta ZumaAIUnavailable y el
endpoint responde 503 limpio — el core de verificacion nunca depende de la IA.
Por diseno solo viaja texto corto (question/plan/context): el payload se
compone y trunca a MAX_QUESTION_LEN, asi que fotos base64 o dumps de datos
de clientes no caben fisicamente en la peticion.
"""

import httpx

from .config import settings

# Contrato del wrapper zuma-ai-nb: un solo campo de texto, 3..2000 chars
MAX_QUESTION_LEN = 2000


class ZumaAIUnavailable(Exception):
    """El asistente IA no esta configurado o no responde."""


def build_payload(question: str, plan: str | None = None, context: str | None = None) -> dict:
    """Compone el texto final. Solo strings; nada binario ni estructuras."""
    parts = [question.strip()]
    if plan:
        parts.append(f"Plan: {plan.strip()}")
    if context:
        parts.append(f"Contexto: {context.strip()}")
    text = "\n\n".join(parts)[:MAX_QUESTION_LEN]
    return {"question": text}


def ask(question: str, plan: str | None = None, context: str | None = None) -> dict:
    """Consulta al asistente. Retorna {answer, model, latency_ms}.

    Raises:
        ZumaAIUnavailable: URL sin configurar, error de red o respuesta no-200.
    """
    if not settings.zuma_ai_url:
        raise ZumaAIUnavailable("ZUMA_AI_URL no configurada (fail-closed)")

    try:
        response = httpx.post(
            settings.zuma_ai_url,
            json=build_payload(question, plan, context),
            headers={"X-Zuma-Key": settings.zuma_ai_key},
            timeout=settings.zuma_ai_timeout,
        )
    except httpx.HTTPError as e:
        raise ZumaAIUnavailable(f"Asistente IA inalcanzable: {e}")

    if response.status_code != 200:
        raise ZumaAIUnavailable(f"Asistente IA respondio {response.status_code}")

    return response.json()
