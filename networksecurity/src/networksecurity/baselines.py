"""
baselines.py -- non-LLM comparison detectors (rolling z-score, Isolation
Forest). Plain statistics/scikit-learn, no API calls, no cost -- run for
comparison against the Claude-based classification.
"""

import os

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .config import FEATURES, RNG, DEFAULT_OUT_DIR


def fit_benign_baseline(benign_files, n_train_rows):
    """Read benign part files one at a time, accumulating rows until we have
    enough to train on -- avoids loading every benign file fully at once."""
    chunks = []
    total = 0
    for file_path in benign_files:
        df = pd.read_csv(file_path)
        chunks.append(df[FEATURES])
        total += len(df)
        if total >= n_train_rows:
            break
    pool = pd.concat(chunks, ignore_index=True)
    train_idx = RNG.choice(len(pool), size=min(n_train_rows, len(pool)), replace=False)
    train = pool.iloc[train_idx]
    mean, std = train.mean(), train.std().replace(0, np.nan)
    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42).fit(train)
    return mean, std, iso


def run_baselines(manifest, class_files, benign_class, out_dir=DEFAULT_OUT_DIR):
    if benign_class is None:
        print("  No class name matched 'Benign' -- skipping baselines (they need a normal-traffic "
              "class to train on). Pass --benign-class explicitly to enable them.")
        return None

    mean, std, iso = fit_benign_baseline(class_files[benign_class], n_train_rows=5000)

    rows = []
    for source_file, group in manifest.drop_duplicates("sample_id").groupby("source_file"):
        df = pd.read_csv(source_file)
        for _, row in group.iterrows():
            feat = df.iloc[row.row_start:row.row_end][FEATURES].mean()
            z = (feat - mean) / std
            z_flag = bool((z.abs() > 4.0).any())
            iso_flag = iso.predict(feat.to_frame().T)[0] == -1
            rows.append({"sample_id": row.sample_id, "true_class": row.true_class,
                         "true_is_attack": row.true_class != benign_class,
                         "zscore_flagged_attack": z_flag, "isoforest_flagged_attack": iso_flag})
        del df

    results = pd.DataFrame(rows)
    results.to_csv(os.path.join(out_dir, "baseline_results.csv"), index=False)
    return results
