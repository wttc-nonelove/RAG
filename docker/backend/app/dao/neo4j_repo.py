from neo4j import GraphDatabase
from app.config import get_settings

_settings = get_settings()
_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(_settings.NEO4J_URI, auth=(_settings.NEO4J_USER, _settings.NEO4J_PASSWORD))
    return _driver


def query_subgraph(terms: list[str], limit: int = 20) -> dict:
    driver = get_driver()
    with driver.session() as session:
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
    driver = get_driver()
    with driver.session() as session:
        # 先获取所有实体节点
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

        # 再获取关系（limit=0 表示不限制）
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
    driver = get_driver()
    with driver.session() as session:
        session.run("""
        MERGE (e:Entity {name: $name})
        SET e.type = $type, e.description = $description, e.doc_id = $doc_id
        """, name=name, type=entity_type, description=description, doc_id=doc_id)


def create_relation(source: str, relation: str, target: str) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run(f"""
        MATCH (a:Entity {{name: $source}}), (b:Entity {{name: $target}})
        MERGE (a)-[r:`{relation}`]->(b)
        """, source=source, target=target)


def delete_by_doc_id(doc_id: int) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (e:Entity {doc_id: $doc_id}) DETACH DELETE e", doc_id=doc_id)


def delete_entity(entity_id: str) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (e:Entity {name: $name}) DETACH DELETE e", name=entity_id)


def search(keyword: str, limit: int = 20) -> dict:
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
    driver = get_driver()
    with driver.session() as session:
        # 先获取该类型的所有实体（包括孤立节点）
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

        # 再获取涉及该类型实体的关系
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
    driver = get_driver()
    with driver.session() as session:
        session.run("""
        MATCH (e:Entity {name: $name})
        SET e.type = $type, e.description = $description
        """, name=name, type=entity_type, description=description)


def delete_relation(source: str, relation: str, target: str) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run(f"""
        MATCH (a:Entity {{name: $source}})-[r:`{relation}`]->(b:Entity {{name: $target}})
        DELETE r
        """, source=source, target=target)


def get_entity_neighbors(entity_name: str, limit: int = 50) -> dict:
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
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("RETURN 1")
        return True
    except Exception:
        return False
