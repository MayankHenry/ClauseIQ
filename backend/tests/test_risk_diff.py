"""
Unit tests for the risk-diffing engine, using a fake call_llm_fn so no
real API call is needed -- fast and CI-friendly.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.risk_diff import (
    group_clauses_by_type,
    build_compare_prompt,
    parse_compare_response,
    diff_clauses,
)


def make_clause(clause_id, clause_type, text="Some clause text."):
    return {"clause_id": clause_id, "clause_type": clause_type, "text": text}


def test_group_clauses_by_type_groups_correctly():
    clauses = [make_clause("1", "termination"), make_clause("2", "payment"), make_clause("3", "termination")]
    groups = group_clauses_by_type(clauses)
    assert len(groups["termination"]) == 2
    assert len(groups["payment"]) == 1


def test_build_compare_prompt_includes_both_texts_and_clause_type():
    prompt = build_compare_prompt("termination", "Template text.", "New text.")
    assert "Template text." in prompt
    assert "New text." in prompt
    assert "termination" in prompt


def test_parse_compare_response_valid_json():
    raw = '{"differs": true, "severity": 0.7, "description": "Notice period shortened."}'
    result = parse_compare_response(raw)
    assert result["differs"] is True
    assert result["severity"] == 0.7
    assert "shortened" in result["description"]


def test_parse_compare_response_strips_markdown_fences():
    raw = '```json\n{"differs": false, "severity": 0.0, "description": ""}\n```'
    result = parse_compare_response(raw)
    assert result["differs"] is False


def test_parse_compare_response_malformed_json_fails_safe():
    """A parse failure must never look the same as 'no risk found' --
    it should flag for manual review, not silently pass."""
    result = parse_compare_response("not valid json at all")
    assert result["differs"] is True
    assert result["severity"] == 0.5
    assert "manual review" in result["description"].lower()


def test_diff_clauses_flags_missing_clause_type():
    template = [make_clause("t1", "confidentiality")]
    new = []  # new document has no confidentiality clause at all
    fake_llm = lambda prompt: '{"differs": false, "severity": 0.0, "description": ""}'
    flags = diff_clauses(template, new, call_llm_fn=fake_llm)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "missing"
    assert flags[0]["clause_type"] == "confidentiality"
    assert flags[0]["clause_id"] is None


def test_diff_clauses_flags_changed_clause_when_llm_says_differs():
    template = [make_clause("t1", "termination", "60 days notice required.")]
    new = [make_clause("n1", "termination", "No notice required.")]
    fake_llm = lambda prompt: (
        '{"differs": true, "severity": 0.9, "description": "Notice requirement removed entirely."}'
    )
    flags = diff_clauses(template, new, call_llm_fn=fake_llm)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "changed"
    assert flags[0]["severity"] == 0.9
    assert flags[0]["clause_id"] == "n1"


def test_diff_clauses_does_not_flag_consistent_clauses():
    template = [make_clause("t1", "governing_law", "Delaware law applies.")]
    new = [make_clause("n1", "governing_law", "Delaware law applies.")]
    fake_llm = lambda prompt: '{"differs": false, "severity": 0.0, "description": ""}'
    flags = diff_clauses(template, new, call_llm_fn=fake_llm)
    assert flags == []


def test_diff_clauses_ignores_clause_types_only_in_new_document():
    """A clause_type present only in the new doc (not the template) should
    not be flagged -- risk-diffing measures deviation FROM the template,
    not an exhaustive audit of every clause in the new document."""
    template = [make_clause("t1", "termination", "text")]
    new = [make_clause("n1", "termination", "text"), make_clause("n2", "force_majeure", "text")]
    fake_llm = lambda prompt: '{"differs": false, "severity": 0.0, "description": ""}'
    flags = diff_clauses(template, new, call_llm_fn=fake_llm)
    assert flags == []


def test_diff_clauses_handles_multiple_clause_types_independently():
    template = [
        make_clause("t1", "termination", "text A"),
        make_clause("t2", "payment", "text B"),
    ]
    new = [
        make_clause("n1", "termination", "text A"),
        # payment clause missing entirely from new document
    ]

    def fake_llm(prompt):
        # termination clause is unchanged -> no flag
        return '{"differs": false, "severity": 0.0, "description": ""}'

    flags = diff_clauses(template, new, call_llm_fn=fake_llm)
    assert len(flags) == 1
    assert flags[0]["clause_type"] == "payment"
    assert flags[0]["flag_type"] == "missing"
