"""
Clause-aware chunker.

This is ClauseIQ's core technical differentiator: instead of splitting
documents into fixed-size token windows (the tutorial-RAG approach),
it splits by legal structure — numbered sections/articles first,
falling back to paragraph boundaries for short documents (e.g. a
2-page NDA with no numbered sections at all).

Each chunk also gets a heuristic clause_type tag (termination,
auto_renewal, confidentiality, etc.) via keyword matching, which
later powers the risk-diffing engine's clause-to-clause comparison.
"""

import re
from typing import List, Dict, Optional

# Matches section/article headers like:
#   "1. Termination"
#   "Section 4.2: Confidentiality"
#   "ARTICLE III Payment Terms"      (roman numerals)
SECTION_PATTERN = re.compile(
    r'^\s*(?:(?:ARTICLE|Article|Section|SECTION)\s+)?'
    r'((?:\d+(?:\.\d+)*)|(?:[IVXLCDM]+))[\.\):]?\s+'
    r'([A-Z][A-Za-z \-/&,]{2,80})\s*$'
)

# Keyword -> clause_type. Checked in order; first match wins.
# Extend this list as you encounter more clause types in real contracts.
CLAUSE_TYPE_KEYWORDS = {
    "termination": ["terminat", "end of agreement", "expiration"],
    "auto_renewal": ["automatically renew", "auto-renew", "renewal term"],
    "confidentiality": ["confidential", "non-disclosure", " nda"],
    "indemnification": ["indemnif"],
    "liability": ["limitation of liability", "liability", "liable"],
    "payment": ["payment", "invoice", "fees", "compensation"],
    "governing_law": ["governing law", "jurisdiction", "venue"],
    "intellectual_property": ["intellectual property", "ip rights", "copyright", "trademark"],
    "force_majeure": ["force majeure"],
    "assignment": ["assignment", "assign this agreement"],
    "dispute_resolution": ["arbitration", "dispute resolution", "mediation"],
    "warranty": ["warrant"],
}

# Sections longer than this get sub-split by paragraph so retrieval
# stays precise on long contracts (e.g. a 200-page MSA) instead of
# returning one giant low-precision chunk per article.
MAX_CHUNK_CHARS = 3000


def classify_clause_type(text: str, title: Optional[str] = None) -> str:
    """
    Classifies a clause by keyword match. The section TITLE (e.g. "Confidentiality",
    "Intellectual Property") is checked first and is authoritative when it hits —
    it's short and reliable. Only if the title gives no match do we fall back to
    scanning the full clause body, since body text often mentions unrelated clause
    types in passing (e.g. a confidentiality clause mentioning "termination of this
    Agreement") and would otherwise misclassify.
    """
    if title:
        lowered_title = title.lower()
        for clause_type, keywords in CLAUSE_TYPE_KEYWORDS.items():
            if any(kw in lowered_title for kw in keywords):
                return clause_type

    lowered = text.lower()
    for clause_type, keywords in CLAUSE_TYPE_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return clause_type
    return "general"


def split_into_paragraphs(text: str) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras if paras else ([text.strip()] if text.strip() else [])


def chunk_page_text(text: str, page: Optional[int]) -> List[Dict]:
    """
    Splits one page's (or one document's) raw text into clause-level
    chunks by detecting numbered section headers. If no headers are
    found at all (common in short, informally-written NDAs), falls
    back to paragraph-level chunking instead.
    """
    lines = text.split("\n")
    chunks = []
    current_section = None
    current_title = None
    found_any_header = False
    buffer: List[str] = []

    def flush():
        if not buffer:
            return
        chunk_text = "\n".join(buffer).strip()
        if not chunk_text:
            return
        chunks.append({
            "text": chunk_text,
            "section_number": current_section,
            "clause_type": classify_clause_type(chunk_text, current_title),
            "page": page,
        })

    for line in lines:
        match = SECTION_PATTERN.match(line)
        if match:
            flush()
            buffer = []
            found_any_header = True
            current_section = match.group(1)
            current_title = match.group(2)
            buffer.append(line)
        else:
            buffer.append(line)
    flush()

    # Fallback: no numbered/lettered section headers were found anywhere in this
    # text (common for short, informally-written NDAs). In that case `chunks`
    # still holds one giant whole-page chunk from the flush() above — discard
    # it and split by paragraph instead, which gives much better retrieval
    # granularity than treating a whole document as a single clause.
    if not found_any_header:
        chunks = []
        for para in split_into_paragraphs(text):
            chunks.append({
                "text": para,
                "section_number": None,
                "clause_type": classify_clause_type(para),
                "page": page,
            })

    # Sub-split any section that's too large to stay a precise retrieval unit
    final_chunks = []
    for chunk in chunks:
        if len(chunk["text"]) <= MAX_CHUNK_CHARS:
            final_chunks.append(chunk)
        else:
            for para in split_into_paragraphs(chunk["text"]):
                final_chunks.append({
                    "text": para,
                    "section_number": chunk["section_number"],
                    "clause_type": classify_clause_type(para),
                    "page": chunk["page"],
                })
    return final_chunks


def chunk_document(pages: List[Dict]) -> List[Dict]:
    """
    pages: output of parsers.parse_document() —
           a list of {"page": int|None, "text": str}

    Returns a flat list of clause-level chunks across the whole
    document, each with {text, clause_type, section_number, page}.
    This is what gets embedded and stored in Qdrant + Postgres (Day 3).
    """
    all_chunks = []
    for page_data in pages:
        page_chunks = chunk_page_text(page_data["text"], page_data["page"])
        all_chunks.extend(page_chunks)
    return all_chunks
