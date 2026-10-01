"""Pure validation and counting. Rates describe recorded trials, never predictions."""
from datetime import date


class SchemaError(ValueError):
    """An input field violates the documented schema."""


FIELDS = {"id", "synthetic", "date", "objection", "response", "outcome"}
OUTCOMES = {"accepted", "rejected", "pending", "untested"}


def validate(record, as_of):
    if not isinstance(record, dict):
        raise SchemaError("record: expected object")
    missing, extra = FIELDS - record.keys(), record.keys() - FIELDS
    if missing or extra:
        raise SchemaError(f"fields: missing={sorted(missing)}, unknown={sorted(extra)}")
    for field, limit in (("id", 200), ("objection", 10000), ("response", 10000)):
        value = record[field]
        if not isinstance(value, str) or len(value) > limit or (field != "response" and not value.strip()):
            raise SchemaError(f"{field}: expected nonblank string up to {limit} characters")
        if any(ord(c) < 32 and c not in "\n\t" for c in value):
            raise SchemaError(f"{field}: control characters forbidden")
        if "\u2014" in value:
            raise SchemaError(f"{field}: em dash forbidden; use a hyphen")
    if type(record["synthetic"]) is not bool:
        raise SchemaError("synthetic: expected boolean")
    try:
        parsed = date.fromisoformat(record["date"])
        cutoff = date.fromisoformat(as_of)
        if parsed.isoformat() != record["date"] or parsed > cutoff:
            raise ValueError()
    except (ValueError, TypeError):
        raise SchemaError("date: expected YYYY-MM-DD no later than as-of") from None
    if not isinstance(record["outcome"], str) or record["outcome"] not in OUTCOMES:
        raise SchemaError("outcome: expected accepted, rejected, pending, or untested")
    if record["outcome"] != "untested" and not record["response"].strip():
        raise SchemaError("response: required for recorded trial")
    return dict(record)


def analyze(records, as_of):
    rows, seen = [], set()
    for raw in records:
        row = validate(raw, as_of)
        if row["id"] in seen:
            raise SchemaError(f"id: duplicate {row['id']!r}")
        seen.add(row["id"])
        rows.append(row)
    rows.sort(key=lambda r: r["id"])
    counts = {key: sum(r["outcome"] == key for r in rows) for key in sorted(OUTCOMES)}
    pairs = []
    for objection, response in sorted({(r["objection"], r["response"]) for r in rows}):
        subset = [r for r in rows if (r["objection"], r["response"]) == (objection, response)]
        tally = {key: sum(r["outcome"] == key for r in subset) for key in sorted(OUTCOMES)}
        pairs.append({"objection": objection, "response": response, "counts": tally,
                      "record_ids": [r["id"] for r in subset]})
    return {"as_of": as_of, "total": len(rows), "counts": counts,
            "tested": counts["accepted"] + counts["rejected"],
            "provenance_counts": {"real": sum(not r["synthetic"] for r in rows),
                                  "synthetic": sum(r["synthetic"] for r in rows)},
            "accepted_record_ids": [r["id"] for r in rows if r["outcome"] == "accepted"],
            "pairs": pairs, "records": rows,
            "unmeasured": {"time_saved": "unmeasured: no measured baseline supplied",
                           "money_saved": "unmeasured: no measured baseline supplied"}}
