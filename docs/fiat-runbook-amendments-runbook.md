# Runbook: runbook amendment receipts

### Source receipts

```text
study sha256: 1258efb979883681cc97e850dc9b641dd63f37a0f7beaf5bd5029d705ef76806
starting ref: 84abae32d6d65b3a3ce27648ca144852a9e22e98
run branch: fiat/554-runbook-amendment-receipts
task issue: https://github.com/wildcat-finance/skills/issues/554
```

The topic is one capability with two dependency-ordered steps. Step 1 freezes
the accepted proposition in the tracked tree. Step 2 changes the two governed
skills together, demonstrates that a replacement exit reaches both delegated
consumers, and publishes one generation row for each skill without moving
either held frontier.

## Step 1: Publish the accepted runbook-amendment specification

**Goal.** Commit byte-identical tracked copies of the receipted study and
runbook, with their links, structure, source digest, and repository reading
boundary checked before controller code changes.

**Entry.** The exact run branch
`fiat/554-runbook-amendment-receipts` at starting ref
`84abae32d6d65b3a3ce27648ca144852a9e22e98`; the study receipt names SHA-256
`1258efb979883681cc97e850dc9b641dd63f37a0f7beaf5bd5029d705ef76806`.
No tracked file from this run exists at entry.

**Exit.** The following all hold:

1. `docs/fiat-runbook-amendments-study.md` is byte-identical to the receipted
   `.hexaemeron/study.md`.
2. `docs/fiat-runbook-amendments-runbook.md` is byte-identical to the
   receipted `.hexaemeron/runbook.md`.
3. Protasis accepts both tracked artefacts, Imprimatur reports no defect on
   either, and every relative link resolves from both publication locations.
4. The deterministic Horos scan describes the resulting tracked tree.
5. The root and Hexaemeron suites remain green and `git diff --check` exits 0.

**Files.** Create only:

- `docs/fiat-runbook-amendments-study.md`;
- `docs/fiat-runbook-amendments-runbook.md`;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/AUDIT.md` only for append-only Warden round records.

No canonical skill, script, test, manifest, ledger, CI file, or dependency
changes in this step's implementation. The Warden record is the only later-phase
addition.

**Tests.** Copy the two receipted artefacts without rewriting them, then run:

```bash
cmp -s .hexaemeron/study.md docs/fiat-runbook-amendments-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-runbook-amendments-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-runbook-amendments-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-runbook-amendments-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-runbook-amendments-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-runbook-amendments-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-runbook-amendments-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because this step adds static Markdown and no
new input or execution boundary. ephoros: none, because it adds no unattended
operation. metron: none, because it makes no performance claim. elenchus:
byte-identity, link, structural, boundary, and suite regressions stop the step
and any repair uses the exact runner above. hypomnema: the tracked study and
runbook are the durable homes selected by the accepted proposition.

## Step 2: Implement and demonstrate receipted runbook amendments

**Goal.** Add the bounded `hexctl amend runbook` transition, its recoverable
receipt and blocking rules, and the exact effective-step source consumed by
Mason and Warden; demonstrate a complete replacement exit and a causally bound
repair of a study-amendment block.

**Entry.** Step 1's signed, audited, prose-checked branch tip. The tracked
study and runbook are byte-identical to their receipts. The entry controller
has only `hexctl amend study`; appending any runbook bytes causes digest drift,
and `source_runbook_step` cannot carry a replacement criterion. Preserve those
red reproductions before changing the mechanism.

**Exit.** The following all hold:

1. `hexctl amend runbook --artifact <candidate>` accepts only one real final
   dated four-field block whose exact byte prefix hashes to the current
   runbook receipt, while build steps are active.
2. The candidate passes Protasis in runbook mode, cannot add, remove, reorder,
   renumber, rename, or duplicate steps, cannot touch completed steps, and
   carries one unambiguous entry-and-exit verdict for every unbuilt step.
3. The receipt records the prior, new, and amendment digests, date, touched
   steps, ordered verdicts, and current study digest under `amend:runbook`.
   `verify` recomputes both receipted artefacts.
4. Subject-labelled write-ahead recovery makes interrupted study and runbook
   amendments finish or roll back exactly once. One pending subject blocks
   every other command; two pending subjects refuse without deleting either.
   Legacy study markers and version-1 controller state remain readable.
5. `source_runbook_step` keeps one numbered and titled baseline block, ends
   the last baseline step before the first real amendment, and carries every
   digest-matched amendment that names that step in receipt order. It never
   admits a fenced decoy, duplicate step block, unrelated amendment, stale
   study binding, or later unreceipted drift.
6. A runbook amendment with a broken current-step verdict remains blocked. A
   holding amendment clears a study-amendment block only when it names the
   current step, carries the complete replacement field, and binds the current
   study digest; a later study amendment makes the older repair inapplicable.
7. The positive demo receipts a two-step runbook whose old exit checks
   `fiat-v1.0.0`, appends a complete exit checking `fiat-v2.0.0`, and observes
   the exact baseline and replacement bytes in both Mason and Warden packets.
   The repair demo starts from a broken study verdict and proves the causal
   clearing rule above.
8. Product negative guards cover subject confusion, prefix forgery,
   amendment selection, field ambiguity, verdict coverage, duplicate and
   effective source, repair precedence, partial write, pending collision,
   checker binding, later drift, legacy recovery, evidence overclaim, and
   generation collision. Cold review, not product code, discharges the
   Elenchus-identifier and audit-record-scope rows before this runbook is
   receipted.
9. Fiat exposes a separate `fiat-runbook-amendment` Promise whose successful
   evidence is limited to checked continuity, structure, receipt history, and
   source carriage. Promise Machine contracts and coverage remain complete.
10. On the recorded base, Fiat is `fiat-v5.21.1` and Protasis is
    `protasis-v4.7.0`. Each matching frontmatter, ledger header, and single
    generation row retains the prior frontier revision, digest, status,
    current-frontier text, and next job. Neither evolution counter moves and
    this run never uses `--frontier`.
11. If `main` has consumed either result label before integration, the run
    follows the study's collision rule: choose the next unused generation only
    while every held field and compatibility premise still matches, otherwise
    stop for a receipted amendment or halt. All changed artefacts and checks
    then agree on the final labels.
12. The focused tests, full suites, Promise Machine checks, three non-Solidity
    lints, prose lints, evolution checks, Horos check, syntax check, and diff
    check below all exit 0; an independent Warden round closes with zero
    findings.

**Files.** Scope is limited to:

- the Step 1 tracked study and runbook copies if a receipted amendment is
  required;
- `audit/AUDIT.md` for append-only Warden records;
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
- `plugins/hexaemeron/skills/fiat/SKILL.md`;
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/skills/protasis/EVOLUTION.md`;
- `plugins/hexaemeron/skills/protasis/SKILL.md`;
- `plugins/hexaemeron/skills/protasis/scripts/protasis.py`;
- `plugins/hexaemeron/tests/test_fiat_skill.py`;
- `plugins/hexaemeron/tests/test_hexctl.py`;
- `plugins/hexaemeron/tests/test_protasis_checker.py`;
- `tests/promise_machine_coverage.json`;
- `tests/test_evolution_contract.py` only if the existing generation contract
  lacks a guard required by this exact transition;
- `tests/test_promise_machine_contract.py` only if the new Promise shape needs
  a focused structural guard;
- `.horos/boundary.json` only if the deterministic scan changes it.

No state-version change, dependency, CI edit, manifest change, dynamic target
version relation, lost-ledger repair, stack-topology repair, generic
transaction framework, or Solidity file is in scope.

**Tests.** Add focused red-to-green guards to the existing Fiat and Protasis
suites. At minimum, name positive tests for the complete replacement exit in a
Mason packet, the same effective source in a Warden packet, and the bound
study-block repair. Add one negative guard for each mechanism in Exit and the
risk register. Run, in order:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_protasis_checker -v
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

The source-bound Elenchus runner contract for every repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-runbook-amendments-step-2.json
```

Warden must observe a repair guard red on the unfixed signed parent before
recording `guarded`. A no-fix round carries no Elenchus verdict. A missing,
stale, empty, malformed, or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: candidate paths, Markdown, checker subprocesses,
pending files, and delegated source are trust boundaries with bounded reads,
fixed argv, no shell, exact digests, atomic writes, and fail-closed recovery.
ephoros: receipts, status, next, verify, and packets answer the study's four
operator questions without a service metric or alert. metron: none, because
linear parsing stays inside existing safety ceilings and no speed claim is
made. elenchus: every failure is reproduced and each repair has a red guard on
the unfixed signed parent plus the exact reporter above. hypomnema: the two
canonical skill contracts, generation ledgers, tracked spec, Promise, and
append-only audit record are the selected durable homes.

After the complete Step 2 tree exists, run these gates in addition to Tests:

```bash
cmp -s .hexaemeron/study.md docs/fiat-runbook-amendments-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-runbook-amendments-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-runbook-amendments-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-runbook-amendments-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/protasis/SKILL.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/protasis/EVOLUTION.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-runbook-amendments-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-runbook-amendments-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m py_compile plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/tests/test_hexctl.py plugins/hexaemeron/tests/test_protasis_checker.py
git diff --check
```

The security suite is waived because the declared surface is Python and
Markdown only. The waiver does not replace the complete Phylax, Ephoros,
Hypomnema, Sapheneia-shaped audit record, risk-register disposition, or
independent zero-finding round. If round eight still has a finding, stop at
Fiat's `audit-verdict` instead of claiming closure.
