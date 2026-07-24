"""
Unit tests for citation-grounded synthesis, using a fake call_llm_fn so
no real API call / network / API key is needed. These tests specifically
exercise the anti-hallucination guardrail — the most important behavior
in the synthesis layer.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.synthesis import build_prompt, extract_cited_clause_ids, synthesize_answer


def make_candidate(clause_id, text="Some clause text."):
    return {
        "clause_id": clause_id,
        "text": text,
        "section_number": "3",
        "clause_type": "termination",
        "document_id": "doc-1",
    }


def test_extract_cited_clause_ids_finds_all_tags():
    text = "Some answer [clause:abc123] and also [clause:def456]."
    assert extract_cited_clause_ids(text) == ["abc123", "def456"]


def test_extract_cited_clause_ids_returns_empty_for_no_citations():
    assert extract_cited_clause_ids("No citations in this answer.") == []


def test_build_prompt_includes_clause_ids_and_question():
    candidates = [make_candidate("abc123", "Termination clause text.")]
    prompt = build_prompt("When can we terminate?", candidates)
    assert "abc123" in prompt
    assert "When can we terminate?" in prompt
    assert "Termination clause text." in prompt


def test_synthesize_answer_grounded_when_citation_is_valid():
    candidates = [make_candidate("abc123")]
    fake_llm = lambda prompt: "You can terminate for breach [clause:abc123]."
    result = synthesize_answer("When can we terminate?", candidates, call_llm_fn=fake_llm)
    assert result["grounded"] is True
    assert result["cited_clause_ids"] == ["abc123"]


def test_synthesize_answer_ungrounded_when_citation_is_hallucinated():
    """The core guardrail test: a citation referencing a clause_id that was
    never provided as context must be caught, not silently trusted."""
    candidates = [make_candidate("abc123")]
    fake_llm = lambda prompt: "You can terminate anytime [clause:hallucinated999]."
    result = synthesize_answer("When can we terminate?", candidates, call_llm_fn=fake_llm)
    assert result["grounded"] is False


def test_synthesize_answer_ungrounded_when_no_citation_given():
    candidates = [make_candidate("abc123")]
    fake_llm = lambda prompt: "You can terminate at will, no restrictions."
    result = synthesize_answer("When can we terminate?", candidates, call_llm_fn=fake_llm)
    assert result["grounded"] is False


def test_synthesize_answer_with_no_candidates_returns_ungrounded():
    result = synthesize_answer("Some question", [], call_llm_fn=lambda p: "should never be called")
    assert result["grounded"] is False
    assert "don't have any relevant" in result["answer"].lower()


def test_synthesize_answer_mixed_valid_and_invalid_citations_is_ungrounded():
    candidates = [make_candidate("abc123"), make_candidate("def456")]
    fake_llm = lambda prompt: "Valid point [clause:abc123] and fake point [clause:ghost000]."
    result = synthesize_answer("Some question", candidates, call_llm_fn=fake_llm)
    assert result["grounded"] is False
