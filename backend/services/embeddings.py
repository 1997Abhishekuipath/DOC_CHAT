"""OpenAI embeddings + ChromaDB vector store."""
from typing import List, Optional

import chromadb
from openai import AsyncOpenAI

from core.config import CHROMA_DIR, EMBEDDING_MODEL, OPENAI_API_KEY

_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _chroma_client.get_or_create_collection(
    name="docchat_chunks", metadata={"hnsw:space": "cosine"}
)

_openai_client: Optional[AsyncOpenAI] = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


async def embed_texts(texts: List[str]) -> List[List[float]]:
    client = _get_openai()
    resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


async def embed_query(query: str) -> List[float]:
    embs = await embed_texts([query])
    return embs[0]


async def add_chunks(
    document_id: str,
    owner_id: str,
    filename: str,
    chunks: List[dict],
) -> int:
    """chunks = [{id, text, page, index}, ...]"""
    if not chunks:
        return 0
    texts = [c["text"] for c in chunks]
    embeddings = await embed_texts(texts)
    ids = [c["id"] for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "owner_id": owner_id,
            "filename": filename,
            "page": c.get("page", 1),
            "chunk_index": c.get("index", 0),
        }
        for c in chunks
    ]
    _collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return len(chunks)


async def search_chunks(
    query: str,
    document_ids: List[str],
    top_k: int = 5,
) -> List[dict]:
    """Retrieve top_k chunks across the given document_ids."""
    if not document_ids:
        return []
    query_emb = await embed_query(query)
    where = {"document_id": {"$in": document_ids}} if len(document_ids) > 1 else {"document_id": document_ids[0]}
    results = _collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        where=where,
    )
    hits = []
    if not results.get("ids") or not results["ids"][0]:
        return hits
    for i, _id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        hits.append(
            {
                "chunk_id": _id,
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename"),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
            }
        )
    return hits


def delete_document_chunks(document_id: str) -> None:
    try:
        _collection.delete(where={"document_id": document_id})
    except Exception:
        pass
