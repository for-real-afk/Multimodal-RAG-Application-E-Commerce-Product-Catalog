"""
ingest.py — Multimodal embedding generation using Google Gemini (FIXED).

- Uses gemini-embedding-001
- Uses gemini-1.5-flash for image understanding
- Compatible with latest google-genai SDK
- Auto-loads .env file
"""

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# ✅ Load .env BEFORE reading env vars
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))  # also check project root

import base64
import requests
from typing import List, Optional, Dict, Any
from google import genai

_api_key = os.environ.get("GEMINI_API_KEY", "")
if not _api_key:
    raise ValueError(
        "\n\n[ERROR] GEMINI_API_KEY not found!\n"
        "Create a .env file in the backend/ folder with:\n"
        "  GEMINI_API_KEY=your_key_here\n"
        "Get a free key at: https://aistudio.google.com/app/apikey\n"
    )

client = genai.Client(api_key=_api_key)


def fetch_image_base64(url: str, timeout: int = 10) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception as e:
        print(f"  [WARN] Could not fetch image {url}: {e}")
        return None


def build_text_content(product: Dict[str, Any]) -> str:
    features_text = "; ".join(
        product["features"] if isinstance(product["features"], list)
        else [product["features"]]
    )
    return (
        f"Title: {product['title']}\n"
        f"Category: {product['category']}\n"
        f"Brand: {product['brand']}\n"
        f"Price: ${product['price']}\n"
        f"Rating: {product['rating']}/5.0\n"
        f"Description: {product['description']}\n"
        f"Features: {features_text}"
    )


def generate_text_embedding(text: str) -> List[float]:
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"  [ERROR] Embedding failed: {e}")
        return []


def generate_multimodal_embedding(product: Dict[str, Any]) -> List[float]:
    text_content = build_text_content(product)
    image_description = ""

    img_b64 = fetch_image_base64(product.get("image_url", ""))
    if img_b64:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{
                    "role": "user",
                    "parts": [
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                        {"text": "Describe this product image focusing on color, shape, material, and design in 2-3 sentences."}
                    ]
                }]
            )
            image_description = response.text.strip()
        except Exception as e:
            print(f"  [WARN] Image description failed for {product.get('product_id')}: {e}")

    combined = text_content
    if image_description:
        combined += f"\nVisual Description: {image_description}"

    return generate_text_embedding(combined)


def generate_query_embedding(
    query_text: str,
    image_b64: Optional[str] = None,
) -> List[float]:
    combined_query = query_text

    if image_b64:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[{
                    "role": "user",
                    "parts": [
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                        {"text": f"The user query is: '{query_text}'. Describe the image in a way useful for product search."}
                    ]
                }]
            )
            combined_query += "\n" + response.text.strip()
        except Exception as e:
            print(f"  [WARN] Query image processing failed: {e}")

    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=combined_query
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"  [ERROR] Query embedding failed: {e}")
        return []