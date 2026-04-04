"""
main.py — FastAPI backend for the Multimodal RAG E-Commerce application.

Endpoints:
  GET    /products              — list/filter products (paginated)
  POST   /products              — create product + embed
  GET    /products/{id}         — get single product
  PUT    /products/{id}         — update product (re-embed if needed)
  DELETE /products/{id}         — delete from DB + vector store
  POST   /search                — RAG-powered semantic search
  GET    /categories            — list all categories
  GET    /explorer/db           — data explorer: all DB products
  GET    /explorer/vectors      — data explorer: all vectors + sync status
  GET    /health                — health check
"""

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import database as db
import vector_store as vs
from ingest import generate_multimodal_embedding
from retriever import retrieve
from generator import generate_answer

app = FastAPI(
    title="Multimodal RAG E-Commerce API",
    description="Product catalog with semantic search powered by Gemini",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    db.init_db()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_id: str
    title: str
    category: str
    brand: str
    price: float = Field(gt=0)
    rating: float = Field(ge=0, le=5)
    review_count: int = Field(ge=0)
    description: str = Field(min_length=50)
    features: List[str] = Field(min_length=3)
    image_url: str


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    image_url: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    image_b64: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    n_results: int = Field(default=5, ge=1, le=20)


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "db_products": db.get_all_products(page_size=1)["total"],
        "vector_count": vs.vector_count(),
    }


# ─── Categories ──────────────────────────────────────────────────────────────

@app.get("/categories")
def get_categories():
    return {"categories": db.get_categories()}


# ─── Products CRUD ───────────────────────────────────────────────────────────

@app.get("/products")
def list_products(
    keyword: str = "",
    category: str = "",
    min_price: float = 0,
    max_price: float = 9999,
    min_rating: float = 0,
    sort_by: str = "title",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 20,
):
    return db.get_all_products(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@app.post("/products", status_code=201)
def create_product(payload: ProductCreate):
    if db.get_product(payload.product_id):
        raise HTTPException(
            status_code=409,
            detail=f"Product {payload.product_id} already exists",
        )

    product_dict = payload.model_dump()
    db.insert_product(product_dict)

    try:
        embedding = generate_multimodal_embedding(product_dict)
        vs.upsert_product(payload.product_id, embedding, product_dict)
    except Exception as e:
        print(f"[WARN] Embedding failed for {payload.product_id}: {e}")

    return db.get_product(payload.product_id)


@app.put("/products/{product_id}")
def update_product(product_id: str, payload: ProductUpdate):
    if not db.get_product(product_id):
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = db.update_product(product_id, updates)

    if "description" in updates or "image_url" in updates or "features" in updates:
        try:
            full_product = db.get_product(product_id)
            vs.delete_product(product_id)
            embedding = generate_multimodal_embedding(full_product)
            vs.upsert_product(product_id, embedding, full_product)
        except Exception as e:
            print(f"[WARN] Re-embedding failed for {product_id}: {e}")

    return updated


@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if not db.get_product(product_id):
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    db.delete_product(product_id)
    vs.delete_product(product_id)

    return {"deleted": product_id, "status": "ok"}


# ─── RAG Search ──────────────────────────────────────────────────────────────

@app.post("/search")
def rag_search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = retrieve(
        query_text=request.query,
        image_b64=request.image_b64,
        n_results=request.n_results,
        category=request.category,
        min_price=request.min_price,
        max_price=request.max_price,
    )

    answer = generate_answer(
        query=request.query,
        retrieved_products=results,
        image_provided=bool(request.image_b64),
    )

    return {
        "query": request.query,
        "answer": answer,
        "results": results,
        "total_results": len(results),
    }


# ─── Data Explorer ───────────────────────────────────────────────────────────

@app.get("/explorer/db")
def explorer_db(
    sort_by: str = "title",
    sort_dir: str = "asc",
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 50,
):
    return db.get_all_products(
        keyword=keyword,
        category=category,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@app.get("/explorer/vectors")
def explorer_vectors():
    all_db = db.get_all_products(page_size=200)["products"]
    db_ids = {p["product_id"] for p in all_db}
    indexed_ids = set(vs.get_indexed_ids())
    vectors = vs.get_all_vectors()

    for v in vectors:
        v["in_db"] = v["vector_id"] in db_ids

    return {
        "vector_count": len(vectors),
        "vectors": vectors,
        "missing_vectors": [pid for pid in db_ids if pid not in indexed_ids],
        "orphan_vectors": [v["vector_id"] for v in vectors if not v["in_db"]],
    }