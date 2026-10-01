"""Deterministic reports with provenance and unmeasured benefit labels."""
import json


def banner(result):
    p = result["provenance_counts"]
    return (f"Data provenance: {p['real']} real records (Henry's own data, entered by him, "
            f"as declared by input); {p['synthetic']} SYNTHETIC fixture records. "
            "Outcomes are recorded observations, not predictions; declarations are not independently verified.")


def render(result, format):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result}, ensure_ascii=False,
                          indent=2, sort_keys=True) + "\n"
    lines = ["# Objection Library", "", banner(result), "", f"As of: {result['as_of']}",
             f"Records: {result['total']}", f"Completed tests: {result['tested']}"]
    if "input_source" in result:
        lines.insert(4, "Input source: " + json.dumps(result["input_source"], ensure_ascii=False))
    lines += [f"{key.capitalize()}: {value}" for key, value in sorted(result["counts"].items())]
    lines += ["", "Time saved: unmeasured (no measured baseline supplied).",
              "Money saved: unmeasured (no measured baseline supplied).", "",
              "Illustrative or hypothetical benefit figures are not computed.", "", "## Recorded responses"]
    for pair in result["pairs"]:
        # JSON quoting preserves arbitrary multiline text without injecting Markdown structure.
        lines += ["", "Objection: " + json.dumps(pair["objection"], ensure_ascii=False),
                  "Response: " + json.dumps(pair["response"], ensure_ascii=False),
                  ", ".join(f"{k}={v}" for k, v in sorted(pair["counts"].items())),
                  "Record IDs: " + ", ".join(pair["record_ids"])]
    return "\n".join(lines) + "\n"
