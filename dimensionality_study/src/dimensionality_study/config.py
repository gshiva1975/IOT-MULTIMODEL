"""
config.py -- central constants for the dimensionality_study pipeline.

This project is a focused follow-on to ../networksecurity: instead of
asking "is the model's citation grounded," it asks "does the DIMENSIONALITY
of the traffic visualization itself (2D multi-panel vs. a single fused 3D
scene) change classification accuracy," holding the underlying data, the
sample set, the classes, and the model constant.

Nothing here calls the network or reads the filesystem -- pure config, safe
to import from anywhere (including tests) without side effects.
"""

import os

import numpy as np

# Same fixed seed as networksecurity/config.py, deliberately -- if you point
# --data-dir at the same folder, the 2D condition's sampling here reproduces
# the exact same windows the citation-grounding study used, which makes the
# two studies easier to cross-reference later.
RNG = np.random.default_rng(7)

# Defaults to the dataset already downloaded for the sibling networksecurity
# project, so this project doesn't need its own multi-GB copy of the data.
DEFAULT_DATA_DIR = os.path.join("..", "networksecurity", "data", "CSV")
DEFAULT_OUT_DIR = "results"

BENIGN_CLASS_NAME = "Benign"

# Rows per rendered traffic-visualization window (~100 packets/window in the
# underlying CIC-IoT-2023 feature aggregation) -- same as networksecurity,
# so a given sample_id means the same underlying traffic slice in both
# projects.
GROUP_SIZE = 30

MODEL = "claude-sonnet-5"

# Observed on the sibling project's pilot run -- used only for the pre-run
# cost estimate printed to the user; update if pricing or response length
# changes materially (e.g. once a real pilot here gives its own number).
EMPIRICAL_COST_PER_CALL = 0.0061

FLAG_COLS = ["fin_flag_number", "syn_flag_number", "rst_flag_number", "psh_flag_number", "ack_flag_number"]
PROTO_COLS = ["TCP", "UDP", "HTTP", "HTTPS", "ICMP", "DNS"]
FEATURES = ["Rate"] + FLAG_COLS + ["TCP", "UDP", "HTTP", "HTTPS", "AVG", "Std", "IAT"]

# The two things being compared. Each sample gets rendered once per
# dimensionality and classified once per rendering -- so total API calls =
# n_samples * len(DIMENSIONALITIES), not n_samples * 3 like the citation
# study (no naive/text-grounded/rag_grounded split here; this project holds
# the prompt constant and varies only the image).
DIMENSIONALITIES = ["2d", "3d"]

RESULT_COLUMNS = [
    "sample_id", "true_class", "dimensionality", "classification",
    "justification", "input_tokens", "output_tokens", "raw_response",
]
