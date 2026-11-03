"""Cliente centralizado para NVIDIA NIM, compatible con Chat Completions."""

import json
import os
import re
from functools import lru_cache
from typing import Any, Mapping, Sequence

from openai import OpenAI


class NvidiaServiceError(RuntimeError):
    """Error seguro para exponer al resto de la aplicación."""


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "qwen/qwen3.5-397b-a17b"


def configured_model() -> str:
    return os.getenv("NVIDIA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def is_configured() -> bool:
    return bool(os.getenv("NVIDIA_API_KEY", "").strip())


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not api_key:
        raise NvidiaServiceError("El servicio de IA no está configurado.")
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("NVIDIA_BASE_URL", NVIDIA_BASE_URL).strip() or NVIDIA_BASE_URL,
        timeout=float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "45")),
        max_retries=int(os.getenv("NVIDIA_MAX_RETRIES", "2")),
    )


def reset_client_cache() -> None:
    """Útil únicamente en pruebas cuando cambian las variables de entorno."""
    _client.cache_clear()


def complete(messages: Sequence[Mapping[str, str]], *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
    """Ejecuta una petición no streaming y devuelve contenido de texto válido."""
    try:
        response = _client().chat.completions.create(
            model=configured_model(), messages=list(messages), temperature=temperature,
            top_p=0.95, extra_body={"top_k": 20, "repetition_penalty": 1}, max_tokens=max_tokens,
        )
        content = response.choices[0].message.content if response.choices else None
    except NvidiaServiceError:
        raise
    except Exception as exc:
        # No incluir la petición, cabeceras ni clave en el error de la API.
        raise NvidiaServiceError("El proveedor de IA no respondió correctamente.") from exc
    if not content or not content.strip():
        raise NvidiaServiceError("El proveedor de IA devolvió una respuesta vacía.")
    return content.strip()


def json_completion(messages: Sequence[Mapping[str, str]], *, temperature: float = 0.2, max_tokens: int = 2048) -> dict[str, Any]:
    """Solicita JSON y tolera cercas Markdown sin aceptar texto arbitrario."""
    content = complete(messages, temperature=temperature, max_tokens=max_tokens)
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE).strip()
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise NvidiaServiceError("El proveedor de IA no devolvió JSON válido.") from exc
    if not isinstance(value, dict):
        raise NvidiaServiceError("El proveedor de IA devolvió un formato JSON inválido.")
    return value
