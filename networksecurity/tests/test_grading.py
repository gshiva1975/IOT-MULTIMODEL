"""Unit tests for wilson_ci() and grade_citation(). No network, no API key,
no filesystem needed -- pure function tests."""

import math

from networksecurity.grading import wilson_ci, grade_citation


def test_wilson_ci_zero_n_is_nan():
    p, lo, hi = wilson_ci(0, 0)
    assert math.isnan(p) and math.isnan(lo) and math.isnan(hi)


def test_wilson_ci_all_correct_upper_bound_below_100():
    # Even 5/5 shouldn't claim a exact point estimate of 100% with a tight CI --
    # Wilson correctly keeps some uncertainty at small n.
    p, lo, hi = wilson_ci(5, 5)
    assert p == 1.0
    assert lo < 1.0
    assert hi == 1.0


def test_wilson_ci_half_is_centered():
    p, lo, hi = wilson_ci(5, 10)
    assert p == 0.5
    assert lo < 0.5 < hi


def test_wilson_ci_wider_at_small_n():
    _, lo_small, hi_small = wilson_ci(5, 10)
    _, lo_big, hi_big = wilson_ci(50, 100)
    assert (hi_small - lo_small) > (hi_big - lo_big)


def test_grade_benign_is_na():
    assert grade_citation("Benign", "N/A", benign_class="Benign") == "n/a-benign"


def test_grade_no_citation_variants():
    for ref in ["N/A", "n/a", "NaN", "None", "", "  "]:
        assert grade_citation("DDoS-TCP_Flood", ref, benign_class="Benign") == "no-citation"


def test_grade_real_and_correct():
    # CAPEC-482 (TCP Flood) legitimately covers DDoS-TCP_Flood per the corpus.
    assert grade_citation("DDoS-TCP_Flood", "CAPEC-482", benign_class="Benign") == "real-and-correct"


def test_grade_real_but_wrong_family():
    # CAPEC-482 does NOT cover XSS.
    assert grade_citation("XSS", "CAPEC-482", benign_class="Benign") == "real-but-wrong-family"


def test_grade_real_but_generic():
    # CAPEC-125 is in generic_ids -- always generic regardless of class match.
    assert grade_citation("DDoS-ACK_Fragmentation", "CAPEC-125", benign_class="Benign") == "real-but-generic"


def test_grade_verified_wrong_family_id():
    # CAPEC-130 is explicitly in verified_wrong_family_ids.
    assert grade_citation("DDoS-TCP_Flood", "CAPEC-130", benign_class="Benign") == "real-but-wrong-family"


def test_grade_unverified_unknown_id():
    result = grade_citation("DDoS-TCP_Flood", "CAPEC-99999", benign_class="Benign")
    assert result.startswith("UNVERIFIED")
