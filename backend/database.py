"""
database.py — SQLite database layer for the e-commerce RAG application.
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DB_PATH = "products.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id   TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                category     TEXT NOT NULL,
                brand        TEXT NOT NULL,
                price        REAL NOT NULL,
                rating       REAL NOT NULL,
                review_count INTEGER NOT NULL,
                description  TEXT NOT NULL,
                features     TEXT NOT NULL,   -- JSON array stored as string
                image_url    TEXT NOT NULL,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_timestamp
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP
                WHERE product_id = NEW.product_id;
            END
        """)


# ─── CRUD helpers ────────────────────────────────────────────────────────────

def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    d["features"] = json.loads(d["features"])
    return d


def insert_product(product: Dict[str, Any]) -> Dict[str, Any]:
    with db_session() as conn:
        conn.execute("""
            INSERT INTO products
                (product_id, title, category, brand, price, rating,
                 review_count, description, features, image_url)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            product["product_id"],
            product["title"],
            product["category"],
            product["brand"],
            float(product["price"]),
            float(product["rating"]),
            int(product["review_count"]),
            product["description"],
            json.dumps(product["features"]),
            product["image_url"],
        ))
    return get_product(product["product_id"])


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_all_products(
    keyword: str = "",
    category: str = "",
    min_price: float = 0,
    max_price: float = 9999,
    min_rating: float = 0,
    sort_by: str = "title",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    allowed_sort = {"title", "price", "rating", "review_count", "category", "brand"}
    if sort_by not in allowed_sort:
        sort_by = "title"
    sort_dir = "DESC" if sort_dir.lower() == "desc" else "ASC"

    conditions = ["price BETWEEN ? AND ?", "rating >= ?"]
    params: List[Any] = [min_price, max_price, min_rating]

    if keyword:
        conditions.append("(title LIKE ? OR description LIKE ? OR brand LIKE ?)")
        kw = f"%{keyword}%"
        params += [kw, kw, kw]
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM products {where} ORDER BY {sort_by} {sort_dir}"

    with get_connection() as conn:
        all_rows = conn.execute(query, params).fetchall()

    total = len(all_rows)
    start = (page - 1) * page_size
    page_rows = all_rows[start: start + page_size]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "products": [_row_to_dict(r) for r in page_rows],
    }


def update_product(product_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    allowed = {"title", "category", "brand", "price", "rating",
                "review_count", "description", "features", "image_url"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return get_product(product_id)

    if "features" in filtered:
        filtered["features"] = json.dumps(filtered["features"])

    set_clause = ", ".join(f"{k} = ?" for k in filtered)
    params = list(filtered.values()) + [product_id]

    with db_session() as conn:
        conn.execute(
            f"UPDATE products SET {set_clause} WHERE product_id = ?", params
        )
    return get_product(product_id)


def delete_product(product_id: str) -> bool:
    with db_session() as conn:
        cur = conn.execute(
            "DELETE FROM products WHERE product_id = ?", (product_id,)
        )
    return cur.rowcount > 0


def get_categories() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products ORDER BY category"
        ).fetchall()
    return [r[0] for r in rows]
