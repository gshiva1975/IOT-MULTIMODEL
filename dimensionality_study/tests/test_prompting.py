from dimensionality_study.prompting import build_prompt, parse_response


def test_build_prompt_lists_all_classes():
    prompt = build_prompt(["Benign_Final", "DDoS-TCP_Flood", "Mirai-udpplain"])
    assert "Benign_Final" in prompt
    assert "DDoS-TCP_Flood" in prompt
    assert "Mirai-udpplain" in prompt
    assert "CLASSIFICATION:" in prompt
    assert "JUSTIFICATION:" in prompt


def test_build_prompt_does_not_mention_citations():
    # This project deliberately holds citation-grounding out of scope --
    # it's testing visualization dimensionality, not hallucination.
    prompt = build_prompt(["Benign_Final", "DDoS-TCP_Flood"])
    assert "CAPEC" not in prompt
    assert "CVE" not in prompt
    assert "REFERENCE_ID" not in prompt


def test_parse_response_basic():
    text = "CLASSIFICATION: DDoS-TCP_Flood\nJUSTIFICATION: High packet rate spike."
    parsed = parse_response(text)
    assert parsed["classification"] == "DDoS-TCP_Flood"
    assert parsed["justification"] == "High packet rate spike."


def test_parse_response_case_insensitive_labels():
    text = "classification: Benign_Final\njustification: Steady low-rate traffic."
    parsed = parse_response(text)
    assert parsed["classification"] == "Benign_Final"


def test_parse_response_missing_fields():
    parsed = parse_response("some unrelated text")
    assert parsed["classification"] is None
    assert parsed["justification"] is None
