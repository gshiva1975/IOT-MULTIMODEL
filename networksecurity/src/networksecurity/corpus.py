"""
corpus.py -- the hand-verified CAPEC/CVE reference corpus.

Provenance: every entry below was independently checked against
capec.mitre.org / nvd.nist.gov before being added (see the inline comments
for audit notes and dates). This is the SAME corpus used for both (a)
restricting what the rag_grounded prompting condition is allowed to cite,
and (b) grading every condition's citations afterward -- using one shared
source for both roles means the citation rules and the grading can never
silently drift apart.

Coverage is honest, not exhaustive: DDoS/DoS flood variants, the 3 Mirai
classes, and the additional classes audited after the GPT-4o cross-model run
are covered; anything not listed here will correctly show up as
"no matching reference" rather than being force-fit to a plausible-looking ID.

Do not add entries to this file without independently confirming them
against the primary source (MITRE CAPEC / NVD) first -- the entire point of
this corpus is that every ID in it is guaranteed real and correctly
described.
"""

CVE_CORPUS = {
    "entries": [
        {
            "cve_id": "CVE-2016-10401",
            "attack_families": ["Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain"],
            "description": (
                "ZyXEL PK5001Z devices have zyad5001 as the su password, making it easier for "
                "remote attackers to obtain root access if a non-root account password is known. "
                "(Relevant to Mirai's credential-based device-compromise/propagation phase, not "
                "the flood technique itself.)"
            ),
            "source_url": "https://nvd.nist.gov/vuln/detail/CVE-2016-10401",
        },
        {
            "cve_id": "CVE-2017-17215",
            "attack_families": ["Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain"],
            "description": (
                "Huawei HG532 with some customized versions has a remote code execution "
                "vulnerability via crafted packets to port 37215. (Exploited by the Satori/Okiru "
                "Mirai variant for device compromise, not the flood technique itself.)"
            ),
            "source_url": "https://nvd.nist.gov/vuln/detail/CVE-2017-17215",
        },
    ],

    # Verified against capec.mitre.org.
    "capec_entries": [
        {
            "capec_id": "CAPEC-482", "name": "TCP Flood",
            "attack_families": ["DDoS-TCP_Flood", "DoS-TCP_Flood", "DDoS-SYN_Flood", "DoS-SYN_Flood"],
            "description": (
                "An adversary may execute a flooding attack using the TCP protocol with the intent "
                "to deny legitimate users access to a service, often using TCP SYN messages that "
                "exploit connection-state weaknesses. (CAPEC-482's own description explicitly covers "
                "SYN-flood traffic; there is no separate, more specific CAPEC entry for SYN Flood.)"
            ),
            "source_url": "https://capec.mitre.org/data/definitions/482.html",
        },
        {
            "capec_id": "CAPEC-469", "name": "HTTP DoS",
            "attack_families": ["DDoS-HTTP_Flood", "DoS-HTTP_Flood"],
            "description": (
                "An attacker performs flooding at the HTTP level using legitimate session-based HTTP "
                "requests to exhaust web server resources, targeting resource depletion weaknesses "
                "rather than raw volumetric flooding."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/469.html",
        },
        {
            "capec_id": "CAPEC-488", "name": "HTTP Flood",
            "attack_families": ["DDoS-HTTP_Flood", "DoS-HTTP_Flood"],
            "description": (
                "An adversary may execute a flooding attack using the HTTP protocol with the intent "
                "to deny legitimate users access to a service by consuming resources at the "
                "application layer, using legitimate session-based HTTP GET requests, which makes it "
                "difficult to detect."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/488.html",
        },
        {
            "capec_id": "CAPEC-486", "name": "UDP Flood",
            "attack_families": ["DDoS-UDP_Flood", "DoS-UDP_Flood", "Mirai-udpplain"],
            "description": (
                "An adversary may execute a flooding attack using the UDP protocol with the intent "
                "to deny legitimate users access to a service by consuming available network "
                "bandwidth; the session-less nature of UDP makes the source easy to spoof."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/486.html",
        },
        {
            "capec_id": "CAPEC-487", "name": "ICMP Flood",
            "attack_families": ["DDoS-ICMP_Flood"],
            "description": (
                "An adversary may execute a flooding attack using the ICMP protocol with the intent "
                "to deny legitimate users access to a service by consuming available network "
                "bandwidth, typically from a wide range of spoofed source addresses."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/487.html",
        },
        {
            "capec_id": "CAPEC-495", "name": "UDP Fragmentation",
            "attack_families": ["DDoS-UDP_Fragmentation"],
            "description": (
                "An attacker executes a UDP Fragmentation attack using large UDP packets that force "
                "IP fragmentation, consuming more bandwidth with fewer packets and potentially "
                "exhausting server CPU/memory used for reassembly."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/495.html",
        },
        {
            "capec_id": "CAPEC-125", "name": "Flooding (generic parent pattern)",
            "attack_families": [
                "Mirai-greeth_flood", "Mirai-greip_flood", "DDoS-ACK_Fragmentation",
                "DDoS-PSHACK_FLOOD", "DDoS-RSTFINFLOOD", "DDoS-SlowLoris",
                "DDoS-SynonymousIP_Flood", "DDoS-ICMP_Fragmentation",
            ],
            "description": (
                "A general flooding attack pattern consuming target resources with a large volume of "
                "traffic. Used here as the honest fallback for flood techniques (including Mirai's "
                "GRE-based greeth/greip floods) that don't have a more specific CAPEC entry -- no "
                "dedicated 'GRE Flood' CAPEC entry exists as of this writing, so citing anything more "
                "specific for those two classes would be fabrication."
            ),
            "source_url": "https://capec.mitre.org/data/definitions/125.html",
        },
        # --- Added after a manual citation audit against capec.mitre.org. These are IDs the
        # model cited on its own initiative in the naive/text-grounded conditions for classes
        # outside the original 15-class corpus. Each was independently fetched and confirmed
        # real; the attack_families below reflect what the ID *actually* means per MITRE, not
        # what the model claimed.
        {"capec_id": "CAPEC-66", "name": "SQL Injection", "attack_families": ["SqlInjection"],
         "description": "SQL Injection.", "source_url": "https://capec.mitre.org/data/definitions/66.html"},
        {"capec_id": "CAPEC-63", "name": "Cross-Site Scripting (XSS)", "attack_families": ["XSS"],
         "description": "Cross-Site Scripting.", "source_url": "https://capec.mitre.org/data/definitions/63.html"},
        {"capec_id": "CAPEC-300", "name": "Port Scanning", "attack_families": ["Recon-PortScan"],
         "description": "Port scanning.", "source_url": "https://capec.mitre.org/data/definitions/300.html"},
        {"capec_id": "CAPEC-88", "name": "OS Command Injection", "attack_families": ["CommandInjection"],
         "description": "OS command injection.", "source_url": "https://capec.mitre.org/data/definitions/88.html"},
        {"capec_id": "CAPEC-94", "name": "Adversary in the Middle (AiTM)", "attack_families": ["MITM-ArpSpoofing"],
         "description": "Adversary positions itself between two communicating parties.",
         "source_url": "https://capec.mitre.org/data/definitions/94.html"},
        {"capec_id": "CAPEC-292", "name": "Host Discovery", "attack_families": ["Recon-HostDiscovery"],
         "description": "Ping-sweep-style host discovery.", "source_url": "https://capec.mitre.org/data/definitions/292.html"},
        {"capec_id": "CAPEC-112", "name": "Brute Force", "attack_families": ["DictionaryBruteForce"],
         "description": "Brute-force credential guessing.", "source_url": "https://capec.mitre.org/data/definitions/112.html"},
        {"capec_id": "CAPEC-49", "name": "Password Brute Forcing", "attack_families": ["DictionaryBruteForce"],
         "description": "Password brute forcing.", "source_url": "https://capec.mitre.org/data/definitions/49.html"},
        {"capec_id": "CAPEC-312", "name": "Active OS Fingerprinting", "attack_families": ["Recon-OSScan"],
         "description": "Active OS fingerprinting via protocol-response probing.",
         "source_url": "https://capec.mitre.org/data/definitions/312.html"},
        {"capec_id": "CAPEC-142", "name": "DNS Cache Poisoning", "attack_families": ["DNS_Spoofing"],
         "description": "DNS cache poisoning.", "source_url": "https://capec.mitre.org/data/definitions/142.html"},
        {"capec_id": "CAPEC-650", "name": "Upload a Web Shell to a Web Server", "attack_families": ["Uploading_Attack"],
         "description": "Uploading a malicious web shell.", "source_url": "https://capec.mitre.org/data/definitions/650.html"},
        {"capec_id": "CAPEC-550", "name": "Install New Service", "attack_families": ["Backdoor_Malware"],
         "description": "Installing a malicious service for persistence.",
         "source_url": "https://capec.mitre.org/data/definitions/550.html"},
        {"capec_id": "CAPEC-551", "name": "Modify Existing Service", "attack_families": ["Backdoor_Malware"],
         "description": "Modifying an existing service for persistence.",
         "source_url": "https://capec.mitre.org/data/definitions/551.html"},
        {"capec_id": "CAPEC-701", "name": "Browser in the Middle (BiTM)", "attack_families": ["BrowserHijacking"],
         "description": "Transparent browser session hijacking.",
         "source_url": "https://capec.mitre.org/data/definitions/701.html"},
        # --- Added after auditing GPT-4o's citations (second-model cross-validation run). Same
        # methodology: each ID was independently fetched from capec.mitre.org and graded by
        # reading its actual description, not its title.
        {"capec_id": "CAPEC-310", "name": "Scanning for Vulnerable Software", "attack_families": ["VulnerabilityScan"],
         "description": "Scanning to find vulnerable/unpatched software versions and services.",
         "source_url": "https://capec.mitre.org/data/definitions/310.html"},
        {"capec_id": "CAPEC-86", "name": "XSS Through HTTP Headers", "attack_families": ["XSS"],
         "description": "Cross-Site Scripting technique that injects script via HTTP headers.",
         "source_url": "https://capec.mitre.org/data/definitions/86.html"},
    ],

    # Real, verified, but generic/parent-level patterns -- always graded "real-but-generic"
    # regardless of which class they're cited for (too broad to count as a specific match).
    "generic_ids": [
        "CAPEC-125", "CAPEC-169", "CAPEC-141", "CAPEC-224", "CAPEC-1", "CAPEC-233",
        # From the GPT-4o citation audit. Note: CAPEC-303 (TCP Xmas Scan) and CAPEC-489 (SSL
        # Flood) were each cited for a mix of classes where they're a plausible generic match
        # for SOME and a real mismatch for OTHERS; CAPEC-489 skewed heavily mismatched (7/9
        # citations) so it's graded wrong-family below instead -- a documented simplification,
        # since the grader doesn't currently support a per-class-subset verdict for the same ID.
        "CAPEC-108", "CAPEC-137", "CAPEC-151", "CAPEC-170", "CAPEC-242", "CAPEC-272", "CAPEC-303",
    ],

    # Real, verified CAPEC/CVE IDs that were cited by the model but do NOT describe any class
    # in this taxonomy (confirmed by reading the actual MITRE/NVD description) -- always graded
    # "real-but-wrong-family". Included explicitly so the automated grader can distinguish
    # "real ID, wrong/fabricated justification" from "ID we simply haven't looked up yet".
    "verified_wrong_family_ids": {
        "CAPEC-130": "Excessive Allocation -- explicitly NOT a flooding technique per its own MITRE description",
        "CAPEC-98": "Phishing -- unrelated to any traffic-flood or scan class in this dataset",
        "CAPEC-230": "Serialized Data with Nested Payloads -- XML/parser DoS, not a network flood",
        "CAPEC-530": "Provide Counterfeit Component -- hardware supply-chain attack, unrelated",
        "CAPEC-666": "BlueSmacking -- real flooding pattern but for Bluetooth L2CAP, not IP traffic",
        "CAPEC-560": "Use of Known Domain Credentials -- credential theft, not a malware backdoor mechanism",
        "CAPEC-181": "Flash File Overlay -- narrow Flash-specific clickjacking, not general browser hijacking",
        "CAPEC-609": "Cellular Traffic Intercept -- unrelated cellular-network technique",
        "CAPEC-467": "Cross Site Identification -- social-network info harvesting, distinct technique",
        "CAPEC-621": "Analysis of Packet Timing and Sizes -- side-channel traffic analysis, unrelated",
        "CAPEC-309": "Network Topology Mapping -- distinct recon technique from OS fingerprinting",
        # From the GPT-4o citation audit. CAPEC-484 is the standout finding: a DEPRECATED entry
        # cited 34 times as the justification for nearly every DDoS/DoS flood class, with zero
        # topical connection to flooding even pre-deprecation.
        "CAPEC-106": "DEPRECATED (XSS through Log Files, redirects to CAPEC-93/CAPEC-63) -- unrelated to ARP spoofing/MITM",
        "CAPEC-111": "JSON Hijacking -- steals AJAX/JSON response data via same-origin-policy bypass, not browser hijacking",
        "CAPEC-115": "Authentication Bypass -- generic access-control bypass, not specific to ARP/MITM spoofing",
        "CAPEC-131": "Resource Leak Exposure -- memory/resource-leak exhaustion, unrelated to DNS response falsification",
        "CAPEC-139": "Relative Path Traversal -- directory traversal via dot/slash sequences, unrelated to DNS spoofing",
        "CAPEC-155": "Screen Temporary Files for Sensitive Information -- reads insecure temp files, unrelated to ARP/MITM",
        "CAPEC-157": "Sniffing Attacks -- explicitly defined as entirely passive, unlike active ARP spoofing/MITM",
        "CAPEC-163": "Spear Phishing -- targeted social-engineering email attack, unrelated to ARP spoofing",
        "CAPEC-166": "Force the System to Reset Values -- abuses an app's config-reset function, unrelated to ARP spoofing",
        "CAPEC-176": "Configuration/Environment Manipulation -- tampers with external config files, not backdoor malware",
        "CAPEC-192": "Protocol Analysis -- reverse-engineering an unknown protocol's syntax, not DNS falsification",
        "CAPEC-196": "Session Credential Falsification through Forging -- forges session tokens, unrelated to SYN flood",
        "CAPEC-210": "Abuse Existing Functionality (category) -- broad grouping with no DNS-spoofing member",
        "CAPEC-226": "Session Credential Falsification through Manipulation -- tampers with a sniffed cookie, unrelated to SYN flood",
        "CAPEC-227": "Sustained Client Engagement -- explicitly differentiated from flooding attacks in its own description",
        "CAPEC-308": "UDP Scan -- probes ports of an already-identified host, unrelated to host-discovery/ping-sweep",
        "CAPEC-409": "DEPRECATED (Information Gathering from Non-Traditional Sources) -- unrelated to Mirai UDP flood",
        "CAPEC-449": "DEPRECATED (Malware Propagation via USB Stick) -- unrelated to ICMP flooding",
        "CAPEC-484": "DEPRECATED (XML Client-Side Attack) -- no relation to any TCP/UDP/ICMP flood; cited 34 times as a mismatched catch-all",
        "CAPEC-485": "Signature Spoofing by Key Recreation -- cryptographic key/signature forgery, unrelated to flooding",
        "CAPEC-489": "SSL Flood -- specifically an SSL/TLS renegotiation flood, mismatched for 7 of 9 non-SSL flood classes it was cited for",
        "CAPEC-491": "Quadratic Data Expansion -- XML/serialized-data entity-expansion DoS, unrelated to ICMP fragmentation",
        "CAPEC-501": "Android Activity Hijack -- mobile app UI-spoofing technique, unrelated to a network SYN flood",
        "CAPEC-55": "Rainbow Table Password Cracking -- offline hash-cracking with no live network brute-force signature",
        "CAPEC-583": "Disabling Network Hardware -- physical hardware sabotage, unrelated to application-layer SlowLoris",
        "CAPEC-593": "Session Hijacking -- session-token theft/reuse family, distinct CAPEC branch from XSS/Code Injection",
        "CAPEC-604": "Wi-Fi Jamming -- RF jamming/deauth flooding, unrelated to application-layer SlowLoris",
        "CAPEC-639": "Probe System Files -- reads improperly protected local files, unrelated to ICMP flooding",
        "CAPEC-64": "Using Slashes and URL Encoding to Bypass Validation Logic -- encoding/path-traversal bypass, distinct from command injection",
        "CVE-2000-0428": "Buffer overflow RCE in InterScan Virus Wall's SMTP gateway (2000) -- unrelated to a TCP flood DDoS",
    },
}


def known_reference_map():
    """ref_id -> set of class names it's a valid, specific match for."""
    known = {e["capec_id"]: set(e["attack_families"]) for e in CVE_CORPUS["capec_entries"]}
    known.update({e["cve_id"]: set(e["attack_families"]) for e in CVE_CORPUS["entries"]})
    return known


def generic_ids():
    return set(CVE_CORPUS.get("generic_ids", []))


def wrong_family_ids():
    return set(CVE_CORPUS.get("verified_wrong_family_ids", {}).keys())
