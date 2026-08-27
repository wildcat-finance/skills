# Runbook: receipt Elenchus verdicts on Fiat audit fixes

This run implements issue 327 in three stacked, green steps. It keeps the
study's chosen predicate: only `audit-round --fixes-commit` claims a bug fix.
The checkout controller drives this self-change, while the installed 1.5.4
controller continues to receipt the run itself.

The pinned toolchain command for the complete Hexaemeron suite is:

```bash
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
```

Every step's audit uses the same runbook-owned Elenchus contract after step 1
adds report output to that command:

```text
test command: python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
report file: .elenchus/hexaemeron-unittest.json
```

The Warden records every id from the study's risk register as reviewed or not
applicable. A non-`guarded` verdict is evidence, not a controller failure in
this generation.

## Step 1: Bind the runbook test command to the Elenchus contract

**Goal.** Give Hexaemeron's existing test command bounded
`unittest-json-v1` output, commit the accepted study and runbook, and state the
source-to-Warden handoff in Elenchus and Protasis without changing Fiat's
controller yet.

**Entry.** Run branch
`fiat/327-elenchus-2-feed-the-guard-verdict-into-fiat` at
`454bf3c9930c94985e5eb6179f3b01be2bf741c2`; Elenchus is
`elenchus-v1.1.0`, Protasis is `protasis-v4.5.0`, and
`plugins/hexaemeron/tests/run_tests.py` has no report mode.

**Exit.** `run_tests.py --elenchus-report <path>` writes one complete
`elenchus.unittest.v1` object from the result it just ran and keeps the same
process exit semantics. Missing, repeated, or malformed CLI input is refused
without a report. The committed study and runbook are byte-identical to the
receipted artefacts except for links made relative to their committed
directory. Elenchus `v1.2.0` and Protasis `v4.6.0` each carry one generation
row retaining their prior frontier revision, digest, status, and held target
byte-for-byte. Their contracts name the exact test command, report format,
and report file as Warden-owned inputs. Prove the boundary with:

```bash
python3.12 -m unittest \
  plugins.hexaemeron.tests.test_elenchus_checker \
  plugins.hexaemeron.tests.test_fiat_skill \
  plugins.hexaemeron.tests.test_protasis_checker -q
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/elenchus-audit-round-verdict/runbook.md
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 -m unittest discover -s tests
git diff --check
```

**Files.**

- `plugins/hexaemeron/tests/run_tests.py`
- `plugins/hexaemeron/tests/test_elenchus_checker.py`
- `plugins/hexaemeron/skills/elenchus/SKILL.md`
- `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`
- `plugins/hexaemeron/skills/protasis/SKILL.md`
- `plugins/hexaemeron/skills/protasis/EVOLUTION.md`
- `plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md`
- `plugins/hexaemeron/docs/elenchus-audit-round-verdict/runbook.md`

**Tests.** Extend the Elenchus test module with a runner-result fixture that
checks the exact report schema, all unittest counters, parent directory
creation, unchanged pass/fail exit codes, and refusal before write for bad
arguments. Runbook Elenchus test command:
`python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: the runner accepts a report path and must write only
the explicitly supplied regular-file target without shell evaluation.
ephoros: its JSON and exit status must distinguish completed tests from CLI or
write failure. metron: none, no speed or resource claim is made. elenchus: the
new mode is the report adapter this runbook gives every audit fix. hypomnema:
the three generation decisions and retained frontiers are expensive to
reinterpret, so their ledgers hold them once.

## Step 2: Receipt the four verdicts and source-bind Warden

**Goal.** Make `audit-round` require and store one canonical Elenchus verdict
exactly when it verifies a fixes commit, and give Warden the exact receipted
runbook step that owns the command/report contract.

**Entry.** Step 1's merged exit. The runner and two source contracts exist,
but Fiat `v5.11.1` still accepts a fixes commit with no verdict and its Warden
packet carries only the study risk register.

**Exit.** `audit-round --fixes-commit <sha>` refuses a missing verdict and
accepts exactly `guarded`, `unguarded`, `passed`, or `inconclusive` through
`--elenchus-verdict`. A verdict without a fixes commit and every unknown value
are refused before state or ledger mutation. Every new round writes
`elenchus_verdict` as the accepted string or null; legacy rounds may omit it.
`next` exposes the conditional obligation and Warden's deterministic packet
adds the exact `runbook_step` object without changing Mason's copy. Receipt
stdout names a recorded verdict. Fiat's SKILL, audit-loop reference, Warden
contract, `fiat-v5.12.1` generation row, two plugin manifests, two marketplace
entries, and version tests agree. The Fiat frontier revision, digest, current
frontier, and issue 363 held target remain byte-identical. Prove it with:

```bash
python3.12 -m unittest \
  plugins.hexaemeron.tests.test_hexctl \
  plugins.hexaemeron.tests.test_fiat_skill -q
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
git diff --check
```

**Files.**

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
- `plugins/hexaemeron/tests/test_hexctl.py`
- `plugins/hexaemeron/tests/test_fiat_skill.py`
- `plugins/hexaemeron/skills/fiat/SKILL.md`
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/agents/warden.md`
- `plugins/hexaemeron/.claude-plugin/plugin.json`
- `plugins/hexaemeron/.codex-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `tests/test_evolution_contract.py`
- `tests/test_version_propagation.py`
- `tests/promise_machine_coverage.json` only if the canonical promise text changes

**Tests.** Add table-driven CLI cases for all four values; missing, unknown,
and unbound verdict refusals with unchanged state and ledger digests; null on a
no-fix round; a legacy absent key through `status`, `next`, `verify`, a later
round, and audit close; stdout and ledger preservation; and deterministic
Warden reconstruction with exact runbook bytes, path, SHA-256, number, and
title. Runbook Elenchus test command:
`python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: the controller validates a closed CLI enum and passes
source bytes without executing or interpolating them. ephoros: `next`, refusal
text, stored state, ledger transition, and receipt stdout expose the owed and
recorded value without report contents. metron: none, the added constant-size
field has no performance claim. elenchus: red cases first prove the old
controller accepts an unreceipted fix, then all four classifier states remain
distinct. hypomnema: Fiat's generation row and audit-loop reference own the
predicate, field name, and checked-not-attested boundary.

## Step 3: Demonstrate legacy and release compatibility

**Goal.** Run the checkout controller through a fresh, disposable Fiat state
for all four verdicts and the legacy path, record bounded proof, then cold-read
every changed marketplace surface for one coherent release.

**Entry.** Step 2's merged exit. All behavior and contracts exist at their new
skill and package versions; only the end-to-end proof and final currency pass
remain.

**Exit.** A temporary git repository demonstrates four accepted fixes ranges,
both missing-value refusals without drift, one null no-fix round, exact packet
reconstruction, and one hand-edited legacy round surviving `status`, `next`,
`verify`, a later round, and close. The proof records commands, observed
statuses, and digests without credentials or raw signature output. The
committed study, runbook, proof, skill frontmatter, ledgers, agent contract,
runtime reference, manifests, marketplaces, version constants, and Promise
Machine declaration tell the same bounded story. Issue 429 and 453 remain
dependent work. Every repository check covering changed areas exits 0:

```bash
python3.12 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  'python3.12 plugins/hexaemeron/tests/run_tests.py'
python3.12 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md
python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  plugins/hexaemeron/docs/elenchus-audit-round-verdict/runbook.md
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  README.md AGENTS.md .agents plugins docs
python3.12 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Run Imprimatur on every changed prose path, then Brevitas on the study,
runbook, proof, skill contracts, audit-loop reference, ledgers, Warden contract,
and final pull-request drafts.

**Files.**

- `plugins/hexaemeron/docs/elenchus-audit-round-verdict/proof.md`
- `plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md`
- `plugins/hexaemeron/docs/elenchus-audit-round-verdict/runbook.md`
- any mutable release surface proved stale by the cold read
- `.horos/boundary.json` only if Horos proves the tracked tree changed its boundary
- `audit/AUDIT.md`

**Tests.** The proof invokes the real checkout controller and asserts exact
state/ledger digests before and after each refusal. It reruns step 2's focused
regressions plus the full commands above. Runbook Elenchus test command:
`python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Elenchus report format: `unittest-json-v1`. Elenchus report file:
`.elenchus/hexaemeron-unittest.json`.

**Disciplines.** phylax: the disposable demo uses generated local paths and no
secret-bearing output. ephoros: proof binds each operator question to a JSON
field, refusal, or digest. metron: none, the demo measures correctness rather
than speed. elenchus: the demonstration preserves all four states and proves
missing evidence stays missing. hypomnema: the proof records only durable
decisions and observable commands; historical logs and downstream issue scope
remain untouched.
