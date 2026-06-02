"""
LLM 客户端模块
功能：封装与大语言模型 API 的交互，支持多种供应商和模型
支持：DeepSeek、OpenAI、通义千问等 OpenAI 兼容 API
"""

import httpx
from app.config import get_settings
from app.utils.encryption import decrypt


class LLMClient:
    """LLM 客户端类，提供多种调用方式"""

    def __init__(self):
        self._settings = get_settings()

    async def chat(self, model: str, messages: list[dict], temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 2048) -> dict:
        """
        传统方法：使用环境变量中的 DeepSeek 配置（向后兼容）

        参数:
            model: 模型名称（如 deepseek-chat）
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-2，越低越确定）
            top_p: 核采样参数（0-1）
            max_tokens: 最大生成 token 数

        返回:
            dict: {"content": "回答内容", "tokens_used": 消耗的token数}
        """
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
        """
        使用指定供应商配置调用 LLM

        参数:
            api_base_url: API 基础地址
            api_key: API 密钥
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大生成 token 数

        返回:
            dict: {"content": "回答内容", "tokens_used": 消耗的token数}
        """
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
        """
        从数据库解析模型配置和供应商，然后调用 API（推荐方式）

        参数:
            db: 数据库会话
            model_name: 模型名称（如 deepseek-chat）
            messages: 消息列表
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大生成 token 数

        返回:
            dict: {"content": "回答内容", "tokens_used": 消耗的token数}

        异常:
            ValueError: 未找到模型配置或供应商
        """
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


# 全局单例
llm_client = LLMClient()
