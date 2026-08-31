# Runbook: validate the dead-code suppressions file at the checkout

This run starts from `main` at
`c79d6781e2278642d1653d50671acdabb5867ef8` under CPython 3.14.6. It delivers
the study's selected `checkout-suppressions-command` as one capability. The
single step is both the scaffold fixed point, carrying the committed study and
runbook, and the demonstration fixed point, running the live checkout command
through the checked runner.

The existing repository layout, `.python-version`, workflow, `LICENSE`, and
standard-library-only toolchain remain the scaffold. This run adds no second
bootstrap, dependency, schema, generated product, or workflow-local command.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 1d61f2c933cd6872cdc9127a5a0b0d7a40467ad3aa485ccbe8a9126d62dba1d8
candidate | checkout-suppressions-command
```

## Step 1: Implement and demonstrate checkout suppression validation

**Goal.** Add one read-only command that validates committed suppressions
against the complete static report for the same clean current commit, and make
the `dead-code` scope run it.

**Entry.** Branch
`fiat/962-validate-the-dead-code-suppressions-file-at` at
`c79d6781e2278642d1653d50671acdabb5867ef8`, with the study and design lock
receipted, a clean tracked tree, and the existing
`python3 scripts/dead_code.py baseline --check` command green. The absent
`suppressions` subcommand on this parent is the reproduced gap. Before creating
the decision record, fetch `origin/main` and confirm that the temporary
unnumbered path below does not collide; its repository-global ADR number is
allocated only during integration against the then-current default branch.

**Exit.** All of the following hold:

1. `python3 scripts/dead_code.py suppressions --check` refuses a dirty tracked
   tree, resolves the current commit once, builds the fixed
   `BASELINE_ANALYSERS` report, requires usable analyser states, reads
   `.dead-code/suppressions.json` as a bounded regular file from that same Git
   commit, and delegates validity to the existing `load_suppressions` and
   `parse_suppressions` contract. It writes no product artefact. Success prints
   one bounded line naming the command, commit, analyser states, finding count,
   and suppression count; refusal is bounded stderr plus a nonzero exit.
2. Missing, directory, symlink, oversized, malformed, duplicate-key, broad,
   duplicate, unsorted, stale-target, mismatched-target, and unused suppression
   data refuse. Empty canonical entries and one exact non-empty entry pass.
   Dirty-tree, repository-substitution, and incomplete-analyser cases also
   refuse without producing a validation result.
3. `tests/check-map-v1.json` owns a separate literal-argv live check in the
   `dead-code` scope alongside `dead-code-suite`. The existing workflow's
   `python3 scripts/run_checks.py --scope dead-code` invocation selects both;
   `.github/workflows/dead-code.yml` gains no duplicate command.
4. `baseline --check` still reads suppressions from its recorded source commit,
   retains its `published`, `currency`, and `status` summary, and does not adopt
   checkout-suppression semantics. Ordinary `report` retains its no-analyser
   modes and remains independent of suppressions.
5. `docs/promise-machine/dead-code-v1.md` documents the dedicated command,
   bounded success and refusal meanings, and the direct correction-and-rerun
   recovery path. The temporary decision record
   `docs/decisions/check-current-dead-code-suppressions-separately.md` records
   the chosen placement, cites ADR-045, ADR-053, and ADR-059, and preserves the
   rejected `report` mode and dual-snapshot alternatives. Integration assigns
   the next free `ADR-NNN` identity and moves every current reference together.
6. `docs/dead-code-checkout-suppressions/study.md` and
   `docs/dead-code-checkout-suppressions/runbook.md` are byte-identical to the
   receipted artefacts. The `dead_code` capability entry in
   `tests/promise_machine_coverage.json` binds the changed runtime, tests, and
   operator document and names the new hostile selectors.
7. The focused suite, Elenchus report runner, checked `dead-code` scope, root
   selected checks, Protasis checks, prose checks, discipline lints, audit
   synopsis check, Horos check, and `git diff --check` all exit zero. The live
   empty suppression file passes. `/usr/bin/time -p` records both the checkout
   validator and `baseline --check` at or below 46 seconds on the same clean
   commit and interpreter; this is budget evidence, not an optimisation claim.

**Files.** Change `scripts/dead_code.py`, `tests/test_dead_code.py`,
`tests/check-map-v1.json`, `docs/promise-machine/dead-code-v1.md`, and
`tests/promise_machine_coverage.json`. Create
`docs/dead-code-checkout-suppressions/study.md`,
`docs/dead-code-checkout-suppressions/runbook.md`, and the temporary
`docs/decisions/check-current-dead-code-suppressions-separately.md`; integration
renames only that decision record and its current references to the next free
numbered ADR. Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` last only when the deterministic scan changes them. Leave
`.dead-code/baseline.json`, `.dead-code/suppressions.json`, both dead-code
schemas, `.github/workflows/dead-code.yml`, ADR-045, ADR-053, ADR-059, and the
existing issue #437 and #936 study/runbook copies unchanged. The controller's
audit record is not an implementation file.

**Tests.** Add focused tests for the two accepted cases and every refusal named
in Exit items 1 through 4, including current-commit binding, preservation of
historical baseline-source semantics, bounded diagnostics, check-map ownership,
and actual `dead-code` scope selection. No existing assertion is removed or
relaxed. Record the parent-red absence of the command, then the fixed-green
focused case and full affected scope. Run these exact commands from the
repository root:

```text
python3 scripts/dead_code.py suppressions --check
python3 scripts/dead_code.py baseline --check
python3 -m unittest tests.test_dead_code -v
python3 tests/emit_dead_code_report.py .elenchus/fiat-962-step-1.json
python3 scripts/run_checks.py --plan --scope dead-code
python3 scripts/run_checks.py --scope dead-code
python3 scripts/run_checks.py --base c79d6781e2278642d1653d50671acdabb5867ef8
cmp -s .hexaemeron/study.md docs/dead-code-checkout-suppressions/study.md
cmp -s .hexaemeron/runbook.md docs/dead-code-checkout-suppressions/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/dead-code-checkout-suppressions/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/dead-code-checkout-suppressions/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/dead-code-checkout-suppressions/study.md docs/dead-code-checkout-suppressions/runbook.md docs/decisions/check-current-dead-code-suppressions-separately.md docs/promise-machine/dead-code-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/check-current-dead-code-suppressions-separately.md docs/promise-machine/dead-code-v1.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
/usr/bin/time -p python3 scripts/dead_code.py suppressions --check > /dev/null
/usr/bin/time -p python3 scripts/dead_code.py baseline --check > /dev/null
git diff --check
```

The source-bound Elenchus runner for an audit repair is exactly
`python3 tests/emit_dead_code_report.py {report}` with one `{report}` argument.
Its report format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its report file is
`.elenchus/fiat-962-step-1.json`. The path must be fresh. A missing, stale,
empty, malformed, or infrastructure-failed report is `inconclusive`, not proof
that a repair is guarded.

**Disciplines.** phylax: the repository directory, Git object bytes, fixed
analyser subprocesses, and declared check argv cross existing bounded input and
execution boundaries; no shell, URL, credential, worktree-byte fallback, or new
dependency opens. ephoros: the bounded success line identifies the validated
commit and analyser states, while distinct command identities and actionable
stderr keep checkout validation separate from the historical baseline proof.
metron: both analyser-bearing commands have a 46-second wall-time ceiling and
zero durable-output budget, measured with the study's exact commands before and
after the change. elenchus: the missing command is the parent red; each hostile
cause gains the smallest fixed-green guard, the complete affected scope then
runs, and later audit repairs use the exact report contract above. hypomnema:
the numbered ADR will own the costly public-command and check-map placement,
the operator guide owns recovery, and the code and tests own interface details
and executable refusals.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Tests: Add focused tests for the two
accepted cases and every refusal named in Exit items 1 through 4, including
current-commit binding, preservation of historical baseline-source semantics,
bounded diagnostics, check-map ownership, and actual `dead-code` scope
selection. No existing assertion is removed or relaxed. Record the parent-red
absence of the command, then the fixed-green focused case and full affected
scope. Run these exact commands from the repository root:

```text
python3 scripts/dead_code.py suppressions --check
python3 scripts/dead_code.py baseline --check
python3 -m unittest tests.test_dead_code -v
python3 tests/emit_dead_code_report.py .elenchus/fiat-962-step-1.json
python3 scripts/run_checks.py --plan --scope dead-code
python3 scripts/run_checks.py --scope dead-code
python3 scripts/run_checks.py --base c79d6781e2278642d1653d50671acdabb5867ef8
cmp -s .hexaemeron/study.md docs/dead-code-checkout-suppressions/study.md
cmp -s .hexaemeron/runbook.md docs/dead-code-checkout-suppressions/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/dead-code-checkout-suppressions/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/dead-code-checkout-suppressions/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/dead-code-checkout-suppressions/study.md docs/dead-code-checkout-suppressions/runbook.md docs/decisions/check-current-dead-code-suppressions-separately.md docs/promise-machine/dead-code-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/check-current-dead-code-suppressions-separately.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/promise-machine/dead-code-v1.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
/usr/bin/time -p python3 scripts/dead_code.py suppressions --check > /dev/null
/usr/bin/time -p python3 scripts/dead_code.py baseline --check > /dev/null
git diff --check
```

The source-bound Elenchus runner for an audit repair is exactly
`python3 tests/emit_dead_code_report.py {report}` with one `{report}` argument.
Its report format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its report file is
`.elenchus/fiat-962-step-1.json`. The path must be fresh. A missing, stale,
empty, malformed, or infrastructure-failed report is `inconclusive`, not proof
that a repair is guarded.
**Why.** The receipted command supplied two positional drafts to a Brevitas CLI
that accepts one. The exact original invocation exited 2 with `unrecognized
arguments`, while each split single-draft invocation exits 0. Splitting only
that check preserves its two-file coverage without adding a capability or
changing product scope.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.
