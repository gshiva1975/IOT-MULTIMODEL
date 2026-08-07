"""
fetch_capec_bulk.py
--------------------
Downloads the FULL CAPEC catalog (~559 attack patterns, version-dependent)
from MITRE and parses it into capec_entries.json.

This could not run inside the original sandbox: capec.mitre.org was blocked
at the sandbox's outbound proxy for direct requests, and the one available
web-fetch tool truncated the ~4-8MB XML file after ~14 entries. On a normal
machine with unrestricted outbound internet, this just works via `requests`.

Usage:
    pip install requests
    python3 fetch_capec_bulk.py
Output:
    capec_entries.json -- list of {id, kind, name, attack_families, description, source_url}
"""

import json
import re
import xml.etree.ElementTree as ET
import requests

CAPEC_XML_URL = "https://capec.mitre.org/data/xml/capec_latest.xml"
NS = {"capec": "http://capec.mitre.org/capec-3"}
OUTPUT_PATH = "capec_entries.json"


def fetch_xml(url: str = CAPEC_XML_URL, timeout: int = 60) -> bytes:
    print(f"Fetching {url} ...")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    print(f"Downloaded {len(resp.content) / 1024:.0f} KB")
    return resp.content


def parse_capec_xml(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    entries = []
    for ap in root.iter("{http://capec.mitre.org/capec-3}Attack_Pattern"):
        capec_id = ap.attrib.get("ID")
        name = ap.attrib.get("Name", "")
        desc_el = ap.find("capec:Description", NS)
        description = "".join(desc_el.itertext()).strip() if desc_el is not None else ""
        description = re.sub(r"\s+", " ", description)
        if not capec_id or not description:
            continue
        entries.append({
            "id": f"CAPEC-{capec_id}",
            "kind": "capec",
            "name": name,
            "attack_families": [],  # not present in raw CAPEC XML; fill in downstream if needed
            "description": description,
            "source_url": f"capec.mitre.org/data/definitions/{capec_id}.html",
        })
    return entries


def main():
    xml_bytes = fetch_xml()
    entries = parse_capec_xml(xml_bytes)
    print(f"Parsed {len(entries)} CAPEC entries")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
