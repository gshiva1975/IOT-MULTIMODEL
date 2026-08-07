import pandas as pd

from dimensionality_study.grading import wilson_ci, fmt_ci, score_and_summarize


def test_wilson_ci_zero_n():
    p, lo, hi = wilson_ci(0, 0)
    assert p != p  # nan


def test_wilson_ci_perfect_score_wide_at_small_n():
    p, lo, hi = wilson_ci(5, 5)
    assert p == 1.0
    assert lo < 1.0  # Wilson interval doesn't claim 100% confidence at n=5
    assert hi == 1.0


def test_wilson_ci_narrows_with_larger_n():
    _, lo_small, _ = wilson_ci(50, 100)
    _, lo_large, _ = wilson_ci(500, 1000)
    assert lo_large > lo_small  # same point estimate, tighter interval at larger n


def test_fmt_ci_format():
    s = fmt_ci(5, 10)
    assert "50.0%" in s
    assert "n=10" in s


def test_score_and_summarize_paired_comparison(tmp_path):
    df = pd.DataFrame([
        {"sample_id": "A_0000", "true_class": "A", "dimensionality": "2d", "classification": "A"},
        {"sample_id": "A_0000", "true_class": "A", "dimensionality": "3d", "classification": "B"},
        {"sample_id": "A_0001", "true_class": "A", "dimensionality": "2d", "classification": "A"},
        {"sample_id": "A_0001", "true_class": "A", "dimensionality": "3d", "classification": "A"},
    ])
    lines = score_and_summarize(df, out_dir=str(tmp_path))
    text = "\n".join(lines)
    assert "2d" in text
    assert "3d" in text
    assert (tmp_path / "summary.txt").exists()


def test_score_and_summarize_ignores_errors_in_paired_comparison(tmp_path):
    df = pd.DataFrame([
        {"sample_id": "A_0000", "true_class": "A", "dimensionality": "2d", "classification": "A"},
        {"sample_id": "A_0000", "true_class": "A", "dimensionality": "3d", "classification": "ERROR"},
    ])
    # should not raise even though one side of the pair errored out
    lines = score_and_summarize(df, out_dir=str(tmp_path))
    assert lines
