"""Unit tests for prompt construction and response parsing. No network needed."""

import pytest

from networksecurity.prompting import build_prompt, parse_response, response_format
from networksecurity.corpus import CVE_CORPUS


CLASS_NAMES = ["Benign", "DDoS-TCP_Flood", "XSS"]


def test_naive_prompt_has_no_corpus_text():
    p = build_prompt("naive", CLASS_NAMES)
    assert "CAPEC-482" not in p
    assert "Classify this traffic" in p


def test_cve_text_grounded_prompt_has_no_corpus_text_either():
    # This condition relies on the model's own knowledge, not our corpus --
    # the corpus text must NOT leak in here, or the whole point of the
    # naive/text-grounded/rag-grounded comparison breaks.
    p = build_prompt("cve_text_grounded", CLASS_NAMES)
    assert "CAPEC-482" not in p
    assert "own knowledge" in p


def test_rag_grounded_prompt_contains_full_corpus():
    p = build_prompt("rag_grounded", CLASS_NAMES)
    for entry in CVE_CORPUS["capec_entries"]:
        assert entry["capec_id"] in p


def test_rag_grounded_prompt_restricts_citation():
    p = build_prompt("rag_grounded", CLASS_NAMES)
    assert "ONLY a reference ID from the database above" in p


def test_unknown_condition_raises():
    with pytest.raises(ValueError):
        build_prompt("not_a_real_condition", CLASS_NAMES)


def test_response_format_lists_all_classes():
    fmt = response_format(CLASS_NAMES)
    for name in CLASS_NAMES:
        assert name in fmt


def test_parse_response_roundtrip():
    text = (
        "CLASSIFICATION: DDoS-TCP_Flood\n"
        "REFERENCE_ID: CAPEC-482\n"
        "JUSTIFICATION: Rate spikes with SYN flags match a TCP flood signature."
    )
    parsed = parse_response(text)
    assert parsed["classification"] == "DDoS-TCP_Flood"
    assert parsed["reference_id"] == "CAPEC-482"
    assert "TCP flood" in parsed["justification"]


def test_parse_response_handles_missing_fields():
    parsed = parse_response("CLASSIFICATION: Benign\n")
    assert parsed["classification"] == "Benign"
    assert parsed["reference_id"] is None
    assert parsed["justification"] is None
