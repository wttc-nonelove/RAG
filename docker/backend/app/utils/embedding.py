import hashlib
import math
import re
from collections import Counter


class EmbeddingClient:
    """Embedding client with local fallback and provider-based API support."""

    def __init__(self, dim: int = 1536):
        self._dim = dim

    def _tokenize(self, text: str) -> list[str]:
        tokens = []
        for m in re.finditer(r'[一-鿿]+|[a-zA-Z]+|\d+', text):
            word = m.group()
            tokens.append(word)
            for i in range(len(word)):
                for l in (2, 3, 4):
                    if i + l <= len(word):
                        tokens.append(word[i:i + l])
        return tokens

    def _text_to_vector(self, text: str) -> list[float]:
        tokens = self._tokenize(text.lower())
        counts = Counter(tokens)
        vec = [0.0] * self._dim
        for token, count in counts.items():
            h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            h2 = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            weight = (1 + math.log(count)) if count > 0 else 1.0
            for k in range(3):
                idx = (h1 + k * h2) % self._dim
                sign = 1 if ((h1 >> k) & 1) == 0 else -1
                vec[idx] += sign * weight
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def encode(self, text: str) -> list[float]:
        """Local hash-based encoding (fallback)."""
        return self._text_to_vector(text)

    async def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Local hash-based batch encoding (fallback)."""
        return [self._text_to_vector(t) for t in texts]

    async def encode_with_provider(self, api_base_url: str, api_key: str, model: str, text: str) -> list[float]:
        """Call remote embedding API (e.g., 通义千问, OpenAI-compatible)."""
        import httpx
        base = api_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    async def encode_batch_with_provider(self, api_base_url: str, api_key: str, model: str, texts: list[str]) -> list[list[float]]:
        """Call remote embedding API in batch."""
        import httpx
        base = api_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            sorted_items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_items]

    async def encode_from_db(self, db, text: str) -> list[float]:
        """Resolve default embedding config from DB, call API or fall back to local."""
        from app.dao import model_dao
        from app.utils.encryption import decrypt
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            return self._text_to_vector(text)
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            return self._text_to_vector(text)
        try:
            api_key = decrypt(provider.api_key_encrypted)
            return await self.encode_with_provider(provider.api_base_url, api_key, config.model_name, text)
        except Exception:
            return self._text_to_vector(text)

    async def encode_batch_from_db(self, db, texts: list[str]) -> list[list[float]]:
        """Resolve default embedding config from DB, call API batch or fall back to local."""
        from app.dao import model_dao
        from app.utils.encryption import decrypt
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            return [self._text_to_vector(t) for t in texts]
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            return [self._text_to_vector(t) for t in texts]
        try:
            api_key = decrypt(provider.api_key_encrypted)
            return await self.encode_batch_with_provider(provider.api_base_url, api_key, config.model_name, texts)
        except Exception:
            return [self._text_to_vector(t) for t in texts]


embedding_client = EmbeddingClient()
