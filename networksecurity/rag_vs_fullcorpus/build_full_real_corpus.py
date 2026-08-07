"""
build_full_real_corpus.py
--------------------------
Merges capec_entries.json (from fetch_capec_bulk.py) and nvd_entries.json
(from fetch_nvd_bulk.py) into full_real_corpus.json: a single real corpus
that can be sliced to any size up to its total length, with no synthetic
padding required.

The 15 hand-verified REAL_ANCHOR_ENTRIES / REAL_ANCHOR_QUERIES from
real_corpus.py are kept as the fixed query set (ground truth is already
known for those), and are guaranteed to be present in the merged corpus
regardless of size (deduplicated by ID, inserted first).

Usage (after running fetch_capec_bulk.py and fetch_nvd_bulk.py):
    python3 build_full_real_corpus.py
Output:
    full_real_corpus.json
"""

import json
import random

from real_corpus import REAL_ANCHOR_ENTRIES

CAPEC_PATH = "capec_entries.json"
NVD_PATH = "nvd_entries.json"
OUTPUT_PATH = "full_real_corpus.json"
SEED = 42


def load_json(path: str) -> list[dict]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ! {path} not found -- run its fetch script first. Skipping.")
        return []


def main():
    capec = load_json(CAPEC_PATH)
    nvd = load_json(NVD_PATH)

    merged = {}
    # Anchors first and always present, in their hand-verified form.
    for eid, kind, name, families, desc in REAL_ANCHOR_ENTRIES:
        merged[eid] = {
            "id": eid, "kind": kind, "name": name,
            "attack_families": families, "description": desc,
            "source_url": "(hand-verified, see real_corpus.py)",
        }
    for e in capec + nvd:
        merged.setdefault(e["id"], e)  # don't overwrite hand-verified anchor versions

    entries = list(merged.values())
    rng = random.Random(SEED)
    rng.shuffle(entries)

    print(f"CAPEC entries loaded: {len(capec)}")
    print(f"NVD entries loaded:   {len(nvd)}")
    print(f"Anchors (always included): {len(REAL_ANCHOR_ENTRIES)}")
    print(f"Total merged corpus size: {len(entries)}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")

    if len(entries) < 200:
        print("\nNote: merged corpus is smaller than 200 entries. If you were expecting the "
              "full ~559 CAPEC catalog, check that fetch_capec_bulk.py ran successfully "
              "(capec_entries.json should have ~559 entries) -- this script only merges "
              "what those fetch scripts actually produced.")


if __name__ == "__main__":
    main()
