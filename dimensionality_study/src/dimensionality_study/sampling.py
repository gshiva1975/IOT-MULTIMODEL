"""
sampling.py -- picks which traffic windows become samples.

Deliberately factored out from both visualizers: it's called exactly ONCE
per sample, and the resulting (source_file, row_start, row_end) triple is
shared by the 2D and 3D renderers. That's the crux of the experiment design
-- the 2D and 3D conditions must be rendered from IDENTICAL underlying rows,
or any accuracy difference we measure could just be sampling noise instead
of a real dimensionality effect.
"""

from .config import GROUP_SIZE, RNG


def sample_windows(df, n_samples, group_size=GROUP_SIZE, rng=RNG):
    max_start = len(df) - group_size
    if max_start <= 0:
        return []
    starts = rng.choice(max_start, size=min(n_samples, max_start), replace=False)
    return sorted(starts.tolist())


def distribute_across_files(total, n_files):
    """Split `total` samples as evenly as possible across n_files files."""
    base, remainder = divmod(total, n_files)
    return [base + (1 if i < remainder else 0) for i in range(n_files)]
