"""
corpus.py
---------
Generates a reproducible synthetic CAPEC/CVE-style reference corpus for the
Full-Corpus vs. RAG experiment.

Design:
  * A fixed set of ANCHOR entries (+ paraphrased natural-language queries that
    should map to them) is included in every corpus, at every size. These are
    modeled on the three real entries shown in the ClearSight report
    (CAPEC-482 TCP Flood, CAPEC-488 HTTP Flood, CVE-2016-10401 Mirai) plus
    synthetic siblings covering the other CIC-IoT-2023 attack families
    (recon, spoofing, brute force, web-based, DoS/DDoS variants, Mirai
    variants, benign).
  * DISTRACTOR entries are generated to pad the corpus up to the target size.
    They intentionally reuse vocabulary from the anchors (attack type words,
    protocol names, CWE/OWASP-style phrasing) so that retrieval is genuinely
    contested as the corpus grows -- this is what makes the recall@k decay
    with corpus size a real (not trivially perfect) measurement.

Because the anchor set never changes, any change in recall@k across corpus
sizes is attributable to distractor pressure, not to the query set changing.
"""

import random
import hashlib

RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Anchor entries: (id, kind, name, attack_families, description)
# Modeled on CIC-IoT-2023's 7 attack categories / 33 attack types + benign.
# ---------------------------------------------------------------------------
ANCHOR_ENTRIES = [
    ("CAPEC-482", "capec", "TCP Flood",
     ["DDoS-TCP_Flood", "DoS-TCP_Flood", "DDoS-SYN_Flood", "DoS-SYN_Flood"],
     "Flooding attack using TCP, often TCP SYN messages that exploit connection-state weaknesses."),
    ("CAPEC-488", "capec", "HTTP Flood",
     ["DDoS-HTTP_Flood", "DoS-HTTP_Flood"],
     "Flooding attack using HTTP, consuming resources at the application layer via legitimate session-based HTTP GET requests."),
    ("CAPEC-486", "capec", "UDP Flood",
     ["DDoS-UDP_Flood", "DoS-UDP_Flood"],
     "Flooding attack using UDP datagrams sent at high rate to overwhelm target bandwidth or processing."),
    ("CAPEC-487", "capec", "ICMP Flood",
     ["DDoS-ICMP_Flood", "DoS-ICMP_Flood"],
     "Flooding attack using ICMP echo request packets to consume network and target resources."),
    ("CAPEC-98", "capec", "Phishing",
     ["Recon-PortScan", "Recon-OSScan"],
     "Reconnaissance technique enumerating open ports and services prior to exploitation."),
    ("CAPEC-292", "capec", "Host Discovery",
     ["Recon-HostDiscovery", "Recon-PingSweep"],
     "Reconnaissance technique identifying live hosts on a network segment via ICMP or ARP probing."),
    ("CAPEC-49", "capec", "Password Brute Forcing",
     ["DictionaryBruteForce"],
     "Systematic guessing of authentication credentials against a login service using a dictionary of common passwords."),
    ("CAPEC-141", "capec", "Cache Poisoning",
     ["DNS_Spoofing"],
     "Injection of forged responses into a DNS resolver cache to redirect victims to attacker-controlled hosts."),
    ("CAPEC-94", "capec", "Adversary in the Middle",
     ["MITM-ArpSpoofing"],
     "Interception of network traffic between two parties by forging ARP responses to redirect traffic through the attacker."),
    ("CAPEC-66", "capec", "SQL Injection",
     ["SqlInjection"],
     "Injection of malicious SQL statements into an application's input fields to manipulate backend database queries."),
    ("CAPEC-63", "capec", "Cross-Site Scripting",
     ["XSS"],
     "Injection of malicious script into web content viewed by other users, executing in their browser context."),
    ("CAPEC-153", "capec", "Command Injection",
     ["CommandInjection"],
     "Injection of operating system commands into an application that passes unsanitized input to a system shell."),
    ("CAPEC-137", "capec", "Parameter Injection",
     ["Uploading_Attack"],
     "Manipulation of file upload parameters to place malicious payloads on a target web server."),
    ("CAPEC-536", "capec", "Data Exfiltration via Backdoor",
     ["Backdoor_Malware"],
     "Use of a covert channel or implanted backdoor to exfiltrate data from a compromised device."),
    ("CVE-2016-10401", "cve", "ZyXEL PK5001Z default su password",
     ["Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain"],
     "ZyXEL PK5001Z devices have zyad5001 as the su password, giving easier root access for remote attackers. Relevant to Mirai's device-compromise phase, not the flood technique itself."),
    ("CVE-2017-17215", "cve", "Huawei HG532 remote code execution",
     ["Mirai-greeth_flood", "Mirai-greip_flood"],
     "Huawei HG532 devices allow remote attackers to execute arbitrary code via crafted UPnP requests, a known Mirai-variant infection vector."),
    ("CVE-2014-9583", "cve", "Realtek SDK miniigd UPnP SOAP buffer overflow",
     ["Mirai-udpplain"],
     "Buffer overflow in the miniigd SOAP service in Realtek SDK allows remote attackers to execute arbitrary code via a crafted NewInternalClient request."),
    ("CAPEC-13", "capec", "Subverting Environment Variable Values",
     ["Vulnerability_scan"],
     "Automated scanning of a target host or network for known software vulnerabilities prior to exploitation."),
    ("CAPEC-585", "capec", "DNS Domain Seizure",
     ["DNS_Spoofing"],
     "Manipulation of DNS records to redirect legitimate domain traffic to an attacker-controlled destination."),
    ("BENIGN-0", "capec", "Benign Traffic Baseline",
     ["BenignTraffic"],
     "Normal, non-malicious IoT device traffic exhibiting regular periodic communication patterns with no attack signature."),
]

# Natural-language "traffic descriptions" (simulating the plain-English
# summary an analyst or the vision model would produce from a traffic image)
# paraphrased away from the entry text, each pointing at exactly one anchor id.
ANCHOR_QUERIES = [
    ("Sustained high-rate SYN packets with no completed handshake, targeting a single host on a T-flow window.", "CAPEC-482"),
    ("Repeated legitimate-looking HTTP GET requests at a rate far exceeding normal session behavior.", "CAPEC-488"),
    ("Large volume of UDP datagrams directed at a fixed destination port, no application-layer payload structure.", "CAPEC-486"),
    ("Burst of ICMP echo requests saturating outbound bandwidth toward one target IP.", "CAPEC-487"),
    ("Sequential connection attempts across a wide range of destination ports on a single host.", "CAPEC-98"),
    ("Broadcast ICMP probes sweeping the local subnet to enumerate live hosts.", "CAPEC-292"),
    ("Rapid sequence of failed authentication attempts against a login service using varying credentials.", "CAPEC-49"),
    ("DNS responses with mismatched transaction IDs and unexpected source addresses.", "CAPEC-141"),
    ("Unsolicited ARP replies causing traffic redirection through an intermediate host.", "CAPEC-94"),
    ("Anomalous SQL-like tokens embedded in an HTTP request body targeted at a login form.", "CAPEC-66"),
    ("Script-like payload embedded in a URL query parameter directed at a web application.", "CAPEC-63"),
    ("Shell metacharacters embedded in a form submission directed at a device's management interface.", "CAPEC-153"),
    ("Unusual multipart file upload with executable payload signature to a device's web interface.", "CAPEC-137"),
    ("Periodic small outbound connections to an uncommon external port following a compromise event.", "CAPEC-536"),
    ("Device establishing a UDP flood immediately after a known ZyXEL default-credential SSH login.", "CVE-2016-10401"),
    ("Device sending crafted UPnP requests preceding a greeth-flood burst, consistent with Huawei router exploitation.", "CVE-2017-17215"),
    ("Crafted SOAP request to an embedded UPnP service followed by outbound flood traffic.", "CVE-2014-9583"),
    ("Sequential service-version probes against multiple ports consistent with a vulnerability scan.", "CAPEC-13"),
    ("DNS zone transfer inconsistency suggesting record tampering at the resolver level.", "CAPEC-585"),
    ("Low, steady packet rate with regular inter-arrival timing and no protocol anomalies.", "BENIGN-0"),
]

_VOCAB_ADJ = ["intermittent", "low-rate", "encrypted", "fragmented", "spoofed", "malformed",
              "reflected", "amplified", "encapsulated", "tunneled", "obfuscated", "throttled"]
_VOCAB_NOUN = ["session", "handshake", "payload", "beacon", "probe", "request", "response",
               "datagram", "segment", "header", "credential", "endpoint"]
_VOCAB_PROTO = ["TCP", "UDP", "HTTP", "HTTPS", "DNS", "ARP", "ICMP", "MQTT", "CoAP", "Telnet", "SSH", "SNMP"]
_VOCAB_FAMILY = ["Flood", "Scan", "Injection", "Spoofing", "BruteForce", "Exfiltration",
                 "Backdoor", "Reconnaissance", "Overflow", "Hijack"]


def _distractor_entry(i: int, rng: random.Random) -> dict:
    """Deterministic pseudo-realistic distractor entry, seeded by index."""
    adj = rng.choice(_VOCAB_ADJ)
    noun = rng.choice(_VOCAB_NOUN)
    proto = rng.choice(_VOCAB_PROTO)
    family = rng.choice(_VOCAB_FAMILY)
    is_cve = rng.random() < 0.35
    if is_cve:
        year = rng.choice([2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022])
        num = rng.randint(1000, 99999)
        eid = f"CVE-{year}-{num:05d}"
        name = f"{proto} {family.lower()} vulnerability in synthetic device firmware v{rng.randint(1,9)}.{rng.randint(0,9)}"
        desc = (f"A {adj} {noun} handling flaw in the {proto} service of a generic embedded device "
                f"allows an unauthenticated attacker to trigger a {family.lower()}-class condition "
                f"via a crafted {noun}.")
    else:
        num = 1000 + i
        eid = f"CAPEC-{num}"
        name = f"{proto} {family}"
        desc = (f"An attack pattern involving {adj} {proto} {noun}s used to achieve a {family.lower()} "
                f"effect against a target device or service.")
    return {
        "id": eid,
        "kind": "cve" if is_cve else "capec",
        "name": name,
        "attack_families": [f"{proto}-{family}_{i}"],
        "description": desc,
        "source_url": f"{'nvd.nist.gov/vuln/detail/' + eid if is_cve else 'capec.mitre.org/data/definitions/' + str(num) + '.html'}",
    }


def build_corpus(target_size: int, seed: int = RANDOM_SEED) -> list[dict]:
    """
    Build a corpus of `target_size` entries: all ANCHOR_ENTRIES plus
    deterministic synthetic distractors padding up to target_size.
    target_size must be >= len(ANCHOR_ENTRIES).
    """
    if target_size < len(ANCHOR_ENTRIES):
        raise ValueError(f"target_size must be >= {len(ANCHOR_ENTRIES)} (number of anchors)")

    rng = random.Random(seed)  # fixed seed -> distractors are reproducible
    corpus = []
    for eid, kind, name, families, desc in ANCHOR_ENTRIES:
        corpus.append({
            "id": eid, "kind": kind, "name": name,
            "attack_families": families, "description": desc,
            "source_url": f"{'nvd.nist.gov/vuln/detail/' + eid if kind == 'cve' else 'capec.mitre.org/data/definitions/' + eid.split('-')[1] + '.html'}",
        })

    n_distractors = target_size - len(ANCHOR_ENTRIES)
    for i in range(n_distractors):
        corpus.append(_distractor_entry(i, rng))

    # Shuffle so anchors aren't clustered at the front (would bias TF-IDF
    # matrix ordering effects, e.g. cache locality -- keep it fair).
    shuffle_rng = random.Random(seed + 1)
    shuffle_rng.shuffle(corpus)
    return corpus


def entry_text(entry: dict) -> str:
    """The text representation sent to the model / indexed for retrieval."""
    return f"{entry['name']}. Families: {', '.join(entry['attack_families'])}. {entry['description']}"


def get_queries():
    """Fixed query set: (query_text, ground_truth_entry_id), same at every corpus size."""
    return list(ANCHOR_QUERIES)


if __name__ == "__main__":
    c = build_corpus(100)
    print(f"Built corpus of {len(c)} entries. Example:")
    print(c[0])
    print(f"\n{len(get_queries())} fixed queries. Example:")
    print(get_queries()[0])
