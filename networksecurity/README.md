# networksecurity

Citation-grounded, multimodal LLM classification of IoT/OT network traffic. Claude
looks at a rendered image of a slice of network traffic, classifies it, and cites a
specific CAPEC attack-pattern or CVE vulnerability ID to justify that classification.
Every citation is then checked against a hand-verified reference corpus in real time —
so instead of trusting an AI's explanation on its own authority, the system tells you
whether it's grounded in a real, correctly-matched reference, or not.

This is a clean, deployable, greenfield implementation of that pipeline: a proper
Python package (not a single script), a CLI, tests that don't require an API key, and
deployment tooling (a setup script and a Dockerfile). The reference corpus, prompting
logic, and grading rules are ported byte-for-byte from the original research code (see
`src/networksecurity/corpus.py`'s module docstring for provenance) — this project
reorganizes and packages that logic, it doesn't re-derive it, because re-deriving
CAPEC/CVE citations from scratch risks introducing exactly the kind of unverified claim
this whole project exists to catch.

## What actually calls the API

Only one file: `src/networksecurity/claude_client.py`, invoked via
`scripts/run_pipeline.py`. Everything else — the corpus, prompt construction, citation
grading, chart generation — is pure, network-free Python, which is deliberate: it makes
the rest of the codebase unit-testable without an API key, and makes it obvious where
real money gets spent.

## Quick start

```bash
git clone <this-project>   # or just use the folder as-is
cd networksecurity
./deploy.sh                          # creates venv/, installs requirements.txt, verifies setup
source venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...  # or copy .env.example to .env and fill it in

# Point --data-dir at a folder laid out as one subfolder per class, each full of CSV
# traffic files (see "Data layout" below).
python3 scripts/run_pipeline.py --data-dir data/CSV --list-classes      # free, no API call
python3 scripts/run_pipeline.py --data-dir data/CSV --limit 5 --samples-per-class 5   # cheap pilot, ~$0.09
python3 scripts/generate_rag_report.py                                  # free, no API call
```

### Example: multi-class pilot

`--limit` and `--samples-per-class` are per-class, not a total across the run — so to
get 10 samples spread across two specific classes (5 each), restrict with `--classes`:

```bash
python3 scripts/run_pipeline.py --data-dir data/CSV \
    --classes DDoS-TCP_Flood,Mirai-udpplain --limit 5 --samples-per-class 5
```

That's 10 samples × 3 conditions = 30 API calls, ~$0.18. Drop `--classes` to run against
every class discovered under `--data-dir` instead (see the cost table below for what
that costs at different scales). `--samples-per-class` controls how many images get
*rendered* per class (free); `--limit` controls how many of those rendered images
actually get *sent to Claude* (the part that costs money) — set them equal, as above, to
avoid rendering images that never get classified.

## Setting up on a new machine

Full checklist for moving this project to a different Mac (or any machine) from
scratch:

**1. Prerequisites.** Python 3.9+ and git:

```bash
python3 --version
git --version
```

If either's missing: `brew install python3 git`, or `xcode-select --install` for the
Xcode Command Line Tools.

**2. Clone the repo.**

```bash
git clone git@github.com:gshiva1975/IOT-MULTIMODEL.git
cd IOT-MULTIMODEL/networksecurity
```

Use the HTTPS URL instead (`https://github.com/gshiva1975/IOT-MULTIMODEL.git`) if SSH
keys aren't set up on this machine yet.

**3. Run the deploy script.**

```bash
./deploy.sh
```

Creates a fresh `venv/`, installs `requirements.txt`, and verifies the install. Should
complete with no manual steps.

**4. Get the dataset onto this machine.** `data/CSV/` is gitignored on purpose (a
multi-GB dataset doesn't belong in git — see "Known simplifications" below), so cloning
the repo brings over code only, not data. Copy `data/CSV/` over separately — external
drive, cloud sync, AirDrop from another Mac, or a fresh download of the CIC-IoT-2023 CSV
export — so the layout ends up as `networksecurity/data/CSV/<class_name>/*.pcap.csv`.

**5. Set your API key.**

```bash
source venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...
```

or copy `.env.example` to `.env` and fill it in — `deploy.sh` and both scripts pick it
up from there automatically.

**6. Verify everything's wired up, free of charge.**

```bash
python3 scripts/run_pipeline.py --data-dir data/CSV --list-classes
python3 -m pytest tests/ -v
```

First command should discover your classes with zero API cost; second should show all
24 tests passing with no API key needed.

**7. Run a cheap pilot to confirm the API key actually works end to end.**

```bash
python3 scripts/run_pipeline.py --data-dir data/CSV --classes DDoS-TCP_Flood --limit 2 --samples-per-class 2
```

~6 API calls, a few cents — confirms image rendering → API call → parsing → grading all
work on this machine before running anything larger.

Alternatively, skip steps 1-3 entirely and use Docker (see "Docker" below) — no local
Python/venv setup needed, just Docker Desktop.

## Data layout

```
data/CSV/
  BenignTraffic/BenignTraffic.pcap.csv
  DDoS-TCP_Flood/DDoS-TCP_Flood.pcap.csv
  DDoS-SynonymousIP_Flood/DDoS-SynonymousIP_Flood.pcap.csv
  DDoS-SynonymousIP_Flood/DDoS-SynonymousIP_Flood1.pcap.csv
  ... (as many numbered part files per class as you have)
```

Every subfolder under `--data-dir` becomes a class; every `*.csv` inside it is treated
as one part file of that class's traffic. Files are loaded one at a time, not all
concatenated in memory, so this scales to many large files. This project was built and
tested against the CIC-IoT-2023 dataset's feature-CSV export format (columns like
`Rate`, `syn_flag_number`, `TCP`, `AVG`, etc. — see `src/networksecurity/config.py`'s
`FEATURES` list) but will work with any traffic dataset in the same column shape.

## Project layout

```
networksecurity/
  README.md
  requirements.txt / requirements-dev.txt
  deploy.sh                        -- one-command setup + verification (no API cost)
  Dockerfile / .dockerignore       -- containerized deployment
  .env.example                     -- copy to .env and fill in ANTHROPIC_API_KEY
  src/networksecurity/
    config.py                      -- constants (model id, feature columns, paths)
    corpus.py                      -- the verified CAPEC/CVE reference corpus
    data_loader.py                 -- discover classes/files from a data directory
    visualization.py               -- render traffic windows into 4-panel PNG images
    prompting.py                   -- the 3 prompting conditions + response parsing
    claude_client.py               -- THE ONLY MODULE THAT CALLS THE API
    baselines.py                   -- non-LLM comparison detectors (z-score, Isolation Forest)
    grading.py                     -- Wilson 95% CI + citation-quality grading
    reporting.py                   -- per-condition chart + input-export generation
  scripts/
    run_pipeline.py                -- CLI: full experiment (costs money)
    generate_rag_report.py         -- CLI: chart + export one condition (free)
  tests/                           -- unit tests, no API key or network needed
  data/                            -- put your --data-dir here (gitignored)
  results/                         -- pipeline output lands here (gitignored)
```

## The three prompting conditions

Every sample is classified three times, once per condition, so their citation quality
can be directly compared:

- **naive** — classify only, no reference material offered at all.
- **cve_text_grounded** — classify + cite a CVE/CAPEC ID from the model's own training
  knowledge, no corpus provided.
- **rag_grounded** — classify + cite ONLY from the corpus text serialized directly into
  the prompt, every call. This is "context-stuffing," not vector-index retrieval — the
  full corpus goes in every time, not just the top-k relevant entries. That's a
  deliberate simplification for this research stage (see the inline comments in
  `prompting.py` and `claude_client.py`): it guarantees the correct entry is always
  available to cite, at the cost of prompt size scaling with total corpus size rather
  than with what's relevant to one sample. A production version would replace this with
  real retrieval (embed the corpus once, fetch only the top few relevant entries per
  query) once the corpus grows large enough that resending it all every call stops being
  cheap.

## Citation grading

Every citation gets graded against `corpus.py`'s reference corpus:

| Grade | Meaning |
|---|---|
| `real-and-correct` | A real, verified ID that correctly describes this attack type |
| `real-but-generic` | A real ID, but too broad/parent-level to count as a specific match |
| `real-but-wrong-family` | A real ID that describes a *different* attack technique |
| `no-citation` | Model said N/A or gave no reference |
| `UNVERIFIED` | An ID not yet checked against MITRE/NVD — needs manual verification before being treated as either correct or fabricated |

All percentages are reported with a Wilson 95% confidence interval (`grading.py`), not
a bare ratio — at small sample sizes (a n=5 pilot, say) a plain percentage overstates
confidence; Wilson intervals correctly widen at small n.

## Cost estimates

`run_pipeline.py` prints a cost estimate and pauses before spending anything (pass
`--yes` to skip the pause in scripts). Based on an observed ~$0.0061/call:

| Run | API calls | Est. cost |
|---|---|---|
| `--list-classes` | 0 | $0 |
| `--skip-llm` (baselines only) | 0 | $0 |
| `--limit 5` on 1 class | 15 | ~$0.09 |
| `--limit 5 --samples-per-class 5` on 34 classes | ~510 | ~$3 |
| `--limit 40 --samples-per-class 40` on 34 classes (submission-grade) | ~4,080 | ~$25 |

`generate_rag_report.py` always costs $0 — it only re-processes data `run_pipeline.py`
already produced.

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

24 tests, all pure-function — no API key, no network, no sample data needed. They cover
Wilson CI bounds, every citation-grading branch, prompt construction per condition, and
internal consistency of the reference corpus (no ID double-counted as both generic and
wrong-family, every corpus entry has required fields, etc.).

## Docker

```bash
docker build -t networksecurity .
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/results:/app/results" \
  networksecurity \
  python3 scripts/run_pipeline.py --data-dir data/CSV --limit 5 --samples-per-class 5
```

## Resume behavior

`run_pipeline.py` writes results incrementally, one row per (sample, condition) API
call. A rerun with the same arguments automatically skips already-completed calls and
retries only `ERROR` rows (billing/rate-limit/network failures that never actually got
billed) — so an interruption never costs you a redo of work you already paid for. Pass
`--no-resume` to force a clean run instead.

## Known simplifications (documented, not hidden)

- `rag_grounded` context-stuffs the full corpus every call rather than doing real
  vector-index retrieval — see "The three prompting conditions" above.
- The corpus's coverage is honest, not exhaustive: classes without a verified CAPEC/CVE
  entry will correctly show up as `no-citation` / "no matching reference" rather than
  being force-fit to a plausible-looking ID.
- `--samples-per-class` random sampling uses a fixed seed (`RNG` in `config.py`), so
  which traffic windows get sampled is deterministic given the same data — useful for
  reproducibility, but means rerunning with the same arguments will pick the same
  samples rather than a fresh random draw.
