"""
visualization_2d.py -- the "2D" condition: four stacked 2D panels (packet
rate, TCP flag composition, protocol mix, packet size), exactly the
rendering used in the sibling ../networksecurity project. Ported unchanged
so the 2D condition here is a faithful baseline, not a reimplementation
that could silently drift.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .config import FLAG_COLS, PROTO_COLS


def render_2d(df_slice, class_name, sample_id):
    fig, axes = plt.subplots(4, 1, figsize=(7, 8), sharex=True)
    x = np.arange(len(df_slice))
    axes[0].plot(x, df_slice["Rate"].to_numpy(), color="#c53030", linewidth=1.2)
    axes[0].set_ylabel("Rate (pkt/s)")
    axes[0].set_title(f"{class_name} — sample {sample_id} (2D)", fontsize=10)
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
