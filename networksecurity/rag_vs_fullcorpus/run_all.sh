#!/usr/bin/env bash
# run_all.sh
# -----------
# One-command run for a machine with normal (unrestricted) internet access.
# Fetches the real, full CAPEC catalog + relevant real NVD CVEs, merges them
# into one real corpus (no synthetic padding), runs the recall@k / cost /
# latency sweep, and plots the results.
#
# Usage:
#   ./run_all.sh                # TF-IDF retrieval (no extra install needed)
#   ./run_all.sh --embedder sentence-transformers   # real dense embeddings
#                                                     # (installs sentence-transformers,
#                                                      downloads model weights on first run)
#
# Set NVD_API_KEY in your environment first if you have one (free, from
# https://nvd.nist.gov/developers/request-an-api-key) -- without it,
# fetch_nvd_bulk.py runs at the slower unauthenticated rate limit.

set -euo pipefail
cd "$(dirname "$0")"

EMBEDDER="tfidf"
if [[ "${1:-}" == "--embedder" && -n "${2:-}" ]]; then
  EMBEDDER="$2"
fi

echo "== 1/5: installing dependencies =="
pip install -r requirements.txt -q
if [[ "$EMBEDDER" == "sentence-transformers" || "$EMBEDDER" == "auto" ]]; then
  pip install sentence-transformers -q
fi

echo "== 2/5: fetching full CAPEC catalog (capec.mitre.org) =="
python3 fetch_capec_bulk.py

echo "== 3/5: fetching relevant real CVEs (services.nvd.nist.gov) =="
python3 fetch_nvd_bulk.py

echo "== 4/5: merging into one real corpus =="
python3 build_full_real_corpus.py

echo "== 5/5: running experiment (embedder=$EMBEDDER) and plotting =="
python3 full_experiment.py --embedder "$EMBEDDER"
python3 plot_full_results.py

echo ""
echo "Done. Results:"
echo "  full_results_by_size.csv"
echo "  full_results_by_k.csv"
echo "  fig8_full_recall_vs_corpus_size.png"
echo "  fig9_full_recall_vs_k.png"
