"""
Risk-diffing engine: compares a newly uploaded contract's clauses against
an org's designated "standard template" document of the same contract_type,
flagging clauses that are missing or substantively changed, each with an
LLM-assigned severity score (0.0-1.0).

Matching is done by clause_type rather than section number/position, since
clause numbering varies between contracts even when the underlying clause
types are the same (robust to reordering/renumbering).

For each clause_type present in the template:
  - If absent from the new document entirely -> flagged as "missing".
  - If present in both -> the LLM compares the two texts and flags a
    substantive difference as "changed" (with severity + description),
    or is silently skipped if the LLM finds them consistent.
Clause types present only in the new document (not in the template) are
NOT flagged -- risk-diffing is about deviation from the template, not an
exhaustive audit of every clause.

`call_llm_fn` is injectable for testability, same pattern as synthesis.py.
"""

import json
import re
from typing import List, Dict, Optional, Callable

CallLLMFn = Callable[[str], str]


def _default_call_llm(prompt: str) -> str:
    from openai import OpenAI
    from app.core.config import settings

    client = OpenAI(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )
    response = client.chat.completions.create(
        model="nex-agi/nex-n2.5-pro:free",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def group_clauses_by_type(clauses: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for c in clauses:
        groups.setdefault(c["clause_type"], []).append(c)
    return groups


def build_compare_prompt(clause_type: str, template_text: str, new_text: str) -> str:
    return f"""You are a contract risk analyst. Compare the STANDARD TEMPLATE clause \
below against the NEW clause of the same type ("{clause_type}") from an uploaded \
contract.

Respond ONLY with a single JSON object (no markdown fences, no other text) in this \
exact form:
{{"differs": true or false, "severity": a number from 0.0 to 1.0, "description": \
"a one to two sentence explanation of what changed and why it matters, or empty \
string if differs is false"}}

Severity guide: 0.0-0.2 trivial wording difference, 0.3-0.5 moderate difference \
worth reviewing, 0.6-0.8 significant obligation/liability shift, 0.9-1.0 severe \
risk (e.g. missing protection entirely, one-sided term).

STANDARD TEMPLATE clause:
{template_text}

NEW clause:
{new_text}

JSON response:"""


def parse_compare_response(raw: str) -> Dict:
    """
    Parses the LLM's JSON response defensively. If the model didn't return
    valid JSON, fails SAFE by flagging the clause for manual review rather
    than silently treating a parse failure as "no risk found" -- an
    unreviewable comparison should never look identical to a clean one.
    """
    try:
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        return {
            "differs": bool(data.get("differs", False)),
            "severity": float(data.get("severity", 0.5)),
            "description": str(data.get("description", "")),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "differs": True,
            "severity": 0.5,
            "description": "Could not automatically compare this clause -- flagged for manual review.",
        }


def diff_clauses(
    template_clauses: List[Dict],
    new_clauses: List[Dict],
    call_llm_fn: Optional[CallLLMFn] = None,
) -> List[Dict]:
    """
    template_clauses / new_clauses: list of dicts with at least
    {clause_id, clause_type, text}.

    Returns a list of risk flag dicts:
        {clause_id, clause_type, flag_type, severity, description}
    flag_type is "missing" (template clause type absent from new doc) or
    "changed" (present in both, LLM found a substantive difference).
    """
    call_llm = call_llm_fn or _default_call_llm

    template_by_type = group_clauses_by_type(template_clauses)
    new_by_type = group_clauses_by_type(new_clauses)

    flags = []

    for clause_type, template_group in template_by_type.items():
        if clause_type not in new_by_type:
            flags.append({
                "clause_id": None,
                "clause_type": clause_type,
                "flag_type": "missing",
                "severity": 0.8,
                "description": (
                    f"No '{clause_type}' clause found in the uploaded contract, "
                    f"but the standard template includes one."
                ),
            })
            continue

        # MVP: compares the first clause of each type per document. Multi-clause
        # merging (e.g. two separate "payment" clauses) is a future improvement.
        template_clause = template_group[0]
        new_clause = new_by_type[clause_type][0]

        prompt = build_compare_prompt(clause_type, template_clause["text"], new_clause["text"])
        raw = call_llm(prompt)
        result = parse_compare_response(raw)

        if result["differs"]:
            flags.append({
                "clause_id": new_clause["clause_id"],
                "clause_type": clause_type,
                "flag_type": "changed",
                "severity": result["severity"],
                "description": result["description"],
            })

    return flags
