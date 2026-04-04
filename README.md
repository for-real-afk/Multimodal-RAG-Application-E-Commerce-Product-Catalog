# Multimodal RAG Application — E-Commerce Product Catalog

A production-grade Multimodal Retrieval-Augmented Generation (RAG) application built with **FastAPI**, **Streamlit**, **ChromaDB**, and **Google Gemini**.

## Architecture

```
products.json
     │
     ▼
load_data.py ──► SQLite (products.db)
     │
     ▼
Gemini 1.5 Flash (image → description)
     │
     ▼
text-embedding-004 (768-dim embedding)
     │
     ▼
ChromaDB (vector store)
     │
     ▼
FastAPI (/search) ──► retriever.py ──► generator.py ──► Answer
     │
     ▼
Streamlit (5-page UI)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI + Uvicorn |
| Database | SQLite (built-in) |
| Vector Store | ChromaDB (persistent) |
| Embedding | Google text-embedding-004 |
| Image Understanding | Google Gemini 1.5 Flash |
| Answer Generation | Google Gemini 1.5 Flash |
| Frontend | Streamlit |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Gemini API key

```bash
export GEMINI_API_KEY=your_gemini_api_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

### 3. Load data (one-time)

```bash
cd backend
python load_data.py
```

This will:
- Create `products.db` (SQLite) with all 100 products
- Generate multimodal embeddings for each product
- Store embeddings in `chroma_db/`

Expected time: ~5-8 minutes (100 products × ~3s each)

### 4. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Start the Streamlit frontend

```bash
cd frontend
streamlit run app.py
```

Opens at: http://localhost:8501

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + counts |
| GET | `/products` | List/filter products (paginated) |
| POST | `/products` | Create product + embed |
| GET | `/products/{id}` | Get single product |
| PUT | `/products/{id}` | Update (re-embeds if needed) |
| DELETE | `/products/{id}` | Delete from DB + vector store |
| POST | `/search` | Multimodal RAG search |
| GET | `/categories` | List all categories |
| GET | `/explorer/db` | DB explorer view |
| GET | `/explorer/vectors` | Vector store explorer |

## UI Pages

1. **🔍 RAG Search** — Natural language + optional image query, category/price filters, top-5 result cards + AI answer
2. **📦 Product Catalog** — Paginated product grid with filters (keyword, category, price, rating, sort)  
3. **➕ Add Product** — Full create form with image preview, character counter, dynamic feature rows
4. **✏️ Manage Products** — Edit modal (auto re-embeds on description/image change) + delete with confirmation
5. **🗄️ Data Explorer** — DB table view + vector store view with sync status highlighting

## Running Evaluations

```bash
cd evals
python evals.py
```

Results saved to `results/eval_report.md` and `results/eval_report.json`.

## Project Structure

```
submission/
├── dataset/
│   └── products.json          # 100 products, 10 categories
├── backend/
│   ├── main.py                # FastAPI app + all endpoints
│   ├── load_data.py           # One-time data seeding script
│   ├── ingest.py              # Multimodal embedding generation
│   ├── retriever.py           # RAG retrieval pipeline
│   ├── generator.py           # Gemini answer generation
│   ├── database.py            # SQLite CRUD layer
│   └── vector_store.py        # ChromaDB operations
├── frontend/
│   └── app.py                 # Streamlit 5-page UI
├── evals/
│   └── evals.py               # Evaluation suite (4 metrics)
├── results/
│   ├── query_results.md       # 5 mandatory test case results
│   └── eval_report.md         # Evaluation metrics report
├── requirements.txt
└── README.md
```

## Key Design Decisions

**Multimodal Embedding Strategy:**  
Rather than using a native multimodal embedding model (which Gemini doesn't expose directly), we use a two-step approach:
1. Gemini 1.5 Flash generates a rich visual description of the product image
2. This description is concatenated with the text fields (title, category, description, features)
3. The combined text is embedded with `text-embedding-004`

This produces embeddings that capture both visual and semantic product attributes.

**Vector Store Sync:**  
Every write operation (CREATE, UPDATE, DELETE) is atomic across both storage systems. Updates to `description`, `image_url`, or `features` automatically trigger re-embedding.

**Error Handling:**  
Image fetch failures gracefully fall back to text-only embedding. The API uses consistent HTTP status codes (201, 404, 409) and never silently fails.
