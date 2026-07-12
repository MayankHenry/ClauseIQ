"""
Document parsers — turns PDF/DOCX/TXT files into a normalized list of
{"page": int|None, "text": str} dicts, one entry per page (PDF) or
one entry total (DOCX/TXT, which have no reliable page concept).

This is the input layer for the clause-aware chunker (chunker.py).
"""

from typing import List, Dict


def parse_pdf(path: str) -> List[Dict]:
    """Extract text per page from a PDF using pdfplumber."""
    import pdfplumber

    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages


def parse_docx(path: str) -> List[Dict]:
    """Extract text from a DOCX. DOCX has no native pagination, so page=None."""
    from docx import Document as DocxDocument

    doc = DocxDocument(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return [{"page": None, "text": text}]


def parse_txt(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page": None, "text": text}]


def parse_document(path: str) -> List[Dict]:
    """
    Dispatches to the right parser based on file extension.
    Returns a list of {"page": int|None, "text": str}.
    """
    ext = path.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return parse_pdf(path)
    elif ext == "docx":
        return parse_docx(path)
    elif ext == "txt":
        return parse_txt(path)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")
