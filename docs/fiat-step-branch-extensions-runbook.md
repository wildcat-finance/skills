# Runbook: honest step-branch extensions after push receipts

Derived from `.hexaemeron/study.md`, whose Study receipt binds SHA-256
`f04eaa0963cb1ff461193c4d3565f40829fa9cb20f58c079ae3e8db67bc32992`.
The run starts from `main` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`. Two steps keep the accepted
specification separate from the controller change while requiring the
classification, executable guard, durable guidance, generated copy, and
version record to ship as one product change.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation is not a reservation. The implementation may project the next
ordinary generation while building, but integration resolves the row against
one exact integration base. The held issue #363 frontier, its digest, and every
unrelated carryover remain unchanged.

## Step 1: Commit the receipted specification

**Goal.** Put the current run's accepted Study and Runbook in stable repository
locations before controller behaviour changes.

**Entry.** Run branch
`fiat/923-honest-step-branch-extensions-after-push-rec` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`, with the Study receipt and
post-spec marketplace receipt recorded, both ignored artefacts mechanically
clean, and no tracked worktree change.

**Exit.** `docs/fiat-step-branch-extensions-study.md` matches the receipted
Study under one exact presentation-only transformation: terminal two-space
Markdown hard breaks on physical lines 3, 4, and 5 become terminal `<br>`
tags. `docs/fiat-step-branch-extensions-runbook.md` is byte-identical to
`.hexaemeron/runbook.md`. Relative links resolve from their tracked locations.
Protasis accepts both tracked files, Imprimatur finds no defect, Hypomnema
accepts their pointers, the checked repository runner selects and passes every
owner required by the diff, and the tree has no undeclared tracked change.
Prove the exit with:

```bash
cmp <(sed '3,5s/  $/<br>/' .hexaemeron/study.md) docs/fiat-step-branch-extensions-study.md
cmp .hexaemeron/runbook.md docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-step-branch-extensions-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md
python3 scripts/run_checks.py
git diff --check
```

**Files.** `docs/fiat-step-branch-extensions-study.md`,
`docs/fiat-step-branch-extensions-runbook.md`,
`audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md`, its
generated synopsis, and `.horos/boundary.json` only when the deterministic
scan earns a change.

**Tests.** No product test changes in this step. Run the exact transformed
Study comparison, byte-identical Runbook comparison, Protasis in both modes,
Imprimatur, Hypomnema, the checked runner, and diff check from the Exit. The
source-bound audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-1.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: no executable boundary changes; the two bounded UTF-8
documents add no dependency, process, URL fetch, credential, or model action.
ephoros: no runtime signal changes; the Study already names the later operator
questions. metron: none, because this step makes no performance change or
claim. elenchus: no failure is repaired in this step, so no new guard is
claimed. hypomnema: the tracked copies preserve the design source, while the
governed Fiat generation row remains the standing decision record written in
Step 2.

## Step 2: Classify descendant tips and reverify their complete range

**Goal.** Let a waiting step branch continue only when its receipted head is
still in native history, while retaining every later signature, provenance,
GitHub, author, committer, pull-request, order, and integration gate.

**Entry.** Step 1's signed, audited, green head on the exact branch named by
the Step 2 implement directive. The tracked Study and Runbook match their
receipts, the run remains before integration, Fiat v5.38.1's author/publisher
split is unchanged, and `refuse_rewritten_stack` still rejects every unequal
waiting tip.

**Exit.** Equality remains the zero-relation-call path. After legacy
abbreviated identity resolution, an unequal waiting tip passes the topology
guard only when native `git merge-base --is-ancestor <recorded> <tip>` answers
status 0. Status 1 refuses with both exact commits and the branch without
asserting an unobserved GitHub cause; a missing object, timeout, start failure,
output cap, or any other status refuses as unknown. Fixed argv disables
replacement objects, lazy fetch, prompts, and inherited `GIT_*` substitution.
Current and already merged steps retain their existing skip rules. Every
refusal occurs before state or ledger mutation.

The focused real-repository fixture proves `P -> E`, equality without a
relation call, unrelated history, unavailable ancestry, replacement-ref
resistance, hostile inherited Git state, legacy abbreviated ancestor and
non-ancestor cases, skip behaviour, and byte-identical refusal state. The
descendant's later `done merge-step` proof records a repaired `effective_push`
for the exact live range after local signature/trailer and GitHub verification,
with author and committer attribution re-derived together, while the original
push receipt stays unchanged. Existing rewritten-stack, stack-topology, PR
head/base, run-branch movement, attribution, publisher-separation, and final
integration tests remain green.

The operator rule is aligned in `push-discipline.md`; ADR-021 is narrowed only
where it equated every unequal tip with a rewrite; the Fiat skill and Promise
Machine wording distinguish topology admission from current effective-push
evidence. ADR-052 remains unchanged. A proof document records the focused
red-on-parent and green-on-head results plus the three issue-904 ancestry
checks. The Fiat generation row records the chosen ancestry rule, the deferred
merge-time verification trade, the rejected re-receipt, repeated-preflight,
and permanent-equality options, the public issue and delivery links, and the
unchanged held frontier. The governed skill metadata matches the resolved row.
Hexaemeron package metadata advances by the repository's package-version rule,
portable runtime copies and their manifest are regenerated, Promise Machine
coverage agrees, and Horos reaches a deterministic fixpoint.

Prove the exit with:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_step_branch_extensions.py' -v
python3 plugins/hexaemeron/tests/test_push_receipt_identity.py -v
python3 plugins/hexaemeron/tests/test_stack_topology.py -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests -p 'test_version_propagation.py'
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md docs/fiat-step-branch-extensions-proof.md docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 scripts/run_checks.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`,
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`,
`audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md`, its
generated synopsis, and `.horos/boundary.json` as generated by Horos. No other
product path is in scope.

**Tests.** First preserve the raw-equality failure against Step 2's entry and
then the passing implementation result. Run every focused case and complete
suite named above without skips being counted as executed. The source-bound
audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_step_branch_extensions.py`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-2.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once. Warden
must return the Elenchus verdict without translating an inconclusive report
into a guard.

**Disciplines.** phylax: review exact remote-ref and native local-graph inputs,
fixed argv, the scrubbed Git environment, `--no-replace-objects`, status
0/1/error separation, timeout/output bounds, and the unchanged later GitHub
evidence boundary. ephoros: refusals name the step, branch, recorded head,
observed tip, and whether the answer is non-ancestor or unknown; they claim no
unobserved rewrite cause and add no persistent telemetry. metron: no
performance claim; equality remains zero-call and each unequal waiting branch
gets at most one bounded local relation call. elenchus: reproduce issue 904's
raw-equality failure in a minimal real `P -> E` graph, observe the new focused
test red on the unfixed parent and green on the implementation, and keep every
neighbouring test green. hypomnema: the Fiat generation row is the one durable
decision home; ADR-021 and operator guidance are aligned without a duplicate
ADR, ADR-052 stays separate, and interface comments explain the deferred
evidence boundary rather than restating code.

## Integration boundary

Before integration, reread `origin/main` and resolve the declared Fiat relation
against that one exact commit. If the projected generation or package metadata
is stale, use only the controller's signed `sync-run` path with a complete
affected-path revalidation receipt. Halt if any evolution epoch, maturity,
frontier status, held target, or digest changed unexpectedly, or if the current
controller cannot carry the correction without rewriting product history.

Merge Step 1 and then Step 2 into the run branch in controller order. Open one
run-level pull request to `main` whose exact body contains
`Closes wildcat-finance/skills#923`. Shoggoth remains the Git author; Laurence
Day is the explicitly authorised committer and signer under key
`B83B60AE16F5DD1A`; the `shoggoth-wildcat-labs[bot]` application publishes the
pull requests and issue comment. The closing comment carries the four relation
outcomes, exact guard and suite evidence, the merge-time verification-window
qualification, the unchanged issue #363 frontier, and every unrelated PR-922
carryover as outside this delivery. Shape it with Sapheneia, then run
Imprimatur, Vulgate with content held fixed, and Imprimatur again on the exact
posted bytes. Read every publication back without credentials and require HTTP
200 before receipting integration.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`docs/fiat-step-branch-extensions-runbook.md` as the byte-identical tracked
copy of this amended receipt, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, and
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`; permit Warden to append the Step 2 round
to `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` and
regenerate its synopsis; regenerate `.horos/boundary.json` after every other
source and generated path is final. After that complete source commit is
signed and the tree is clean, generate `.dead-code/baseline.json` with
`python3 scripts/dead_code.py baseline --write` and publish it as the only path
in a separate signed descendant commit, as the baseline's own publication
contract requires. No other product path is in scope.

Complete replacement Tests: First preserve the raw-equality failure against
Step 2's entry and then the passing implementation result. Run every focused
case and complete suite named in Step 2's `Prove the exit with` block without
skips being counted as executed. The source-bound audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_step_branch_extensions.py`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-2.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once. Warden
must return the Elenchus verdict without translating an inconclusive report
into a guard. Once every Step 2 source, documentation, generated runtime,
coverage and Horos change passes its named checks, commit that complete source
tree with a valid signature and the required trailers. From that clean source
commit run `python3 scripts/dead_code.py baseline --write`, require that only
`.dead-code/baseline.json` changes, commit that file alone as a separately
signed descendant with the same provenance, and then run
`python3 scripts/dead_code.py baseline --check`, every command in the original
Step 2 exit list, the complete base-scoped checked runner, and
`git diff --check` at the final implementation head. The check must report the
source commit as an ancestor, the baseline publication diff as exactly its
owned record, and zero added, resolved, or stale-suppression drift; candidate
count remains report-only.

**Why.** PR #934's public `dead-code / report` job failed after Step 1 because
`.horos/boundary.json` selected the workflow while the pinned baseline still
named the pre-run source. Its exact refusal listed the five Step 1 paths as
changes after publication. Step 2 also changes Horos, so the final delivery
cannot satisfy that command contract unless the generated baseline is
republished. This evidence appeared after the runbook receipt. The baseline
tool excludes its own record from the analysed source and accepts only a
second commit whose diff is exactly `.dead-code/baseline.json`, which is why
the added file cannot share the source commit.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`, and only the
`RewrittenStackRefusal` fixture, description, and assertions in
`plugins/hexaemeron/tests/test_hexctl.py` needed to drive native ancestry
status 1 and require the non-ancestor diagnostic without the unobserved GitHub
cause; change `plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`docs/fiat-step-branch-extensions-runbook.md` as the byte-identical tracked
copy of this amended receipt, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, and
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`; permit Warden to append the Step 2 round
to `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` and
regenerate its synopsis; regenerate `.horos/boundary.json` after every other
source and generated path is final. After that complete source commit is
signed and the tree is clean, generate `.dead-code/baseline.json` with
`python3 scripts/dead_code.py baseline --write` and publish it as the only path
in a separate signed descendant commit, as the baseline's own publication
contract requires. No other product path is in scope.

**Why.** The focused Step 2 guard is green, but the complete Hexaemeron suite
still contains `RewrittenStackRefusal`, whose synthetic unequal tips never
answer the new ancestry question and whose assertions require the removed
GitHub stacked-rebase causal claim. The required suite and the new diagnostic
contract cannot both pass while that fixture stays unchanged. Updating only
that test surface to return native status 1 preserves its actual purpose: a
waiting non-ancestor is refused before another merge receipt, the branch and
both commits are named, the wrong public-key repair remains ruled out, and no
cause the controller did not observe is asserted.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`, only the
`RewrittenStackRefusal` fixture, description, and assertions in
`plugins/hexaemeron/tests/test_hexctl.py` needed to drive native ancestry
status 1 and require the non-ancestor diagnostic without the unobserved GitHub
cause, and only `INTEGRATED_CONTROLLER_SHA256` in
`plugins/hexaemeron/tests/test_issue_429_recovery.py` needed to bind that
permanent composition guard to the changed controller; change
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`docs/fiat-step-branch-extensions-runbook.md` as the byte-identical tracked
copy of this amended receipt, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, and
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`; permit Warden to append the Step 2 round
to `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` and
regenerate its synopsis; regenerate `.horos/boundary.json` after every other
source and generated path is final. After that complete source commit is
signed and the tree is clean, generate `.dead-code/baseline.json` with
`python3 scripts/dead_code.py baseline --write` and publish it as the only path
in a separate signed descendant commit, as the baseline's own publication
contract requires. No other product path is in scope.

**Why.** The permanent issue-429 composition guard pins the integrated
controller digest and requires every Promise Machine binding to match it. Its
focused test now runs one case, exits 1 with one failure and no errors, and
compares the changed controller digest
`a9a28e3e22cb99ddb0f25a90aff0b8b3286d7734f590a281c498ee8b2e2bf4a1`
with the old `310dac029bca484532900068257fd8c6e9836e31e5f87b55aab9c8d4c0261115`.
The old digest occurs only in the already-authorised coverage manifest and
this one unscoped literal. Updating the literal moves existing integrity
evidence; it changes no issue-429 history or behaviour.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`, only the
`RewrittenStackRefusal` fixture, description, and assertions in
`plugins/hexaemeron/tests/test_hexctl.py` needed to drive native ancestry
status 1 and require the non-ancestor diagnostic without the unobserved GitHub
cause, and only `INTEGRATED_CONTROLLER_SHA256` in
`plugins/hexaemeron/tests/test_issue_429_recovery.py` needed to bind that
permanent composition guard to the changed controller; change
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`docs/fiat-step-branch-extensions-runbook.md` as the byte-identical tracked
copy of this amended receipt, and only the current-version sentence in
`docs/a-child-or-a-golden-retriever-study.md`; change
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, only the two current Fiat version
assertions in `tests/test_evolution_contract.py`,
`tests/test_child_or_golden_retriever_primer.py`, only
`EXPECTED_HEX_VERSION` and `EXPECTED_FIAT_VERSION` in
`scripts/build_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, and
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`; permit Warden to append the Step 2 round
to `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` and
regenerate its synopsis; regenerate `.horos/boundary.json` after every other
source and generated path is final. After that complete source commit is
signed and the tree is clean, generate `.dead-code/baseline.json` with
`python3 scripts/dead_code.py baseline --write` and publish it as the only path
in a separate signed descendant commit, as the baseline's own publication
contract requires. No other product path is in scope.

**Why.** The required evolution-contract suite runs 10 tests and fails one,
with no errors, because its two current-version assertions still pin Fiat
v5.38.1 while this step publishes Fiat v5.39.1. The required beginner
primer suite also reaches its deterministic current-state check and reports
nine passes and one failure because the builder still pins Hexaemeron `1.6.12`
and Fiat `5.38.1`; after those constants move, that same check requires the
study's explicit current-version sentence to carry `1.6.13` and `5.39.1`.
Updating these five literals keeps the version-bound guard and prose truthful.
It does not change the primer's historical starting versions, layout, source
art, generated bytes, or accepted product content.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`, only the
`RewrittenStackRefusal` fixture, description, and assertions in
`plugins/hexaemeron/tests/test_hexctl.py` needed to drive native ancestry
status 1 and require the non-ancestor diagnostic without the unobserved GitHub
cause, and only `INTEGRATED_CONTROLLER_SHA256` in
`plugins/hexaemeron/tests/test_issue_429_recovery.py` needed to bind that
permanent composition guard to the changed controller; change
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`docs/fiat-step-branch-extensions-runbook.md` as the byte-identical tracked
copy of this amended receipt, and only the current-version sentence in
`docs/a-child-or-a-golden-retriever-study.md`; change
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, and only
`test_fiat_state_shape_frontier_holds_the_task_identity_successor` in
`tests/test_evolution_contract.py`: require v5.39.1 as current/latest with the
issue #923, ADR-021, study and runbook evidence the new row actually carries;
require v5.38.1 immediately behind it with its unchanged issue #906, issue
#903 and ADR-052 evidence; and shift the existing v5.37.1 through v5.28.1
relative row positions back by one without changing any expected historical
version or evidence. Change `tests/test_child_or_golden_retriever_primer.py`,
only `EXPECTED_HEX_VERSION` and `EXPECTED_FIAT_VERSION` in
`scripts/build_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`, and
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`; permit Warden to append the Step 2 round
to `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` and
regenerate its synopsis; regenerate `.horos/boundary.json` after every other
source and generated path is final. After that complete source commit is
signed and the tree is clean, generate `.dead-code/baseline.json` with
`python3 scripts/dead_code.py baseline --write` and publish it as the only path
in a separate signed descendant commit, as the baseline's own publication
contract requires. No other product path is in scope.

**Why.** Moving only the two current-version assertions exposes the rest of
the same append-only successor test: its latest-row evidence still describes
v5.38.1, and its relative history starts at v5.37.1. The required suite runs
10 tests and fails one at the first stale evidence assertion; if that assertion
alone moved, the next stale negative index would fail. Rewriting or deleting
the v5.38.1 ledger row would destroy accepted history. The bounded test update
instead names the new row, preserves v5.38.1 as the immediate predecessor, and
moves every older positional assertion exactly one slot while keeping its
content fixed.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Tests: Preserve the raw-equality
failure against Step 2's entry and the passing implementation result. Run every
focused case and complete suite named in Step 2's `Prove the exit with` block,
plus every test added by the earlier amendments. Every focused behavioural,
legacy, version, generated-runtime, coverage, lint, prose, Horos, dead-code and
diff command must exit zero. The source-bound audit-fix runner remains
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_step_branch_extensions.py`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-2.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once. Warden
must return the Elenchus verdict without translating an inconclusive report
into a guard.

The complete unfiltered `python3 plugins/hexaemeron/tests/run_tests.py` census
must execute its whole manifest. On this Darwin checkout it may exit 3 only
with exactly 1,834 executed tests, two failure events, one error event and zero
skips, all three matching the entry evidence below; any additional or changed
failure, error, skip, missing test or scheduler fault refuses completion:

- `test_hexctl_checkpoint.HexctlCheckpointTests.test_resource_limits_refuse_before_publish`
  errors with macOS `Errno 63` while its unchanged fixture constructs the fifth
  200-byte path component below this already-long worktree, before controller
  code receives the deliberately overlong specimen;
- `test_issue_429_recovery.Issue429RecoveryTests.test_root_audit_is_the_exact_pinned_base_blob`
  reports current root-audit SHA-256
  `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`
  against its stale pinned digest
  `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`;
  the 93-line later append is already present at the anchored base; and
- `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`
  reports the same 14 pre-existing `plugins/homologia/**` paths whose sorted,
  newline-terminated list has SHA-256
  `24546ae5296e36960544549c6f43c570dfb09782e30bb9dc9388181b6e139c1b`.

Reproduce those three outcomes against the Step 2 entry or anchored-base bytes
before accepting the candidate census. No Step 2 product path may change to
repair, suppress or skip them. The complete base-scoped checked runner must
also execute; it may return nonzero only where it propagates this exact
three-event Hexaemeron census, while every other selected check succeeds.

Once every Step 2 source, documentation, generated runtime, coverage and Horos
change satisfies that acceptance, commit the complete source tree with a valid
signature and the required trailers. From that clean source commit run
`python3 scripts/dead_code.py baseline --write`, require that only
`.dead-code/baseline.json` changes, commit that file alone as a separately
signed descendant with the same provenance, and then run
`python3 scripts/dead_code.py baseline --check`, every command in the original
Step 2 exit list under this replacement acceptance, the complete base-scoped
checked runner, and `git diff --check` at the final implementation head. The
baseline check must report the source commit as an ancestor, the publication
diff as exactly its owned record, and zero added, resolved or stale-suppression
drift; candidate count remains report-only.

**Why.** The complete runner executed 1,834 tests after the fifth amendment
and exposed three events outside the focused Step 2 surface. Each reproduces at
entry: the macOS path ceiling is reached while the unchanged checkpoint test
builds its specimen, the legacy issue-429 equality predates this run's
controller-digest change, and the Homologia ownership gap already exists in
the anchored check map. Repairing any of them would broaden issue #923 into
unrelated plugin, historical-proof or cross-platform fixture work. Recording
the exact unchanged census keeps the complete runner visible without calling
those failures green or hiding a new regression.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds.
