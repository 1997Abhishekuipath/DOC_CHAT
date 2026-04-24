"""RAG orchestration: retrieve -> prompt -> answer (with confidence)."""
from typing import AsyncIterator, List

from .embeddings import search_chunks
from .llm import chat_stream, chat_complete


SYSTEM_PROMPT = """You are DocChat, a precise document-grounded assistant.

Rules:
- Answer ONLY using the provided context.
- Every factual sentence MUST include an inline citation like [1], [2] that maps to the context sources.
- If the context does not contain the answer, reply exactly: "I don't have enough information in the provided documents to answer that."
- Prefer concise, well-structured markdown. Use lists, tables, and bold where helpful.
- Never invent source names, page numbers, or facts not present in the context.
"""


def _build_context(hits: List[dict]) -> str:
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(
            f"[{i}] Source: {h['filename']} (page {h['page']})\n{h['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def _confidence_from_hits(hits: List[dict]) -> str:
    """Map best retrieval distance to HIGH/MEDIUM/LOW. Cosine distance: lower=better."""
    if not hits:
        return "LOW"
    best = min((h.get("distance") or 1.0) for h in hits)
    # Cosine distance: 0 = identical, 2 = opposite
    if best < 0.35:
        return "HIGH"
    if best < 0.6:
        return "MEDIUM"
    return "LOW"


async def retrieve(query: str, document_ids: List[str], top_k: int = 5) -> List[dict]:
    return await search_chunks(query, document_ids, top_k=top_k)


def build_messages(query: str, hits: List[dict], history: List[dict] | None = None) -> List[dict]:
    context = _build_context(hits) if hits else "(no relevant context retrieved)"
    msgs: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        msgs.extend(history[-6:])  # last 3 turns
    msgs.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        }
    )
    return msgs


async def answer_stream(
    query: str, document_ids: List[str], history: List[dict] | None = None, top_k: int = 5
) -> tuple[AsyncIterator[str], List[dict], str]:
    hits = await retrieve(query, document_ids, top_k=top_k)
    messages = build_messages(query, hits, history)
    confidence = _confidence_from_hits(hits)
    return chat_stream(messages), hits, confidence


async def answer(
    query: str, document_ids: List[str], history: List[dict] | None = None, top_k: int = 5
) -> tuple[str, List[dict], str]:
    hits = await retrieve(query, document_ids, top_k=top_k)
    messages = build_messages(query, hits, history)
    confidence = _confidence_from_hits(hits)
    text = await chat_complete(messages)
    return text, hits, confidence


async def suggest_followups(query: str, answer_text: str, hits: List[dict]) -> List[str]:
    """Generate 3 short follow-up questions."""
    if not hits:
        return []
    doc_summary = ", ".join({h["filename"] for h in hits})
    prompt = (
        f"Given this question: \"{query}\"\nAnd this answer: \"{answer_text[:500]}\"\n"
        f"Suggest 3 short follow-up questions a user might ask next, based strictly on the documents ({doc_summary}).\n"
        "Respond as a JSON array of 3 strings, nothing else."
    )
    try:
        raw = await chat_complete(
            [
                {"role": "system", "content": "You output only valid JSON arrays."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        import json
        import re

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(0))
        return [str(x) for x in data][:3]
    except Exception:
        return []
