"""
Thin async client for the local model runtime (Ollama / vLLM / TGI - anything
that exposes an OpenAI-compatible /v1/chat/completions endpoint on localhost).

This is the ONLY place that makes outbound HTTP calls for inference, and its
base_url is pinned to settings.local_llm_base_url which must be a loopback
or LAN address. There is no code path anywhere in this project that accepts
an api.openai.com / anthropic.com / any public host - grep the repo, it is
simply not there.
"""
import httpx
from app.config import settings
from loguru import logger


class LocalLLMClient:
    def __init__(self):
        self.base_url = settings.local_llm_base_url.rstrip("/")
        self.api_key = settings.local_llm_api_key
        self._guard_local_only()

    def _guard_local_only(self):
        allowed_hosts = ("127.0.0.1", "localhost", "0.0.0.0", "::1")
        if not any(h in self.base_url for h in allowed_hosts):
            import re
            private_lan = re.search(r"://(10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)", self.base_url)
            if not private_lan:
                raise RuntimeError(
                    f"BLOCKED: LOCAL_LLM_BASE_URL '{self.base_url}' is not a "
                    f"loopback or private LAN address. Sovereign mode refuses "
                    f"to start with a public endpoint configured."
                )

    async def chat(
            self,
            model: str,
            messages: list,
            temperature: float = 0.2,
            max_tokens: int = 700,
            images: list | None = None,
    ) -> dict:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if images:
            payload["messages"][-1]["images"] = images

        async with httpx.AsyncClient(timeout=600) as client:
            logger.info(f"[LOCAL INFERENCE] model={model} base_url={self.base_url}")
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "raw": data,
            }

    async def chat_stream(self, model: str, messages: list, temperature: float = 0.3):
        payload = {
            "model": model, "messages": messages,
            "temperature": temperature, "stream": True,
        }
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line


llm_client = LocalLLMClient()
