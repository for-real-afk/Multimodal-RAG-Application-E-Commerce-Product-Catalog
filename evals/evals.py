"""
evals.py — Evaluation suite for RAG system (FIXED for new Gemini SDK)
"""

import os
import sys
import json
import time
from typing import List, Dict
from google import genai
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# Fix path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ─────────────────────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "TC1",
        "query": "noise cancelling headphones under 100 with bass",
        "expected_ids": ["WH006"],
    },
    {
        "id": "TC2",
        "query": "eco friendly yoga mat non slip thick",
        "expected_ids": ["YM001", "YM003"],
    },
]

# ─────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────

def precision_at_k(retrieved, relevant, k=5):
    top_k = retrieved[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / k


def reciprocal_rank(retrieved, relevant):
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            return 1 / i
    return 0.0


# ─────────────────────────────────────────────────────────────
# LLM JUDGE (FIXED)
# ─────────────────────────────────────────────────────────────

def llm_score(prompt: str) -> float:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text = response.text.strip()

        # 🔥 Extract FIRST FLOAT (robust fix)
        match = re.search(r"\d+(\.\d+)?", text)

        if match:
            score = float(match.group())
            return max(0.0, min(1.0, score))

        return 0.5

    except Exception as e:
        print("LLM ERROR:", e)
        return 0.5


def judge_faithfulness(answer, products):
    context = "\n".join([p["title"] for p in products])

    prompt = f"""
Rate from 0 to 1.

Context:
{context}

Answer:
{answer}

Score:
"""
    return llm_score(prompt)


def judge_relevance(query, answer):
    prompt = f"""
Rate from 0 to 1.

Query: {query}
Answer: {answer}

Score:
"""
    return llm_score(prompt)


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

def run():
    from retriever import retrieve
    from generator import generate_answer

    all_p, all_rr = [], []

    for tc in TEST_CASES:
        print(f"\n🔍 {tc['query']}")

        retrieved = retrieve(tc["query"], n_results=5)
        ids = [p["product_id"] for p in retrieved]

        answer = generate_answer(tc["query"], retrieved)

        p = precision_at_k(ids, tc["expected_ids"])
        rr = reciprocal_rank(ids, tc["expected_ids"])

        faith = judge_faithfulness(answer, retrieved)
        rel = judge_relevance(tc["query"], answer)

        print("IDs:", ids)
        print("Answer:", answer[:120])
        print(f"P@5={p:.2f} | RR={rr:.2f} | Faith={faith:.2f} | Rel={rel:.2f}")

        all_p.append(p)
        all_rr.append(rr)

        time.sleep(1)

    print("\n==== FINAL ====")
    print("Avg Precision:", sum(all_p)/len(all_p))
    print("MRR:", sum(all_rr)/len(all_rr))


if __name__ == "__main__":
    run()