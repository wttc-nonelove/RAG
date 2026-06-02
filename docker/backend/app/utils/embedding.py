"""
Embedding 客户端模块
功能：将文本转换为向量（嵌入），支持远程 API 和本地 fallback
远程 API：OpenAI、通义千问等支持 /embeddings 端点的服务
本地 fallback：基于哈希的简单向量化（不消耗 token，但质量较低）
"""

import hashlib
import math
import re
from collections import Counter


class EmbeddingClient:
    """Embedding 客户端，支持远程 API 和本地 fallback"""

    def __init__(self, dim: int = 1536):
        """
        初始化

        参数:
            dim: 向量维度（默认 1536，与 OpenAI text-embedding-ada-002 兼容）
        """
        self._dim = dim

    def _tokenize(self, text: str) -> list[str]:
        """
        中文分词（简单实现：提取中文词、英文单词、数字，并生成 2-4 字的子串）

        参数:
            text: 待分词的文本

        返回:
            list[str]: token 列表
        """
        tokens = []
        for m in re.finditer(r'[一-鿿]+|[a-zA-Z]+|\d+', text):
            word = m.group()
            tokens.append(word)
            # 生成 2-4 字的子串（n-gram）
            for i in range(len(word)):
                for l in (2, 3, 4):
                    if i + l <= len(word):
                        tokens.append(word[i:i + l])
        return tokens

    def _text_to_vector(self, text: str) -> list[float]:
        """
        将文本转换为向量（本地哈希方法，不消耗 token）

        原理：
        1. 分词并统计词频
        2. 对每个词计算 MD5 和 SHA256 哈希值
        3. 根据哈希值确定向量中的位置和符号
        4. 使用 TF 权重（1 + log(count)）
        5. 最后归一化到单位向量

        参数:
            text: 待向量化的文本

        返回:
            list[float]: 向量（长度为 self._dim）
        """
        tokens = self._tokenize(text.lower())
        counts = Counter(tokens)
        vec = [0.0] * self._dim
        for token, count in counts.items():
            # 计算两个哈希值
            h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            h2 = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            # TF 权重
            weight = (1 + math.log(count)) if count > 0 else 1.0
            # 在向量中放置权重
            for k in range(3):
                idx = (h1 + k * h2) % self._dim
                sign = 1 if ((h1 >> k) & 1) == 0 else -1
                vec[idx] += sign * weight
        # 归一化
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def encode(self, text: str) -> list[float]:
        """
        本地哈希编码（fallback，不消耗 token）

        参数:
            text: 待编码的文本

        返回:
            list[float]: 向量
        """
        return self._text_to_vector(text)

    async def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """
        本地哈希批量编码（fallback）

        参数:
            texts: 待编码的文本列表

        返回:
            list[list[float]]: 向量列表
        """
        return [self._text_to_vector(t) for t in texts]

    async def encode_with_provider(self, api_base_url: str, api_key: str, model: str, text: str) -> dict:
        """
        调用远程 Embedding API

        参数:
            api_base_url: API 基础地址
            api_key: API 密钥
            model: 模型名称
            text: 待编码的文本

        返回:
            dict: {"embeddings": [向量], "tokens_used": 消耗的token数}
        """
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
        """
        批量调用远程 Embedding API

        参数:
            api_base_url: API 基础地址
            api_key: API 密钥
            model: 模型名称
            texts: 待编码的文本列表

        返回:
            dict: {"embeddings": [向量列表], "tokens_used": 消耗的token数}
        """
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
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            return {"embeddings": [item["embedding"] for item in sorted_items], "tokens_used": tokens_used}

    async def encode_from_db(self, db, text: str) -> dict:
        """
        从数据库解析 Embedding 配置，调用 API 或回退到本地（推荐方式）

        参数:
            db: 数据库会话
            text: 待编码的文本

        返回:
            dict: {"embeddings": [向量], "tokens_used": 消耗的token数}
        """
        from app.dao import model_dao
        from app.utils.encryption import decrypt
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            return {"embeddings": [self._text_to_vector(text)], "tokens_used": 0}
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            return {"embeddings": [self._text_to_vector(text)], "tokens_used": 0}
        try:
            api_key = decrypt(provider.api_key_encrypted)
            return await self.encode_with_provider(provider.api_base_url, api_key, config.model_name, text)
        except Exception:
            return {"embeddings": [self._text_to_vector(text)], "tokens_used": 0}

    async def encode_batch_from_db(self, db, texts: list[str]) -> dict:
        """
        从数据库解析 Embedding 配置，批量调用 API 或回退到本地

        参数:
            db: 数据库会话
            texts: 待编码的文本列表

        返回:
            dict: {"embeddings": [向量列表], "tokens_used": 消耗的token数}
        """
        from app.dao import model_dao
        from app.utils.encryption import decrypt
        config = await model_dao.get_default_config(db, "embedding")
        if not config:
            return {"embeddings": [self._text_to_vector(t) for t in texts], "tokens_used": 0}
        provider = await model_dao.get_provider_by_id(db, config.provider_id)
        if not provider:
            return {"embeddings": [self._text_to_vector(t) for t in texts], "tokens_used": 0}
        try:
            api_key = decrypt(provider.api_key_encrypted)
            return await self.encode_batch_with_provider(provider.api_base_url, api_key, config.model_name, texts)
        except Exception:
            return {"embeddings": [self._text_to_vector(t) for t in texts], "tokens_used": 0}


# 全局单例
embedding_client = EmbeddingClient()
