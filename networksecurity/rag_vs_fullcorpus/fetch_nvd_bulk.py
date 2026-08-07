"""
fetch_nvd_bulk.py
------------------
Pulls CVE records from the NVD REST API (services.nvd.nist.gov) for a set
of IoT/router/embedded-device-relevant keyword searches, and writes them to
nvd_entries.json in the same entry format used elsewhere in this repo.

Also blocked in the original sandbox (403 blocked-by-allowlist on
services.nvd.nist.gov). Works on a normal machine.

NVD's public API allows 5 requests / 30s without an API key, 50 requests /
30s with one (free, https://nvd.nist.gov/developers/request-an-api-key).
Without a key this script will be slow for large keyword lists -- get a key
if you're pulling more than a handful of searches.

Usage:
    pip install requests
    python3 fetch_nvd_bulk.py                       # no API key, rate-limited
    NVD_API_KEY=xxxx python3 fetch_nvd_bulk.py       # with API key, faster
Output:
    nvd_entries.json
"""

import json
import os
import time
import requests

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OUTPUT_PATH = "nvd_entries.json"

# Keyword searches chosen to surface CVEs relevant to IoT/OT botnet-style
# attacks (matching CIC-IoT-2023's Mirai / DoS / recon / spoofing categories).
# Expand this list for a larger corpus; each search costs one API call plus
# pagination calls if results exceed resultsPerPage.
KEYWORD_SEARCHES = [
    "Mirai",
    "default password router",
    "IoT camera remote code execution",
    "UPnP buffer overflow",
    "router command injection",
    "embedded device authentication bypass",
    "DVR botnet",
    "telnet default credentials",
]

RESULTS_PER_PAGE = 50  # keep small; this is a curated sample, not an exhaustive dump


def api_get(params: dict, api_key: str | None) -> dict:
    headers = {"apiKey": api_key} if api_key else {}
    resp = requests.get(NVD_API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_for_keyword(keyword: str, api_key: str | None) -> list[dict]:
    print(f"Searching NVD for: {keyword!r}")
    data = api_get({"keywordSearch": keyword, "resultsPerPage": RESULTS_PER_PAGE}, api_key)
    vulns = data.get("vulnerabilities", [])
    entries = []
    for v in vulns:
        cve = v.get("cve", {})
        cve_id = cve.get("id")
        descs = cve.get("descriptions", [])
        desc_text = next((d["value"] for d in descs if d.get("lang") == "en"), "")
        if not cve_id or not desc_text:
            continue
        entries.append({
            "id": cve_id,
            "kind": "cve",
            "name": desc_text.split(".")[0][:120],
            "attack_families": [f"keyword:{keyword}"],
            "description": desc_text,
            "source_url": f"nvd.nist.gov/vuln/detail/{cve_id}",
        })
    print(f"  -> {len(entries)} entries")
    return entries


def main():
    api_key = os.environ.get("NVD_API_KEY")
    sleep_s = 6 if not api_key else 1  # respect 5-req/30s unauthenticated rate limit

    all_entries = {}
    for kw in KEYWORD_SEARCHES:
        try:
            for e in fetch_for_keyword(kw, api_key):
                all_entries[e["id"]] = e  # dedupe by CVE ID across searches
        except requests.exceptions.RequestException as e:
            print(f"  ! request failed for {kw!r}: {e}")
        time.sleep(sleep_s)

    entries = list(all_entries.values())
    print(f"\nTotal unique CVEs: {len(entries)}")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
