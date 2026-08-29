# Runbook: recover issue 429 from pull request 552

Derived from `.hexaemeron/study.md`. Two steps keep the evidence layers
separate. Step 1 creates the one product-first composition commit and makes the
current audit topology work with the inherited product. Step 2 drives the
checked-in controller in a disposable repository, records the proof, and
allocates release versions only after rereading the live predecessors.

## Operating contract

Every step runs from this recovery worktree. The composition procedure first
cuts the controller-named step branch from the controller-named run branch. It
then resolves a no-commit merge of product head
`f11fe174161f46bf79080422169ad943214e1b4f`, writes that resolved tree, and
creates one signed commit with the product as first parent and pinned base
`c4650f02a979e859ce36374779eac9cd70744288` as second parent. The branch ref is
advanced to that commit without a rebase, squash, cherry-pick, or hard reset.

Both steps give Warden this source-bound Elenchus runner contract:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
```

## Step 1: Compose the signed product with the current audit topology

**Goal.** Preserve the complete signed #552 product as ancestry while making
its schema, timestamp, synopsis, and append-only evidence work on the pinned
Fiat 5.24.1 tree.

**Entry.** Run branch
`fiat/429-recover-issue-429-from-pull-request-552` at
`c4650f02a979e859ce36374779eac9cd70744288`, with the study and runbook
receipted, no step commit, #552 head fixed at
`f11fe174161f46bf79080422169ad943214e1b4f`, and the controller-configured
audit path
`audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md`.

**Exit.** The signed composition commit has exactly two parents: #552 head
first and the pinned base second. All 52 inherited commits remain reachable,
locally signature-valid, hosted-valid with reason `valid`, and carry each
required provenance trailer exactly once. A checked composition manifest names
all 16 overlap paths and the current and product behaviours retained at each.
The current root audit bytes are unchanged. The exact 574-line product suffix
is instead stored at
`audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md`, with 29
records distributed 12, 15, and 2 across the old steps and SHA-256
`51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d`.

The checked-in controller accepts strict, explicitly tagged
`fiat-audit-round/v1` and `fiat-audit-round/v2` records and refuses malformed,
duplicate, incomplete, non-UTC, out-of-order, or context-reinterpreted tagged
records before controller-state mutation. Untagged historical prose remains
readable. Legacy `AUDIT.md` sources map to `AUDIT_SYNOPSIS.md`; each other
direct `audit/rounds/*.md` source maps to a sibling `<stem>.synopsis.md`.
Synopsis files are excluded from discovery, every source maps to one unique
destination, every unresolved lead and present Elenchus verdict is retained,
and every output obeys `100 * synopsis_lines < 15 * source_lines`.

The six legacy sources, two pinned-base round sources, and imported product
source have fresh byte-identical synopses. The current per-run audit path,
controller-currency receipt, runbook-amendment, integration-revalidation,
final-visible-state, and ordinary non-frontier behaviour from Fiat 5.24.1 stay
covered. The accepted study and runbook have committed recovery copies, and
ADR-034 records the product-first compatibility decision. Prove the exit with:

```bash
python3 plugins/hexaemeron/tests/test_issue_429_recovery.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl \
  plugins.hexaemeron.tests.test_fiat_skill \
  plugins.hexaemeron.tests.test_issue_429_release \
  tests.test_audit_prefix_integrity \
  tests.test_audit_synopsis_currency -q
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.**
`plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/study.md`,
`plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/runbook.md`,
`plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/composition-manifest.json`,
`docs/decisions/ADR-034-recover-signed-fiat-product-across-an-audit-topology-change.md`,
the three inherited files under
`plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/`,
`audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md`, all sibling
synopses for the six legacy and three round sources,
`plugins/hexaemeron/README.md`, `plugins/hexaemeron/agents/warden.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_issue_429_release.py`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/fixtures/audit-prefixes.json`, `tests/fixtures/audit-synopsis/`,
`tests/test_audit_prefix_integrity.py`,
`tests/test_audit_synopsis_currency.py`, and
`tests/promise_machine_coverage.json`. The merge also examines
`.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`,
`audit/AUDIT.md`, both Hexaemeron plugin manifests, and Fiat's `EVOLUTION.md`;
their pinned-base release bytes remain unchanged in this step.

**Tests.** Preserve all inherited #552 guards and add permanent recovery cases
for exact parent order, 52-commit reachability, signatures, trailers, the
composition manifest, the relocated suffix digest and record distribution,
v1/v2 separation, two round files in one directory, synopsis-source exclusion,
unique destination mapping, current-root prefix preservation, stale output,
lead and verdict retention, line-budget equality, path escape, symlink input,
bounded input, refusal without partial writes, and current Fiat features. Each
new defect guard is first demonstrated red against the unresolved or
unadapted composition. Elenchus test command:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`tmp/elenchus/fiat-429-recovery-step-1.json`.

**Disciplines.** phylax: audit discovery, strict parsing, Git and GitHub reads,
and sibling replacement cross bounded path, byte, subprocess, and external
evidence boundaries. ephoros: the manifest and deterministic per-source rows
answer which parents, commits, conflicts, sources, outputs, schemas, leads,
verdicts, and refusals were checked. metron: none; the physical-line ratio is
an acceptance rule and no speed claim is made. elenchus: the collision, grammar,
ancestry, digest, path, and refusal guards must fail on the unfixed composition
before their causes are repaired. hypomnema: ADR-034 and the recovery documents
hold the expensive compatibility decision and its operating rules.

## Step 2: Prove the checked-in controller and publish current generations

**Goal.** Demonstrate the composed product from a disposable repository and
publish release surfaces that name the immediate live successors without
widening into neighbouring Fiat issues.

**Entry.** Step 1's audited and pushed exit. The product-first composition and
its nine-source synopsis set are present, the recovery run's Warden record and
its collision-free synopsis now supply a tenth source, and release surfaces
still name Fiat 5.24.1 and Hexaemeron 1.6.0.

**Exit.** A committed proof drives only the checked-in controller and generator
inside a fresh temporary Git repository. It proves each required-field,
timestamp, grammar, risk-id, count, verdict, stale-synopsis, collision, path,
parent, signature, trailer, and predecessor refusal without state, ledger, or
destination drift. It accepts a clean v2 round, reads the imported v1 product
records, maps two round sources in one directory to different siblings,
regenerates every synopsis exactly, and records source and output paths,
digests, physical line counts, schema counts, verdicts, leads, elapsed time,
and bounded output size. It verifies all 52 inherited commits locally and
through GitHub and binds the checked controller, generator, composition, base,
product, study, runbook, manifest, and proof digests.

Immediately before editing versions, the step rereads `origin/main`, Fiat's
newest generation row, both Hexaemeron plugin manifests, and both marketplace
manifests. If they still publish the pinned predecessors, the next generations
are `fiat-v5.25.1` / Fiat `5.25.1` and Hexaemeron `1.6.1`. Any different live
predecessor or occupied successor blocks the step until a receipted runbook
amendment names the complete replacements. One generation row records #429
while retaining the `state-shape-validation` frontier revision, digest, open
status, and issue #363 target. Every version surface and Promise Machine
binding agrees on the released controller digest. Issues #557, #608, #453,
#369, and #363 remain outside the implementation. Prove the exit with:

```bash
python3 plugins/hexaemeron/tests/test_issue_429_recovery.py --proof
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run Imprimatur and then Brevitas on each changed prose path. Generated
synopses use their currency, retention, and physical-line checks instead of a
prose rewrite.

**Files.**
`plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/proof.md`,
the recovery study and runbook if a path-only publication adjustment is
needed, `.agents/plugins/marketplace.json`,
`.claude-plugin/marketplace.json`, both Hexaemeron plugin manifests,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/test_evolution_contract.py`, `tests/test_version_propagation.py`,
`tests/promise_machine_coverage.json`, and every synopsis whose source changed
after step 1. The Warden-owned run source and sibling synopsis are
`audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` and
`audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.synopsis.md`.

**Tests.** Extend the recovery proof guard to run the real composed controller
and generator in a disposable repository; require the ten-source topology,
v1/v2 success, every named refusal, exact source/output regeneration, all 52
local and hosted verification results, version predecessor and propagation
checks, controller digest propagation, and cleanup of temporary state. The
full suites, Promise Machine check, five prose/tree checks, Horos currency, and
diff check remain mandatory. Elenchus test command:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`tmp/elenchus/fiat-429-recovery-step-2.json`.

**Disciplines.** phylax: the disposable proof confines generated paths,
subprocess arguments, network evidence, output, and cleanup without exposing
credentials. ephoros: the proof stores the exact counts, digests, parent order,
version predecessors, per-source results, refusal deltas, and final released
generations needed to explain the run. metron: none; elapsed time and output
size are diagnostic observations, not optimisation claims. elenchus: every
failure class is replayed against the checked-in controller and any audit fix
uses the declared structured report. hypomnema: the proof and one Fiat
generation row record what shipped while ADR-034 remains the decision home.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Files: `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/study.md`, `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/runbook.md`, `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis-recovery/composition-manifest.json`, `docs/decisions/ADR-034-recover-signed-fiat-product-across-an-audit-topology-change.md`, the three inherited files under `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/`, `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md`, all sibling synopses for the six legacy and three round sources, `plugins/hexaemeron/README.md`, `plugins/hexaemeron/agents/warden.md`, `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/references/audit-loop.md`, `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/audit_record_schema_cases.py`, `plugins/hexaemeron/tests/test_fiat_skill.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_issue_429_release.py`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, `tests/fixtures/audit-prefixes.json`, `tests/fixtures/audit-synopsis/`, `tests/test_audit_prefix_integrity.py`, `tests/test_audit_synopsis_currency.py`, and `tests/promise_machine_coverage.json`. The merge also examines `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`, `audit/AUDIT.md`, both Hexaemeron plugin manifests, and Fiat's `EVOLUTION.md`; their pinned-base release bytes remain unchanged in this step.
**Why.** Composing the inherited and current controller guards made `plugins/hexaemeron/tests/test_hexctl.py` 317,580 bytes, beyond the repository's 262,144-byte bounded-read contract. Moving only `AuditRecordSchemaTests` to the named helper keeps the same guards loaded by `test_hexctl.py` while restoring the bounded source file.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.
