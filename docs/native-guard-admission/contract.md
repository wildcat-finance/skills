# Audit applicability declaration

This describes the accepted `protasis-audit-applicability/v1` design.
Step 2 checks source witnesses and their existing target routes. Fiat capture,
replay and execution conformance remain due in Steps 3 and 4.

## Closed fields

One isolated column-zero `audit-applicability` JSON fence may appear in the
study. Absence means no attempted marker exists; malformed, indented,
duplicate, partial or unterminated markers must refuse. The object has exactly
`schema`, `source_views` and `entries`.

Each source view carries `id`, `path`, `source_sha256` and `view_sha256`.
The complete set must equal the checked known-failure inventory, including
its explicit no-known claim when empty. Each entry has exactly `id`,
`source_ref`, `source_span`, `source_status`, `disposition`, `rationale`,
`finding_id`, `criterion_id` and `tracking`.

Entry ids are unique kebab-case strings. Split `source_ref` at its first
colon: its prefix equals one source id, and its non-empty opaque suffix keeps
the original finding or lead locator. `source_span` has only `start_byte`,
`end_byte` and `sha256`, selecting a non-empty UTF-8 interval of the
authoritative source. The end offset is exclusive. Booleans are not offsets.
`source_status` is exact text occurring in that span, or null for unknown
status. `rationale` retains the reviewer's judgment and qualifications.
`tracking` lists canonical GitHub issue URLs; the checker neither opens them
nor infers current issue status.

## Four dispositions

| Disposition | Required target | Evidence still owed |
| --- | --- | --- |
| `local-regression` | Captured `finding_id`; null `criterion_id` | Existing parent assertion failure and final green evidence |
| `integration-requirement` | Joined `criterion_id`; null `finding_id` | Actual controller-observed execution at its consuming step |
| `historical` | Both ids null | Original repair status and its limits, with no current success |
| `out-of-scope` | Both ids null | Unchanged boundary and existing tracking, with no current success |

The captured regression set must appear exactly once. Several source concerns
may share one criterion; unreferenced ordinary criteria remain valid.
The owning capture or descriptor supplies the step and command. Entries
cannot supply another command or step.

A status witness establishes cited bytes, not the truth of a repair, the
adequacy of a rationale or source-reading completeness. Open upstream status
remains open even when a later target demonstrates a mitigation.

## Bounds and custody

Documents are at most 256 KiB; declarations carry at most 32 source/view pairs
and 128 entries. Rationale and source reference are at most 4,096 UTF-8 bytes;
status is at most 1,024 bytes; each entry has at most eight tracking URLs.
Spans are at most 64 KiB, source/view files at most 2 MiB each, and their
aggregate at most 16 MiB. Duplicate keys, non-finite numbers, aliases,
links, replaced or unstable files and overflow refuse.

`load_checked_applicability(study_path, runbook_path, repository_root)` returns
an immutable `ApplicabilityLoadResult`: `status`, canonical `capture_bytes`
or null, and a tuple of fixed-code findings. The `capture` property returns a
fresh JSON projection; changing that projection leaves the result unchanged.
The parser runs no declared command and writes no controller state. A clean
result binds declaration/document digests, the checked inventory and criterion
join digests, source views, unchanged entries and derived routes. Each route
has `entry_id`, `owner`, `binding` and `binding_sha256`. The owner is
`known-failure`, `success-criteria` or null; the binding is the existing
checked finding or joined criterion, or null for an inert row. Canonical
applicability JSON uses sorted ASCII keys, compact separators and one final LF.
Fiat will freeze the complete
semantics at admission, retain historical receipt bytes and use existing
criteria execution for integration requirements. Changes to classifications
require a fresh reviewed run. A zero exit never proves criterion adequacy.

## Synthetic fixture boundary

`fixtures/source.md` and `fixtures/source-view.md` are authored specimens,
not imported audits or a checked synopsis. `fixtures/applicability.json`
illustrates the declaration shape; `fixtures/targets.json` identifies the
synthetic regression and criterion it names, without asserting either has
executed. The provenance manifest binds these bytes. Fixture tests check
shape, exact spans, source statuses and custody only. They do not admit a
known-failure inventory or establish parser conformance.

## Refusal interface

Parser findings carry only `code`, a fixed `field` and a numeric `row` or
null. A000 names document or secure-read failure; A001 a fence; A002 strict
JSON/schema; A003 the checked inventory; A004 source/view equality; A005 row
shape; A006 a source/span/status witness; A007 regression routing; A008 the
criterion join; A009 final input stability. Restore the named input and rerun.
These codes contain no source text.

`proof.py` accepts only the three reviewed candidate ids and six conformance
criterion ids. The selected candidate now runs `applicability-parser` and
`bounded-reader`. Other operations return bounded JSON identifying `candidate`,
`criterion`, `code`, `available_step` and `report_written: false`. Exit 2 and
`operation-unavailable` mean the requested proof has no implementation yet.
Malformed arguments use `invalid-arguments`; occupied leaves use
`report-exists`; invalid paths use `report-path-invalid`; filesystem
inspection errors use `report-path-unavailable`. Recover by correcting the
operand or waiting for the named implementation step. No refusal is a
successful design report.

A successful resolver writes an exclusive `protasis-design-report/v1` and
an evidence companion named `<report-stem>.evidence.json`, evidence first.
The companion binds the design-report digest, inspected source digests,
executed test counts and any budget observations. Existing leaves are never
replaced. A failure after the first write may leave a companion to inspect;
retry with a fresh report path. Source drift uses `proof-source-drift`; a
changed report directory uses `report-path-changed`. A failed exercised proof
records `value: false` and exits 1. Neither result executes a declared Exit
or supplies a Fiat receipt.
