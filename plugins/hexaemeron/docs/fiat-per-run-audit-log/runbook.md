# Runbook: give each Fiat run its own audit log path

Derived from `.hexaemeron/study.md`. Five steps. The two controller surfaces
the study chose are separate steps because they close separate boundaries: one
is a string reaching a filesystem path, the other is a declared value against a
configured one. The prose and the ledger row come after both, so no document
describes a rule the tree does not yet enforce, and the ledger row is written
at the last possible moment because two records took the same free identifier
in this repository twice this month.

Every step runs from the run worktree. `<entry>` in a step's commands is that
step's entry commit.

## Step 1: Commit the study and the runbook

**Goal.** Put the specification in the repository before any controller code
changes.

**Entry.** Run branch `fiat/576-give-each-fiat-run-its-own-audit-log-path` at
`103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`, study receipt recorded, no tracked
changes in the run worktree.

**Exit.** `plugins/hexaemeron/docs/fiat-per-run-audit-log/study.md` and
`runbook.md` exist and are byte-identical to the run's `.hexaemeron` copies.
Prove it with:

```bash
cmp .hexaemeron/study.md plugins/hexaemeron/docs/fiat-per-run-audit-log/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-per-run-audit-log/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/docs/fiat-per-run-audit-log/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/fiat-per-run-audit-log/runbook.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/docs/fiat-per-run-audit-log/study.md` and
`plugins/hexaemeron/docs/fiat-per-run-audit-log/runbook.md`.

**Tests.** None new; the step adds no code. Expect the suites unchanged at 349
root and 986 Hexaemeron. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-1.json`.

**Disciplines.** phylax: none, the step adds no code and opens no boundary.
ephoros: none, two committed documents emit nothing at runtime. metron: none,
no performance claim. elenchus: none, no failure in hand at this step.
hypomnema: this step is itself the record of what the run intends; the decision
record the study's item 12 names is step 4's.

## Step 2: Derive the run's audit log path at init and constrain the override

**Goal.** A run gets a log path no other run writes, with no operator action,
and `config set audit.log_path` can no longer name another run's file.

**Entry.** Step 1's exit state, on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path-step-1-commit-the-study-and-the-runbook`.

**Exit.** `DEFAULT_CONFIG` holds no literal audit log path. `cmd_init` writes
`audit/rounds/<flattened run branch>.md` into the run's config after the deep
copy, so `config get audit.log_path` answers with it before any round runs.
`cmd_config` refuses an `audit.log_path` value that is absolute, carries a `..`
component, carries a control character, escapes the target directory once
resolved, or whose basename differs from the run's derived name; it accepts one
that only moves the directory. A run whose state records no `run_branch` keeps
the unconstrained behaviour, because there is nothing to derive from. A refused
value leaves the state file byte-identical. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 scripts/promise_machine.py check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and
`plugins/hexaemeron/tests/test_hexctl.py`.

**Tests.** A new `AuditLogPathTests` class in
`plugins/hexaemeron/tests/test_hexctl.py`. Cases: a fresh run derives
`audit/rounds/<flattened run branch>.md`; two runs of different branches derive
different paths; an override that only moves the directory is accepted; an
override with a foreign basename is refused; an absolute path is refused; a
`..` component is refused; a control character is refused; a path escaping the
target is refused; a refusal leaves the state digest unchanged; and a run with
no `run_branch` in state keeps the unconstrained override. Expect about 10 new
tests, so roughly 996 Hexaemeron and 349 root. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-2.json`.

**Disciplines.** phylax: this step opens both string-to-path boundaries the
study's item 9 names, the branch name at `init` and the operator value at
`config set`. ephoros: the refusal is the only signal an operator gets, so it
names the supplied value and the required basename rather than reporting a bad
path. metron: none, one string operation at `init` and one comparison at
`config set`, with no performance claim. elenchus: the failure in hand is the
sync recorded by pull request 583, where the root log entered the overlap set
and owed a check; the guard is the derivation test, which fails against this
step's entry state. hypomnema: none here, the decision record is step 4's.

## Step 3: Bind the recorded round log to the configured path

**Goal.** An audit round can only record the file it was told to write, and
`hexctl next` says which file that is before the round is recorded.

**Entry.** Step 2's exit state, on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path-step-2-derive-the-run-s-audit-log-path`.

**Exit.** `audit-round --log` and `done audit --log` refuse a value that differs
from `config audit.log_path` once both are normalised, naming both paths in the
refusal. An omitted `--log` records the configured path rather than null,
because that is the file the round was under obligation to write. The
`audit-round` directive from `hexctl next` carries `log_path`. Rounds already
recorded in existing state keep the values they hold and are never rewritten. A
refused round appends nothing to `rounds` and leaves the state file
byte-identical. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 scripts/promise_machine.py check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and
`plugins/hexaemeron/tests/test_hexctl.py`.

**Tests.** A new `AuditRoundLogBindingTests` class in
`plugins/hexaemeron/tests/test_hexctl.py`. Cases: a round naming the configured
path is recorded; a round naming another path is refused and appends nothing; a
round with no `--log` records the configured path; a round naming the same path
in a different but equivalent spelling is accepted; `done audit --log` refuses a
divergent path; `next` names `log_path` on the audit-round directive; a round
recorded before this change keeps its stored value through a later round; and a
refused round leaves the state digest unchanged. Expect about 8 new tests, so
roughly 1,004 Hexaemeron and 349 root. The nine existing call sites that pass
`--log audit/AUDIT.md` move to the run's derived path. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-3.json`.

**Disciplines.** phylax: the step narrows an operator string that already
reached a receipt, so the boundary closes rather than opens; no new sink.
ephoros: the directive gains `log_path`, which is the signal answering which
file a round owes, and the round receipt records it. metron: none, two string
comparisons and no performance claim. elenchus: the failure in hand is the
free-string receipt the study's item 1 names, where a round could record a path
it never opened; the guard is the divergent-path test, which fails against this
step's entry state. hypomnema: none here; what the receipt now means is stated
in step 4's prose.

## Step 4: Reconcile the prose and record the decision

**Goal.** Every document that says where rounds go says the same thing, and the
reason the record is split is written where a reader will find it.

**Entry.** Step 3's exit state, on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path-step-3-bind-the-recorded-round-log-to-t`.

**Exit.** `plugins/hexaemeron/skills/fiat/references/audit-loop.md` states the
derived path and drops `audit/AUDIT.md` from its round commands.
`plugins/hexaemeron/README.md`'s config table states the derived default.
`plugins/hexaemeron/skills/fiat/SKILL.md`'s audit note says where a round's
record goes. `plugins/hexaemeron/skills/protasis/SKILL.md` item 2 stops naming
a default that no longer exists; that is a prose reconciliation and earns
Protasis no ledger row. `audit/AUDIT.md` gains an appended pointer and loses no
existing line. A decision record under `docs/decisions/` carries the split,
numbered against `main` immediately before the run's pull request merges.
Prove it with:

```bash
test "$(git diff <entry> -- audit/AUDIT.md | grep -c '^-[^-]')" = 0
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <changed prose>
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <changed prose>
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/README.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`, `audit/AUDIT.md`, and one new
file under `docs/decisions/`.

**Tests.** None new. `tests/test_shipped_prose_lints.py`,
`tests/test_marketplace_prose.py`, `tests/test_decision_records.py` and
`plugins/hexaemeron/tests/test_fiat_skill.py` already cover these files, and
`test_decision_records.py` is what catches a duplicated record number. Expect
the counts unchanged from step 3. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-4.json`.

**Disciplines.** phylax: none, the step changes documents and opens no
boundary. ephoros: none at runtime; the operator-facing signal shipped in step
3. metron: none, no performance claim. elenchus: none, no failure in hand.
hypomnema: this is the step the study's item 12 names, and it decides which
record each surface earns, from the decision record down to the appended
pointer.

## Step 5: Record the ledger row and demonstrate

**Goal.** Show the change working under a run the new controller initialises,
and record one generation row for it.

**Entry.** Step 4's exit state, on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path-step-4-reconcile-the-prose-and-record-t`.

**Exit.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new
generation row, retaining the prior frontier revision and digest byte for byte
and leaving the held issue 363 job untouched, with its version read from `main`
immediately before it is written.
`plugins/hexaemeron/skills/fiat/SKILL.md`'s frontmatter version matches it.
`plugins/hexaemeron/docs/fiat-per-run-audit-log/proof.md` records a scratch run
initialised in a temporary git repository by the tree at this step: its derived
`config audit.log_path`, a round recorded against that path, the same command
refused for a path that differs, and a `config set` refused for a foreign
basename. `.horos/boundary.json` matches the tree. `.hexaemeron/run-pr.md`
carries a `## Carried forward` section. Prove it with:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git diff --exit-code .horos/boundary.json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/fiat-per-run-audit-log/proof.md
```

**Files.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/docs/fiat-per-run-audit-log/proof.md`,
`.horos/boundary.json` if the scan earns an entry, and `.hexaemeron/run-pr.md`.

**Tests.** None new. `tests/test_evolution_contract.py` and
`plugins/hexaemeron/tests/test_evolution.py` check the row's arithmetic,
digest, and header agreement; `tests/test_version_propagation.py` checks the
frontmatter against the ledger; `tests/test_boundary_currency.py` checks the
boundary against the tree. Expect the counts unchanged from step 3. Elenchus
runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-5.json`.

**Disciplines.** phylax: none, the step writes documents and a ledger row and
opens no boundary. ephoros: none at runtime. metron: none, no performance
claim. elenchus: none, no failure in hand; the proof is a demonstration rather
than a reproduction. hypomnema: the ledger row is the record this step owes,
and the study's item 12 states why it is written last.
