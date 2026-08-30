# Runbook: assign ADR numbers at merge

Derived from the receipted study, SHA-256
`f7b2df81d3ad58e8ee606e9560546ba74a277e8c9bc88d9b4e028d544de99773`.
The run starts from `main` at
`6e42389ef20c11c948b2c97a4915d4c592503ee8`. The repository already supplies
its Python 3.14.6 pin, Apache-2.0 licence, plugin layout, signed Fiat controller,
and root and Hexaemeron CI. Step 1 preserves those foundations and adds the
tracked specification before executable behaviour changes.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
hypomnema | plugins/hexaemeron/skills/hypomnema/EVOLUTION.md | next-generation-after-integration-base
```

The relations allocate nothing while the branch is being built. Each skill may
project its next generation for the step branches, but the controller resolves
both rows together against the exact integration base and candidate head.
Neither held frontier moves.

## Integration assignment boundary

After all four step pull requests have merged into the run branch, the standing
record still exists only as
`docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md` and all
tracked prose cites `adr/assign-adr-numbers-at-merge-not-at-authoring`.
Immediately before the run-level pull request is admitted, fetch `origin/main`
and bind its exact commit as assignment base `B`. Use the checked-in Hypomnema
allocator to derive the canonical report from `B` and the signed product tip,
apply only the reported rename and first-heading substitution, then sign the
composition commit with the report's ordered `ADR-Assignment-Base` and
`ADR-Assignment` trailers.

Use the checked-in Fiat verifier read-only against that commit and report. The
active, init-pinned controller records the canonical bootstrap receipt before
any final GitHub mutation. When the controller directs `sync-run`, the signed
assignment composition is the active sync and carries the full integration
revalidation report. When `B` is already the product ancestor and no sync is
needed, the same checked report and trailers sit in one signed descendant; the
existing honest-descendant gate must accept its complete range before the
run-level pull request opens. A base move after either form invalidates the
mapping and requires a replacement composition from the unchanged product tip.

This bootstrap proves the repository mechanism. It does not make
`adr-assignments` required or change ruleset `21830871`. Production race
freedom remains pending a separately authorised canary and a live ruleset with
`enforcement=active`, strict up-to-date checks, the exact base-owned context,
and no bypass actors.

## Step 1: Commit the specification and unnumbered record

**Goal.** Put the accepted study, build steps, and standing unnumbered decision
record in their durable homes without changing executable behaviour.

**Entry.** Clean run branch
`fiat/888-assign-adr-numbers-at-merge-not-at-authoring-r2` at
`6e42389ef20c11c948b2c97a4915d4c592503ee8`, with the Study and marketplace
receipts verified and root 766-test and Hexaemeron 2,047-test baselines green.

**Exit.** The tracked study and runbook are byte-identical to their receipted
sources. The draft record has slug
`assign-adr-numbers-at-merge-not-at-authoring`, starts with
`# Decision: Assign ADR numbers at merge, not at authoring time`, carries the
repository's dated status and five decision sections, and contains no assigned
ADR number. Existing records and repository behaviour are unchanged. Prove the
exit with:

```bash
cmp .hexaemeron/study.md docs/adr-merge-assignment/study.md
cmp .hexaemeron/runbook.md docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/adr-merge-assignment/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/adr-merge-assignment docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/adr-merge-assignment docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 -m unittest tests.test_decision_records -v
python3 scripts/run_checks.py
git diff --check
```

**Files.** Create `docs/adr-merge-assignment/study.md`,
`docs/adr-merge-assignment/runbook.md`, and
`docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md`.
Permit Warden to append the configured issue-888 audit record and regenerate
its synopsis. Regenerate `.horos/boundary.json` only if the deterministic scan
earns a change. No other product path is in scope.

**Tests.** Add no product test in this step. Preserve the 766 root tests and
2,047 Hexaemeron tests and run every command in Exit. The source-bound audit
fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
its CLI format is `unittest-json-v1`, expected schema is
`elenchus.unittest.v1`, and report file is
`.elenchus/fiat-888-step-1.json`. The fresh report must contain non-zero
executed tests and no scheduler error.

**Disciplines.** phylax: none, because this step adds bounded Markdown and no
process, network, credential, dependency, or model boundary. ephoros: none,
because no unattended path changes. metron: none, because there is no
performance claim. elenchus: no observed executable failure is repaired here.
hypomnema: the tracked specification and unnumbered record establish the one
durable home for the cross-cutting decision without assigning its number early.

## Step 2: Add stable references and deterministic allocation

**Goal.** Teach Hypomnema to validate stable `adr/<slug>` identities and to
plan and apply the bounded `max(exact base)+1` draft transform from Git objects.

**Entry.** Step 1's signed, audited, green head on the branch named by the Step
2 implement directive. Its tracked study, runbook, and unnumbered record match
their receipts and no assignment exists.

**Exit.** Hypomnema accepts one prospective draft or final file for each
lowercase ASCII slug and resolves `adr/<slug>` in Markdown and supported source
comments. It refuses duplicate, dangling, malformed, non-ASCII, traversal,
control-character, oversized, or draft/final-mismatched identities. The
allocator reads complete immutable base and product commits with replacement
objects and inherited repointing variables disabled, ignores numeric holes,
sorts at most 32 slugs by ASCII bytes, changes only path and exact first
heading, preserves mode and all remaining bytes, and writes one canonical
`fiat-decision-assignments/v1` report with full object ids, blob ids, result
tree, ordered mapping, and fixed limits. Plan, apply, and replay agree or refuse
before mutation.

Legacy numbered records and `ADR-NNN` references stay valid. The unnumbered
issue-888 record remains a draft. The Hypomnema contract, governed generation
row, Promise Machine coverage, portable runtime copy, package metadata, and
marketplace metadata agree. Prove the exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_decision_assignments -v
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_checker -v
python3 -m unittest tests.test_decision_records -v
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/hypomnema/SKILL.md`,
`plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`,
`plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`,
`tests/test_decision_records.py`, `tests/promise_machine_coverage.json`, the
Hexaemeron package manifests, the two marketplace manifests, and the generated
Hypomnema files below `.agents/skills/promise-machine/runtime/`. Create
`plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py`,
`plugins/hexaemeron/tests/test_hypomnema_decision_assignments.py`, and bounded
fixtures below
`plugins/hexaemeron/tests/fixtures/hypomnema/decision-assignments/`. Permit the
configured audit record and synopsis plus `.horos/boundary.json` when their
owning phase or generator changes them. No other product path is in scope.

**Tests.** Start with red focused cases for a base ending at ADR-060 with holes
at 026, 027, and 059; bytewise multi-draft ordering; exact H1-only mutation;
duplicate and hostile slugs; shallow or wrong-typed objects; replacement and
repointed Git state; report/blob drift; and rollback on refusal. Make them green
without weakening the legacy checker suite. Preserve all existing tests and
report the final focused and full counts. The audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_hypomnema_decision_assignments.py`;
its CLI format is `unittest-json-v1`, expected schema is
`elenchus.unittest.v1`, and report file is
`.elenchus/fiat-888-step-2.json`.

**Disciplines.** phylax: hostile paths, Git objects, environment, file bytes,
and subprocess results cross the allocator boundary, so fixed argv, native
object reads, byte and count ceilings, no replacement objects, and atomic
refusal are mandatory. ephoros: the report exposes base, product, result tree,
mapping, limits, and bounded refusal code without secrets. metron: none,
because bounded correctness, not speed, decides acceptance. elenchus: the
old branch-local `max+1` behaviour is reproduced with two equal candidates and
the focused suite kills hole-filling and non-H1 mutation. hypomnema: stable
identity, placement, transform, and the governed generation row live in the
owning skill, while the repository ADR remains the cross-skill decision.

## Step 3: Bind assignment evidence to Fiat composition

**Goal.** Make Fiat verify the assignment report, signed trailers, exact sync
objects, and supersession history before recording or integrating a mapping.

**Entry.** Step 2's signed, audited, green head on the branch named by the Step
3 implement directive, with the Hypomnema allocator and report schema fixed and
the issue-888 decision still unnumbered.

**Exit.** Fiat has a read-only command that replays one canonical assignment
report against immutable base, product, and candidate commits. `done sync-run`
accepts an assignment report only when the path delta includes the exact
reported draft removals and final additions, the result tree and blobs match,
the signed composition carries one exact base trailer and the ordered mapping
trailers, and the worktree is unchanged. Its receipt records the report schema,
object ids, ordered mapping, commit-message digest, and limits. Missing,
duplicate, extra, malformed, stale, unsigned, moved-head, wrong-tree, or
superseded evidence refuses before state and ledger mutation. A replacement
sync recomputes the mapping and keeps the prior receipt only in bounded
append-only supersession history. `verify`, `status`, recovery, checkpoint, and
`done integrate` replay the active evidence.

The bootstrap path validates the checked-in code without replacing the
init-pinned controller: the new verifier is read-only, and the active
controller may store its canonical result under the versioned generic receipt
key used only by this self-hosting run. Later runs use the dedicated
`done sync-run` transition. The Fiat contract, push discipline, governed row,
Promise Machine coverage, portable copy, and package manifests agree. Prove the
exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_fiat_decision_assignments -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl_integration_path_bounds -v
python3 -m unittest plugins.hexaemeron.tests.test_fiat_skill -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 scripts/run_checks.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`, the generated Fiat files below
`.agents/skills/promise-machine/runtime/`, and package or marketplace metadata
already opened by Step 2. Create
`plugins/hexaemeron/tests/test_fiat_decision_assignments.py`. Permit the
configured audit record and synopsis plus `.horos/boundary.json` when their
owning phase or generator changes them. No other product path is in scope.

**Tests.** Add red-on-entry fixtures for stale base, altered result tree,
mismatched input or output blob, unordered or extra trailers, missing
signature, moved head, dirty worktree, partial receipt, recovery replay, and a
superseded sync retained in active ancestry. Add the passing exact report and
replacement-sync cases. Preserve existing sync, version-relation, checkpoint,
integration-path, and controller-state tests and report all counts. The
audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_fiat_decision_assignments.py`;
its CLI format is `unittest-json-v1`, expected schema is
`elenchus.unittest.v1`, and report file is
`.elenchus/fiat-888-step-3.json`.

**Disciplines.** phylax: reports, Git objects, signatures, trailers, inherited
Git state, and candidate bytes are untrusted, so parsing is closed and bounded
and every external command uses fixed argv with substitution disabled.
ephoros: receipts and refusals name exact base, product, candidate, mapping,
head, superseded sync, and bounded reason without claiming an unseen GitHub
cause. metron: none, because the controller adds no performance claim and keeps
existing object ceilings. elenchus: each malformed or stale evidence form must
fail against the entry implementation and pass only after the cause-level
guard. hypomnema: Fiat records transition evidence and one governed row; it
does not become a second home for the ADR placement or allocation policy.

## Step 4: Add the base-owned gate and demonstrate stale-base exclusion

**Goal.** Publish an unprivileged repository bootstrap whose base-owned status
validates the exact pull-request head and whose local demo proves the losing
same-number candidate must recompute.

**Entry.** Step 3's signed, audited, green head on the branch named by the Step
4 implement directive, with allocator and controller evidence complete, the
ruleset still observed as `evaluate`, and the issue-888 decision still a draft.

**Exit.** `.github/workflows/adr-assignments.yml` runs on
`pull_request_target`, checks out only the event's exact protected-base policy,
fetches base and candidate commits into a fresh bounded bare repository, never
executes candidate code, hooks, aliases, or configuration, and writes pending
then terminal `adr-assignments` status only on the exact event head. The
validator refuses an incomplete history, moved head, stale assignment base,
malformed report or trailers, report replay failure, and any candidate adding
a final decision record without the active assignment composition.

The root fixture starts two candidates at the same base ending in ADR-060,
observes both choose 061, advances fixture main with one, proves the other
`stale-base`, rebuilds it against the new base, and observes 062. Reverting the
base comparison makes that fixture fail. Workflow tests prove candidate scripts
and hostile Git configuration are never executed. A tracked proof records the
local commands and keeps the live qualification: ruleset `21830871` is not
changed, the context is not required, and production race freedom is not yet
claimed. All generated package, portable, check-map, audit-synopsis, and Horos
state is current. Prove the exit with:

```bash
python3 -m unittest tests.test_adr_assignment_workflow -v
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_decision_assignments -v
python3 -m unittest plugins.hexaemeron.tests.test_fiat_decision_assignments -v
python3 -m unittest tests.test_decision_records -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/adr-merge-assignment docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 scripts/run_checks.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Create `.github/workflows/adr-assignments.yml`,
`tests/test_adr_assignment_workflow.py`, and
`docs/adr-merge-assignment/local-proof.md`. Change
`tests/check-map-v1.json` and any exact workflow assertion that owns the new
base-owned status. Regenerate the portable runtime, package and marketplace
metadata, configured audit synopsis, and `.horos/boundary.json` only through
their owning commands. No live ruleset, status, canary, permission, bypass,
merge-method, issue, or other repository setting is changed by this step.

**Tests.** Add the two-candidate stale-base mutation test, exact-head status
lifecycle, base-only checkout, candidate-as-data, hostile hook/config/script,
shallow history, moved head, wrong integration id, bounded output, and missing
status cases. Preserve every earlier focused case, the 766 root-test baseline,
and 2,047 Hexaemeron-test baseline, then report final counts. The audit-fix
runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
its CLI format is `unittest-json-v1`, expected schema is
`elenchus.unittest.v1`, and report file is
`.elenchus/fiat-888-step-4.json`.

**Disciplines.** phylax: the privileged workflow consumes GitHub event fields,
remote Git objects, candidate paths, bytes, trailers, and statuses; candidate
code remains inert data and permissions stay least-privilege. ephoros: pending
and terminal statuses bind the exact head and expose base, mapping, enforcement
qualification, and fixed refusal reason while secrets and token material stay
absent. metron: none, because the hosted check has fixed byte, object, count,
and timeout ceilings but no speed claim. elenchus: the same-base two-candidate
fixture is the causal regression, and the mutation that removes the base check
must turn it red. hypomnema: the tracked local proof points to the standing
draft and the two governed skill rows instead of copying policy into a third
home.

## Final integration and external boundary

Merge Step 1 through Step 4 into the run branch in controller order. Reread
`origin/main`, perform the Integration assignment boundary above, run complete
affected-path revalidation, resolve both declared version relations against the
same exact base and assignment-bearing head, and open one run-level pull request
whose body contains `Closes wildcat-finance/skills#888`. Use a merge commit so
the checked base and candidate remain the final parents in controller order.

The final PR body and issue comment state exact commits, report digest, assigned
number, focused and complete test counts, audit verdicts, and the remaining
external prerequisite. Freeze those facts; shape the complete bytes with
Sapheneia, run Imprimatur, apply Vulgate without changing protected content,
and rerun Imprimatur on the exact publishable bytes. Publish through the
authorised human identity or GitHub App as repository policy directs, never the
flagged account. Read each published object back without credentials and
require HTTP 200 before the controller receipts integration and closes #888.

Do not activate or edit ruleset `21830871` in this run. A later separately
authorised operation must run the canary, verify Actions integration `15368` on
the exact head, make `adr-assignments` required under strict up-to-date checks,
set enforcement active, retain no bypass actors, and then record the live query.
Until then, describe this delivery as a complete local and repository bootstrap,
not an enforced production exclusion guarantee.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Exit: The tracked study and runbook are
byte-identical to their receipted sources. The draft record has slug
`assign-adr-numbers-at-merge-not-at-authoring`, starts with
`# Decision: Assign ADR numbers at merge, not at authoring time`, carries the
repository's dated status and five decision sections, and contains no assigned
ADR number. Existing records and repository behaviour are unchanged. Prove the
exit with:

```bash
cmp .hexaemeron/study.md docs/adr-merge-assignment/study.md
cmp .hexaemeron/runbook.md docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/adr-merge-assignment/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/adr-merge-assignment docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/adr-merge-assignment/study.md docs/adr-merge-assignment/runbook.md docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 -m unittest tests.test_decision_records -v
python3 scripts/run_checks.py
git diff --check
```

**Why.** The original Imprimatur command named the
`docs/adr-merge-assignment` directory, but that CLI reads each positional
argument as a file and refused the directory before checking any prose. The
replacement names the same two in-scope Markdown files explicitly and retains
the draft path.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: The tracked study and runbook are
byte-identical to their receipted sources. The draft record has slug
`assign-adr-numbers-at-merge-not-at-authoring`, starts with
`# Decision: Assign ADR numbers at merge, not at authoring time`, carries the
repository's dated status and five decision sections, and contains no assigned
ADR number. Existing decision records and executable behaviour are unchanged.
The dead-code baseline records the clean source commit containing the complete
Step 1 source tree and is published by a signed descendant that changes only
`.dead-code/baseline.json`. Prove the exit with:

```bash
cmp .hexaemeron/study.md docs/adr-merge-assignment/study.md
cmp .hexaemeron/runbook.md docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/adr-merge-assignment/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/adr-merge-assignment/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/adr-merge-assignment docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/adr-merge-assignment/study.md docs/adr-merge-assignment/runbook.md docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md
python3 -m unittest tests.test_decision_records -v
python3 scripts/run_checks.py --base 6e42389ef20c11c948b2c97a4915d4c592503ee8
python3 scripts/dead_code.py baseline --check
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest tests.test_boundary_currency.BoundaryCurrencyTests.test_the_committed_boundary_matches_a_fresh_scan -v
git diff --check
```

Complete replacement Files: Create `docs/adr-merge-assignment/study.md`,
`docs/adr-merge-assignment/runbook.md`, and
`docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md`.
Regenerate `.dead-code/baseline.json` through its clean-source, two-commit
publication sequence after every other Step 1 product byte is stable. Permit
Warden to append the configured issue-888 audit record and regenerate its
synopsis. Regenerate `.horos/boundary.json` only if the deterministic scan earns
a change. No other product path is in scope.

Complete replacement Tests: Add no product test in this step. Preserve the 767
root tests and 2,047 Hexaemeron tests and run every command in Exit. The
dead-code baseline's existing two-commit publication tests remain the guard for
the CI failure reproduced on pull requests 998 and 999. The source-bound audit
fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
its CLI format is `unittest-json-v1`, expected schema is
`elenchus.unittest.v1`, and report file is
`.elenchus/fiat-888-step-1.json`. A fresh report must contain non-zero executed
tests and no scheduler error when an audit fix requires one.

**Why.** Both published Step 1 branches failed the `report` job because
`python3 scripts/dead_code.py baseline --check` found source changes after the
recorded baseline. The local committed-diff selector did not run that
release-only check. The replacement adds the generated baseline to the bounded
file set and requires its own two-commit proof before the push receipt.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
