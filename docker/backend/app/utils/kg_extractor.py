import json
import re
from app.utils.llm_client import llm_client


EXTRACT_PROMPT = """请从以下文本中提取实体和关系，返回 JSON 格式：
{{"entities": [{{"name": "实体名", "type": "类型", "description": "描述"}}], "relations": [{{"source": "源实体", "relation": "关系", "target": "目标实体"}}]}}

实体类型包括：人物、组织、地点、概念、技术、产品、事件、制度、指标、流程

文本：
{text}

只返回 JSON，不要其他内容。"""


async def extract(text: str, doc_id: int, doc_name: str, db=None, model_name: str = None) -> dict:
    try:
        prompt = EXTRACT_PROMPT.format(text=text[:3000])
        messages = [{"role": "user", "content": prompt}]

        if db:
            # 从 system_config 读取 kg_model 配置
            if not model_name:
                from app.dao import config_dao
                config = await config_dao.get_all(db)
                kg_model = None
                for c in config:
                    if c.config_key == "kg_model":
                        kg_model = c.config_value
                        break
                model_name = kg_model if kg_model else None

            if model_name:
                result = await llm_client.chat_from_db(db, model_name, messages, temperature=0.1, max_tokens=2048)
            else:
                # 回退到默认 chat 模型
                from app.dao import model_dao
                default_config = await model_dao.get_default_config(db, "chat")
                if default_config:
                    result = await llm_client.chat_from_db(db, default_config.model_name, messages, temperature=0.1, max_tokens=2048)
                else:
                    result = await llm_client.chat("deepseek-chat", messages, temperature=0.1, max_tokens=2048)
        else:
            result = await llm_client.chat("deepseek-chat", messages, temperature=0.1, max_tokens=2048)

        content = result["content"]
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            raw = json_match.group()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                raw = re.sub(r",\s*([}\]])", r"\1", raw)
                data = json.loads(raw)
            for e in data.get("entities", []):
                e["doc_id"] = doc_id
                e["doc_name"] = doc_name
            return data
    except Exception as e:
        import loguru
        loguru.logger.error(f"KG extraction failed: {e}")
    return {"entities": [], "relations": []}
