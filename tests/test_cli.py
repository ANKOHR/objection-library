import json
from pathlib import Path
import subprocess
import sys
import time
import pytest
from objection_library.cli import main


def setup_fixture(tmp_path):
    folder, state = tmp_path / "input", tmp_path / "state.json"
    assert main(["fixtures", "--out", str(folder)]) == 0
    assert main(["--state", str(state), "run", "--input", str(folder)]) == 0
    return folder, state


def test_run_completes_on_fixture(tmp_path):
    start = time.perf_counter()
    _, state = setup_fixture(tmp_path)
    assert main(["--state", str(state), "report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    state = tmp_path / "state.json"
    assert main(["--state", str(state), "run", "--input", str(tmp_path)]) == 0
    assert main(["--state", str(state), "report"]) == 0
    assert "Records: 0" in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "records.jsonl").write_text('# comment\n{"broken":\n', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    text = capsys.readouterr().err
    assert "ParseError" in text and "records.jsonl" in text and "line 2" in text
    assert "Traceback" not in text


def test_determinism_byte_identical(tmp_path):
    folder, state = setup_fixture(tmp_path)
    first = state.read_bytes()
    assert main(["--state", str(state), "run", "--input", str(folder)]) == 0
    assert state.read_bytes() == first
    report = tmp_path / "report.json"
    args = ["--state", str(state), "report", "--format", "json", "--out", str(report)]
    assert main(args) == 0
    first = report.read_bytes()
    assert main(args) == 0
    assert first == report.read_bytes()


def test_cli_smoke_all_subcommands(tmp_path):
    _, state = setup_fixture(tmp_path)
    assert main(["--state", str(state), "responses", "--objection", "Budget"]) == 0
    assert main(["add", "--input", str(tmp_path / "real"), "--id", "r1", "--date", "2026-09-01", "--objection", "Budget"]) == 0
    for command in ("fixtures", "run", "report", "add", "responses"):
        completed = subprocess.run([sys.executable, "-m", "objection_library.cli", command, "--help"], capture_output=True, text=True)
        assert completed.returncode == 0
        assert "Example:" in completed.stdout


def test_report_write_failure_no_partial_files(tmp_path, capsys):
    _, state = setup_fixture(tmp_path)
    target = tmp_path / "destination"
    target.mkdir()
    assert main(["--state", str(state), "report", "--out", str(target)]) == 2
    assert "WriteOrReadError" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["destination", "input", "state.json"]


def test_missing_input_usage_hint(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_schema_error_file_line(tmp_path, capsys):
    (tmp_path / "records.jsonl").write_text('{"amount": -1}\n', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and "amount" in error and "line 1" in error


def test_five_record_hand_written_input(tmp_path):
    rows = [dict(id=f"h{i}", date="2026-09-01", synthetic=True, objection="Budget", response="Trial", outcome=outcome)
            for i, outcome in enumerate(["accepted", "accepted", "rejected", "pending", "untested"])]
    (tmp_path / "records.jsonl").write_text("# SYNTHETIC handwritten\n" + "\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    state = tmp_path / "state.json"
    assert main(["--state", str(state), "run", "--input", str(tmp_path)]) == 0
    assert json.loads(state.read_text())["counts"] == dict(accepted=2, rejected=1, pending=1, untested=1)


def test_corrupted_fixture_report_changes(tmp_path):
    folder, state = setup_fixture(tmp_path)
    source = folder / "records.jsonl"
    lines = source.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["outcome"] = "rejected"
    lines[1] = json.dumps(row)
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert main(["--state", str(state), "run", "--input", str(folder)]) == 0
    report = tmp_path / "report.json"
    assert main(["--state", str(state), "report", "--format", "json", "--out", str(report)]) == 0
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["counts"]["accepted"] == 49
    assert result["counts"]["rejected"] == 51
    assert "s000" not in result["accepted_record_ids"]


def test_state_schema_error_named(tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text('{"records":false,"as_of":"2026-10-01","input_source":"demo"}', encoding="utf-8")
    assert main(["--state", str(state), "report"]) == 2
    assert "SchemaError" in capsys.readouterr().err


def test_invalid_input_preserves_existing_state(tmp_path):
    folder, state = setup_fixture(tmp_path)
    before = state.read_bytes()
    (folder / "records.jsonl").write_text("bad json\n", encoding="utf-8")
    assert main(["--state", str(state), "run", "--input", str(folder)]) == 2
    assert state.read_bytes() == before
