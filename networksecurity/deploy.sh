#!/usr/bin/env bash
# deploy.sh -- one-command setup for the networksecurity project.
#
# What it does:
#   1. Creates a venv (if one doesn't already exist)
#   2. Installs requirements.txt into it
#   3. Loads ANTHROPIC_API_KEY from .env if present (and the var isn't already set)
#   4. Verifies the install by running --list-classes against --data-dir (no API cost)
#
# It does NOT run the paid pipeline for you -- that's a deliberate choice, since a
# deploy script silently spending your API budget is a bad surprise. Run
# scripts/run_pipeline.py yourself once you're ready (see README.md for the exact
# command and cost estimate).
#
# Usage:
#   ./deploy.sh                          # setup + verify only
#   ./deploy.sh --data-dir path/to/CSV   # verify against a specific data directory

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

DATA_DIR="data/CSV"
if [[ "${1:-}" == "--data-dir" && -n "${2:-}" ]]; then
  DATA_DIR="$2"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== networksecurity deploy =="

if [[ -d venv && ! -f venv/bin/activate ]]; then
  echo "-- Found an incomplete venv/ (no bin/activate -- likely from an interrupted run). Removing it..."
  rm -rf venv
fi

if [[ ! -d venv ]]; then
  echo "-- Creating virtual environment (venv/)..."
  "$PYTHON_BIN" -m venv venv
else
  echo "-- Reusing existing venv/"
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "-- Installing requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [[ -z "${ANTHROPIC_API_KEY:-}" && -f .env ]]; then
  echo "-- Loading ANTHROPIC_API_KEY from .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo ""
  echo "NOTE: ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in,"
  echo "      or 'export ANTHROPIC_API_KEY=sk-ant-...' before running the pipeline."
  echo "      Setup will continue -- the key is only needed for run_pipeline.py, not for"
  echo "      installation or --list-classes."
fi

echo ""
echo "-- Verifying install (no API cost -- just discovers classes under $DATA_DIR)..."
if [[ -d "$DATA_DIR" ]]; then
  python3 scripts/run_pipeline.py --data-dir "$DATA_DIR" --list-classes
else
  echo "   ($DATA_DIR not found yet -- point --data-dir at your CIC-IoT-2023-style folder "
  echo "    once you have one. Everything else installed successfully.)"
fi

echo ""
echo "== Setup complete =="
echo ""
echo "Next steps:"
echo "  source venv/bin/activate"
echo "  export ANTHROPIC_API_KEY=sk-ant-...        # if not already set via .env"
echo "  python3 scripts/run_pipeline.py --data-dir $DATA_DIR --limit 5 --samples-per-class 5   # cheap pilot"
echo "  python3 scripts/generate_rag_report.py                                                  # free, no API cost"
echo ""
echo "See README.md for full usage, cost estimates, and the Docker option."
