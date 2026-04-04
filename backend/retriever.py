"""
retriever.py — RAG retrieval pipeline.
"""

from typing import List, Dict, Any, Optional
from ingest import generate_query_embedding
from vector_store import search as vs_search


def retrieve(
    query_text: str,
    image_b64: Optional[str] = None,
    n_results: int = 5,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Generate query embedding and retrieve top-n matching products.
    
    Returns list of product dicts with match_score field added.
    """
    query_embedding = generate_query_embedding(query_text, image_b64)
    
    results = vs_search(
        query_embedding=query_embedding,
        n_results=n_results,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )
    
    return results
