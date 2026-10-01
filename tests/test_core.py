import pytest
from objection_library.core import analyze, SchemaError
from objection_library.fixtures import fixture_records


@pytest.mark.parametrize("change", [
    {"id": ""}, {"synthetic": 1}, {"date": "2099-01-01"}, {"date": "bad"},
    {"amount": -1}, {"outcome": "won"}, {"objection": "x" * 10001},
    {"response": ""}, {"id": "x\x00"}, {"objection": "bad\u2014text"},
])
def test_rejects_adversarial_values(change):
    with pytest.raises(SchemaError):
        analyze([{**fixture_records()[0], **change}], "2026-10-01")


def test_duplicate_ids():
    with pytest.raises(SchemaError, match="duplicate"):
        analyze([fixture_records()[0]] * 2, "2026-10-01")


def test_handles_unicode_and_long_inputs():
    row = {**fixture_records()[0], "objection": "预算 café " + "a" * 9000,
           "response": "C:\\Users\\henry\\data 你好"}
    assert analyze([row], "2026-10-01")["records"] == [row]


def test_corrupted_ground_truth_changes_computed_figures():
    rows = fixture_records()
    before = analyze(rows, "2026-10-01")
    rows[0]["outcome"] = "rejected"
    after = analyze(rows, "2026-10-01")
    assert after["counts"]["accepted"] == before["counts"]["accepted"] - 1
    assert after["counts"]["rejected"] == before["counts"]["rejected"] + 1
