from app.dao import neo4j_repo


def get_overview(limit: int = 200) -> dict:
    return neo4j_repo.get_overview(limit)


def search_graph(keyword: str, limit: int = 20) -> dict:
    return neo4j_repo.search(keyword, limit)


def create_entity(name: str, entity_type: str, description: str = "", doc_id: int = None) -> None:
    neo4j_repo.create_entity(name, entity_type, description, doc_id)


def create_relation(source: str, relation: str, target: str) -> None:
    neo4j_repo.create_relation(source, relation, target)


def delete_entity(entity_id: str) -> None:
    neo4j_repo.delete_entity(entity_id)
