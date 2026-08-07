import numpy as np
import pandas as pd

from dimensionality_study.config import FLAG_COLS, PROTO_COLS
from dimensionality_study.visualization_2d import render_2d
from dimensionality_study.visualization_3d import render_3d


def _fake_slice(n=30, seed=0):
    rng = np.random.default_rng(seed)
    data = {
        "Rate": rng.uniform(1000, 50000, n),
        "AVG": rng.uniform(50, 70, n),
        "Std": rng.uniform(1, 10, n),
    }
    for c in FLAG_COLS:
        data[c] = rng.uniform(0, 0.1, n)
    for c in PROTO_COLS:
        data[c] = rng.uniform(0, 1, n)
    return pd.DataFrame(data)


def test_render_2d_produces_figure():
    fig = render_2d(_fake_slice(), "TestClass", "TestClass_0000")
    assert fig is not None
    assert len(fig.axes) == 4  # rate, flags, protocol mix, packet size


def test_render_3d_produces_figure():
    fig = render_3d(_fake_slice(), "TestClass", "TestClass_0000")
    assert fig is not None
    assert len(fig.axes) >= 1


def test_render_3d_handles_empty_slice_gracefully():
    # a group_size=0 edge case shouldn't crash the floor-projection logic
    fig = render_3d(_fake_slice(n=1), "TestClass", "TestClass_0000")
    assert fig is not None
