# Obligation gate demonstration: evidence report

Issue #884 recorded ten obligation classes that stayed green while nothing
evaluated the promised fact. This report is the Step 7 demonstration that each
of the ten now reaches a gate, and it states what the demonstration still does
not establish.

The machine-readable half is
[`demonstration-run.json`](demonstration-run.json). Every count, digest, gate
class, registry row and test selector in it recomputes in
`tests/test_obligation_gate_demonstration.py`. If an obligation, relation,
history row or evaluation case moves and this record does not, that module
fails.

## Reproduce it

Run from a clean checkout at the Step 7 head. The sequence writes only
`.reports/` and `.elenchus/`, both ignored, and the Horos boundary when
regeneration changes it.

~~~sh
test -z "$(git status --porcelain)"
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check

work="$(mktemp -d)"
python3 tests/promise_evaluation_driver.py emit --out "$work/packet"
python3 tests/promise_evaluation_driver.py verify \
  --packet "$work/packet" \
  --answers docs/promise-machine/obligation-gates/evaluation-answers.json \
  --run docs/promise-machine/obligation-gates/evaluation-run.json

python3 scripts/promise_machine.py sync --check
python3 scripts/portable_promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
test -z "$(git status --porcelain)"

python3 scripts/run_checks.py --full --jobs 12 --report .reports/issue-884-full.json
python3 tests/run_tests.py --elenchus-report .elenchus/promise-obligations-step-7.json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/promise-machine/obligation-gates/study.md \
  docs/promise-machine/obligation-gates/runbook.md \
  docs/promise-machine/obligation-gates/demonstration-evidence.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md \
  .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md \
  plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
test -z "$(git status --porcelain)"
~~~

The recorded exit status of each stage is in `commands` in the run record. One
stage returns non-zero on this host; the section on repository checks below
names it, its two causes and their independent reproduction.

## The ten gate classes

Rows counts the obligation registry rows a class claims. The ten classes
partition all eighteen rows, and the partition is asserted rather than
described. Tests counts the contract-suite methods that exercise the class's
finding codes, including the two registry-wide methods that run every specimen
and hold every marker against its authored clause.

| Gate class | Issue obligation | Evaluator | Rows | Negative cases | Findings | Tests |
| --- | --- | --- | --- | --- | --- | --- |
| `result-binding` | result binding | `check --only runtime` | 1 | 35 runtime binding rows | `PM095` | 14 |
| `level-3-separation` | level-3 separation | `check --only obligations` | 1 | 4 consequence specimens | `PM090` | 11 |
| `exception-resolution` | exception resolution | `check --only exceptions` | 1 | 1 exception specimen | `PM093`, `PM038` | 17 |
| `composition` | all seven composition clauses | `check --only composition` | 7 | 7 composition relations | `PM097` | 10 |
| `field-semantics` | semantic contract fields | `check --only law,obligations` | 5 | 5 law obligation specimens | `PM005`, `PM006`, `PM007`, `PM008`, `PM009` | 20 |
| `upstream-provenance` | upstream vendored identity | `check --only overlays` | none | 12 declared provenance cases | `PM052`, `PM054`, `PM056`, `PM057`, `PM060`, `PM061`, `PM062`, `PM063` (plus `PV003`, `PV004` upstream) | 11 |
| `refusal-shape` | complete refusal reports | `check --only obligations` | 1 | 1 finding specimen | `PM092` | 4 |
| `unknown-evidence` | non-authorising unknown evidence | `check --only obligations` | 1 | 1 consequence specimen | `PM091` | 7 |
| `id-history` | historical ID stability | `check --only history` | none | 9 declared history cases | `PM100`, `PM102`, `PM103`, `PM104`, `PM105`, `PM106` | 8 |
| `no-side-effect` | enforced no-network and no-evidence-command boundary | `check --only imports` | 1 | 1 import specimen | `PM094` | 5 |

Two classes claim no registry row. `upstream-provenance` and `id-history` are
evaluated by `check_overlays` and `check_history` rather than by a marked
clause in the authored law, so the demonstration names their checker function
and their finding codes instead of a specimen path. That asymmetry is recorded
as a fact about the current design, not as a defect.

`PV003` and `PV004` are marked upstream because
`scripts/verify_vendored_provenance.py` raises them, not the offline core
checker. The run record separates them into `network_findings` so they cannot
read as core-checker coverage, and the currency guard refuses any core finding
code placed there or any declared provenance case whose finding the offline
checker cannot emit and that nobody named.

## Counts

| Subject | Count |
| --- | --- |
| Obligation markers in `PROMISE_MACHINE.md` | 18 |
| Obligation registry rows | 18 |
| Distinct negative specimen files | 12 |
| Runtime binding rows | 35 |
| Composition relations | 7 |
| Promise-id history rows | 80 |
| Active history ids | 80 |
| Declared history cases | 9 |
| Declared upstream-provenance cases | 12 |
| Evaluation cases | 11 |
| Evaluation outcomes | 55 |
| Issue-listed gate classes | 10 |
| Declared promises | 80 |
| Coverage rows | 80 |
| Selected repository scopes | 24 |
| Selected repository checks | 25 |

## Bound inputs

Each digest is checked byte for byte by the currency guard.

- `PROMISE_MACHINE.md`, SHA-256 `2b16db71ac2ca1e380bc391fcae8ac1f1db88cf1147ce9f0fd9cbd6b4ebc862f`, 27980 bytes
- `tests/promise_machine_obligations.json`, SHA-256 `384512818a3001477f919968a0e4a8c8d3aae90de621e548d906996f8c09954f`, 9630 bytes
- `tests/promise_machine_coverage.json`, SHA-256 `13d8e72c7d69c7379ac87a3d4ff25d64a38a3e262bb9689472c348959157c3fa`, 195143 bytes
- `tests/promise_machine_id_history.json`, SHA-256 `82787c820dcf7b96a7f9e5fda4417e5583689888c94578039cacf7d18b325f3b`, 44329 bytes
- `tests/fixtures/promise-machine/composition/cases.json`, SHA-256 `4513dd956d6faa04c3852428313651b847b789a059a2a9236647e127608d99f0`, 26778 bytes
- `tests/fixtures/promise-machine/history/cases.json`, SHA-256 `9051ac6c291330f527705177bffa70985657ec7f96707b7a9349d4e574cfc3f0`, 685 bytes
- `tests/fixtures/promise-machine/upstream-provenance/cases.json`, SHA-256 `f60821b1edf450d47a581f12562c13e1931c2b09c960bce2fb8a0b1767c154cf`, 935 bytes
- `docs/promise-machine/obligation-gates/evaluation-answers.json`, SHA-256 `3ebdb3a8e7b86dc7fd8c7be77acd72632b966c107aa2034668702e96e12b8855`, 1911 bytes
- `docs/promise-machine/obligation-gates/evaluation-run.json`, SHA-256 `c20acd1daa13444018fb9c58ef3ce22334f34846c58e54ddbb0fa9cfa255b524`, 3231 bytes

## When a gate stops the line

Read a refusal in this order.

1. **Which gate failed.** The finding code is in every refusal, in text and in
   JSON. Find its class in the table above; the `Evaluator` column is the
   narrowest command that reproduces it.
2. **Which transition stopped.** For a class that claims registry rows, the row
   carries `blocked_transition` verbatim; the run record repeats it per class
   in `blocked_transitions`. That is the thing you are now not allowed to do.
3. **Which evidence was checked.** The row's `specimen` names the exact bytes
   the gate read. For `upstream-provenance` and `id-history` the checked
   evidence is the overlay declaration and `tests/promise_machine_id_history.json`.
4. **How to recover.** The row carries `recovery` verbatim, repeated per class
   in `recovery_actions`. A refusal never deletes or rewrites the failing
   source to produce a pass.

What a refusal does not tell you: whether the promise it guards is true in
fact. A green gate establishes that the named structural or binding fact held
on the bytes it read, and nothing further.

## Repository checks on this host

`python3 scripts/run_checks.py --full --jobs 12` selects 24 scopes and 25
checks. Twenty-three passed. Two failed, both for reasons that reproduce
unchanged at the pinned Step 6 parent
`29a7eb7567634283b6504ac4bbfb7e68da6a6864` with this step's changes stashed:

- `synkrisis-suite`: `BudgetCommandTests.test_small_budget_run_passes_and_records_its_method`.
  The run reports `peak_rss_mib` 29184 against a 512 MiB recorded budget, which
  is the macOS peak-RSS unit interpretation Step 6 already recorded. 116 tests,
  1 failure, at the parent and at this head.
- `lazarus-suite`: 599 tests, 15 failures and 86 errors inside the check graph,
  which inherits the default `/var/folders` temporary directory whose path
  length defeats the fixture stage on macOS. Re-run directly with
  `TMPDIR=/private/tmp` the same suite reports 599 tests and 10 failures, every
  one stopping at the existing macOS `platform cannot anchor fixture stage`
  refusal, with identical counts at the parent and at this head. The narrower
  run is the one to compare.

Neither suite reads any file this step changed. The step touches six paths:
`.gitignore`, `.horos/boundary.json`,
`plugins/hexaemeron/tests/test_check_runner.py`,
`tests/test_obligation_gate_demonstration.py`, and this report beside its run
record. The boundary changes only because deterministic regeneration walks the
three added files, moving `files_walked` from 2170 to 2173; no entry,
classification or byte total moves with it.

The root suite passes 941 tests at the parent and 964 at this head. The
difference is the twenty-three cases of the currency guard; the run-report
guard lands in the Hexaemeron suite instead.

## What this step repaired

The exit clause's own command exposed a defect. `run_checks.py --report
.reports/<name>.json` writes its report after building its plan, so the
invocation that writes one completes. `.reports/` was neither ignored nor owned
by the check map, so every later invocation saw it as a relevant untracked path
with no declared owner and refused with `unknown-ownership` before starting a
single check. The tree the step must prove clean was also no longer clean.

`/.elenchus/` already carried that rule for the Elenchus runner's report, with
the same rationale written into `.gitignore`. `/.reports/` now joins it. The
guard lives beside the Elenchus case it mirrors, in
`plugins/hexaemeron/tests/test_check_runner.py`, and fails without the ignore
rule.

## Unknowns

- The nine history cases and twelve upstream-provenance cases are declared
  inventories. No code reads either `cases.json`, so each case name is joined
  to the test that exercises its finding code by this record rather than by a
  gate. The finding codes themselves are exercised by the named methods.
- `PM005` is emitted by the checker, but no contract-suite method names it
  literally. Its coverage rests on the registry-wide specimen method rather
  than on a case of its own.
- The eleven-case evaluation grade is one recorded run of one named local model
  on one date. It establishes labelled-case classification and says nothing
  about repeatability, variance, or a second model.
- `scripts/verify_vendored_provenance.py` reaches upstream over the network and
  was deliberately not run. Upstream byte identity at the pinned commits is not
  re-established here; only the locally recorded digests and status fields were
  checked. That verifier also defines `PV001` and `PV002`, which no declared
  provenance case names, so those two paths stay unexercised by this record.
- Every exit status here is one run on one host: macOS on arm64, under the
  interpreter [`.python-version`](../../../.python-version) pins. Windows,
  Linux and other builds remain unobserved. The run record carries the exact
  interpreter string in `host`, and the currency guard holds it to the pin.
- Durations were observed and are reported as observation. On this host with
  twelve slots the whole check graph took 440s in the recorded run and 973s in
  an earlier pass; the Hexaemeron suite is its long pole at 431s and 577s
  respectively, so the graph is close to that one suite's own cost. Nothing
  here is a budget, a threshold or an optimisation claim.

## Non-goals

- Rewriting any skill result into a framework-owned schema.
- Claiming that the eighty declared promises are true in fact.
- Replacing Fizz, Solidity Auditor, Hypomnema, Sapheneia or Vulgate domain
  evaluation with a framework assertion.
- Reporting the recorded model grade as domain execution. The grade satisfies
  the `labelled-case-classification` gate and no other.
- Making any GitHub mutation. This demonstration is local and reads nothing
  outside the checkout.

## References

- Study and runbook: [`study.md`](study.md), [`runbook.md`](runbook.md)
- Standing decision record: `docs/decisions/ADR-066-bind-promise-obligations-to-gates.md`
- Evaluation packet contract and the run it verifies:
  [`evaluation-run.json`](evaluation-run.json),
  [`evaluation-answers.json`](evaluation-answers.json)
- Currency guard: `tests/test_obligation_gate_demonstration.py`
