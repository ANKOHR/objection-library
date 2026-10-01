"""Labelled synthetic fixtures; no randomness or inferred outcomes."""
import json


def fixture_records():
    rows = []
    for i in range(200):
        group = i // 50
        rows.append({"id": f"s{i:03d}", "synthetic": True, "date": "2026-09-01",
                     "objection": ["Budget", "Timing", "Existing supplier", "No need"][group],
                     "response": ["Offer scoped trial", "Ask for review date", "Offer comparison", "Ask qualification question"][group],
                     "outcome": ["accepted", "rejected", "pending", "untested"][i % 4]})
    return rows


def expectations():
    # Hand arithmetic: 200 / 4 = 50 each. Each block of 50 has 12 full cycles
    # and 2 remainder records. Alternating blocks start at accepted or pending.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth",
            "total": 200, "tested": 100,
            "counts": {"accepted": 50, "rejected": 50, "pending": 50, "untested": 50},
            "provenance_counts": {"real": 0, "synthetic": 200},
            "accepted_record_ids": [f"s{i:03d}" for i in range(0, 200, 4)],
            "pair_counts": [{"accepted": 13, "rejected": 13, "pending": 12, "untested": 12},
                            {"accepted": 12, "rejected": 12, "pending": 13, "untested": 13},
                            {"accepted": 13, "rejected": 13, "pending": 12, "untested": 12},
                            {"accepted": 12, "rejected": 12, "pending": 13, "untested": 13}]}


def fixture_files():
    return {"records.jsonl": "# SYNTHETIC: labelled demonstration data\n" + "".join(
        json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in fixture_records()),
        "expectations.json": json.dumps(expectations(), indent=2, sort_keys=True) + "\n",
        "README.md": "<!-- SYNTHETIC -->\n# Synthetic fixtures\nAll 200 records are synthetic. Expectations use hand arithmetic, not the engine.\n"}
