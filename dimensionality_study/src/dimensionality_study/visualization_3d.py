"""
visualization_3d.py -- the "3D" condition: the SAME underlying features as
the 2D condition (packet rate, packet size, TCP-flag intensity, protocol
mix), fused into a single 3D scene instead of four stacked 2D panels.

Design (kept deliberately close to the 2D condition so the comparison
isolates dimensionality, not "how much information is shown"):
  x-axis: window index (time)          -- same as the 2D panels' x-axis
  y-axis: packet rate                  -- same data as 2D panel 1
  z-axis: average packet size          -- same data as 2D panel 4
  point color: TCP-flag intensity (sum of the 5 flag fractions) -- same
               data as 2D panel 2, now encoded as color instead of a line
  point size: dominant protocol's share of the mix -- same data as 2D
               panel 3, now encoded as marker size instead of a stacked area
  a thin connecting line + a floor projection ("shadow") are included
  because unaided 3D scatter plots are notoriously hard to read depth from
  -- this is a genuine best-effort 3D rendering, not a strawman, so the
  eventual accuracy comparison is fair to the 3D condition.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers the 3d projection)
import numpy as np

from .config import FLAG_COLS, PROTO_COLS


def render_3d(df_slice, class_name, sample_id):
    x = np.arange(len(df_slice))
    rate = df_slice["Rate"].to_numpy()
    pkt_size = df_slice["AVG"].to_numpy()
    flag_intensity = df_slice[FLAG_COLS].to_numpy().sum(axis=1)
    dominant_share = df_slice[PROTO_COLS].to_numpy().max(axis=1)

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="3d")

    # Floor projection ("shadow"): helps a viewer judge depth/position along
    # x-y without needing stereo vision -- a standard mitigation for 3D
    # scatter occlusion, included so this is a fair, competently-rendered
    # 3D condition rather than a deliberately weak one.
    floor_z = np.full_like(rate, pkt_size.min() if len(pkt_size) else 0)
    ax.plot(x, rate, floor_z, color="#999999", linewidth=0.8, alpha=0.5, linestyle="--")

    # Trajectory line through time, then a scatter on top colored/sized by
    # the two features that were separate panels in the 2D condition.
    ax.plot(x, rate, pkt_size, color="#c53030", linewidth=1.0, alpha=0.6)
    sizes = 20 + 180 * np.nan_to_num(dominant_share, nan=0.0)
    sc = ax.scatter(x, rate, pkt_size, c=flag_intensity, cmap="viridis",
                     s=sizes, edgecolor="black", linewidth=0.3, depthshade=True)

    ax.set_xlabel("Window index (time)", fontsize=8)
    ax.set_ylabel("Rate (pkt/s)", fontsize=8)
    ax.set_zlabel("Avg packet size", fontsize=8)
    ax.set_title(f"{class_name} — sample {sample_id} (3D)\n"
                 f"color = TCP-flag intensity, size = dominant-protocol share",
                 fontsize=9)
    ax.view_init(elev=22, azim=-60)

    cbar = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1)
    cbar.set_label("TCP-flag intensity (sum of 5 flag fractions)", fontsize=7)
    cbar.ax.tick_params(labelsize=6)

    fig.tight_layout()
    return fig
