"""
networksecurity -- citation-grounded, multimodal LLM classification of
IoT/OT network traffic, with real-time verification of every cited
CAPEC/CVE reference against a hand-checked corpus.

This package is a clean, modular reimplementation of the original
run_experiment_local.py / visualize_rag_grounded.py research scripts,
organized for deployment rather than as a single monolithic file. The
corpus data, prompting logic, and grading rules are ported verbatim from
the original (independently verified) research code -- see
src/networksecurity/corpus.py for provenance notes.
"""

__version__ = "1.0.0"
