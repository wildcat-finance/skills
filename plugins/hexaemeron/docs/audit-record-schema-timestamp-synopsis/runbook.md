# runbook: schema, timestamp, and synopsis for fiat audit records

this run implements issue 429 in three stacked, green steps. the first step
commits the accepted proposition, freezes the append-only baseline, and makes
future audit entries strict. the second derives and checks the six synopses.
the last proves the changed controller in a disposable run and reconciles the
release surfaces.

the pinned repository commands are:

```bash
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
```

every step gives Warden the same source-bound Elenchus runner contract:

```text
test command: npx --yes --package=node@26.6.0 -- python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
report file: .elenchus/hexaemeron-unittest.json
```

Warden records every id from the study risk register as `reviewed` or
`not-applicable`. after step 1, each new round also uses
`fiat-audit-round/v1`, a whole-second UTC heading, explicit negative space, the
canonical findings table, a leads value, and the exact Elenchus value or
`null`. after step 2, the same signed round commit regenerates the root
synopsis. this run's v5.12.1 controller may receipt those rounds but cannot
claim it enforced rules introduced by v5.13.1; step 3 proves the checked-in
controller separately.

## Step 1: freeze the evidence prefix and check future audit entries

**Goal.** Commit the accepted study and runbook, protect every starting audit
byte, and make Fiat refuse a future round whose schema, risk coverage,
negative space, findings, leads, UTC timestamp, or Elenchus field is absent or
inconsistent.

**Entry.** Run branch
`fiat/429-audit-record-schema-timestamp-synopsis` at
`ced4e6f439021b7509833ed5da66348c86d22f01`. Fiat is `v5.12.1`,
Hexaemeron is `1.5.5`, the six logs total 731,613 bytes and 11,729 lines, and
no `AUDIT_SYNOPSIS.md` exists.

**Exit.** The committed study and runbook equal the receipted artefacts. A
baseline fixture pins each of the six source prefixes by repository-relative
path, byte length, SHA-256, line count, and starting ref; its test fails on any
shortening or changed prefix while allowing an append. `audit-round` resolves
the contained configured `audit.log_path`, reads the final H2 record through a
bounded regular UTF-8 path, and accepts only `fiat-audit-round/v1`. The heading
matches topic, step, next round, and a calendar-valid
`YYYY-MM-DDTHH:MM:SSZ`. `Covered` contains each study risk id exactly once as
`reviewed` or `not-applicable`, with no unknown id. `Not checked` and
`Leads not pursued` have non-empty same-line values. The canonical findings
table has exactly `--findings` data rows, using the specified zero-finding row
when clean. `Elenchus verdict` equals the CLI value or `null`. A supplied
`--log` must name the configured path. Every refusal precedes state and ledger
mutation and names the failing field without printing source content.

An accepted round stores the schema, canonical log path, record timestamp,
entry SHA-256, log end offset, findings, lint exits, fixes range, and the exact
issue-327 verdict. Legacy rounds may omit every new leaf. The audit-loop
reference and Warden contract carry one complete example and keep Warden as
the signed append owner. Fiat becomes `v5.13.1`; Hexaemeron becomes `1.5.6` on
both plugin manifests and both marketplace manifests. One Fiat generation row
records the schema, timestamp, append-only compatibility, and planned derived
view while retaining the `state-shape-validation` frontier revision, digest,
status, and issue-363 held target byte-for-byte. These commands prove the
step:

```bash
python3.12 -m unittest \
  plugins.hexaemeron.tests.test_hexctl \
  plugins.hexaemeron.tests.test_fiat_skill \
  tests.test_audit_prefix_integrity -q
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
git diff --check
```

**Files.**

- `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md`
- `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md`
- `tests/fixtures/audit-prefixes.json`
- `tests/test_audit_prefix_integrity.py`
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
- `plugins/hexaemeron/tests/test_hexctl.py`
- `plugins/hexaemeron/tests/test_fiat_skill.py`
- `plugins/hexaemeron/skills/fiat/SKILL.md`
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `plugins/hexaemeron/agents/warden.md`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/.claude-plugin/plugin.json`
- `plugins/hexaemeron/.codex-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `tests/test_evolution_contract.py`
- `tests/test_version_propagation.py`
- `tests/promise_machine_coverage.json`

**Tests.** Before changing the controller, add focused cases that expose the
old acceptance of a date-only or malformed tail, each missing field, duplicate
and unknown risk ids, count and verdict mismatches, an escaping or non-regular
log, invalid UTF-8, oversized input, and a mismatched `--log`; capture the red
parent result. Add the clean zero row, all four Elenchus values, `null`, and a
legacy missing-key sequence through `status`, `next`, `verify`, a later round,
and audit close. Each refusal test hashes state and ledger before and after.
The prefix test mutates one old byte, truncates, inserts inside the prefix, and
appends after it. Runbook Elenchus test command:
`npx --yes --package=node@26.6.0 -- python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: authored Markdown and a configured path cross into
controller authority, so type, size, containment, file kind, encoding, and
content are checked before mutation. ephoros: stable diagnostics and receipt
leaves answer which entry passed and why one refused. metron: none, the
`synopsis_lines * 100 < audit_lines * 15` rule is a product invariant and no
speed claim is made. elenchus: new focused tests must fail against the old
acceptance before the cause is fixed.
hypomnema: the schema, timestamp, compatibility rule, and rejected sidecar
design belong in Fiat's generation row and runtime reference.

## Step 2: derive and bind the six audit synopses

**Goal.** Generate one deterministic, compact sibling synopsis for every audit
log and make a future audit receipt refuse missing, stale, lossy, oversized,
or over-budget output.

**Entry.** Step 1's verified exit. New strict entries are checked and the six
starting prefixes are pinned, but there is no generator, committed synopsis,
or synopsis evidence in an audit receipt.

**Exit.** `audit_synopsis.py --write .` discovers the sorted six
`**/audit/AUDIT.md` regular files inside the real repository and atomically
replaces only their sibling `AUDIT_SYNOPSIS.md` files. `--check .` renders in
memory and requires byte identity with every committed sibling. The renderer
emits one metadata line and one physical line per H2 source record, without a
generation clock. It retains source order, the exact heading, strict fields,
canonical findings table, recognised legacy risk tables, every physical
`Leads not pursued` occurrence, and the rest of each leads section; missing
legacy fields remain labelled missing rather than inferred. The metadata binds
schema, relative source path, source SHA-256, and H2 count.

The CLI refuses symlinks, escape, invalid UTF-8, inputs over 16 MiB, more than
10,000 H2 records, physical lines over 1 MiB, malformed strict entries, and an
output at or above the integer rule
`synopsis_lines * 100 < audit_lines * 15`. Errors name paths, rules, counts,
and digests but no source content. Writes use a same-directory temporary file,
flush, atomic replacement, cleanup, and an exact post-write read. All six
synopses are committed, each below 15%; every one is byte-identical to fresh
generation; the source-leading multiset and issue-327 verdict strings are
preserved.

The checked-in controller calls the same renderer before accepting a strict
tail and stores the synopsis SHA-256 beside the step-1 leaves. A missing, stale,
lossy, or over-budget synopsis refuses before state and ledger mutation. Warden
regenerates the root synopsis in the same signed commit that appends a round,
before handing the commit to the orchestrator. Fiat's runtime contract,
audit-loop reference, Warden contract, README, tests, Promise runtime binding,
and existing generation row agree. Prove it with:

```bash
python3.12 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3.12 -m unittest \
  plugins.hexaemeron.tests.test_hexctl \
  plugins.hexaemeron.tests.test_fiat_skill \
  tests.test_audit_prefix_integrity \
  tests.test_audit_synopsis_currency -q
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
python3.12 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.**

- `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`
- `tests/test_audit_synopsis_currency.py`
- `tests/fixtures/audit-synopsis/`
- `audit/AUDIT_SYNOPSIS.md`
- `plugins/ariadne/audit/AUDIT_SYNOPSIS.md`
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`
- `plugins/pandects/audit/AUDIT_SYNOPSIS.md`
- `plugins/probitas/audit/AUDIT_SYNOPSIS.md`
- `plugins/tabularium/audit/AUDIT_SYNOPSIS.md`
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
- `plugins/hexaemeron/tests/test_hexctl.py`
- `plugins/hexaemeron/tests/test_fiat_skill.py`
- `plugins/hexaemeron/skills/fiat/SKILL.md`
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `plugins/hexaemeron/agents/warden.md`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/README.md`
- `tests/promise_machine_coverage.json`
- `.horos/boundary.json` only if the currency check proves the tracked-tree
  boundary changed without classifying a synopsis as a hard entry

**Tests.** Add fixtures for date-only and prose headings, zero findings as
prose and as a canonical row, H3 and inline leads, wrapped lead reasons,
duplicate leads, several risk-table headings, non-round H2 sections, strict
entries, all four verdicts, `null`, and missing legacy values. See the currency
test fail after a source append, source edit, synopsis edit, missing sibling,
dropped duplicate lead, line-budget breach, unsafe path, cap breach, and
interrupted replacement; see exact regeneration repair each recoverable case.
Controller tests prove synopsis refusal has no state or ledger drift. Runbook
Elenchus test command:
`npx --yes --package=node@26.6.0 -- python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: repository discovery and generated-file replacement
open read, path, size, encoding, symlink, and partial-write boundaries; hostile
fixtures exercise each control. ephoros: per-path check output exposes source
lines, synopsis lines, integer-budget verdict, source digest, fresh digest, and
committed-byte verdict without echoing audit content. metron: none, the 15%
ratio is checked as a correctness budget and no runtime optimisation is made.
elenchus: stale, lossy, and partial-write failures get red-before-fix guards.
hypomnema: the derived format and atomic replacement rule stay in Fiat's
existing generation record and interface docs, not a second ADR.

## Step 3: demonstrate legacy compatibility and release currency

**Goal.** Exercise the checked-in controller and generator end to end, record
bounded proof, and cold-read the complete release without widening into any
downstream issue.

**Entry.** Step 2's verified exit. Strict receipt validation, deterministic
generation, all six committed synopses, and their focused tests exist; only the
disposable demonstration and final release reconciliation remain.

**Exit.** A fresh temporary git repository driven by the tracked v5.13.1
controller proves every required-field refusal, count/risk/verdict/timestamp
mismatch, missing and stale synopsis, and path boundary without state or ledger
drift. It then accepts one clean round, four signed fixes carrying `guarded`,
`unguarded`, `passed`, and `inconclusive`, one explicit `null`, and a legacy
round missing all new leaves through `status`, `next`, `verify`, a later round,
and close. The proof binds the exact controller and generator digests,
commands, exit statuses, state/ledger digests, entry/synopsis digests, prefix
digests, line counts, and ratio verdicts without credentials or raw signature
output.

All six live source prefixes still match the step-1 fixture; all six synopses
are regenerated after every issue-429 audit append and pass currency, lead
occurrence, verdict preservation, and strict line-budget checks. A fresh Horos
scan leaves all synopsis paths outside the hard boundary. The committed study,
runbook, proof, Fiat and Warden contracts, generation row, README, controller,
generator, manifests, marketplace entries, version tests, and Promise Machine
binding tell one bounded story. #369, #453, and #363 remain open and unchanged.
Every covering command exits 0:

```bash
python3.12 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
python3.12 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run Imprimatur on every changed prose path, then Brevitas in report mode on the
study, runbook, proof, changed contracts, ledgers, README, Warden contract, and
final pull-request drafts. Generated synopses use their stricter currency,
retention, and line-budget checks instead of a prose rewrite.

**Files.**

- `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/proof.md`
- `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md`
- `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md`
- `audit/AUDIT_SYNOPSIS.md`
- `plugins/ariadne/audit/AUDIT_SYNOPSIS.md`
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`
- `plugins/pandects/audit/AUDIT_SYNOPSIS.md`
- `plugins/probitas/audit/AUDIT_SYNOPSIS.md`
- `plugins/tabularium/audit/AUDIT_SYNOPSIS.md`
- `audit/AUDIT.md`
- any mutable release surface proved stale by the cold read
- `.horos/boundary.json` only if a fresh scan proves its tracked currency changed

**Tests.** The proof invokes the real checkout controller and generator in a
disposable repository, asserts exact state and ledger digests around each
refusal, and reruns the focused guards plus every command above. Runbook
Elenchus test command:
`npx --yes --package=node@26.6.0 -- python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: the demo uses generated local paths, bounded output,
and no network, shell-built data, or secret-bearing diagnostics. ephoros: the
proof binds each operator question to a stored field, refusal, digest, count,
or ratio. metron: none, the demonstration checks the stated product budget and
makes no speed claim. elenchus: it replays every failure class and preserves
all issue-327 verdict states plus legacy absence. hypomnema: the proof records
observable evidence while Fiat's generation row remains the sole standing
decision record.
