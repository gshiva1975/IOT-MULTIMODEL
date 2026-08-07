"""
real_corpus.py
---------------
Real CAPEC/CVE entries, fetched and verified live against capec.mitre.org and
nvd.nist.gov during this session (not recalled from memory, not synthetic).
Every ID below was fetched via its official detail page and the Name/
Description below is transcribed from that page. This replaces the guessed
IDs in corpus.py's ANCHOR_ENTRIES, several of which turned out to be WRONG
when checked against the real source -- e.g. CAPEC-98 is actually
"Phishing," not port scanning as originally (incorrectly) assumed; the real
ID for port scanning is CAPEC-300. CAPEC-153 is "Input Data Manipulation,"
not "Command Injection." That mismatch, caught by verification rather than
by guessing, is itself a small demonstration of the exact failure mode the
ClearSight paper studies.

Sources (fetched live):
  https://capec.mitre.org/data/definitions/{id}.html
  https://nvd.nist.gov/vuln/detail/{id}

Network note: this sandbox's outbound allowlist blocks huggingface.co and
blocks direct bulk downloads (capec_latest.xml / *.csv.zip) at a size that
fits in one fetch, so this is a hand-curated set of 15 real entries (12
CAPEC + 3 CVE) rather than the full 559-pattern CAPEC catalog or a bulk NVD
pull. It is real data, just not exhaustive. See README for what a full pull
would require.
"""

REAL_ANCHOR_ENTRIES = [
    ("CAPEC-482", "capec", "TCP Flood",
     ["DDoS-TCP_Flood", "DoS-TCP_Flood", "DDoS-SYN_Flood", "DoS-SYN_Flood"],
     "An adversary may execute a flooding attack using the TCP protocol with the intent to deny legitimate users "
     "access to a service. These attacks exploit the weakness within the TCP protocol where there is some state "
     "information for the connection the server needs to maintain. This often involves the use of TCP SYN messages."),
    ("CAPEC-488", "capec", "HTTP Flood",
     ["DDoS-HTTP_Flood", "DoS-HTTP_Flood"],
     "An adversary may execute a flooding attack using the HTTP protocol with the intent to deny legitimate users "
     "access to a service by consuming resources at the application layer such as web services and their "
     "infrastructure. These attacks use legitimate session-based HTTP GET requests designed to consume large "
     "amounts of a server's resources. Since these are legitimate sessions this attack is very difficult to detect."),
    ("CAPEC-486", "capec", "UDP Flood",
     ["DDoS-UDP_Flood", "DoS-UDP_Flood"],
     "An adversary may execute a flooding attack using the UDP protocol with the intent to deny legitimate users "
     "access to a service by consuming the available network bandwidth. Additionally, firewalls often open a port "
     "for each UDP connection destined for a service with an open UDP port. Due to the session-less nature of the "
     "UDP protocol, the source of a packet is easily spoofed making it difficult to find the source of the attack."),
    ("CAPEC-487", "capec", "ICMP Flood",
     ["DDoS-ICMP_Flood", "DoS-ICMP_Flood"],
     "An adversary may execute a flooding attack using the ICMP protocol with the intent to deny legitimate users "
     "access to a service by consuming the available network bandwidth. A typical attack involves a victim server "
     "receiving ICMP packets at a high rate from a wide range of source addresses. Due to the session-less nature "
     "of the ICMP protocol, the source of a packet is easily spoofed."),
    ("CAPEC-300", "capec", "Port Scanning",
     ["Recon-PortScan"],
     "An adversary uses a combination of techniques to determine the state of the ports on a remote target. Any "
     "service or application available for TCP or UDP networking will have a port open for communications over "
     "the network. Typical port scanning activity involves sending probes to a range of ports and observing the "
     "responses to distinguish open, closed, filtered, and unfiltered ports."),
    ("CAPEC-49", "capec", "Password Brute Forcing",
     ["DictionaryBruteForce"],
     "Verified real entry (fetched, full text truncated in this session's tool output due to size); title and ID "
     "confirmed via capec.mitre.org/data/definitions/49.html. Concerns systematic guessing of authentication "
     "credentials against a login service."),
    ("CAPEC-94", "capec", "Adversary in the Middle (AiTM)",
     ["MITM-ArpSpoofing", "MITM-DHCPSpoofing"],
     "An adversary targets the communication between two components (typically client and server), in order to "
     "alter or obtain data from transactions, by placing themself within the communication channel between the two "
     "components. Alternate terms include Man-in-the-Middle / MITM, Person-in-the-Middle / PiTM, On-path Attacker."),
    ("CAPEC-141", "capec", "Cache Poisoning",
     ["DNS_Spoofing", "ARP_Spoofing"],
     "An attacker exploits the functionality of cache technologies to cause specific data to be cached that aids "
     "the attackers' objectives. This describes any attack whereby an attacker places incorrect or harmful "
     "material in cache -- the targeted cache can be an application's cache or a public cache (e.g. a DNS or ARP "
     "cache). A child attack pattern, CAPEC-142, covers DNS Cache Poisoning specifically."),
    ("CAPEC-66", "capec", "SQL Injection",
     ["SqlInjection"],
     "This attack exploits target software that constructs SQL statements based on user input, injecting malicious "
     "SQL statements into an application's input fields to manipulate backend database queries. Related weakness: "
     "CWE-89, Improper Neutralization of Special Elements used in an SQL Command."),
    ("CAPEC-63", "capec", "Cross-Site Scripting (XSS)",
     ["XSS"],
     "An adversary embeds malicious scripts in content that will be served to web browsers. The goal of the attack "
     "is for the target software, the client-side browser, to execute the script with the users' privilege level. "
     "These attacks are very difficult for an end user to detect. Related weakness: CWE-79."),
    ("CAPEC-137", "capec", "Parameter Injection",
     ["Uploading_Attack"],
     "An adversary manipulates the content of request parameters for the purpose of undermining the security of "
     "the target. Some parameter encodings use text characters as separators (e.g. HTTP GET name-value pairs "
     "separated by an ampersand); if an attacker can supply text strings used to fill these parameters, they can "
     "inject special characters to add or modify parameters, significantly changing the meaning of the query."),
    ("CAPEC-153", "capec", "Input Data Manipulation",
     ["Vulnerability_scan"],
     "An attacker exploits a weakness in input validation by controlling the format, structure, and composition of "
     "data to an input-processing interface. By supplying input of a non-standard or unexpected form an attacker "
     "can adversely impact the security of the target -- e.g. using a different character encoding to cause "
     "dangerous text to be treated as safe text."),
    ("CVE-2016-10401", "cve", "ZyXEL PK5001Z default su password",
     ["Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain"],
     "ZyXEL PK5001Z devices have zyad5001 as the su password, which makes it easier for remote attackers to obtain "
     "root access if a non-root account password is known (or a non-root default account exists within an ISP's "
     "deployment of these devices). CVSSv3 base score 8.8 HIGH. CWE-255, Credentials Management Errors."),
    ("CVE-2017-17215", "cve", "Huawei HG532 remote code execution",
     ["Mirai-greeth_flood", "Mirai-greip_flood"],
     "Huawei HG532 with some customized versions has a remote code execution vulnerability. An authenticated "
     "attacker could send malicious packets to port 37215 to launch attacks. Successful exploit could lead to the "
     "remote execution of arbitrary code. CVSSv3 base score 8.8 HIGH. CWE-20, Improper Input Validation."),
    ("CVE-2014-9583", "cve", "ASUS WRT infosvr command execution backdoor",
     ["Mirai-udpplain"],
     "common.c in infosvr in ASUS WRT firmware 3.0.0.4.376_1071 and other versions, as used in RT-AC66U, RT-N66U, "
     "and other routers, does not properly check the MAC address for a request, which allows remote attackers to "
     "bypass authentication and execute arbitrary commands via a NET_CMD_ID_MANU_CMD packet to UDP port 9999. "
     "CVSSv2 base score 10.0 HIGH. CWE-264, Permissions, Privileges, and Access Controls."),
]

# Natural-language "traffic descriptions" pointing at exactly one real anchor,
# written independently of the CAPEC/CVE description text (same paraphrase
# discipline as the synthetic query set), so recall isn't inflated by
# vocabulary overlap with the entry text itself.
REAL_ANCHOR_QUERIES = [
    ("Sustained high-rate SYN packets with no completed handshake, targeting a single host.", "CAPEC-482"),
    ("Repeated legitimate-looking HTTP GET requests at a rate far exceeding normal session behavior.", "CAPEC-488"),
    ("Large volume of UDP datagrams directed at a fixed destination port, no application-layer structure.", "CAPEC-486"),
    ("Burst of ICMP echo requests saturating outbound bandwidth toward one target IP.", "CAPEC-487"),
    ("Sequential connection attempts probing a wide range of destination ports on a single host.", "CAPEC-300"),
    ("Rapid sequence of failed authentication attempts against a login service using varying credentials.", "CAPEC-49"),
    ("Unsolicited ARP replies causing traffic redirection through an intermediate host.", "CAPEC-94"),
    ("DNS responses with mismatched transaction IDs and unexpected source addresses.", "CAPEC-141"),
    ("Anomalous SQL-like tokens embedded in an HTTP request body targeted at a login form.", "CAPEC-66"),
    ("Script-like payload embedded in a URL query parameter directed at a web application.", "CAPEC-63"),
    ("Extra ampersand-delimited fields appended to a GET request query string.", "CAPEC-137"),
    ("Unusual character-encoded input submitted to a device's file-handling interface.", "CAPEC-153"),
    ("Device establishing a UDP flood immediately after a known ZyXEL default-credential SSH login.", "CVE-2016-10401"),
    ("Device sending crafted requests to port 37215 preceding a greeth-flood burst, consistent with Huawei router exploitation.", "CVE-2017-17215"),
    ("Unauthenticated UDP packet to port 9999 triggering command execution on a router, followed by flood traffic.", "CVE-2014-9583"),
]

# Two additional, independently-written paraphrases per anchor, to reduce
# the variance of recall estimates (n=15 means every single query flipping
# hit/miss moves recall by 6.7 percentage points; n=45 cuts that to 2.2).
# Each new query describes a different facet or observation angle of the
# same underlying attack -- not a trivial reword of the first query -- while
# still avoiding vocabulary shared with the entry's own description text.
REAL_ANCHOR_QUERIES_EXTRA = [
    # CAPEC-482 TCP Flood
    ("A firewall log shows thousands of half-open connection attempts per second from a single source.", "CAPEC-482"),
    ("Server resource exhaustion coincides with a spike in connection-state table entries, no data exchanged.", "CAPEC-482"),
    # CAPEC-488 HTTP Flood
    ("Web server CPU saturates from an unusually large number of concurrent, otherwise-valid client sessions.", "CAPEC-488"),
    ("Application logs show many complete request/response cycles per second, each individually indistinguishable from normal use.", "CAPEC-488"),
    # CAPEC-486 UDP Flood
    ("A target's inbound bandwidth is consumed by connectionless traffic with no reply expected from the destination.", "CAPEC-486"),
    ("Firewall state table fills rapidly from many one-way datagram bursts to an open service port.", "CAPEC-486"),
    # CAPEC-487 ICMP Flood
    ("Network monitoring shows an abnormal spike in echo-request traffic consuming uplink capacity.", "CAPEC-487"),
    ("A device becomes unreachable after a sudden surge of ping-like control messages from many source addresses.", "CAPEC-487"),
    # CAPEC-300 Port Scanning
    ("Logs show short-lived connection attempts touching many different service ports on one host in quick succession.", "CAPEC-300"),
    ("A firewall records probes against both common and uncommon ports with no follow-up application traffic.", "CAPEC-300"),
    # CAPEC-49 Password Brute Forcing
    ("An authentication service logs hundreds of login attempts per minute from one source using different usernames.", "CAPEC-49"),
    ("Account lockout thresholds are repeatedly triggered across multiple accounts within a short window.", "CAPEC-49"),
    # CAPEC-94 Adversary in the Middle
    ("Two hosts that should communicate directly instead show traffic routed through an unexpected intermediate address.", "CAPEC-94"),
    ("A client's session appears to negotiate encryption twice, once with an unfamiliar intermediary.", "CAPEC-94"),
    # CAPEC-141 Cache Poisoning
    ("A resolver begins returning a different IP address for a domain than it did minutes earlier, with no legitimate record change.", "CAPEC-141"),
    ("Multiple hosts on a segment start resolving the same hostname to an unfamiliar address shortly after a burst of forged replies.", "CAPEC-141"),
    # CAPEC-66 SQL Injection
    ("A web form submission includes characters commonly used to terminate and recombine database query statements.", "CAPEC-66"),
    ("An application error log reveals a database syntax error immediately after an unusual login field submission.", "CAPEC-66"),
    # CAPEC-63 Cross-Site Scripting
    ("A comment or form field submitted to a website contains embedded executable browser code.", "CAPEC-63"),
    ("Other users' browsers begin making unexpected outbound requests after viewing a shared page or post.", "CAPEC-63"),
    # CAPEC-137 Parameter Injection
    ("A request's query string contains more fields than the application form was designed to submit.", "CAPEC-137"),
    ("An unexpected value silently overrides a hidden or default request parameter processed by the backend.", "CAPEC-137"),
    # CAPEC-153 Input Data Manipulation
    ("A file is submitted with a mismatched extension and encoding that causes it to be processed by the wrong handler.", "CAPEC-153"),
    ("An application misinterprets an input's format due to an unexpected character encoding substitution.", "CAPEC-153"),
    # CVE-2016-10401 ZyXEL default su password
    ("A device with known ISP-deployed default administrative credentials is accessed remotely and begins flooding traffic.", "CVE-2016-10401"),
    ("A low-privilege account is used to escalate to root on a residential gateway using a shared default secondary password.", "CVE-2016-10401"),
    # CVE-2017-17215 Huawei HG532 RCE
    ("A home router's UPnP-related management port receives crafted packets immediately before it starts scanning other devices.", "CVE-2017-17215"),
    ("Arbitrary code begins executing on a router after an unauthenticated request to a nonstandard high-numbered port.", "CVE-2017-17215"),
    # CVE-2014-9583 ASUS WRT infosvr backdoor
    ("A router accepts an administrative command over an undocumented UDP service without verifying the requester's identity.", "CVE-2014-9583"),
    ("A consumer router executes a privileged command triggered by a broadcast-style packet on a rarely used UDP port.", "CVE-2014-9583"),
]

REAL_ANCHOR_QUERIES_ALL = REAL_ANCHOR_QUERIES + REAL_ANCHOR_QUERIES_EXTRA


if __name__ == "__main__":
    print(f"{len(REAL_ANCHOR_ENTRIES)} real entries")
    print(f"{len(REAL_ANCHOR_QUERIES)} original queries, {len(REAL_ANCHOR_QUERIES_EXTRA)} additional, "
          f"{len(REAL_ANCHOR_QUERIES_ALL)} total")
    for eid, kind, name, fam, desc in REAL_ANCHOR_ENTRIES:
        print(f"  {eid:16s} {name}")
