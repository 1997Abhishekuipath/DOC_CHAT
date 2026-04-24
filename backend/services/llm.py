"""OpenRouter LLM client (OpenAI-compatible)."""
from typing import AsyncIterator, List, Optional

from openai import AsyncOpenAI

from core.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        _client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://docchat.app",
                "X-Title": "DocChat",
            },
        )
    return _client


async def chat_complete(messages: List[dict], model: Optional[str] = None, temperature: float = 0.2) -> str:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=model or OPENROUTER_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


async def chat_stream(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> AsyncIterator[str]:
    client = _get_client()
    stream = await client.chat.completions.create(
        model=model or OPENROUTER_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
