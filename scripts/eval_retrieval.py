"""
Day 7 eval script — runs hand-written test questions against an already-
ingested contract and manually checks whether the expected clause_type
shows up in the top-k results. This is a lightweight recall@k proxy,
good enough to reason about retrieval quality without a full labeled
eval set (and a solid basis for the "how do you evaluate retrieval"
interview question).

Requires: vendor_agreement.txt already ingested (via seed_and_ingest.py
or the /documents/upload API), Postgres + Qdrant running.

Usage (from repo root, backend venv activated):
    python scripts/eval_retrieval.py
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import SessionLocal
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank

# Hand-written test questions with the clause_type we expect to see
# in the top-k retrieved results. Extend this as you add more sample
# contracts and question types.
TEST_QUESTIONS = [
    {"query": "What happens if we want to end this contract early?", "expected_clause_type": "termination"},
    {"query": "Does this agreement automatically renew?", "expected_clause_type": "auto_renewal"},
    {"query": "How much can we be sued for under this agreement?", "expected_clause_type": "liability"},
    {"query": "When do invoices need to be paid?", "expected_clause_type": "payment"},
    {"query": "Can we share confidential information with a third party?", "expected_clause_type": "confidentiality"},
    {"query": "Who owns the work product created under this agreement?", "expected_clause_type": "intellectual_property"},
    {"query": "Which state's law governs this contract?", "expected_clause_type": "governing_law"},
]

TOP_K = 5


def main():
    db = SessionLocal()
    hits = 0

    try:
        for case in TEST_QUESTIONS:
            query = case["query"]
            expected = case["expected_clause_type"]

            candidates = hybrid_retrieve(db, query=query, top_k=20)
            results = rerank(query, candidates, top_k=TOP_K)

            found_types = [r["clause_type"] for r in results]
            hit = expected in found_types
            hits += int(hit)

            status = "HIT " if hit else "MISS"
            print(f"[{status}] \"{query}\"")
            print(f"        expected: {expected} | top-{TOP_K} types: {found_types}")
            if results:
                top = results[0]
                preview = top["text"].replace(chr(10), " ")[:80]
                print(f"        top result (rerank_score={top['rerank_score']:.3f}): \"{preview}...\"")
            print()

        recall_at_k = hits / len(TEST_QUESTIONS)
        print("=" * 60)
        print(f"Recall@{TOP_K}: {hits}/{len(TEST_QUESTIONS)} = {recall_at_k:.0%}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
