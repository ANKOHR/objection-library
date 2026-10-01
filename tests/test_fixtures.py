import json
from objection_library.fixtures import fixture_files, fixture_records, expectations
from objection_library.core import analyze


def test_fixtures_labelled_synthetic():
    files = fixture_files()
    assert files["records.jsonl"].startswith("# SYNTHETIC")
    assert all(row["synthetic"] is True for row in fixture_records())
    assert json.loads(files["expectations.json"])["synthetic"] is True
    assert "SYNTHETIC" in files["README.md"]


def test_fixture_ground_truth_matches_hand_computed():
    result, expected = analyze(fixture_records(), "2026-10-01"), expectations()
    for key in ("total", "tested", "counts", "provenance_counts", "accepted_record_ids"):
        assert result[key] == expected[key]
    pairs = {p["objection"]: p["counts"] for p in result["pairs"]}
    for objection, counts in zip(["Budget", "Timing", "Existing supplier", "No need"], expected["pair_counts"]):
        assert pairs[objection] == counts
