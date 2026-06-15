import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dao import message_dao, model_dao
from app.dao import token_usage_dao
from app.models.system_config import SystemConfig
from app.services.graphrag_service import retrieve_context
from app.utils.llm_client import llm_client


async def get_system_config(db: AsyncSession) -> dict:
    result = await db.execute(select(SystemConfig))
    rows = result.scalars().all()
    return {r.config_key: r.config_value for r in rows}


def _format_history(history) -> str:
    lines = []
    for item in history:
        role = "用户" if item.role == "user" else "助手"
        lines.append(f"{role}: {item.content[:200]}")
    return "\n".join(lines)


def _build_system_prompt(base_instructions: str, context: str, history_text: str) -> str:
    return f"""{base_instructions}

## 参考资料
{context}

## 对话历史
{history_text}

## 回答要求
1. 只基于参考资料、关系路径和对话历史回答，不要编造未给出的事实。
2. 如果提供了多跳关联路径，先解释中间概念如何把两端概念连接起来，再给出结论。
3. 如果多个来源都相关，需要综合不同文档和章节的证据，避免只引用单一片段。
4. 如果参考资料不足，请明确说明缺少什么证据。
5. 使用 Markdown 输出，并在回答末尾注明引用来源。"""


async def rag_pipeline(db: AsyncSession, conversation_id: int, question: str, model_name: str, user_id: int) -> dict:
    start_time = time.time()

    config = await get_system_config(db)
    threshold = float(config.get("similarity_threshold", "0.05"))
    history_rounds = int(config.get("history_rounds", "5"))

    await message_dao.create(db, conversation_id, "user", question)
    await db.commit()

    history = await message_dao.get_recent_history(db, conversation_id, history_rounds)

    retrieval = await retrieve_context(db, question, config)
    context_parts = retrieval["context_parts"]
    sources = retrieval["sources"]
    expanded_sources = retrieval["expanded_sources"]
    kg_references = retrieval["kg_references"]
    reasoning_paths = retrieval["reasoning_paths"]
    max_similarity = retrieval["max_similarity"]

    if max_similarity < threshold and not reasoning_paths:
        fallback_answer = "知识库中暂无相关信息，请尝试更换问题或补充相关文档。"
        msg = await message_dao.create(
            db, conversation_id, "bot", fallback_answer,
            sources=[], kg_references=None, model_name=None
        )
        await db.commit()
        elapsed = int((time.time() - start_time) * 1000)
        return {
            "message_id": msg.id,
            "answer": fallback_answer,
            "sources": [],
            "expanded_sources": [],
            "kg_references": None,
            "reasoning_paths": [],
            "model_used": None,
            "tokens_used": 0,
            "response_time_ms": elapsed,
            "fallback": True,
            "max_similarity": round(max_similarity, 4),
        }

    history_text = _format_history(history)
    context = "\n\n---\n\n".join(context_parts) if context_parts else "暂无相关参考资料"

    model_config = None
    for item in await model_dao.get_configs(db, "chat"):
        if item.model_name == model_name:
            model_config = item
            break
    if not model_config:
        model_config = await model_dao.get_default_config(db, "chat")
    if model_config:
        model_name = model_config.model_name

    base_instructions = (
        model_config.system_prompt
        if model_config and model_config.system_prompt
        else "你是一个专业的企业知识库助手，请根据参考资料和知识图谱证据回答用户的问题。"
    )
    system_prompt = _build_system_prompt(base_instructions, context, history_text)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    temperature = float(config.get("temperature", "0.7"))
    top_p = float(config.get("top_p", "0.9"))
    max_tokens = int(config.get("max_tokens", "2048"))
    llm_result = await llm_client.chat_from_db(db, model_name, messages, temperature, top_p, max_tokens)
    answer = llm_result["content"]
    tokens_used = llm_result["tokens_used"]

    await token_usage_dao.create(
        db,
        model_name=model_name,
        model_type="chat",
        tokens_used=tokens_used,
        source_type="qa",
        source_id=conversation_id,
        source_name=question[:100],
    )

    kg_references = kg_references or {}
    kg_references["expanded_sources"] = expanded_sources
    msg = await message_dao.create(
        db,
        conversation_id,
        "bot",
        answer,
        sources=sources,
        kg_references=kg_references,
        model_name=model_name,
        tokens_used=tokens_used,
    )
    await db.commit()

    elapsed = int((time.time() - start_time) * 1000)
    return {
        "message_id": msg.id,
        "answer": answer,
        "sources": sources,
        "expanded_sources": expanded_sources,
        "kg_references": kg_references,
        "reasoning_paths": reasoning_paths,
        "model_used": model_name,
        "tokens_used": tokens_used,
        "response_time_ms": elapsed,
    }
