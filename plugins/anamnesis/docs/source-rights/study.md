# Retain source rights at the release boundary

Assumptions, unless corrected: the maintainer's corrected scope on issue #1364
is the authority for this new run; its six-field preimage and three replacement
release ids are intentional. Existing source policies remain the recorded
rights decisions. Their truth and legal sufficiency are not established here.
The current run starts afresh; no receipt from the lost run is evidence.

## 1. Problem, user and proving path

A release consumer sees each source's disclosure class but loses its admitted
basis and decision reference. At base `7952eafa337f5ba1c4f45417ceb154673f629c1c`,
`MANIFEST_SOURCE_KEYS` contains only `id`, `sha256`, `bytes` and `disclosure`.
`release_id` hashes the curation policy, `id:sha256:bytes` per sorted source,
then the five graph components. It does not hash the manifest or disclosure.

The prototype retains `basis` and `rights_sha256` beside `disclosure` in every
manifest source row. `rights_sha256` is the lowercase SHA-256 of the existing
`canonical(rights)` byte form: sorted keys, two-space indentation, final newline,
UTF-8. It binds the complete checked rights object: `basis`, `disclosure`,
`holder` and `statement`. Holder and statement text stay outside the release.

The source preimage becomes `id:sha256:bytes:disclosure:basis:rights_sha256`,
with the existing source order, policy bytes and graph-component order retained.
Admission computes the digest from the object it checked. Build and verify
require the six fields, recognised basis and disclosure, and a 64-character
lowercase hexadecimal rights digest. Missing or malformed rights metadata must
produce a named refusal before a release or projection is accepted. Embargoed
sources and digest-only/public combinations remain refused.

Success means the full Anamnesis suite passes with negative cases for missing
and malformed fields; changing any of the four rights fields changes identity;
changing disclosure, basis or decision digest under an unchanged release id
refuses; restricted-source findings remain withheld and counted; and pilot,
estate and synopsis rebuild twice with new ids and unchanged graph semantics.
Only manifest rows, identity-bearing projections and current references move.
Historical evidence retains its original ids.

Fiat controls the final demonstration. Run `python3 -m unittest discover -s
plugins/anamnesis/tests -t plugins/anamnesis`, then, for each of `pilot`,
`estate`, `synopsis`, run `python3
plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen
plugins/anamnesis/specimens/NAME` and `verify-rebuild --specimen
plugins/anamnesis/specimens/NAME --report .hexaemeron/reports/NAME-rebuild.json`
with the same program prefix and fresh report destinations. These are bounded
positive observations on three specimens. The new mutation tests supply the
negative observations; neither establishes general legal authority or corpus
completeness. Run the checked repository runner with Anamnesis and root scope
before each delivery gate.

## 2. Prior art and unresolved work

[The corrected scope](https://github.com/wildcat-finance/skills/issues/1364#issuecomment-5737529213)
was read in full. Admission refusals already ship under `A012`, `A030`, `A031`,
`A032`, `A033`, and existing consumer tests cover restriction and withholding.
ADR-003 supplies the recorded-basis boundary. This run repairs release custody.

The latest subject delivery and its final step,
[PR #1518](https://github.com/wildcat-finance/skills/pull/1518) and
[PR #1516](https://github.com/wildcat-finance/skills/pull/1516), were read in full.
They deliver exact mapper resolution, a synopsis corpus, projection scope and
bounded row parsing. Their open separator loss is
[issue #1517](https://github.com/wildcat-finance/skills/issues/1517), outside this
rights-only change. Their immutable study's line-509 qualifier remains historical
prose. The held per-source mapper/second-producer work remains open. Historical
statements that earlier releases did not move remain true of those deliveries.

The whole-set `audit_synopsis.py --check .` exited zero on this base. The four
Anamnesis source records below were read through their verified sibling synopsis
files, rather than read directly. Those views retain all finding ids and statuses,
Covered, Not checked, Elenchus verdict and Leads not pursued. No legacy unknown
is converted into a passing result.

| Authoritative source under `audit/rounds/` | Reading and disposition |
| --- | --- |
| `fiat-anamnesis-source-bound-curation-and-release-of-a.md` | All 10 rounds via `.synopsis.md`; preserve duplicate-key, manifest-recomputation, checked-byte reuse, regular-file, disclosure and schema guards. Source/read and publication races remain the recorded narrower guarantee; no race-hardening claim. |
| `fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md` | All 7 rounds via `.synopsis.md`; preserve no-empty-suite and complete-prose-sweep guards. No Synkrisis admission or new consumer is claimed; historical corrected-rendering and runner-exit documentation limits remain. |
| `fiat-1351-anamnesis-2-declared-corpus-scope.md` | All 7 rounds via `.synopsis.md`; keep scope/source agreement and estate provenance constraints. Use caller-named fresh reports and a fixed specimen list, avoiding the resolver-overwrite and grep-count defects. Existing schema/runtime drift exposure is addressed for the changed source-row fields; package distribution and other schema coverage remain outside scope. |
| `fiat-1464-make-the-declared-mapper-select-the-impleme.md` | All 8 rounds via `.synopsis.md`; keep resolved identities, scope in observations and possessive row grammar. Commit runnable evidence and content pins without worktree-only skips. The corrected rebuild command includes `--report`; #1517 remains open. |

Discovery also found `audit/rounds/fiat-shoggoth-front-door-derived.md` through
Anamnesis demonstration references. Its verified synopsis was read for Step 2
rounds 1 to 3 and Step 3 rounds 1 to 2, the source-declaration change this run consumes.
`S3-R1-06` is fixed in Step 3 round 2: the demo program must remain digest-bound.
The broader runner, rendering and topology work is outside this run. Its other
rounds are not claimed read. Root `audit/AUDIT.md` and plugin audit files had no
Anamnesis match in the subject search; the four per-run records hold its history.

All findings in the four Anamnesis histories are recorded fixed; remaining leads
above are explicit exclusions or already owned. They supply regression concerns,
not invented new audit findings. The issue-defined missing binding needs fresh
negative tests. No claim of an empty checked known-failure inventory is made.

Within the organisation, existing Anamnesis canonicalisation, schema closure,
digest recomputation and projection checks supply the implementation pattern;
no external repository is required. Outside it,
[Python hashlib](https://docs.python.org/3/library/hashlib.html) defines the
incremental SHA-256 API, and [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)
is a different JSON canonicalisation scheme. This change retains Anamnesis's
existing bytes and does not claim JCS conformance or add a dependency.

## 3. Constraints and non-goals

Starting ref: `main`, resolved to `7952eafa337f5ba1c4f45417ceb154673f629c1c`.
Interpreter: `.python-version` and executed `python3 --version` both read
`3.14.6`. Exact worktree fingerprint: `issue/16777231-874704726`.

Always retain native source, admission-policy and curation-policy bytes; verify
source digests; regenerate all three current releases and projections together;
preserve existing guards and run the checked runner. Step 1 records the study,
design evidence and resolver without product edits. Step 2 changes the release
contract and rebuilds all shipped outputs while keeping its exit green. Step 3
records the generation and demonstrates the complete result.

Ask first only for scope beyond this authority: new external corpus rights,
publication of holder/statement prose, changes to a sibling, or deployment.
The requested preimage change and replacement of the three current shipped
releases are already authorised by the corrected issue and this new run.
Never invent a legal permission, adopt old receipts, change the held frontier,
weaken tests to accept stale releases, or rewrite an accepted historical record.

Compatibility is intentionally strict: old four-field manifests stop verifying
under the new source-row contract. Rebuild from original policies and sources;
do not guess missing rights from disclosure. Keep `anamnesis-release/v1` as the
existing closed format with stricter required fields, as prior scope additions
did; document that old consumers and new manifests are incompatible. Any future
format negotiation needs a separate design. No per-source mapper, second producer,
new admission basis, unknown-source disk fixture, or legal opinion is delivered.

## 4. Checked design selection

`.hexaemeron/design-evidence.json` contains three candidates, seven criteria and
21 matrix cells. Eighteen selection reports were executed with the fresh
`.hexaemeron/reports/resolve.py`; three conformance cells remain pending until
integration, and only the selected candidate's cell is due. The resolver's
`implementation` command runs the real plugin suite and checks all three current
manifests against the selected construction. It must not be reported passed now.

| Candidate | Rights mutations changing id | Rights prose bytes | Source-row bytes | 100 three-corpus hashes, median ms | Changed ids | Repeatable |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `manifest-only` | 0/12 | 0 | 2332 | 108 | 0/3 | yes |
| `full-rights` | 12/12 | 1696 | 4308 | 110 | 3/3 | yes |
| `retained-rights` | 12/12 | 0 | 2332 | 109 | 3/3 | yes |

Each mutation changes one of basis, holder, statement or disclosure in the first
source of each specimen. Space counts the canonical source-row arrays across
all eight source entries. Time is the rounded integer median of seven runs,
each hashing all three graphs 100 times on this machine. Repeatability compares
a JSON round trip and reversed input order. These are construction probes, not
production performance or a security audit. `manifest-only` fails identity
binding; `full-rights` emits the decision text. `retained-rights` alone passes
both hard gates and the intentional three-id migration gate, so
`unique-frontier` selects it irrespective of timing noise. The design-lock
checker exited zero; there is no pending selection evidence.

## 5. Risk register

```risk-register
rights-bound | admission through manifest and release identity | digest the complete checked rights object and bind all six source fields
rights-shape | hostile manifest at build and verify | missing unknown malformed and digest-only-public fields refuse by name without a traceback
private-prose | admission decision to public release | neither holder nor statement enters manifest components events added by this change or projections
projection-disclosure | verified manifest to consumer | mutations under unchanged identity refuse and restricted findings remain withheld and counted
old-release | four-field historical manifest to new verifier | refuse missing rights and document rebuild recovery without inferred defaults
rebuild-drift | three current specimens and identity-bearing references | independent rebuilds agree while graph components and historical evidence stay unchanged
source-custody | preserved sources admission policies and curation policies | original bytes and provenance remain unchanged
frontier-drift | generation and demonstration ledgers | preserve held job revision digest input declaration and previous history rows
report-custody | resolver and conformance report paths | reruns use explicit fresh destinations and never overwrite digest-bound reports
```

## 6. Glossary

Basis: one recognised declared rights category. Decision reference:
`rights_sha256`, a digest of the full checked rights object. Disclosure: the
class controlling projected text. Release identity: the digest of the ordered
policy/source/graph preimage. Generation: an improvement that leaves the held
frontier unchanged. A digest records identity, not legal sufficiency or secrecy.

## 7. Sources

The issue and merged PR links above bind scope and carryover. Repository sources
are pinned to the starting commit:
[program](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py),
[release schema](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/anamnesis/skills/anamnesis/schemas/release-v1.json),
[ADR-003](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/anamnesis/docs/decisions/ADR-003-source-rights.md),
[evolution ledger](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/anamnesis/skills/anamnesis/EVOLUTION.md).
The four audit source paths and sibling views are enumerated in section 2;
`.hexaemeron/audit-read-evidence.json` records their current source and view hashes.

## 8. Signals and on-call questions

[Ephoros](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/hexaemeron/skills/ephoros/SKILL.md)
governs signals. Which source lost its basis? Which field caused refusal? Which
release changed identity? Step 2 answers through named CLI refusals, source ids,
manifest rows and rebuild reports. Existing admission events retain their policy
version and correlation id. Release-integrity refusals do not all emit durable
events today; this study makes no such claim and adds no unattended service.

## 9. Trust boundaries

[Phylax](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/hexaemeron/skills/phylax/SKILL.md)
governs source-policy, hostile-manifest, report and projection boundaries.
Compute rights digests only after policy validation; reuse checked source bytes
and checked component bytes; validate source-row types before membership checks
or formatting. Keep filesystem and byte caps. A self-consistent forged manifest
with a newly computed id is a different release, not authenticated authorisation.
Verification cannot recover the hidden rights statement or establish that its
basis was lawful. Hashing is not encryption: low-entropy decision text may be
guessable. The promise is omitted plaintext plus an exact decision reference.

## 10. Performance and space

[Metron](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/hexaemeron/skills/metron/SKILL.md)
governs measurement. No new production latency or memory budget is declared:
this is rights custody and adds one bounded rights-object hash per source.
The existing release cap remains. Reproduce the design measurement with
`python3 .hexaemeron/reports/resolve.py retained-rights probe-ms`; its number may
vary and no expected literal pins a timing. `row-bytes` measures representation
size; `demo` retains its existing observed duration and memory baseline.

## 11. Failure, guards and recovery

[Elenchus](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/hexaemeron/skills/elenchus/SKILL.md)
governs fixes. Preserve the existing malformed-policy, duplicate-key,
checked-read, no-empty-suite, schema and projection guards. Add tests whose
assertions fail on the old missing-binding implementation; import errors or an
empty test selection are not a guard. The existing `tests/elenchus.py` accepts
steps 1 to 14 and discovers `test_sN_*.py`; use owned files matching the chosen step
numbers without changing its command interface. Missing rights blocks dependent
release and projection only. Recover by restoring checked policy decisions and
rebuilding into fresh directories. A partial build never becomes acceptance.

## 12. Decisions and homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/7952eafa337f5ba1c4f45417ceb154673f629c1c/plugins/hexaemeron/skills/hypomnema/SKILL.md)
governs the durable explanation. The committed study, design record, runnable
resolver and reports belong under `plugins/anamnesis/docs/source-rights/`.
Step 1 adds a standing decision paragraph to the existing ledger, outside its
historical rows, naming `retained-rights`, the rejected alternatives and the
stricter compatibility rule; counters and frontier remain unchanged. Step 3
adds the generation history row with the three new ids after demonstration.
It preserves frontier revision `resolved-mapper` and frontier digest
`df27b276252cc4045a18c202b8b00782fe4dc40835b3eafca3935f48900e13f9`, the full held
job text and the `second-producer-findings` declaration. The generation is the
next generation after the current integration base, not an evolution increment.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | retained-rights
record | plugins/anamnesis/skills/anamnesis/EVOLUTION.md
```

Current demo source/program digests, the pilot observation and front-door card
must be regenerated when their inputs move. Advance only the demo generation;
retain its status, frontier and non-claims. Prior ADRs, audit rounds, earlier
ledger rows and digest-bound kickoff input records remain historical evidence.
The final step names the three new current ids without rewriting that history.
