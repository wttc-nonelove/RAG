import hashlib
import math
import re
from collections import Counter


class EmbeddingClient:
    """Embedding client with local/remote mode support.

    - 当配置了远程embedding且设为默认时，严格使用远程API，失败时抛出异常（不回退本地）
    - 当没有远程配置时，使用本地hash-based embedding
    - 本地embedding维度可通过配置文件的embedding_dimension设定
    """

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

    def _text_to_vector(self, text: str, dim: int = None) -> list[float]:
        """将文本转换为向量，支持自定义维度"""
        use_dim = dim or self._dim
        tokens = self._tokenize(text.lower())
        counts = Counter(tokens)
        vec = [0.0] * use_dim
        for token, count in counts.items():
            h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            h2 = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            weight = (1 + math.log(count)) if count > 0 else 1.0
            for k in range(3):
                idx = (h1 + k * h2) % use_dim
                sign = 1 if ((h1 >> k) & 1) == 0 else -1
                vec[idx] += sign * weight
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def encode(self, text: str, dim: int = None) -> list[float]:
        """Local hash-based encoding."""
        return self._text_to_vector(text, dim)

    async def encode_batch(self, texts: list[str], dim: int = None) -> list[list[float]]:
        """Local hash-based batch encoding."""
        return [self._text_to_vector(t, dim) for t in texts]

    async def encode_with_provider(self, api_base_url: str, api_key: str, model: str, text: str) -> dict:
        """Call remote embedding API. Returns {embeddings: [...], tokens_used: int}."""
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
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            return {"embeddings": [data["data"][0]["embedding"]], "tokens_used": tokens_used}

    async def encode_batch_with_provider(self, api_base_url: str, api_key: str, model: str, texts: list[str]) -> dict:
        """Call remote embedding API in batch. Returns {embeddings: [...], tokens_used: int}.

        自动分批处理，每批最多20条文本（通义千问限制25条，留一些余量）。
        """
        import httpx
        base = api_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"

        all_embeddings = []
        total_tokens = 0
        batch_size = 10  # 通义千问text-embedding-v3限制10条

        async with httpx.AsyncClient(timeout=60) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                resp = await client.post(
                    f"{base}/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": model, "input": batch},
                )
                resp.raise_for_status()
                data = resp.json()
                sorted_items = sorted(data["data"], key=lambda x: x["index"])
                all_embeddings.extend([item["embedding"] for item in sorted_items])
                total_tokens += data.get("usage", {}).get("total_tokens", 0)

        return {"embeddings": all_embeddings, "tokens_used": total_tokens}

    async def _get_embedding_mode(self, db) -> str:
        """获取embedding模式：'remote' 或 'local'"""
        from app.dao import config_dao
        configs = await config_dao.get_all(db)
        config_dict = {c.config_key: c.config_value for c in configs}
        return config_dict.get("embedding_mode", "local")

    async def encode_from_db(self, db, text: str) -> dict:
        """从数据库读取embedding配置并编码。

        策略：
        - embedding_mode=local → 强制使用本地embedding，维度从embedding配置中读取
        - embedding_mode=remote → 严格使用远程API，失败时抛出异常（不回退本地）
        """
        from app.dao import model_dao
        from app.utils.encryption import decrypt

        mode = await self._get_embedding_mode(db)

        if mode == "local":
            # 强制使用本地embedding
            config = await model_dao.get_default_config(db, "embedding")
            dim = config.embedding_dimension if config and config.embedding_dimension else self._dim
            return {"embeddings": [self._text_to_vector(text, dim)], "tokens_used": 0}

        # remote模式：严格使用远程API
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            raise ValueError("远程Embedding模式已启用，但未配置默认Embedding模型，请在模型管理中配置")
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            raise ValueError("远程Embedding模式已启用，但未找到对应的模型供应商")
        api_key = decrypt(provider.api_key_encrypted)
        return await self.encode_with_provider(provider.api_base_url, api_key, config.model_name, text)

    async def encode_batch_from_db(self, db, texts: list[str]) -> dict:
        """从数据库读取embedding配置并批量编码。

        策略：
        - embedding_mode=local → 强制使用本地embedding，维度从embedding配置中读取
        - embedding_mode=remote → 严格使用远程API，失败时抛出异常（不回退本地）
        """
        from app.dao import model_dao
        from app.utils.encryption import decrypt

        mode = await self._get_embedding_mode(db)

        if mode == "local":
            # 强制使用本地embedding
            config = await model_dao.get_default_config(db, "embedding")
            dim = config.embedding_dimension if config and config.embedding_dimension else self._dim
            return {"embeddings": [self._text_to_vector(t, dim) for t in texts], "tokens_used": 0}

        # remote模式：严格使用远程API
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            raise ValueError("远程Embedding模式已启用，但未配置默认Embedding模型，请在模型管理中配置")
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            raise ValueError("远程Embedding模式已启用，但未找到对应的模型供应商")
        api_key = decrypt(provider.api_key_encrypted)
        return await self.encode_batch_with_provider(provider.api_base_url, api_key, config.model_name, texts)


embedding_client = EmbeddingClient()
