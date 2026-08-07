"""
prompting.py -- ONE prompt, held constant across both conditions. Unlike
../networksecurity (which varies the PROMPT across 3 conditions and holds
the image constant), this project varies the IMAGE across 2 conditions and
holds the prompt constant -- that's the whole point: isolate the effect of
visual dimensionality by changing nothing else.
"""

BASE_CONTEXT = (
    "You are analyzing a visualization of IoT network traffic captured from the CIC-IoT-2023 "
    "dataset. The image summarizes a sequence of consecutive traffic windows (each window "
    "summarizes ~100 packets), showing packet rate, TCP flag composition, protocol mix, and "
    "packet size statistics over time."
)


def response_format(class_names):
    return (
        "Respond in EXACTLY this format, nothing else:\n"
        f"CLASSIFICATION: <one of: {', '.join(class_names)}>\n"
        "JUSTIFICATION: <2-4 sentences explaining your classification based on what you see "
        "in the image>"
    )


def build_prompt(class_names):
    return f"{BASE_CONTEXT}\n\nClassify this traffic. {response_format(class_names)}"


def parse_response(text):
    out = {"classification": None, "justification": None}
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("CLASSIFICATION:"):
            out["classification"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("JUSTIFICATION:"):
            out["justification"] = line.split(":", 1)[1].strip()
    return out
