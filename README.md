# Objection Library

`ol` accumulates objections and recorded response trials from explicit local inputs. Henry can review which responses were accepted, rejected, pending or untested, with every count traced to record IDs. Exact text defines a group: the tool does not infer semantic similarity, causality, likely success, demand or qualification.

Hypothesis: deterministic counting with planted ground truth can make this narrow workflow trustworthy. Acceptance: 200 labelled synthetic records, exact counts, all planted accepted cases found with zero false positives, byte-identical repeated outputs and a fixture demo under five seconds. These are local engineering checks, not evidence of business value.

## Quickstart

Python 3.10 or later, CPU only, no runtime dependencies. No network or language-model calls occur in the application. Install locally with existing setuptools and pip:

```powershell
python -m pip install --no-deps --no-build-isolation -e .
ol fixtures --out demo
ol run --input demo
ol report --format md
python -m pytest -q
```

The equivalent source invocation is `python -m objection_library.cli`. The demo folder must be new; fixture generation refuses to overwrite existing fixture files. State defaults to `.ol/results.json`. Specify `--state PATH` before the subcommand for an isolated state file. Run writes a snapshot; later edits to input require another run. Report revalidates and recomputes the snapshot's records, ignoring stored aggregate figures.

On Windows, if the user Python Scripts directory is absent from PATH, add the directory printed by `python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"` to PATH, or use the equivalent module invocation. For an explicitly offline installation, set `PIP_NO_INDEX=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1` before the install command.

The smallest handwritten example is `examples/tiny/records.jsonl`, containing five labelled synthetic records. Run `ol run --input examples/tiny` then `ol report`. Empty directories are valid zero-record inputs. A populated directory missing `records.jsonl` is an error.

## Input format

Only UTF-8 `records.jsonl` is accepted. Each nonblank, noncomment line is one JSON object. Lines starting with `#` after whitespace are comments. JSON, CSV and YAML files are not supported input formats; convert them explicitly to this schema. Other files in a directory are supplementary and are not parsed. Unknown fields are rejected, including amounts, so negative amounts cannot be silently counted or used to imply savings.

```json
{"id":"r1","synthetic":false,"date":"2026-09-30","objection":"Budget","response":"Offer scoped trial","outcome":"accepted"}
```

All six fields are mandatory:

| Field | Rule |
| --- | --- |
| id | Unique nonblank string, at most 200 characters, exact comparison |
| synthetic | Boolean; true for illustrative data, false only for Henry's manually entered real data |
| date | Canonical YYYY-MM-DD, no later than the explicit as-of cutoff |
| objection | Nonblank exact text, at most 10,000 characters |
| response | String up to 10,000 characters; may be blank only for untested records |
| outcome | accepted, rejected, pending or untested |

A record represents one objection occurrence and its response outcome. Repeat trials require distinct IDs. Accepted means the operator recorded acceptance; rejected means recorded rejection. Pending is an attempted response awaiting outcome. Untested means no completed or pending trial. Completed tests equal accepted plus rejected. There are no computed success estimates. Do not enter a second record for a pending trial's resolution: update that original record's outcome and rerun. Dates and grouping are not normalized. Unicode, newlines inside JSON strings and Windows path text are supported. Control characters other than newline and tab, em dashes, duplicate IDs, overlong strings, future dates and schema drift are errors. Input validation is all-or-nothing; invalid records are never silently dropped.

The as-of default is fixed at 2026-10-01 to keep repeated runs deterministic. Use `--as-of YYYY-MM-DD` to advance the cutoff for real work. No random generator is used, so no seed is needed. Source path and cutoff are explicit report inputs; byte identity assumes the same input path, content and arguments.

## Subcommands

| Command | Example | Behavior |
| --- | --- | --- |
| fixtures | `ol fixtures --out demo` | Write labelled 200-record fixture and independent expectations |
| run | `ol run --input demo --as-of 2026-10-01` | Validate, compute and atomically replace state |
| report | `ol report --format json --out report.json` | Render md or json with provenance |
| add | `ol add --input my-data --id r1 --date 2026-09-30 --objection Budget --response "Scoped trial" --outcome accepted` | Validate and append a manually recorded occurrence |
| responses | `ol responses --objection Budget` | Show exact-match response groups from the last snapshot |

Every command provides `--help` and an example. `add` defaults to a real-data declaration; pass `--synthetic` for hypothetical or illustrative inputs. `responses` retains snapshot-wide totals and provenance, while its response section includes only the requested objection. No fuzzy match occurs. Run/report never modify source data. Add replaces the input file atomically after validating the full revised dataset; supplementary comments are not preserved. One writer at a time is required; concurrent modifications are not supported.

## Architecture

```text
records.jsonl -> cli.read_records -> core.validate -> core.analyze
                                                   |
                                                   v
                                            .ol/results.json
                                                   |
                                         core recomputation
                                                   |
                                                   v
                                          report -> md / json
fixtures -> labelled input + independent expectations
```

Core has no I/O. CLI owns UTF-8 parsing and atomic file replacement. Reports include record IDs, input source (JSON snapshot), cutoff and provenance counts. The markdown response groups expose all counted IDs. Fixture expectations are not read by the workflow.

## Honesty boundary and fixture labelling

All figures are counts of supplied records. Recorded outcomes are not independently verified. `synthetic: false` is a declaration by the operator, not proof of authenticity. Each report states real and synthetic counts, including mixed and empty input. Time saved and money saved are always labelled unmeasured because this version accepts no measured baseline. Hypothetical or illustrative benefits are not computed or represented as measured outcomes.

Synthetic JSONL starts with a header comment and every record has `synthetic: true`. Expectations JSON carries `synthetic: true` and a synthetic label, since standard JSON cannot carry a header comment. Fixture Markdown has a synthetic header comment. The handwritten example follows the same policy. Trials from Henry's real operation are not shipped.

The 200 records have four objection groups of 50. Outcomes rotate in cycles of four: accepted, rejected, pending, untested. Each outcome totals 50; completed tests total 100. Blocks 1 and 3 contain 13 accepted, 13 rejected, 12 pending and 12 untested. Blocks 2 and 4 contain 12 accepted, 12 rejected, 13 pending and 13 untested. Accepted IDs are s000, s004, ..., s196. The expectations file expresses this hand arithmetic independently of the engine. Tests corrupt a recorded outcome and verify that counts change.

## Failure modes

Errors return exit code 2 without a traceback. Malformed JSONL produces ParseError with filename, line and column. Missing input produces MissingInput with usage guidance. SchemaError names the offending fields and input line. File access and report write failures produce WriteOrReadError. State/report/input replacement is atomic, and temporary files are removed on failure; an existing output stays intact if replacement fails. Fixture generation is atomic per file, not transactional across all three files, so a disk failure may leave completed fixture files. Remove or move that incomplete fixture directory before retrying.

Limits: exact text splits paraphrases; manual outcomes can be wrong; repeated contacts may not be independent; no causal evidence follows from acceptance counts. This version supports small local datasets and no simultaneous writers. Keep source inputs backed up before editing trials. Counts alone cannot prove demand.

## Evidence-based improvement and verdict

The two-week real-use window starts on Henry's first real run, not on build completion. Log run date, whether the output informed an outreach decision, and a hand-checked sample of record IDs with their expected group and outcome. Measure core error rate as incorrectly counted or grouped sampled records divided by sampled records. Also record the number of days used. Do not report a rate for an empty sample. Record measured manual and CLI elapsed times for the same task before claiming time saved.

After two weeks, if error rate exceeds 10 percent, fix the top evidenced failure cause and recheck, or kill with a recorded reason. If unused, kill. Otherwise record one evidence-based improvement. Verdict is **pending evidence**, not a fabricated business conclusion. In `EVIDENCE.md`, record expand for daily use or revenue, integrate for substantial sibling overlap, commercialise for an evidenced willing buyer, maintain for portfolio evidence, or kill for no use or failed acceptance. No real-use finding or final verdict is claimed at build time.
