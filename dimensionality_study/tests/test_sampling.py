import numpy as np
import pandas as pd

from dimensionality_study.sampling import sample_windows, distribute_across_files


def test_distribute_across_files_even():
    assert distribute_across_files(10, 5) == [2, 2, 2, 2, 2]


def test_distribute_across_files_remainder():
    assert distribute_across_files(11, 5) == [3, 2, 2, 2, 2]
    assert sum(distribute_across_files(11, 5)) == 11


def test_distribute_across_files_single_file():
    assert distribute_across_files(7, 1) == [7]


def test_sample_windows_respects_group_size():
    df = pd.DataFrame({"x": range(100)})
    rng = np.random.default_rng(0)
    starts = sample_windows(df, n_samples=5, group_size=30, rng=rng)
    assert len(starts) == 5
    assert all(0 <= s <= 70 for s in starts)  # 100 - 30 = 70
    assert starts == sorted(starts)


def test_sample_windows_too_few_rows():
    df = pd.DataFrame({"x": range(10)})
    rng = np.random.default_rng(0)
    starts = sample_windows(df, n_samples=5, group_size=30, rng=rng)
    assert starts == []


def test_sample_windows_caps_at_available():
    df = pd.DataFrame({"x": range(35)})
    rng = np.random.default_rng(0)
    # max_start = 35 - 30 = 5, so at most 5 distinct windows even if more requested
    starts = sample_windows(df, n_samples=20, group_size=30, rng=rng)
    assert len(starts) == 5
