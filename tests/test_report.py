import json
from objection_library.core import analyze
from objection_library.fixtures import fixture_records, expectations
from objection_library.report import render


def test_report_matches_ground_truth_exact():
    report = json.loads(render(analyze(fixture_records(), "2026-10-01"), "json"))
    for key in ("total", "tested", "counts", "provenance_counts", "accepted_record_ids"):
        assert report[key] == expectations()[key]


def test_report_zero_false_positives():
    report = analyze(fixture_records(), "2026-10-01")
    actual, expected = set(report["accepted_record_ids"]), set(expectations()["accepted_record_ids"])
    assert actual - expected == set()
    assert expected - actual == set()


def test_report_carries_provenance_banner():
    rows = fixture_records()[:2]
    rows[0]["synthetic"] = False
    for fmt in ("md", "json"):
        text = render(analyze(rows, "2026-10-01"), fmt)
        assert "1 real records" in text and "1 SYNTHETIC" in text
        assert "entered by him" in text


def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        text = render(analyze([], "2026-10-01"), fmt)
        assert "unmeasured" in text and "baseline" in text


def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert "\u2014" not in render(analyze(fixture_records(), "2026-10-01"), fmt)
