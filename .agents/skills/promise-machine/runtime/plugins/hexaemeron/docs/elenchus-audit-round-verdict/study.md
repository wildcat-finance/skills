# Study: feed Elenchus verdicts into Fiat audit rounds

Assuming, unless corrected:

1. "A step claiming a bug fix" means the existing machine claim made when
   `hexctl audit-round` supplies `--fixes-commit`. A title, goal, finding count,
   `Tests` paragraph, or `Disciplines` paragraph is prose, not a receipt claim.
2. Issue 327 records evidence; it does not make `unguarded`, `passed`, or
   `inconclusive` block an audit round. Elenchus deliberately reports those
   states with exit 0 unless the caller chooses `--require-guard`.
3. The runbook remains the authority for the test command and report adapter.
   Fiat carries its exact source block to Warden and does not invent a second
   command or infer one from changed filenames.
4. Existing state-version-1 runs and audit rounds remain readable. A legacy
   round has no known Elenchus verdict; absence is not rewritten as a fifth
   verdict.
5. The exact entry ref is
   `454bf3c9930c94985e5eb6179f3b01be2bf741c2` on
   `fiat/327-elenchus-2-feed-the-guard-verdict-into-fiat`.
6. Delivery uses Python 3.12. The ambient `/usr/bin/python3` is 3.9.6 and
   cannot import the current controller's union annotations. The Elenchus Node
   fixture pins v26.6.0; this host currently has v22.22.3 and v26.0.0, so that
   one entry-baseline assertion is an environment gap rather than a green gate.

The first assumption settles an ambiguous phrase from issue 327. The current
controller has one checked, signed, range-bound fix assertion:
`--fixes-commit`. Treating prose as the predicate would make the controller
guess. If maintainers instead mean an implementation step whose natural-
language goal says "fix", that is a different schema change and must first add
an explicit, source-bound runbook declaration.

## 1. Problem statement

Elenchus already classifies a changed-test comparison as exactly one of
`guarded`, `unguarded`, `passed`, or `inconclusive`. Fiat's audit round records
findings, a log, a verified fixes range, three conditional lint exits, and a
timestamp, but no Elenchus verdict. An audit fix can therefore be receipted
while its guard state survives only as hand-written audit prose.

Build an additive audit-round field named `elenchus_verdict`. When a round
supplies `--fixes-commit`, the controller requires
`--elenchus-verdict <guarded|unguarded|passed|inconclusive>`, checks the value,
stores it in the round and ledger transition, and prints it in the receipt.
Warden receives the exact source-bound runbook step, uses that step's Elenchus
test-command/report contract against the fixes commit, and returns the verdict
for the orchestrator to receipt. A round with no fixes commit records
`elenchus_verdict: null`; a legacy round may omit the key.

The prototype is working when positive, refusal, reconstruction, and legacy
fixtures pass and this demo exits 0 in the repository's pinned Node v26.6.0
environment:

```bash
PATH=/opt/homebrew/opt/node@26/bin:$PATH python3.12 -m unittest \
  plugins.hexaemeron.tests.test_elenchus_checker \
  plugins.hexaemeron.tests.test_hexctl \
  plugins.hexaemeron.tests.test_fiat_skill \
  plugins.hexaemeron.tests.test_protasis_checker -q
```

The demo must show all four accepted values stored byte-for-byte, an omitted or
unknown value refused without state or ledger drift, a Warden packet carrying
the exact runbook step and command/report contract, and a legacy round with no
field surviving `status`, `next`, `verify`, and audit close.

## 2. Prior art

Elenchus `v1.1.0` owns the classifier. Its runner accepts a caller-owned
`--test-command` containing one `{report}` placeholder, one of
`unittest-json-v1`, `forge-junit-v1`, or `node-test-json-v1`, and a bounded
`--report-file`. Its JSON result already carries `ref`, `status`, `tests`, and
`detail`. No classifier change is needed.

Fiat `v5.11.1` supplies the mechanism to copy. Non-Solidity audit rounds owe
three explicit lint exits. `_next_directive` names the owed flags,
`cmd_audit_round` refuses absent or negative values, rejects a zero-finding
claim beside a non-zero lint result, and stores the structured `lints` object.
The Warden packet is source-bound to the study risk register, while only the
Mason packet currently receives `runbook_step`. `source_runbook_step` already
selects the exact numbered block with path and SHA-256; reuse it.

Protasis `v4.5.0` owns the runbook step. `Tests` and `Disciplines` are prose;
`done runbook` keeps only step titles. The generation must say that a step
which expects an audit fix names, under `Tests`, the exact Elenchus
`--test-command`, `--report-format`, and `--report-file` values. Fiat carries
the whole block to Warden rather than parsing a new Markdown grammar. The
reviewer checks that content contract; issue 327 does not turn free prose into
a controller predicate.

The last two merged pull requests touching Elenchus were read. PR 426 removed
the sibling-handoff paragraph across the marketplace. Its carried-forward
unlabelled marketplace-context clauses and pre-existing Brevitas findings in
Janus, Pandects, and Probitas remain outside issue 327; this run neither reopens
nor conceals them. PR 293 established the Promise Machine declaration. Its
host-picker and OAuth captures and the unrelated held skill frontiers remain
open outside this packet.

The two latest merged Fiat changes were also read because this work changes
Fiat. PR 477 created and retired dedicated run worktrees. Its carried-forward
empty-state-directory refusal residue, ignore mismatch, creation race,
archive/removal orphan, historical H003 alerts, and outside-tree reset case
remain out of scope. PR 474 receipted append-only study amendments. Its
runbook-repair transition, general transaction rewrite, operator-truth limit,
historical application-tree timing, and issue 363 remain open or accepted as
that PR states.

The in-scope audit records were read before choosing the design. The Elenchus
structured-runner rounds established the four states and fixed the descendant
report-path and stat/read race. The Fiat receipted-lint rounds established the
conditional-field pattern and its legacy missing-field behavior. The packet
and state-shape rounds established source-bound selectors, deterministic
packet reconstruction, container-only version-1 validation, and the fact that
`verify` does not independently attest arbitrary leaf claims. Protasis's
register rounds rejected a second parser for a format already owned elsewhere.

Issues 429, 369, 453, and 363 were read as downstream contracts. Issue 429's
schema and synopsis must retain the exact optional field and all four values.
Issue 369 must not discard a known value when it replaces full-log reading.
Issue 453 will bind stronger evidence and require `guarded` before production;
this issue must not pre-empt that transition. Issue 363 remains Fiat's held
frontier and is untouched.

## 3. Constraints and non-goals

This is generation work on three governed skills. Expected labels are
`elenchus-v1.2.0`, `fiat-v5.12.1`, and `protasis-v4.6.0`. Each generation row
retains its current frontier revision and SHA-256 byte-for-byte. Elenchus stays
mature with `None -- mature`; Fiat keeps issue 363; Protasis keeps the
amendment-block check. No evolution counter moves. The synchronized Hexaemeron
plugin manifests move together under their existing package rule.

The controller state version stays 1. The new round key is additive. New
rounds write either one accepted string or null. Readers use `.get`, so old
rounds with no key and old runs with no knowledge of this field still load and
verify. No historical audit log or state archive is rewritten.

Non-goals are changing Elenchus classification, adding a fifth status,
requiring `guarded`, proving the reported enum came from the named command,
binding report bytes or finding ids, parsing natural-language step intent,
building issue 429's audit schema/synopsis, building issue 453's pre-production
injection phase, changing state version, or moving issue 363.

**Always.** Use the exact runbook command/report triplet; run Elenchus against
the verified fixes commit; accept only the four canonical strings; record null
rather than inventing a verdict when no fix is claimed; preserve source path
and digest in the Warden packet; run the focused and complete gates with Python
3.12 and Node 26.

**Ask first.** Change the fix-claim predicate; make any verdict block audit
progress; add a state migration; change the Elenchus result schema; add a
dependency; alter issue 429 or 453's scope; rewrite an append-only record.

**Never.** Infer a verdict from process exit or stdout; call a missing field
`unguarded`; treat `passed` as guarded; record an unknown value; silently use a
different test command; parse step titles for intent; advance a held frontier;
edit historical audit entries.

## 4. Design options

### Option A: audit prose only

Tell Warden to append the status to `Leads not pursued`. This keeps the
controller unchanged, but repeats today's failure: no receipt checks presence,
spelling, or preservation. Issue 429 cannot consume it without scraping prose.

### Option B: one enum field, conditional on `--fixes-commit` (chosen)

Add `--elenchus-verdict`, require it exactly when `--fixes-commit` is present,
store one of the four values, and add the exact runbook step to Warden's brief.
Update Protasis and the two skill contracts to state the handoff. This follows
the lint-field pattern and uses a predicate the controller already verifies.

The chosen trade is that the receipt proves checked shape and association with
a verified fixes range, not the truth of the reported verdict or the report
bytes behind it. That is the same epistemic boundary as the lint exit fields.
Issue 453 owns the stronger finding/parent/test/command/report/result binding.

### Option C: parse a new bug-fix declaration from Markdown

Add a `Guard` field or fenced block to every runbook step, parse it during
`done runbook`, and derive the obligation from that marker. This can cover an
implementation whose title claims a fix even when the audit makes no fix
commit. It also adds a second runbook grammar, changes old runbooks, and needs
a repair path when an unplanned audit finding appears after receipt. That is
more machinery than issue 327 asks for.

### Option D: store the complete Elenchus JSON report

Put ref, tests, detail, command, format, file, diagnostics, and verdict into
each round. This gives stronger provenance, but duplicates Elenchus's schema,
expands state and downstream formats, and takes the evidence-binding work from
issue 453. Reject it here.

## 5. Risk register seed

```risk-register
fix-claim-confusion | audit-round fixes_commit and natural-language step intent | only a verified non-empty fixes_commit creates the conditional verdict obligation
enum-drift | Elenchus result status and Fiat CLI or stored round value | tests enumerate exactly guarded, unguarded, passed, and inconclusive and reject every other string
command-substitution | Warden's Elenchus invocation and the receipted runbook step | packet carries exact source bytes, path, and digest and the round uses the named command and report triplet
legacy-round-breakage | version-1 state and audit rounds written before issue 327 | status, next, verify, later rounds, and close accept a missing key without manufacturing a value
receipt-overclaim | operator-reported verdict stored beside a verified fixes range | contracts call the field checked-and-recorded evidence and do not claim report-byte attestation
downstream-loss | issue 429 schema and synopsis then issue 369 study source | fixtures retain the optional field and each of four values without renaming or collapsing them
frontier-drift | generation rows for Elenchus, Fiat, and Protasis | tests recompute versions and prove each prior revision, digest, status, and held target is unchanged
```

The audit loop must cite each id as reviewed or not applicable. A missing owed
verdict or unknown string is a receipt refusal. A non-`guarded` accepted value
is evidence to review, not a controller error in this generation.

## 6. Glossary seeds

| Term | Meaning |
| --- | --- |
| Fix claim | A round supplying the existing, locally verified `--fixes-commit` receipt field. |
| Elenchus verdict | One exact classifier string: `guarded`, `unguarded`, `passed`, or `inconclusive`. |
| Command/report contract | The runbook's exact test command, report format, and report-file values consumed by Elenchus. |
| Source-bound step | Exact numbered runbook Markdown plus path, SHA-256, number, and title. |
| Legacy round | A version-1 audit-round object written before `elenchus_verdict` existed. |
| Checked-and-recorded evidence | A value whose shape and association were checked; not an attestation that the producing command ran honestly. |

## 7. Sources

- Issue 327 and dependency issues 429, 369, 453, and 363 in
  `wildcat-finance/skills`.
- Entry commit `454bf3c9930c94985e5eb6179f3b01be2bf741c2`.
- `plugins/hexaemeron/skills/elenchus/{SKILL.md,EVOLUTION.md,scripts/elenchus.py}`
  and `plugins/hexaemeron/tests/test_elenchus_checker.py`.
- `plugins/hexaemeron/skills/fiat/{SKILL.md,EVOLUTION.md,references/audit-loop.md,scripts/hexctl.py}`
  and `plugins/hexaemeron/tests/{test_hexctl.py,test_fiat_skill.py}`.
- `plugins/hexaemeron/skills/protasis/{SKILL.md,EVOLUTION.md,scripts/protasis.py}`
  and `plugins/hexaemeron/tests/test_protasis_checker.py`.
- `plugins/hexaemeron/agents/warden.md`,
  `plugins/hexaemeron/skills/VERSIONING.md`, root `PROMISE_MACHINE.md`, and
  `tests/promise_machine_coverage.json`.
- Root `audit/AUDIT.md`: structured Elenchus reports, receipted lint rounds,
  delegation-packet rounds, state-shape rounds, and Protasis register rounds.
- Merged PRs 426, 293, 477, and 474 and their reachable
  `.hexaemeron/run-pr.md` carried-forward evidence.

## 8. Signals, and the questions behind them

This remains an interactive command-line controller, so no service telemetry
is added. The design follows [Ephoros](../../skills/ephoros/SKILL.md)
by answering operational questions through bounded JSON and refusal output.

The Warden needs to know which source bytes own the command, whether a verdict
is owed, which value will be stored, and why a receipt stopped. The packet's
runbook path/digest, the directive's conditional field, the audit-round JSON,
and named refusal answer those questions. The controller must not print report
contents or environment secrets.

## 9. Boundaries, per capability

The only new capability boundary is source-to-subprocess handoff: runbook text
supplies arguments to Elenchus. [Phylax](../../skills/phylax/SKILL.md)
owns that boundary. Warden uses the existing Elenchus argv interface without a
shell; Elenchus itself splits the declared test command, confines the report
to its detached worktree, clears inherited report state, and bounds report and
diagnostic reads.

The controller opens no new network, filesystem-write, credential, or package
boundary. It reads already-receipted runbook bytes, validates an enum, and
writes its existing atomic state and append-only ledger. The Promise Machine
boundary stays narrow: Fiat records the Elenchus result but does not widen the
Elenchus promise.

## 10. The budget, or its absence

No new performance claim is made. [Metron](../../skills/metron/SKILL.md)
therefore adds no benchmark. The relevant bound is correctness and existing
controller caps, measured by the focused test command in item 1. Elenchus keeps
its existing timeout and byte caps; this generation adds no unbounded scan or
subprocess.

## 11. The fail-closed posture

[Elenchus](../../skills/elenchus/SKILL.md) owns the four verdicts
and guard convention. Fiat stops before mutation when a fix claim lacks the
field or supplies an unknown value. It leaves state and ledger bytes unchanged
and names `--elenchus-verdict` plus the four accepted values. A valid
`unguarded`, `passed`, or `inconclusive` value is recorded honestly rather than
relabeled or refused; policy enforcement is deferred to issue 453.

The regression order is red first: add focused cases that show the current
controller accepts `--fixes-commit` with no verdict and rejects the new CLI
flag, then implement the gate. The final fixed-tree command is item 1's Python
3.12/Node 26 suite, followed by the complete commands below.

```bash
python3.12 -m unittest discover -s tests
PATH=/opt/homebrew/opt/node@26/bin:$PATH python3.12 plugins/hexaemeron/tests/run_tests.py
python3.12 scripts/promise_machine.py check
python3.12 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py
python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3.12 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For each changed prose file, also run Imprimatur and Brevitas. Run both
Protasis modes over the committed study and runbook. A failing gate stops the
step; it is not converted into an audit verdict.

## 12. Decisions and their homes

[Hypomnema](../../skills/hypomnema/SKILL.md) governs the record
choice. The fix-claim predicate, four-value closed enum, checked-not-attested
receipt boundary, null/missing legacy treatment, and decision not to enforce
`guarded` are governed skill choices. Record them once in the generation rows
of Elenchus, Fiat, and Protasis, with cross-links rather than a duplicate ADR.
The CLI/state field name is part of Fiat's controller interface and belongs in
Fiat's row and audit-loop reference.

Finding a wrong predicate during study costs this paragraph. Finding it after
state and synopsis consumers ship costs a compatibility path, so the runbook
must preserve the exact predicate and field name.

## Success criteria and runbook boundary

1. Four table-driven cases record the four accepted strings in both state and
   ledger; reconstruction returns the same Warden packet and next directive.
2. Missing or unknown values with `--fixes-commit` fail before mutation, name
   the field and accepted values, and leave state and ledger digests unchanged.
3. A no-fix round records null, and a legacy round lacking the key passes
   `status`, `next`, `verify`, a later round, and `done audit`.
4. Warden receives `runbook_step` with exact Markdown, path, SHA-256, number,
   title, and the runbook-owned Elenchus command/report contract; Mason's packet
   stays byte-compatible.
5. Elenchus's four classifier cases and result schema are unchanged; issue 429
   and Promise Machine fixtures preserve the optional field and all values.
6. Generation rows and frontmatter match, each held or mature frontier is
   byte-identical, all commands in items 1 and 11 exit 0 under the pinned
   toolchain, and no unrelated carried-forward item changes state.

The runbook should use three dependency-ordered steps: contract and ledger
surfaces; controller/packet/tests; full demonstration and synchronized package
surfaces. Each begins and ends green. Step 1 records these decisions, step 2
proves the behavior red then green, and the last step runs the demo and all
repository gates. No step may combine issue 429 or 453 work with this change.

## Study readiness

Study-side checks: 9/9 pass. All twelve items are answered; items 8 through 12
answer by citing their owning skill; the last two target PRs and every in-scope
audit record were read; carried-forward work is disposed by name; assumptions,
commands, chosen trade, and operational boundaries are explicit. The six
runbook-shape checks are deferred until the runbook exists, so the complete
pre-receipt count is not yet claimable.

Residual semantic uncertainty: the issue author did not separately define
"claiming a bug fix". The selected `--fixes-commit` reading is the only current
machine claim and therefore governs the runbook; a maintainer correction would
require re-deriving it before implementation. Known entry-environment fact:
the focused 330-test baseline exits 1 only because the fixture requires Node
v26.6.0 while this host has v22.22.3 and v26.0.0. That is not waived from the
delivery gate.

### Amendment -- 2026-08-22

**What changed.** Step 2 may update only the shared Fiat runtime-source digest in `tests/promise_machine_coverage.json` for its three existing runtime bindings when `hexctl.py` changes. The canonical promise text and field maps stay unchanged. Step 3 carries this amendment into the committed study copy.
**Why.** `python3.12 scripts/promise_machine.py check` returned three PM071 findings: the controller change moved the bound source digest from `6118483811cff145275fe04e82880b356bc182c92152039e88d13a941c5e2f13` to `01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870`. The runbook condition that allowed this fixture to change only with canonical promise text is false because the fixture also binds runtime-source bytes.
**Steps touched.** Steps 2 and 3.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
