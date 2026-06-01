import httpx
from app.config import get_settings
from app.utils.encryption import decrypt


class LLMClient:
    def __init__(self):
        self._settings = get_settings()

    async def chat(self, model: str, messages: list[dict], temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 2048) -> dict:
        """Legacy method: uses hardcoded DeepSeek settings from env."""
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.DEEPSEEK_API_KEY}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            }

    async def chat_with_provider(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
    ) -> dict:
        """Provider-based chat: resolves API endpoint and key from database."""
        base = api_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            }

    async def chat_from_db(self, db, model_name: str, messages: list[dict], temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 2048) -> dict:
        """Resolve chat model config and provider from DB, then call the API."""
        from app.dao import model_dao
        configs = await model_dao.get_configs(db, "chat")
        config = None
        for c in configs:
            if c.model_name == model_name:
                config = c
                break
        if not config:
            config = await model_dao.get_default_config(db, "chat")
        if not config:
            raise ValueError(f"未找到对话模型配置: {model_name}")

        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            raise ValueError(f"供应商不存在 (provider_id={config.provider_id})")

        api_key = decrypt(provider.api_key_encrypted)
        return await self.chat_with_provider(
            provider.api_base_url, api_key, config.model_name,
            messages, temperature, top_p, max_tokens,
        )


llm_client = LLMClient()
