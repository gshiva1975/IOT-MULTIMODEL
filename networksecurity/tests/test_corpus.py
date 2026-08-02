"""Sanity checks on the reference corpus itself. No network needed -- these
just check internal consistency, not that the IDs are real (that was
verified by hand against MITRE/NVD when each entry was added; see
corpus.py's module docstring)."""

from networksecurity.corpus import CVE_CORPUS, known_reference_map, generic_ids, wrong_family_ids


def test_all_capec_entries_have_required_fields():
    for e in CVE_CORPUS["capec_entries"]:
        assert e["capec_id"].startswith("CAPEC-")
        assert e["attack_families"], f"{e['capec_id']} has no attack_families"
        assert e["source_url"].startswith("https://capec.mitre.org/")


def test_all_cve_entries_have_required_fields():
    for e in CVE_CORPUS["entries"]:
        assert e["cve_id"].startswith("CVE-")
        assert e["attack_families"]
        assert e["source_url"].startswith("https://nvd.nist.gov/")


def test_no_id_appears_in_both_generic_and_wrong_family():
    overlap = generic_ids() & wrong_family_ids()
    assert not overlap, f"IDs marked both generic and wrong-family: {overlap}"


def test_known_reference_map_covers_all_capec_and_cve_ids():
    known = known_reference_map()
    for e in CVE_CORPUS["capec_entries"]:
        assert e["capec_id"] in known
    for e in CVE_CORPUS["entries"]:
        assert e["cve_id"] in known


def test_no_duplicate_capec_ids():
    ids = [e["capec_id"] for e in CVE_CORPUS["capec_entries"]]
    assert len(ids) == len(set(ids)), "duplicate CAPEC IDs in capec_entries"
