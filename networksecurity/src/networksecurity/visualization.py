"""
visualization.py -- render windows of raw traffic feature rows into the
4-panel PNG images the multimodal LLM actually classifies.

Each sample is a GROUP_SIZE-row window (~100 packets per row in the
underlying CIC-IoT-2023 feature aggregation) rendered as: (1) packet rate
over time, (2) TCP flag composition, (3) protocol mix (stacked area), and
(4) average and standard deviation of packet size.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import FLAG_COLS, PROTO_COLS, GROUP_SIZE, RNG, DEFAULT_OUT_DIR


def sample_windows(df, n_samples, group_size, rng):
    max_start = len(df) - group_size
    if max_start <= 0:
        return []
    starts = rng.choice(max_start, size=min(n_samples, max_start), replace=False)
    return sorted(starts.tolist())


def distribute_across_files(total, n_files):
    """Split `total` samples as evenly as possible across n_files files."""
    base, remainder = divmod(total, n_files)
    return [base + (1 if i < remainder else 0) for i in range(n_files)]


def make_panel(df_slice, class_name, sample_id):
    fig, axes = plt.subplots(4, 1, figsize=(7, 8), sharex=True)
    x = np.arange(len(df_slice))
    axes[0].plot(x, df_slice["Rate"].to_numpy(), color="#c53030", linewidth=1.2)
    axes[0].set_ylabel("Rate (pkt/s)")
    axes[0].set_title(f"{class_name} — sample {sample_id}", fontsize=10)
    for c in FLAG_COLS:
        axes[1].plot(x, df_slice[c].to_numpy(), linewidth=1.0, label=c.replace("_flag_number", ""))
    axes[1].set_ylabel("TCP flag frac.")
    axes[1].legend(fontsize=6, ncol=5, loc="upper right")
    bottom = np.zeros(len(df_slice))
    colors = plt.cm.tab10(np.linspace(0, 1, len(PROTO_COLS)))
    for c, col in zip(PROTO_COLS, colors):
        vals = df_slice[c].to_numpy()
        axes[2].fill_between(x, bottom, bottom + vals, color=col, alpha=0.8, label=c)
        bottom += vals
    axes[2].set_ylabel("Protocol mix")
    axes[2].legend(fontsize=6, ncol=6, loc="upper right")
    axes[3].plot(x, df_slice["AVG"].to_numpy(), color="#2b6cb0", label="avg pkt size")
    axes[3].plot(x, df_slice["Std"].to_numpy(), color="#805ad5", label="std pkt size")
    axes[3].set_ylabel("Packet size")
    axes[3].set_xlabel("Window index (each = ~100 pkts)")
    axes[3].legend(fontsize=6, loc="upper right")
    fig.tight_layout()
    return fig


def build_visualizations(class_files, samples_per_class, out_dir=DEFAULT_OUT_DIR):
    """class_files: {class_name: [csv paths]}. Loads one file at a time (not
    all files for a class concatenated in memory) and distributes the
    per-class sample budget across however many part files that class has."""
    manifest_rows = []
    for class_name, files in class_files.items():
        class_dir = os.path.join(out_dir, "viz", class_name)
        os.makedirs(class_dir, exist_ok=True)
        per_file_budget = distribute_across_files(samples_per_class, len(files))

        total_for_class = 0
        total_rows_seen = 0
        sample_counter = 0
        for file_path, budget in zip(files, per_file_budget):
            if budget <= 0:
                continue
            df = pd.read_csv(file_path)
            total_rows_seen += len(df)
            starts = sample_windows(df, budget, GROUP_SIZE, RNG)
            for start in starts:
                df_slice = df.iloc[start:start + GROUP_SIZE]
                sample_id = f"{class_name}_{sample_counter:04d}"
                sample_counter += 1
                fig = make_panel(df_slice, class_name, sample_id)
                img_path = os.path.join(class_dir, f"{sample_id}.png")
                fig.savefig(img_path, dpi=120)
                plt.close(fig)
                manifest_rows.append({
                    "sample_id": sample_id, "true_class": class_name,
                    "source_file": file_path, "row_start": int(start),
                    "row_end": int(start + GROUP_SIZE), "image_path": img_path,
                })
                total_for_class += 1
            del df  # free memory before loading the next part file

        print(f"  {class_name}: {total_for_class} samples from {len(files)} file(s), "
              f"{total_rows_seen} rows seen")

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(os.path.join(out_dir, "viz", "manifest.csv"), index=False)
    return manifest
