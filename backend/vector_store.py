"""
vector_store.py — Pinecone vector store for multimodal embeddings.

Setup:
  1. Sign up at https://app.pinecone.io (free, no credit card)
  2. Create an index:
       - Name:       products
       - Dimensions: 768         (text-embedding-004 output)
       - Metric:     cosine
  3. Copy your API key → PINECONE_API_KEY in .env
  4. pip install pinecone-client
"""
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))
import os
import json
from typing import List, Dict, Any, Optional

from pinecone import Pinecone, ServerlessSpec

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
INDEX_NAME       = "products"
VECTOR_DIM       = 3072   # text-embedding-004


def _get_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Create index if it doesn't exist yet
    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=VECTOR_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),  # free tier region
        )

    return pc.Index(INDEX_NAME)


# ─── Write operations ─────────────────────────────────────────────────────────

def upsert_product(product_id: str, embedding: List[float], metadata: Dict[str, Any]):
    """Insert or update a product vector with its metadata."""
    index = _get_index()

    # Pinecone metadata values must be str / int / float / bool / list[str]
    meta = {
        "product_id":   str(metadata.get("product_id", product_id)),
        "title":        str(metadata.get("title", "")),
        "category":     str(metadata.get("category", "")),
        "brand":        str(metadata.get("brand", "")),
        "price":        float(metadata.get("price", 0)),
        "rating":       float(metadata.get("rating", 0)),
        "review_count": int(metadata.get("review_count", 0)),
        "description":  str(metadata.get("description", ""))[:500],  # Pinecone 40KB limit
        "features":     json.dumps(metadata.get("features", [])),
        "image_url":    str(metadata.get("image_url", "")),
    }

    index.upsert(vectors=[{"id": product_id, "values": embedding, "metadata": meta}])


def delete_product(product_id: str) -> bool:
    """Delete a product vector."""
    try:
        _get_index().delete(ids=[product_id])
        return True
    except Exception:
        return False


# ─── Search ───────────────────────────────────────────────────────────────────

def search(
    query_embedding: List[float],
    n_results: int = 5,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Semantic search with optional metadata filters."""
    index = _get_index()

    # Build Pinecone filter
    filters: Dict = {}
    conditions = []
    if category:
        conditions.append({"category": {"$eq": category}})
    if min_price is not None:
        conditions.append({"price": {"$gte": min_price}})
    if max_price is not None:
        conditions.append({"price": {"$lte": max_price}})

    if len(conditions) == 1:
        filters = conditions[0]
    elif len(conditions) > 1:
        filters = {"$and": conditions}

    kwargs = dict(
        vector=query_embedding,
        top_k=n_results,
        include_metadata=True,
    )
    if filters:
        kwargs["filter"] = filters

    response = index.query(**kwargs)

    results = []
    for match in response.matches:
        meta = dict(match.metadata)
        meta["features"] = json.loads(meta.get("features", "[]"))
        meta["match_score"] = round(match.score, 4)
        results.append(meta)

    return results


# ─── Explorer helpers ─────────────────────────────────────────────────────────

def get_all_vectors() -> List[Dict[str, Any]]:
    """
    Return metadata for all stored vectors.
    Uses a zero-vector query to list all (works for small indexes up to 10k).
    """
    index = _get_index()
    stats = index.describe_index_stats()
    total = stats.total_vector_count

    if total == 0:
        return []

    zero_vec = [0.0] * VECTOR_DIM
    response = index.query(vector=zero_vec, top_k=min(total, 10000), include_metadata=True)

    results = []
    for match in response.matches:
        meta = dict(match.metadata)
        meta["features"] = json.loads(meta.get("features", "[]"))
        meta["vector_id"] = match.id
        results.append(meta)

    return results


def get_indexed_ids() -> List[str]:
    """Return all product_ids currently indexed."""
    vectors = get_all_vectors()
    return [v["vector_id"] for v in vectors]


def vector_count() -> int:
    index = _get_index()
    return index.describe_index_stats().total_vector_count
