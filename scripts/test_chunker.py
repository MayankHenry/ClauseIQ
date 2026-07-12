"""
Day 2 test script — run the clause-aware chunker against the sample
contracts and print each chunk with its detected metadata.

Usage (from backend/ folder, with venv activated):
    python ../scripts/test_chunker.py
"""

import sys
import os
import json

# Make backend/app importable when running this script directly
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.parsers import parse_document
from app.services.chunker import chunk_document

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_contracts")


def run_on_file(filename: str):
    path = os.path.join(SAMPLE_DIR, filename)
    print("=" * 80)
    print(f"FILE: {filename}")
    print("=" * 80)

    pages = parse_document(path)
    chunks = chunk_document(pages)

    print(f"-> {len(chunks)} clause-level chunks detected\n")

    for i, chunk in enumerate(chunks, start=1):
        preview = chunk["text"].replace("\n", " ")[:90]
        print(f"[{i}] section={chunk['section_number']!s:<6} "
              f"type={chunk['clause_type']:<20} page={chunk['page']!s:<4} "
              f"text=\"{preview}...\"")
    print()


if __name__ == "__main__":
    files = [
        "vendor_agreement.txt",
        "nda_no_headers.txt",
        "software_license_article_style.txt",
    ]
    for f in files:
        run_on_file(f)
