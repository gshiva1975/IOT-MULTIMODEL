"""
prompting.py -- builds the three prompting conditions sent to Claude.

  naive               -- classify only, no reference material offered
  cve_text_grounded    -- classify + cite from the model's own knowledge
  rag_grounded         -- classify + cite ONLY from the corpus text below,
                           which is fully serialized into the prompt every
                           call (this is "context-stuffing", not vector-index
                           retrieval -- see the project README for the
                           distinction and the trade-offs of each).
"""

from .corpus import CVE_CORPUS

BASE_CONTEXT = (
    "You are analyzing a visualization of IoT network traffic captured from the CIC-IoT-2023 "
    "dataset. The image has four panels for a sequence of consecutive traffic windows (each "
    "window summarizes ~100 packets): (1) packet rate over time, (2) TCP flag composition, "
    "(3) protocol mix (stacked area), and (4) average and standard deviation of packet size."
)


def response_format(class_names):
    return (
        "Respond in EXACTLY this format, nothing else:\n"
        f"CLASSIFICATION: <one of: {', '.join(class_names)}>\n"
        "REFERENCE_ID: <a CVE-YYYY-NNNNN or CAPEC-NNN ID you believe explains this traffic, or N/A>\n"
        "JUSTIFICATION: <2-4 sentences explaining your classification and, if applicable, why you "
        "cited that reference ID>"
    )


def build_prompt(condition, class_names):
    fmt = response_format(class_names)
    if condition == "naive":
        return f"{BASE_CONTEXT}\n\nClassify this traffic. {fmt}"
    if condition == "cve_text_grounded":
        return (f"{BASE_CONTEXT}\n\nClassify this traffic. If malicious, cite the specific CVE or "
                f"CAPEC ID for the technique shown, drawing on your own knowledge. {fmt}")
    if condition == "rag_grounded":
        ref_text = "\n\n".join(f"[{e['capec_id']}] {e['name']}: {e['description']}"
                                for e in CVE_CORPUS["capec_entries"])
        note = ("" if CVE_CORPUS["capec_entries"] else
                "(No verified reference entries are available for this run's classes -- say N/A.)")
        return (f"{BASE_CONTEXT}\n\nReference database of known attack patterns:\n\n{ref_text}{note}\n\n"
                f"Classify this traffic. Cite ONLY a reference ID from the database above, or N/A if "
                f"none apply -- even if you recognize the traffic, do not cite anything not listed "
                f"here. {fmt}")
    raise ValueError(condition)


def parse_response(text):
    out = {"classification": None, "reference_id": None, "justification": None}
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("CLASSIFICATION:"):
            out["classification"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("REFERENCE_ID:"):
            out["reference_id"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("JUSTIFICATION:"):
            out["justification"] = line.split(":", 1)[1].strip()
    return out
