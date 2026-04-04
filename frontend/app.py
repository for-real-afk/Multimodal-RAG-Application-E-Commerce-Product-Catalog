"""
app.py — Streamlit frontend for the Multimodal RAG E-Commerce application.

Pages:
  1. 🔍 RAG Search         — Natural language + optional image search
  2. 📦 Product Catalog    — Browse & filter all products (READ)
  3. ➕ Add Product        — Create new product with embedding
  4. ✏️  Manage Products   — Edit & delete products
  5. 🗄️  Data Explorer     — View DB and vector store state

Run with:
    streamlit run app.py
"""

import os
import base64
import requests
import streamlit as st
from PIL import Image
from io import BytesIO
import json

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="🛍️ Multimodal RAG — Product Catalog",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    try:
        resp = requests.request(method, f"{API_BASE}{path}", timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def img_from_url(url: str, width: int = 200):
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content))
        return img
    except Exception:
        return None


def star_rating(rating: float) -> str:
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty


@st.cache_data(ttl=60)
def get_categories():
    data = api("GET", "/categories")
    return [""] + data.get("categories", []) if data else [""]


# ─── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.title("🛍️ RAG Product Catalog")
st.sidebar.caption("Multimodal Search — Powered by Gemini")

page = st.sidebar.radio(
    "Navigate",
    [
        "🔍 RAG Search",
        "📦 Product Catalog",
        "➕ Add Product",
        "✏️ Manage Products",
        "🗄️ Data Explorer",
    ],
)

# Health
health = api("GET", "/health")
if health:
    st.sidebar.success(
        f"✅ Online  |  {health['db_products']} products  |  {health['vector_count']} vectors"
    )
else:
    st.sidebar.error("❌ API Offline — start the FastAPI server")

st.sidebar.divider()
st.sidebar.caption("API: " + API_BASE)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: RAG SEARCH
# ─────────────────────────────────────────────────────────────────────────────
if page == "🔍 RAG Search":
    st.title("🔍 Multimodal RAG Search")
    st.caption("Ask a question in natural language. Optionally upload an image for multimodal search.")

    col_q, col_f = st.columns([3, 1])
    with col_q:
        query = st.text_area(
            "Your Query",
            placeholder="e.g. I need noise-cancelling headphones under $100 with good bass",
            height=80,
        )
        image_file = st.file_uploader(
            "Optional: Upload an image (multimodal query)",
            type=["jpg", "jpeg", "png"],
        )

    with col_f:
        st.subheader("Filters")
        categories = get_categories()
        filter_cat = st.selectbox("Category", categories)
        filter_min_p = st.number_input("Min Price ($)", value=0.0, step=10.0)
        filter_max_p = st.number_input("Max Price ($)", value=1000.0, step=10.0)
        n_results = st.slider("# Results", 1, 10, 5)

    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a search query.")
        else:
            image_b64 = None
            if image_file:
                image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

            with st.spinner("Searching and generating answer..."):
                payload = {
                    "query": query,
                    "image_b64": image_b64,
                    "category": filter_cat or None,
                    "min_price": filter_min_p if filter_min_p > 0 else None,
                    "max_price": filter_max_p if filter_max_p < 1000 else None,
                    "n_results": n_results,
                }
                result = api("POST", "/search", json=payload)

            if result:
                # Generated Answer
                st.subheader("💡 AI Answer")
                st.info(result["answer"])
                st.divider()

                # Result Cards
                st.subheader(f"📦 Top {len(result['results'])} Products")
                for i, p in enumerate(result["results"], 1):
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            img = img_from_url(p.get("image_url", ""))
                            if img:
                                st.image(img, width=130)
                        with c2:
                            score_pct = p.get("match_score", 0) * 100
                            st.markdown(
                                f"**#{i} — {p['title']}**  "
                                f"`{score_pct:.1f}% match`"
                            )
                            st.markdown(
                                f"**{p['brand']}** · ${p['price']:.2f} · "
                                f"{star_rating(p['rating'])} {p['rating']} "
                                f"({p['review_count']:,} reviews)"
                            )
                            st.caption(p.get("description", "")[:200] + "...")
                            feats = p.get("features", [])
                            if feats:
                                feat_str = " · ".join(feats[:3])
                                st.caption(f"✓ {feat_str}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: PRODUCT CATALOG
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📦 Product Catalog":
    st.title("📦 Product Catalog")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kw = st.text_input("Search", placeholder="keyword...")
    with col2:
        cats = get_categories()
        cat = st.selectbox("Category", cats)
    with col3:
        min_p = st.number_input("Min $", value=0.0, step=10.0)
        max_p = st.number_input("Max $", value=1000.0, step=10.0)
    with col4:
        sort_by = st.selectbox("Sort By", ["title", "price", "rating", "review_count"])
        sort_dir = st.radio("Direction", ["asc", "desc"], horizontal=True)

    page_num = st.number_input("Page", value=1, min_value=1)
    page_size = 12

    data = api("GET", "/products", params={
        "keyword": kw, "category": cat, "min_price": min_p,
        "max_price": max_p, "sort_by": sort_by, "sort_dir": sort_dir,
        "page": page_num, "page_size": page_size,
    })

    if data:
        total = data["total"]
        st.caption(f"Showing {len(data['products'])} of {total} products")

        cols = st.columns(3)
        for i, p in enumerate(data["products"]):
            with cols[i % 3]:
                with st.container(border=True):
                    img = img_from_url(p.get("image_url", ""))
                    if img:
                        st.image(img, use_column_width=True)
                    st.markdown(f"**{p['title']}**")
                    st.caption(f"{p['brand']} · {p['category']}")
                    st.markdown(
                        f"**${p['price']:.2f}** · {star_rating(p['rating'])} "
                        f"{p['rating']} ({p['review_count']:,})"
                    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: ADD PRODUCT
# ─────────────────────────────────────────────────────────────────────────────
elif page == "➕ Add Product":
    st.title("➕ Add New Product")

    CATEGORIES = [
        "Wireless Headphones", "Mechanical Keyboards", "Running Shoes",
        "Skincare Serums", "Protein Supplements", "Laptop Bags",
        "Smart Watches", "Yoga Mats", "Coffee Makers", "Desk Lamps",
    ]

    with st.form("add_product"):
        c1, c2 = st.columns(2)
        with c1:
            product_id = st.text_input("Product ID *", placeholder="e.g. WH011")
            title = st.text_input("Title *", placeholder="Full product name")
            category = st.selectbox("Category *", CATEGORIES)
            brand = st.text_input("Brand *")
        with c2:
            price = st.number_input("Price ($) *", min_value=0.01, value=99.99)
            rating = st.slider("Rating", 0.0, 5.0, 4.0, 0.1)
            review_count = st.number_input("Review Count", min_value=0, value=100)
            image_url = st.text_input("Image URL *")

        st.markdown("**Description** (min. 3 sentences / 150 chars)")
        description = st.text_area("Description *", height=100,
                                    placeholder="Full product description...")
        char_count = len(description)
        st.caption(f"{char_count} characters {'✅' if char_count >= 150 else '⚠️ too short'}")

        # Dynamic features
        st.markdown("**Features** (min. 3 required)")
        num_features = st.number_input("Number of features", min_value=3, max_value=10, value=3)
        features = []
        for j in range(int(num_features)):
            f = st.text_input(f"Feature {j+1}", key=f"feat_{j}")
            features.append(f)

        # Image preview
        if image_url:
            img = img_from_url(image_url)
            if img:
                st.image(img, width=200, caption="Image Preview")

        submitted = st.form_submit_button("💾 Save & Generate Embedding", type="primary")

    if submitted:
        errors = []
        if not product_id:
            errors.append("Product ID is required")
        if not title:
            errors.append("Title is required")
        if len(description) < 150:
            errors.append("Description too short (min 150 chars)")
        if len([f for f in features if f.strip()]) < 3:
            errors.append("At least 3 non-empty features required")
        if not image_url:
            errors.append("Image URL is required")

        if errors:
            for e in errors:
                st.error(e)
        else:
            payload = {
                "product_id": product_id,
                "title": title,
                "category": category,
                "brand": brand,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "description": description,
                "features": [f for f in features if f.strip()],
                "image_url": image_url,
            }
            with st.spinner("Saving product and generating multimodal embedding..."):
                result = api("POST", "/products", json=payload)
            if result:
                st.success(f"✅ Product {product_id} created and indexed!")
                st.json(result)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: MANAGE PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "✏️ Manage Products":
    st.title("✏️ Manage Products")

    data = api("GET", "/products", params={"page_size": 200})
    if not data:
        st.stop()

    products = data["products"]
    product_options = {f"{p['product_id']} — {p['title']}": p["product_id"]
                       for p in products}

    selected_label = st.selectbox("Select a Product", list(product_options.keys()))
    selected_id = product_options[selected_label]
    product = api("GET", f"/products/{selected_id}")

    if not product:
        st.stop()

    tab_edit, tab_delete = st.tabs(["✏️ Edit", "🗑️ Delete"])

    with tab_edit:
        with st.form("edit_product"):
            c1, c2 = st.columns(2)
            with c1:
                new_title = st.text_input("Title", value=product["title"])
                new_brand = st.text_input("Brand", value=product["brand"])
                new_price = st.number_input("Price ($)", value=float(product["price"]))
            with c2:
                new_rating = st.slider("Rating", 0.0, 5.0, float(product["rating"]), 0.1)
                new_review_count = st.number_input("Reviews", value=int(product["review_count"]))
                new_image_url = st.text_input("Image URL", value=product["image_url"])

            new_desc = st.text_area("Description", value=product["description"], height=120)
            st.caption("⚠️ Changing description or image will trigger automatic re-embedding")

            features_str = "\n".join(product["features"])
            new_features_raw = st.text_area(
                "Features (one per line)", value=features_str, height=100
            )

            if new_image_url:
                img = img_from_url(new_image_url)
                if img:
                    st.image(img, width=150, caption="Image Preview")

            save_btn = st.form_submit_button("💾 Update Product", type="primary")

        if save_btn:
            new_features = [f.strip() for f in new_features_raw.strip().split("\n") if f.strip()]
            payload = {
                "title": new_title,
                "brand": new_brand,
                "price": new_price,
                "rating": new_rating,
                "review_count": new_review_count,
                "image_url": new_image_url,
                "description": new_desc,
                "features": new_features,
            }
            with st.spinner("Updating and re-embedding if needed..."):
                result = api("PUT", f"/products/{selected_id}", json=payload)
            if result:
                st.success(f"✅ Product {selected_id} updated!")
                st.json(result)

    with tab_delete:
        st.warning(
            f"**Are you sure you want to delete:**  \n"
            f"**{product['title']}** (ID: {selected_id})?\n\n"
            "This will remove the product from both the database **and** the vector store."
        )
        if st.button("🗑️ Confirm Delete", type="primary"):
            result = api("DELETE", f"/products/{selected_id}")
            if result:
                st.success(f"✅ Product {selected_id} deleted from DB and vector store.")
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🗄️ Data Explorer":
    st.title("🗄️ Data Explorer")
    st.caption("Real-time view of the database and vector store state.")

    tab_db, tab_vec = st.tabs(["🗃️ Database View", "🧲 Vector Store View"])

    with tab_db:
        st.subheader("SQLite Products Table")
        db_data = api("GET", "/explorer/db", params={"page_size": 200})
        if db_data:
            st.metric("Total Products in DB", db_data["total"])
            products = db_data["products"]

            # Build display dataframe
            rows = []
            for p in products:
                rows.append({
                    "ID": p["product_id"],
                    "Title": p["title"][:40],
                    "Category": p["category"],
                    "Brand": p["brand"],
                    "Price": f"${p['price']:.2f}",
                    "Rating": f"{p['rating']}★",
                    "Reviews": p["review_count"],
                })

            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=500)

    with tab_vec:
        st.subheader("ChromaDB Vector Store")
        vec_data = api("GET", "/explorer/vectors")
        if vec_data:
            col1, col2, col3 = st.columns(3)
            col1.metric("Indexed Vectors", vec_data["vector_count"])
            col2.metric("Missing Vectors", len(vec_data["missing_vectors"]),
                        delta=f"-{len(vec_data['missing_vectors'])}" if vec_data["missing_vectors"] else None,
                        delta_color="inverse")
            col3.metric("Orphan Vectors", len(vec_data["orphan_vectors"]))

            if vec_data["missing_vectors"]:
                st.warning(
                    f"⚠️ {len(vec_data['missing_vectors'])} products in DB have no vector: "
                    + ", ".join(vec_data["missing_vectors"])
                )

            if vec_data["orphan_vectors"]:
                st.info(
                    f"ℹ️ {len(vec_data['orphan_vectors'])} orphan vectors "
                    "(products deleted from DB): "
                    + ", ".join(vec_data["orphan_vectors"])
                )

            st.subheader("Indexed Products")
            rows = []
            for v in vec_data["vectors"]:
                rows.append({
                    "Vector ID": v["vector_id"],
                    "Title": v.get("title", "")[:35],
                    "Category": v.get("category", ""),
                    "Price": f"${float(v.get('price', 0)):.2f}",
                    "In DB": "✅" if v.get("in_db") else "❌ ORPHAN",
                })

            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=500)
