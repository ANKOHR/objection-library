"""Local file CLI. Input contract is records.jsonl with optional # comments."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile

from .core import SchemaError, analyze, validate
from .fixtures import fixture_files
from .report import render


class InputError(ValueError):
    pass


def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def read_records(directory, as_of):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use ol fixtures --out <dir> or create an input directory")
    path = directory / "records.jsonl"
    if not path.exists():
        if any(directory.iterdir()):
            raise InputError(f"MissingInput: {path}: expected records.jsonl; JSON, CSV and YAML are not input formats")
        return []
    rows, seen = [], set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise InputError(f"ParseError: {path}: line {number}, column {error.colno}: {error.msg}") from None
        try:
            row = validate(row, as_of)
            if row["id"] in seen:
                raise SchemaError(f"id: duplicate {row['id']!r}")
            seen.add(row["id"])
        except SchemaError as error:
            raise InputError(f"SchemaError: {path}: line {number}: {error}") from None
        rows.append(row)
    return rows


def parser():
    root = argparse.ArgumentParser(description="Accumulate objections and recorded response trials from local files.")
    root.add_argument("--state", default=".ol/results.json", help="Results file (default .ol/results.json)")
    commands = root.add_subparsers(dest="command", required=True)
    fixtures = commands.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: ol fixtures --out demo")
    fixtures.add_argument("--out", required=True)
    run = commands.add_parser("run", help="Validate input and compute recorded counts", epilog="Example: ol run --input demo --as-of 2026-10-01")
    run.add_argument("--input", required=True)
    run.add_argument("--as-of", default="2026-10-01", help="Explicit date cutoff; fixed default 2026-10-01 for reproducibility")
    report = commands.add_parser("report", help="Render results with provenance", epilog="Example: ol report --format md")
    report.add_argument("--format", choices=["md", "json"], default="md")
    report.add_argument("--out", help="Atomically write report instead of stdout")
    add = commands.add_parser("add", help="Add an objection or recorded response trial", epilog='Example: ol add --input my-data --id r1 --date 2026-09-30 --objection Budget --response "Scoped trial" --outcome accepted')
    add.add_argument("--input", required=True)
    for field in ("id", "date", "objection"):
        add.add_argument("--" + field, required=True)
    add.add_argument("--response", default="")
    add.add_argument("--outcome", choices=["accepted", "rejected", "pending", "untested"], default="untested")
    add.add_argument("--synthetic", action="store_true", help="Label manually entered illustrative data synthetic")
    add.add_argument("--as-of", default="2026-10-01")
    responses = commands.add_parser("responses", help="Show recorded trials for an exact objection", epilog='Example: ol responses --objection Budget')
    responses.add_argument("--objection", required=True)
    return root


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            target = Path(args.out)
            names = fixture_files()
            if any((target / name).exists() for name in names):
                raise InputError(f"WriteError: {target}: fixture files already exist; choose a new directory")
            for name, content in names.items():
                atomic_write(target / name, content)
            print("Generated 200 SYNTHETIC records; expectations are hand-computed.")
        elif args.command in ("run", "add"):
            try:
                date.fromisoformat(args.as_of)
            except ValueError:
                raise InputError("SchemaError: as-of: expected YYYY-MM-DD") from None
            if args.command == "add":
                row = {field: getattr(args, field) for field in ("id", "date", "objection", "response", "outcome", "synthetic")}
                validate(row, args.as_of)
                directory = Path(args.input)
                rows = read_records(directory, args.as_of) if directory.exists() else []
                analyze(rows + [row], args.as_of)
                text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows + [row])
                atomic_write(directory / "records.jsonl", text)
                print("Added record declared " + ("SYNTHETIC." if args.synthetic else "real, entered by Henry."))
            else:
                result = analyze(read_records(args.input, args.as_of), args.as_of)
                result["input_source"] = Path(args.input).as_posix()
                atomic_write(args.state, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
                print(f"Computed {result['total']} records: {result['provenance_counts']['synthetic']} SYNTHETIC, {result['provenance_counts']['real']} declared real. Benefits unmeasured.")
        else:
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}: run ol run --input <dir> first")
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise InputError(f"ParseError: {path}: line {error.lineno}: {error.msg}") from None
            if not isinstance(stored, dict) or not {"records", "as_of", "input_source"} <= stored.keys():
                raise InputError(f"SchemaError: {path}: required fields records, as_of, input_source")
            if not isinstance(stored["records"], list) or not isinstance(stored["as_of"], str):
                raise InputError(f"SchemaError: {path}: records must be a list and as_of a date string")
            try:
                date.fromisoformat(stored["as_of"])
                result = analyze(stored["records"], stored["as_of"])
            except (SchemaError, ValueError) as error:
                raise InputError(f"SchemaError: {path}: {error}") from None
            result["input_source"] = stored["input_source"]
            if args.command == "responses":
                result["pairs"] = [p for p in result["pairs"] if p["objection"] == args.objection]
                print(render(result, "md"), end="")
            else:
                output = render(result, args.format)
                if args.out:
                    atomic_write(args.out, output)
                else:
                    print(output, end="")
        return 0
    except (InputError, SchemaError, OSError, UnicodeError, TypeError, KeyError, ValueError) as error:
        prefix = "WriteOrReadError: " if isinstance(error, (OSError, UnicodeError)) else ""
        print(prefix + str(error).replace("\u2014", "-"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
