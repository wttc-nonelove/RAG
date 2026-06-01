import json
import re
from app.utils.llm_client import llm_client


EXTRACT_PROMPT = """请从以下文本中提取实体和关系，返回 JSON 格式：
{{"entities": [{{"name": "实体名", "type": "类型", "description": "描述"}}], "relations": [{{"source": "源实体", "relation": "关系", "target": "目标实体"}}]}}

实体类型请根据实体特征自行判断，如：人物、组织、地点、概念、技术、产品、事件、制度、指标、流程、法律、文件、项目、部门、岗位、工具、方法、标准、规范、指标等，也可使用其他更贴切的类型。

文本：
{text}

只返回 JSON，不要其他内容。"""


async def extract(text: str, doc_id: int, doc_name: str, db=None, model_name: str = None) -> dict:
    try:
        prompt = EXTRACT_PROMPT.format(text=text[:5000])  # 增加到5000字符
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
                # 尝试多种修复方式
                try:
                    # 修复尾随逗号
                    raw = re.sub(r",\s*([}\]])", r"\1", raw)
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    # 修复缺少逗号的情况
                    raw = re.sub(r'"\s*\n\s*"', '",\n"', raw)
                    raw = re.sub(r'"\s*}\s*"', '"}', raw)
                    raw = re.sub(r'"\s*]\s*"', ']', raw)
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        # 最后尝试：提取 entities 和 relations 数组
                        entities_match = re.search(r'"entities"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
                        relations_match = re.search(r'"relations"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
                        entities = []
                        relations = []
                        if entities_match:
                            try:
                                entities = json.loads('[' + entities_match.group(1) + ']')
                            except:
                                pass
                        if relations_match:
                            try:
                                relations = json.loads('[' + relations_match.group(1) + ']')
                            except:
                                pass
                        data = {"entities": entities, "relations": relations}
            for e in data.get("entities", []):
                e["doc_id"] = doc_id
                e["doc_name"] = doc_name
            return data
    except Exception as e:
        import loguru
        loguru.logger.error(f"KG extraction failed: {e}")
    return {"entities": [], "relations": []}
