import json
import re
from app.utils.llm_client import llm_client


EXTRACT_PROMPT = """请从以下文本中提取实体和关系，返回 JSON 格式：
{{"entities": [{{"name": "实体名", "type": "类型", "description": "描述"}}], "relations": [{{"source": "源实体", "relation": "关系", "target": "目标实体"}}]}}

实体类型包括：人物、组织、地点、概念、技术、产品、事件

文本：
{text}

只返回 JSON，不要其他内容。"""


async def extract(text: str, doc_id: int, doc_name: str) -> dict:
    try:
        prompt = EXTRACT_PROMPT.format(text=text[:1500])
        result = await llm_client.chat("deepseek-chat", [{"role": "user", "content": prompt}], temperature=0.1, max_tokens=2048)
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
