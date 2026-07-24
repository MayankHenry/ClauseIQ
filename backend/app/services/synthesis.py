"""
Citation-grounded answer synthesis via Claude.

Given a question and a list of retrieved+reranked clause candidates,
builds a strict prompt requiring the model to cite a clause_id for every
claim, then validates the response: any citation referencing a clause_id
that wasn't actually provided as context causes the answer to be marked
ungrounded rather than surfaced as if trustworthy. An answer with zero
citations is also marked ungrounded — either the model is refusing (no
relevant context) or failed to cite, and neither case should be shown
to the user as a confidently-sourced answer.

`call_llm_fn` is injectable so prompt-building and citation-validation
logic can be unit-tested without a real API call.
"""

import re
from typing import List, Dict, Optional, Callable

CallLLMFn = Callable[[str], str]

CITATION_PATTERN = re.compile(r"\[clause:([a-zA-Z0-9\-]+)\]")


def _default_call_llm(prompt: str) -> str:
    import anthropic
    from app.core.config import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def build_prompt(question: str, candidates: List[Dict]) -> str:
    context_blocks = []
    for c in candidates:
        section = c.get("section_number") or "N/A"
        clause_type = c.get("clause_type") or "general"
        context_blocks.append(
            f"[clause:{c['clause_id']}] (Section {section}, type: {clause_type})\n{c['text']}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a contract analysis assistant. Answer the question below \
using ONLY the clauses provided in the context.

Rules:
- Every factual claim in your answer MUST be immediately followed by a citation \
tag in the exact form [clause:CLAUSE_ID], using one of the clause IDs shown below.
- Do NOT cite a clause_id that is not shown in the context.
- If the context does not contain enough information to answer, say so explicitly \
and do not guess.
- Be concise and direct.

Context:
{context}

Question: {question}

Answer (with inline [clause:ID] citations):"""


def extract_cited_clause_ids(answer_text: str) -> List[str]:
    return CITATION_PATTERN.findall(answer_text)


def synthesize_answer(
    question: str,
    candidates: List[Dict],
    call_llm_fn: Optional[CallLLMFn] = None,
) -> Dict:
    """
    Returns:
        {
            "answer": str,
            "grounded": bool,           # False if any citation is invalid or missing
            "cited_clause_ids": [...],
            "valid_clause_ids": [...],  # clause_ids that were actually available as context
        }
    """
    if not candidates:
        return {
            "answer": "I don't have any relevant clauses to answer this question.",
            "grounded": False,
            "cited_clause_ids": [],
            "valid_clause_ids": [],
        }

    call_llm = call_llm_fn or _default_call_llm
    prompt = build_prompt(question, candidates)
    raw_answer = call_llm(prompt)

    valid_clause_ids = {c["clause_id"] for c in candidates}
    cited_clause_ids = extract_cited_clause_ids(raw_answer)

    has_invalid_citation = any(cid not in valid_clause_ids for cid in cited_clause_ids)
    has_no_citation = len(cited_clause_ids) == 0
    grounded = not has_invalid_citation and not has_no_citation

    return {
        "answer": raw_answer,
        "grounded": grounded,
        "cited_clause_ids": cited_clause_ids,
        "valid_clause_ids": list(valid_clause_ids),
    }
