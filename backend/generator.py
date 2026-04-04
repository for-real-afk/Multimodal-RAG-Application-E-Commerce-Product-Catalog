"""
generator.py — Answer generation using Gemini (NEW SDK), grounded in retrieved products.
"""

import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

from typing import List, Dict, Any
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = """You are a helpful e-commerce shopping assistant. 
You answer customer questions based ONLY on the product information provided.
- Be concise and helpful
- Highlight the best matching product(s) first
- Mention specific features relevant to the query
- Include price when relevant
- If no products match well, say so honestly
- Never fabricate product details not in the context"""


def generate_answer(
    query: str,
    retrieved_products: List[Dict[str, Any]],
    image_provided: bool = False,
) -> str:
    if not retrieved_products:
        return "I couldn't find any products matching your query. Please try different search terms or adjust your filters."

    context_parts = []
    for i, p in enumerate(retrieved_products, 1):
        features = p.get("features", [])
        if isinstance(features, list):
            features_text = "\n    - " + "\n    - ".join(features)
        else:
            features_text = str(features)

        context_parts.append(
            f"Product {i} (Match Score: {p.get('match_score', 0):.2%}):\n"
            f"  Title: {p['title']}\n"
            f"  Category: {p['category']}\n"
            f"  Brand: {p['brand']}\n"
            f"  Price: ${p['price']:.2f}\n"
            f"  Rating: {p['rating']}/5.0 ({p.get('review_count', 0):,} reviews)\n"
            f"  Description: {p['description']}\n"
            f"  Features:{features_text}"
        )

    context = "\n\n".join(context_parts)
    image_note = " (User also provided an image of what they're looking for.)" if image_provided else ""

    prompt = f"""{SYSTEM_PROMPT}

Customer Query: {query}{image_note}

Retrieved Products:
{context}

Please provide a helpful, concise answer (3-5 sentences) recommending the best product(s).
Start with your top recommendation and justify using features + price.
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",   # stable, fast, free-tier friendly
            contents=prompt,
        )
        return response.text.strip()

    except Exception as e:
        print("GENERATION ERROR:", e)
        top = retrieved_products[0]
        return (
            f"I found {len(retrieved_products)} relevant products. "
            f"The best match is '{top['title']}' priced at ${top['price']:.2f}. "
            f"It stands out due to its strong features and rating."
        )