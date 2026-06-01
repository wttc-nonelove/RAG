import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dao import chroma_repo, neo4j_repo
from app.dao import conversation_dao, message_dao, model_dao
from app.utils.embedding import embedding_client
from app.utils.llm_client import llm_client
from app.models.model_config import ModelConfig
from app.models.system_config import SystemConfig
from app.dao import config_dao


async def get_system_config(db: AsyncSession) -> dict:
    result = await db.execute(select(SystemConfig))
    rows = result.scalars().all()
    return {r.config_key: r.config_value for r in rows}


async def rag_pipeline(db: AsyncSession, conversation_id: int, question: str, model_name: str, user_id: int) -> dict:
    start_time = time.time()
    config = await get_system_config(db)
    top_k = int(config.get("top_k", "5"))
    threshold = float(config.get("similarity_threshold", "0.6"))
    history_rounds = int(config.get("history_rounds", "5"))
    kg_enabled = config.get("kg_enabled", "true") == "true"

    await message_dao.create(db, conversation_id, "user", question)
    await db.commit()

    history = await message_dao.get_recent_history(db, conversation_id, history_rounds)

    question_embedding = await embedding_client.encode_from_db(db, question)
    results = chroma_repo.query(question_embedding, top_k)

    sources = []
    context_parts = []
    max_similarity = 0.0

    if results and results["documents"] and results["documents"][0]:
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            similarity = 1.0 - dist
            max_similarity = max(max_similarity, similarity)
            if similarity >= threshold:
                context_parts.append(doc)
                sources.append({
                    "doc_name": meta.get("filename", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "excerpt": doc[:200],
                    "similarity": round(similarity, 4),
                })

    if max_similarity < threshold:
        fallback_answer = "知识库中暂无相关信息，请尝试更换问题或补充相关文档。"
        msg = await message_dao.create(db, conversation_id, "bot", fallback_answer, sources=[], kg_references=None, model_name=None)
        await db.commit()
        elapsed = int((time.time() - start_time) * 1000)
        return {
            "message_id": msg.id,
            "answer": fallback_answer,
            "sources": [],
            "kg_references": None,
            "model_used": None,
            "tokens_used": 0,
            "response_time_ms": elapsed,
            "fallback": True,
            "max_similarity": round(max_similarity, 4),
        }

    kg_context = ""
    kg_references = None
    if kg_enabled:
        try:
            import re
            # 用正则提取中文词（2字以上），再用问题全文匹配实体
            raw_terms = re.findall(r"[一-鿿]{2,}", question)
            terms = list(set(raw_terms))
            # 额外用问题全文作为查询词，让 CONTAINS 匹配实体名
            if question not in terms:
                terms.append(question)
            if terms:
                kg_data = neo4j_repo.query_subgraph(terms[:5])
                if kg_data["edges"]:
                    kg_lines = [f"{e['source']} --[{e['rel']}]--> {e['target']}" for e in kg_data["edges"][:5]]
                    kg_context = "\n\n## 知识图谱补充\n" + "\n".join(kg_lines)
                    kg_references = {
                        "entities": kg_data["nodes"],
                        "edges": kg_data["edges"],
                    }
        except Exception:
            pass

    context = "\n\n---\n\n".join(context_parts) if context_parts else "暂无相关参考资料"
    if kg_context:
        context += kg_context

    history_text = ""
    if history:
        lines = []
        for h in history:
            role = "用户" if h.role == "user" else "助手"
            lines.append(f"{role}: {h.content[:200]}")
        history_text = "\n".join(lines)

    # Try to get model-specific system prompt template
    model_config = None
    for c in await model_dao.get_configs(db, "chat"):
        if c.model_name == model_name:
            model_config = c
            break
    if not model_config:
        model_config = await model_dao.get_default_config(db, "chat")

    base_instructions = (model_config.system_prompt if model_config and model_config.system_prompt else
        "你是一个专业的企业知识库助手，请根据以下参考资料回答用户的问题。")

    system_prompt = f"""{base_instructions}

## 参考资料
{context}

## 对话历史
{history_text}

## 回答要求
1. 基于参考资料进行回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确说明
3. 回答结构清晰，使用 markdown 格式
4. 在回答末尾注明引用来源"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": question})

    temperature = float(config.get("temperature", "0.7"))
    top_p = float(config.get("top_p", "0.9"))
    max_tokens = int(config.get("max_tokens", "2048"))

    llm_result = await llm_client.chat_from_db(db, model_name, messages, temperature, top_p, max_tokens)
    answer = llm_result["content"]
    tokens_used = llm_result["tokens_used"]

    msg = await message_dao.create(db, conversation_id, "bot", answer, sources=sources, kg_references=kg_references, model_name=model_name, tokens_used=tokens_used)
    await db.commit()

    elapsed = int((time.time() - start_time) * 1000)
    return {
        "message_id": msg.id,
        "answer": answer,
        "sources": sources,
        "kg_references": kg_references,
        "model_used": model_name,
        "tokens_used": tokens_used,
        "response_time_ms": elapsed,
    }
