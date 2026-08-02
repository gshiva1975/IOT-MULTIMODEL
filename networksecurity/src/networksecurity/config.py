"""
config.py -- central constants for the networksecurity pipeline.

Nothing here calls the network or reads the filesystem; it's pure
configuration, safe to import from anywhere (including tests) without side
effects.
"""

import numpy as np

# Reproducible sampling -- fixed seed so which traffic windows get sampled
# (and which rows go into the benign-baseline training set) is deterministic
# across runs, all else equal.
RNG = np.random.default_rng(7)

DEFAULT_DATA_DIR = "data/CSV"
DEFAULT_OUT_DIR = "results"

# Folder whose name (case-insensitive substring match) is treated as the
# normal-traffic class for baseline training.
BENIGN_CLASS_NAME = "Benign"

# Rows per rendered traffic-visualization window (~100 packets/window in the
# underlying CIC-IoT-2023 feature aggregation).
GROUP_SIZE = 30

# Claude model used as the multimodal LLM under test.
MODEL = "claude-sonnet-5"

# Observed empirically from a real 510-call pilot run: avg 1993 input + 216
# output tokens/call. At Sonnet 5 pricing ($2/M input, $10/M output through
# Aug 31 2026), that's ~$0.0061/call. Used only for the pre-run cost estimate
# printed to the user -- update if pricing changes.
EMPIRICAL_COST_PER_CALL = 0.0061

FLAG_COLS = ["fin_flag_number", "syn_flag_number", "rst_flag_number", "psh_flag_number", "ack_flag_number"]
PROTO_COLS = ["TCP", "UDP", "HTTP", "HTTPS", "ICMP", "DNS"]
FEATURES = ["Rate"] + FLAG_COLS + ["TCP", "UDP", "HTTP", "HTTPS", "AVG", "Std", "IAT"]

CONDITIONS = ["naive", "cve_text_grounded", "rag_grounded"]

RESULT_COLUMNS = [
    "sample_id", "true_class", "condition", "classification", "reference_id",
    "justification", "input_tokens", "output_tokens", "raw_response",
]
