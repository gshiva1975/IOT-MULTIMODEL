"""
build.py -- picks the sample windows once (sampling.py), then renders BOTH
a 2D and a 3D image from each one, and writes a single manifest row per
sample with both image paths. One sampling pass shared by both renderers is
the core methodological guarantee of this project: sample N's 2D image and
sample N's 3D image are always drawn from the exact same rows.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import GROUP_SIZE, RNG, DEFAULT_OUT_DIR
from .sampling import sample_windows, distribute_across_files
from .visualization_2d import render_2d
from .visualization_3d import render_3d


def build_visualizations(class_files, samples_per_class, out_dir=DEFAULT_OUT_DIR):
    """class_files: {class_name: [csv paths]}. Loads one file at a time (not
    all files for a class concatenated in memory) and distributes the
    per-class sample budget across however many part files that class has.
    Writes results/viz/2d/<class>/<id>.png, results/viz/3d/<class>/<id>.png,
    and results/viz/manifest.csv (one row per sample, both image paths)."""
    manifest_rows = []
    for class_name, files in class_files.items():
        dir_2d = os.path.join(out_dir, "viz", "2d", class_name)
        dir_3d = os.path.join(out_dir, "viz", "3d", class_name)
        os.makedirs(dir_2d, exist_ok=True)
        os.makedirs(dir_3d, exist_ok=True)
        per_file_budget = distribute_across_files(samples_per_class, len(files))

        total_for_class = 0
        sample_counter = 0
        for file_path, budget in zip(files, per_file_budget):
            if budget <= 0:
                continue
            df = pd.read_csv(file_path)
            starts = sample_windows(df, budget, GROUP_SIZE, RNG)
            for start in starts:
                df_slice = df.iloc[start:start + GROUP_SIZE]
                sample_id = f"{class_name}_{sample_counter:04d}"
                sample_counter += 1

                fig2d = render_2d(df_slice, class_name, sample_id)
                path_2d = os.path.join(dir_2d, f"{sample_id}.png")
                fig2d.savefig(path_2d, dpi=120)
                plt.close(fig2d)

                fig3d = render_3d(df_slice, class_name, sample_id)
                path_3d = os.path.join(dir_3d, f"{sample_id}.png")
                fig3d.savefig(path_3d, dpi=120)
                plt.close(fig3d)

                manifest_rows.append({
                    "sample_id": sample_id, "true_class": class_name,
                    "source_file": file_path, "row_start": int(start),
                    "row_end": int(start + GROUP_SIZE),
                    "image_path_2d": path_2d, "image_path_3d": path_3d,
                })
                total_for_class += 1
            del df

        print(f"  {class_name}: {total_for_class} samples (2D + 3D each) from {len(files)} file(s)")

    manifest = pd.DataFrame(manifest_rows)
    os.makedirs(os.path.join(out_dir, "viz"), exist_ok=True)
    manifest.to_csv(os.path.join(out_dir, "viz", "manifest.csv"), index=False)
    return manifest
