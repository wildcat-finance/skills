# Audit applicability declaration

This describes the accepted `protasis-audit-applicability/v1` design.
Step 1 publishes its vocabulary and synthetic examples. Parser, capture,
replay and execution conformance remain pending.

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

The parser will return absent, refused or clean without running commands or
writing controller state. A clean result binds declaration/document digests,
source views, entries and derived routes. Fiat will freeze the complete
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

`proof.py` accepts only the three reviewed candidate ids and six conformance
criterion ids. Its bounded JSON answer identifies `candidate`, `criterion`,
`code`, `available_step` and `report_written: false`. Exit 2 and
`operation-unavailable` mean the requested proof has no implementation yet.
Malformed arguments use `invalid-arguments`; occupied leaves use
`report-exists`; invalid paths use `report-path-invalid`; filesystem
inspection errors use `report-path-unavailable`. Recover by correcting the
operand or waiting for the named implementation step. No refusal is a
successful design report.
