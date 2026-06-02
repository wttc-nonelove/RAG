"""
Neo4j 知识图谱数据访问层
功能：封装所有与 Neo4j 图数据库的交互操作，包括实体和关系的增删改查
"""

from neo4j import GraphDatabase
from app.config import get_settings

# 全局配置和驱动（单例模式）
_settings = get_settings()
_driver = None


def get_driver():
    """获取 Neo4j 数据库驱动（懒加载单例）"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(_settings.NEO4J_URI, auth=(_settings.NEO4J_USER, _settings.NEO4J_PASSWORD))
    return _driver


def query_subgraph(terms: list[str], limit: int = 20) -> dict:
    """
    根据关键词查询相关子图

    参数:
        terms: 关键词列表，用于匹配实体名称
        limit: 返回的最大关系数量

    返回:
        dict: {"nodes": [实体列表], "edges": [关系列表]}
    """
    driver = get_driver()
    with driver.session() as session:
        # 使用双向匹配：实体名包含关键词，或关键词包含实体名
        cypher = """
        MATCH (e:Entity)-[r]->(t:Entity)
        WHERE any(term IN $terms WHERE e.name CONTAINS term OR t.name CONTAINS term OR term CONTAINS e.name OR term CONTAINS t.name)
        RETURN e.name AS source, e.type AS source_type, e.description AS source_desc,
               type(r) AS rel,
               t.name AS target, t.type AS target_type, t.description AS target_desc
        LIMIT $limit
        """
        result = session.run(cypher, terms=terms, limit=limit)
        nodes = {}
        edges = []
        for record in result:
            s, s_type, s_desc = record["source"], record["source_type"], record["source_desc"]
            r = record["rel"]
            t, t_type, t_desc = record["target"], record["target_type"], record["target_desc"]
            if s not in nodes:
                nodes[s] = {"name": s, "type": s_type or "概念", "description": s_desc or ""}
            if t not in nodes:
                nodes[t] = {"name": t, "type": t_type or "概念", "description": t_desc or ""}
            edges.append({"source": s, "rel": r, "target": t})
        return {"nodes": list(nodes.values()), "edges": edges}


def get_overview(limit: int = 0) -> dict:
    """
    获取知识图谱全貌（所有节点和关系）

    参数:
        limit: 关系数量限制，0 表示不限制

    返回:
        dict: {"nodes": [所有实体], "edges": [所有关系]}
    """
    driver = get_driver()
    with driver.session() as session:
        # 第一步：获取所有实体节点（包括孤立节点）
        nodes_result = session.run("""
        MATCH (e:Entity)
        RETURN e.name AS name, e.type AS type, e.description AS description, e.doc_id AS doc_id
        """)
        nodes = {}
        for record in nodes_result:
            name = record["name"]
            nodes[name] = {
                "name": name,
                "type": record["type"] or "概念",
                "description": record["description"] or "",
                "doc_id": record["doc_id"],
            }

        # 第二步：获取关系（limit=0 表示不限制）
        if limit > 0:
            edges_result = session.run("""
            MATCH (e:Entity)-[r]->(t:Entity)
            RETURN e.name AS source, type(r) AS rel, t.name AS target
            LIMIT $limit
            """, limit=limit)
        else:
            edges_result = session.run("""
            MATCH (e:Entity)-[r]->(t:Entity)
            RETURN e.name AS source, type(r) AS rel, t.name AS target
            """)
        edges = []
        for record in edges_result:
            edges.append({
                "source": record["source"],
                "rel": record["rel"],
                "target": record["target"],
            })

        return {"nodes": list(nodes.values()), "edges": edges}


def create_entity(name: str, entity_type: str, description: str = "", doc_id: int = None) -> None:
    """
    创建或更新实体（MERGE 语义：存在则更新，不存在则创建）

    参数:
        name: 实体名称
        entity_type: 实体类型（如：人物、组织、概念等）
        description: 实体描述
        doc_id: 来源文档ID
    """
    driver = get_driver()
    with driver.session() as session:
        session.run("""
        MERGE (e:Entity {name: $name})
        SET e.type = $type, e.description = $description, e.doc_id = $doc_id
        """, name=name, type=entity_type, description=description, doc_id=doc_id)


def create_relation(source: str, relation: str, target: str) -> None:
    """
    创建实体间的关系

    参数:
        source: 源实体名称
        relation: 关系类型（如：属于、包含、依赖）
        target: 目标实体名称
    """
    driver = get_driver()
    with driver.session() as session:
        session.run(f"""
        MATCH (a:Entity {{name: $source}}), (b:Entity {{name: $target}})
        MERGE (a)-[r:`{relation}`]->(b)
        """, source=source, target=target)


def delete_by_doc_id(doc_id: int) -> None:
    """
    删除指定文档的所有实体和关系

    参数:
        doc_id: 文档ID
    """
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (e:Entity {doc_id: $doc_id}) DETACH DELETE e", doc_id=doc_id)


def cleanup_orphan_entities(valid_doc_ids: list) -> int:
    """
    清理没有对应文档的孤立实体

    参数:
        valid_doc_ids: 有效文档ID列表

    返回:
        int: 删除的实体数量
    """
    driver = get_driver()
    with driver.session() as session:
        if not valid_doc_ids:
            # 如果没有文档，删除所有实体
            result = session.run("MATCH (e:Entity) DETACH DELETE e RETURN COUNT(*) as deleted")
            return result.single()["deleted"]
        else:
            # 删除 doc_id 不在有效列表中的实体
            result = session.run("""
            MATCH (e:Entity)
            WHERE NOT e.doc_id IN $valid_ids OR e.doc_id IS NULL
            DETACH DELETE e
            RETURN COUNT(*) as deleted
            """, valid_ids=valid_doc_ids)
            return result.single()["deleted"]


def delete_entity(entity_id: str) -> None:
    """
    删除指定实体及其所有关系

    参数:
        entity_id: 实体名称
    """
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (e:Entity {name: $name}) DETACH DELETE e", name=entity_id)


def search(keyword: str, limit: int = 20) -> dict:
    """
    搜索实体和关系

    参数:
        keyword: 搜索关键词
        limit: 返回结果数量限制

    返回:
        dict: {"nodes": [匹配的实体], "edges": [匹配的关系]}
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
        MATCH (e:Entity)-[r]->(t:Entity)
        WHERE e.name CONTAINS $keyword OR t.name CONTAINS $keyword
        RETURN e.name AS source, type(r) AS rel, t.name AS target
        LIMIT $limit
        """, keyword=keyword, limit=limit)
        nodes = {}
        edges = []
        for record in result:
            s, r, t = record["source"], record["rel"], record["target"]
            nodes[s] = {"name": s}
            nodes[t] = {"name": t}
            edges.append({"source": s, "rel": r, "target": t})
        return {"nodes": list(nodes.values()), "edges": edges}


def filter_by_type(entity_type: str, limit: int = 200) -> dict:
    """
    按实体类型筛选知识图谱

    参数:
        entity_type: 实体类型（如：人物、组织、概念等）
        limit: 关系数量限制

    返回:
        dict: {"nodes": [该类型的实体], "edges": [涉及该类型实体的关系]}
    """
    driver = get_driver()
    with driver.session() as session:
        # 第一步：获取该类型的所有实体（包括孤立节点）
        nodes_result = session.run("""
        MATCH (e:Entity)
        WHERE e.type = $entity_type
        RETURN e.name AS name, e.type AS type, e.description AS description, e.doc_id AS doc_id
        """, entity_type=entity_type)
        nodes = {}
        for record in nodes_result:
            name = record["name"]
            nodes[name] = {
                "name": name,
                "type": record["type"] or "概念",
                "description": record["description"] or "",
                "doc_id": record["doc_id"],
            }

        # 第二步：获取涉及该类型实体的关系
        edges_result = session.run("""
        MATCH (e:Entity)-[r]->(t:Entity)
        WHERE e.type = $entity_type OR t.type = $entity_type
        RETURN e.name AS source, type(r) AS rel, t.name AS target
        LIMIT $limit
        """, entity_type=entity_type, limit=limit)
        edges = []
        for record in edges_result:
            s = record["source"]
            r = record["rel"]
            t = record["target"]
            # 如果关系中的实体不在 nodes 中，添加它们
            if s not in nodes:
                nodes[s] = {"name": s, "type": "概念", "description": ""}
            if t not in nodes:
                nodes[t] = {"name": t, "type": "概念", "description": ""}
            edges.append({"source": s, "rel": r, "target": t})
        return {"nodes": list(nodes.values()), "edges": edges}


def get_all_relations(limit: int = 200) -> list:
    """
    获取所有关系列表

    参数:
        limit: 返回数量限制

    返回:
        list: [{"source": "源实体", "rel": "关系", "target": "目标实体"}]
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
        MATCH (e:Entity)-[r]->(t:Entity)
        RETURN e.name AS source, type(r) AS rel, t.name AS target
        LIMIT $limit
        """, limit=limit)
        relations = []
        for record in result:
            relations.append({
                "source": record["source"],
                "rel": record["rel"],
                "target": record["target"],
            })
        return relations


def update_entity(name: str, entity_type: str, description: str = "") -> None:
    """
    更新实体信息

    参数:
        name: 实体名称（用于查找）
        entity_type: 新的实体类型
        description: 新的实体描述
    """
    driver = get_driver()
    with driver.session() as session:
        session.run("""
        MATCH (e:Entity {name: $name})
        SET e.type = $type, e.description = $description
        """, name=name, type=entity_type, description=description)


def delete_relation(source: str, relation: str, target: str) -> None:
    """
    删除指定关系

    参数:
        source: 源实体名称
        relation: 关系类型
        target: 目标实体名称
    """
    driver = get_driver()
    with driver.session() as session:
        session.run(f"""
        MATCH (a:Entity {{name: $source}})-[r:`{relation}`]->(b:Entity {{name: $target}})
        DELETE r
        """, source=source, target=target)


def get_entity_neighbors(entity_name: str, limit: int = 50) -> dict:
    """
    获取实体的邻居节点（关联实体）

    参数:
        entity_name: 实体名称
        limit: 返回数量限制

    返回:
        list: [{"name": "实体名", "type": "类型", "description": "描述", "rel": "关系", "direction": "in/out"}]
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
        MATCH (e:Entity)-[r]-(t:Entity)
        WHERE e.name = $name
        RETURN t.name AS name, t.type AS type, t.description AS description,
               type(r) AS rel, startNode(r).name AS from_node
        LIMIT $limit
        """, name=entity_name, limit=limit)
        neighbors = []
        for record in result:
            neighbors.append({
                "name": record["name"],
                "type": record["type"] or "概念",
                "description": record["description"] or "",
                "rel": record["rel"],
                "direction": "out" if record["from_node"] == entity_name else "in",
            })
        return neighbors


def health() -> bool:
    """
    检查 Neo4j 连接健康状态

    返回:
        bool: 连接正常返回 True，否则返回 False
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("RETURN 1")
        return True
    except Exception:
        return False
