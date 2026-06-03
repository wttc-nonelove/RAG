import chromadb
from app.config import get_settings

_settings = get_settings()
_client = chromadb.HttpClient(host=_settings.CHROMA_HOST, port=_settings.CHROMA_PORT)
_collection = None


def get_collection(name: str = "kb_chunks"):
    global _collection
    if _collection is None:
        _collection = _client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    return _collection


def reset_collection(name: str = "kb_chunks"):
    """重置集合（删除并重新创建）"""
    global _collection
    try:
        _client.delete_collection(name)
    except Exception:
        pass
    _collection = _client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    return _collection


def query(vector: list[float], top_k: int = 5) -> dict:
    col = get_collection()
    return col.query(query_embeddings=[vector], n_results=top_k, include=["documents", "metadatas", "distances"])


def add_batch(ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
    col = get_collection()
    col.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def delete_by_doc_id(doc_id: int) -> None:
    col = get_collection()
    col.delete(where={"doc_id": doc_id})


def count() -> int:
    return get_collection().count()


def health() -> bool:
    try:
        _client.heartbeat()
        return True
    except Exception:
        return False
