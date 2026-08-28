# Study: carry over, inoculate, and complete the affected-scope parallel test runner

Starting revision: `5489863196006d8e8b45799d74b56208cac65e4d`
(`main`). This study governs a replacement Fiat run for
[`wildcat-finance/skills#622`](https://github.com/wildcat-finance/skills/issues/622),
with [`#621`](https://github.com/wildcat-finance/skills/issues/621) retained as
its signing-isolation prerequisite.

## Assumptions

- The published
  [replacement comment](https://github.com/wildcat-finance/skills/issues/622#issuecomment-5423433742),
  `622-CARRYOVER.md` at SHA-256
  `08048f48dfea9dc4bbdc08d08c40b182853c66a74d327e46bb776034c2f6e486`,
  and `622-INOCULATION.patch` at SHA-256
  `108eb3a907c49e8ad99508526fd328e101f331ae343a2a9e63c5595e85541c6e`
  are the sole cumulative reconstruction source. Conversation history and
  intermediate audit deltas are not reconstruction inputs.
- The archived signed tree at
  `f78f6b4c990c41629f4b77ceafe4977f016aeba1` records prior evidence. It is
  neither the new base nor an active controller to resume.
- The packet's Step 1 and Step 2 work is not accepted merely because it once
  passed tests. All eighteen source paths and all twenty-three Step 2 findings
  must be reconstructed on one current-base tree before any product test,
  lint, reporter, acceptance check, or audit round.
- Every invocation discovers its current tests. Tests may be added, removed or
  renamed between implementation and audit loops; no historical count is a
  scheduler input or acceptance constant.
- #621 changes only freshly created, non-signature fixture repositories.
  Contributors may author and sign delivery commits with their own identities
  and keys. No Shoggoth-specific signer belongs in product behavior or policy.
- Step 3, the checked impact map and repository-wide executor, and Step 4, the
  demonstration, measurement and contributor documentation, remain pending.
- Current `main` already owns ADR-035 for a different decision. The packet's
  logical ADR-035 therefore maps to ADR-038 on this base. That rename and its
  reference substitutions are the only currently known non-identity path
  transform.

## 1. Problem statement

The first #622 attempt solved real problems but exhausted its audit loop
without an independent clean round. Its eight Step 2 Warden rounds found
twenty-three medium-severity mechanisms. Each was reproduced, fixed and given
a guard on the halted tree, but every round still found something. That tree
also stopped before the affected-scope selector, the one-budget repository
executor, the final measurement and the contributor-facing documentation were
built. Copying its last green test output would therefore confuse a fixed tree
with a completed delivery.

The replacement has two jobs. First, it must make the complete prior result
present and mechanically inspectable on current `main`, including #621's
disposable-signing boundary and every Step 2 inoculation. Second, it must
finish #622: choose checks from declared scope plus the actual diff, execute
independent work concurrently under one shared quota-aware process budget,
and prove exact coverage of a freshly discovered test manifest. Timing data
may improve assignment only; it never supplies membership or a cached verdict.

The user is a Wildcat contributor waiting on comprehensive local feedback.
A working prototype is the complete current-base inoculation plus a checked
selector and one-budget executor that can print its plan, run that plan, and
prove fresh exact-once coverage. The proving path is the bootstrap gate,
focused parent-red guards, serial and automatic runs on one frozen source, a
full repository plan/run, and an independent zero-finding Warden round.

Success is checkable only when all of the following hold:

1. Both published attachments are downloaded or copied independently and
   match their published SHA-256 values before their content is used. The
   archive commit and tree are verified as provenance, not checked out as the
   new base.
2. One machine-readable inoculation record names all eighteen logical source
   paths, their current-base target paths and content identities, plus all
   twenty-three finding IDs, owner paths, exact guard names and thirteen
   families. A bootstrap verifier compares that record with the verified
   packet and patch rather than trusting the record to validate itself.
3. The complete eighteen-path union is reconstructed on one tree. The
   bootstrap verifier exits zero on that tree before the first product test,
   lint, reporter, acceptance check or Warden round. A partial reconstruction
   has no green state.
4. The ADR collision is resolved deterministically: the logical packet path
   ending in `ADR-035-select-and-schedule-repository-checks-from-one-graph.md`
   lands as the next-free ADR-038 path, and packet references to that decision
   are rewritten together. Any other current-base conflict stops the
   reconstruction until the runbook records a meaning-preserving resolution.
5. #621's hostile inherited-signer guard passes while existing signature
   verification remains intact. No global or source-checkout Git configuration
   changes, and no contributor identity is selected by product code.
6. The Step 2 runner rediscovers a fresh ordered manifest in the coordinator
   and workers, verifies one manifest identity, assigns its disjoint union,
   accounts for every test exactly once and preserves all genuine failures.
   Added audit tests enter the next invocation without a code or policy change.
7. Automatic concurrency is derived from available CPU and quota signals with
   conservative headroom and capped by runnable work. A positive `--jobs`
   override remains explicit. Single-worker and multi-worker execution use the
   same bounded transport and result semantics.
8. Unexpected successes, worker loss, output-drain loss, invalid private
   results, manifest mismatch, duplicate or missing execution and unsafe
   report/cache paths cannot produce green. Test assertion failures remain
   distinct from scheduler and environment failures.
9. `tests/check-map-v1.json` resolves declared scope plus committed, staged,
   unstaged and relevant untracked changes to one deterministic dependency
   closure. Unknown or ambiguous ownership, stale commands and cycles refuse
   before execution. A human plan and a versioned JSON plan explain every
   inclusion and widening.
10. `scripts/run_checks.py` executes independent checks, suite shards and
    ordered groups under one shared process budget. Nested runners receive only
    their allocated capacity, so local parallelism cannot multiply beyond the
    global ceiling.
11. Step 4 compares alternating serial-control and automatic-policy samples on
    one frozen revision. Manifest membership and assertions match for every
    sample; measured gain must exceed observed spread without a new failure
    class or unacceptable resource growth.
12. After the complete fixed tree is green, a Warden who did not implement the
    fixes performs a fresh round and records zero findings. Any new finding is
    reproduced, fixed at cause and added to the cumulative map before another
    independent round. Prose, push and integration remain downstream of that
    zero-finding receipt.

## 2. Prior art

The carryover packet is unusually strong prior art because it records the
whole failed-to-finish attempt rather than only its last delta. It identifies
the signed source chain, final tree, exact patch, audit receipt chain, eighteen
paths, twenty-three findings, guards, families, measurements and evidence
gaps. The published attachment hashes were independently reproducible during
this study. Re-generating the patch from its named preimage to archived fixed
tree also produced the published patch hash. Those checks establish source
identity; they do not establish current acceptance.

The first attempt's ten commits have valid direct-primary signatures from the
recorded Shoggoth primary fingerprint and exact provenance trailers. This is
useful chain evidence only. PRs
[#627](https://github.com/wildcat-finance/skills/pull/627) and
[#626](https://github.com/wildcat-finance/skills/pull/626) expose Step 1 and its
audit for review, but open pull requests are not replacement-run receipts and
Step 2 was never published.

The current runner's merged history also constrains the replacement. PR
[#493](https://github.com/wildcat-finance/skills/pull/493) carries secure,
source-bound Elenchus reporting, and PR
[#579](https://github.com/wildcat-finance/skills/pull/579) binds structured
observation prefixes. The parallel coordinator must aggregate through those
interfaces; workers do not mint independent release evidence. The copied
runner tests require `plugins/hexaemeron/tests/run_tests.py` to remain
self-contained.

Issue [#434](https://github.com/wildcat-finance/skills/issues/434) and merged PR
[#513](https://github.com/wildcat-finance/skills/pull/513) provide the local
precedent for an exhausted Fiat run: reconstruct the complete cumulative union
before tests, retain a mechanism-to-guard map, then earn a later clean round.
The root audit also records that duplicate ADR numbers are corrected by
renumbering and preserving the decision's meaning. This supports ADR-038 here
without pretending the filename collision was a clean patch application.

Current audit sources were read in their governed modes. Root and Hexaemeron
records had fresh generated synopses; the exhausted #622 audit was read
directly from its archive because it is not on current `main`. Its complete
Covered, Not checked, Elenchus verdict and Leads fields remain evidence. No
current audit entry closes the missing independent round.

External mechanisms support, but do not replace, the repository evidence:
Python `unittest` discovery creates the suite objects and honours `load_tests`;
pytest-xdist shows the value of controller/worker collection parity and
index-based distribution; Bazel query demonstrates a maintained dependency
graph for reverse-impact selection; Git clone/config document isolated
snapshot and repository-local configuration; and OS/cgroup interfaces provide
capacity signals rather than one universal worker number.

## 3. Constraints and non-goals

Always:

- begin from the recorded current-base commit and preserve unrelated work;
- verify packet, patch, archive and map identities before reconstruction;
- reconstruct the full cumulative union by path and meaning on one tree before
  any product verification command;
- derive a fresh source identity, impact plan and ordered test manifest for
  every invocation;
- union requested scope with actual changed paths and print every widening;
- preserve canonical discovery, assertions, test timeouts, bounded failure
  output and the existing hardened report interface;
- keep one global process budget across commands, suites, shards and ordered
  groups; and
- treat the machine-readable map and its independent bootstrap verifier as an
  acceptance boundary, not documentation.

The exact starting ref is
`5489863196006d8e8b45799d74b56208cac65e4d` on
`fiat/622-carryover-inoculate-affected-scope-runner`. The observed study
toolchain is CPython 3.14.6, Apple Git 2.50.1, Node.js 26.6.0 and Darwin on
arm64. Product implementation remains Python-standard-library and Git based;
Node.js is observed repository context, not a new dependency.

Ask first:

- before adding a third-party runtime dependency, hosted workflow, remote
  service or result cache;
- before changing a signature-test expectation, production signing policy,
  public report schema or Promise Machine contract;
- before changing ownership or downstream-consumer edges beyond the accepted
  #622 scope; and
- before resolving a newly discovered current-base conflict by anything other
  than a meaning-preserving path transform recorded in the runbook.

Never:

- resume, merge, rebase or cherry-pick the exhausted branch as the new
  controller or acceptance base;
- build and test intermediate audit deltas or claim their earlier results for
  the replacement tree;
- hard-code a discovered test total or fixed automatic worker total;
- use timing history or a prior pass to omit work or supply a verdict;
- change global Git configuration, contributor keys, signer programs or the
  source checkout's Git configuration;
- conceal source movement, partial execution, lost output or unexpected
  successes behind a green aggregate; or
- push, publish, integrate or close either issue before the controller and
  independent audit gates authorize it.

Non-goals:

- Remote execution, remote verdict caching and a hosted scheduler are outside
  this delivery.
- The selector does not infer semantic ownership from imports. Maintainers own
  a checked declarative graph that includes prose, generated surfaces, ordered
  commands and named consumers.
- This work does not optimise individual test bodies, weaken isolation or
  increase existing test timeouts to hide contention.
- Hosted CI expansion and live validation on every operating system and quota
  implementation are evidence gaps, not implied deliverables.
- Solidity code and harness behavior are unchanged. Existing Solidity command
  groups may be represented by the selector, but no contract work is
  authorized.

## 4. Design options

### Option A: resume the exhausted controller and finish its remaining steps

This preserves its local state but violates the packet's restart boundary.
The old base predates current `main`, every Step 2 round found an issue, and
the old controller cannot receipt a current-base reconstruction. Reject.

### Option B: cherry-pick selected fixes or reimplement the remembered shape

This can appear cleaner than a large patch, but selection is exactly how an
audit mechanism, guard or signing fixture gets lost. A hand-built checklist
can agree with itself while omitting a packet row. It also gives no independent
proof that the eighteen-path union was present before tests. Reject.

### Option C: verified cumulative inoculation, then complete the runner

Choose this option. It has one bootstrap boundary and four implementation
stages.

First, preserve verified local copies of the two published attachments under
the run-local carryover directory. Add
`tests/fixtures/issue-622-inoculation-v1.json` with schema
`wildcat.issue-622-inoculation.v1`. It records the attachment hashes, archive
commit/tree, each logical source path and current target path, an archive
content identity, every finding ID, owner, guard set and family, and the sole
ADR transform. Add `scripts/verify_issue_622_inoculation.py`, which accepts the
verified packet, patch, record and repository root as explicit paths. It
recomputes attachment hashes, parses the patch's complete path set, parses the
packet's finding table, compares both with the record, checks current targets,
and uses Python AST discovery to prove every named test guard exists. A focused
product guard invokes the same library against bounded fixtures. The verifier
must not import values solely from the record it is checking.

Second, materialise every path in the following union before executing that
verifier. `source` is the packet/patch identity; `target` is the current-base
home. All mappings are identity mappings except the explicit ADR collision.

| # | source | target | role |
| ---: | --- | --- | --- |
| 1 | `audit/rounds/fiat-622-fix-disposable-fixture-signing-and-add-affec.md` | same | exhausted audit evidence |
| 2 | `audit/rounds/fiat-622-fix-disposable-fixture-signing-and-add-affec.synopsis.md` | same | generated audit synopsis |
| 3 | `docs/affected-scope-test-runner/study.md` | same | first-attempt receipted study copy |
| 4 | `docs/affected-scope-test-runner/runbook.md` | same | first-attempt receipted runbook copy |
| 5 | `docs/decisions/ADR-035-select-and-schedule-repository-checks-from-one-graph.md` | `docs/decisions/ADR-038-select-and-schedule-repository-checks-from-one-graph.md` | standing selector and scheduler decision |
| 6 | `plugins/hermes/skills/hermes/scripts/test_hermes.py` | same | disposable-repository signing isolation |
| 7 | `plugins/hexaemeron/tests/github_transport_cases.py` | same | timing-sensitive transport fixture isolation |
| 8 | `plugins/hexaemeron/tests/run_tests.py` | same | fresh-manifest bounded parallel runner |
| 9 | `plugins/hexaemeron/tests/test_disposable_git_signing.py` | same | hostile inherited-signing matrix |
| 10 | `plugins/hexaemeron/tests/test_elenchus_checker.py` | same | copied reporter and checker compatibility |
| 11 | `plugins/hexaemeron/tests/test_hexctl.py` | same | disposable signing and transport fixtures |
| 12 | `plugins/hexaemeron/tests/test_kronos_scoreboard.py` | same | disposable-repository signing isolation |
| 13 | `plugins/hexaemeron/tests/test_parallel_test_runner.py` | same | scheduler and cumulative inoculation guards |
| 14 | `plugins/horos/tests/test_demonstration.py` | same | disposable-repository signing isolation |
| 15 | `plugins/horos/tests/test_scoped_entry.py` | same | disposable-repository signing isolation |
| 16 | `plugins/horos/tests/test_universe.py` | same | disposable-repository signing isolation |
| 17 | `tests/promise_machine_coverage.json` | same | runner/report release-surface binding |
| 18 | `tests/test_boundary_currency.py` | same | disposable-repository signing isolation |

The word `same` is serialised in the machine record as an exact source-target
equality, not inferred by a human reader. References within the reconstructed
study, runbook and decision are updated from the colliding ADR path to ADR-038
in one declared transform. The verifier rejects an undeclared transform,
omitted path, additional patch path, duplicate target or missing file. Only
after it exits zero may the run execute #621 and Step 2 product checks.

Third, retain the following complete finding map. Every owner is
`plugins/hexaemeron/tests/run_tests.py`; every guard is in
`plugins/hexaemeron/tests/test_parallel_test_runner.py`. The durable JSON uses
arrays for guards and exact strings for IDs, paths and families.

| finding | retained mechanism | owner | guard set | family |
| --- | --- | --- | --- | --- |
| `S2-R1-01` | Validate private worker objects, schemas, slots and replay metadata before use. | `plugins/hexaemeron/tests/run_tests.py` | `test_result_file_slot_is_bound_before_reconciliation`; `test_non_object_result_is_a_scheduler_error_not_an_exception`; `test_invalid_record_cannot_replay_forged_output`; `test_replayed_text_is_bound_to_its_byte_metadata` | `private-result-validation` |
| `S2-R1-02` | Retain validated partial shard execution evidence. | `plugins/hexaemeron/tests/run_tests.py` | `test_scheduler_error_summary_keeps_validated_worker_evidence`; `test_structured_summary_preserves_each_shards_execution_evidence` | `structured-evidence` |
| `S2-R2-01` | Use one bounded manifest, canonical indices and sequence bindings. | `plugins/hexaemeron/tests/run_tests.py` | `test_execution_sequences_correlate_before_result_use`; `test_manifest_and_summary_have_explicit_byte_limits` | `structured-summary-bounds` |
| `S2-R2-02` | Aggregate only validated compact partial counts and outcomes. | `plugins/hexaemeron/tests/run_tests.py` | `test_scheduler_error_summary_keeps_validated_worker_evidence` | `structured-evidence` |
| `S2-R3-01` | Bind truncated replay to exact UTF-8 head, tail, marker and byte count. | `plugins/hexaemeron/tests/run_tests.py` | `test_truncated_output_requires_the_full_bounded_head_and_tail`; `test_bounded_text_capture_has_one_exact_utf8_truncation_shape`; `test_invalid_record_cannot_replay_forged_output` | `bounded-output` |
| `S2-R3-02` | Keep text in coordinator-owned bounded pipes and result JSON bounded. | `plugins/hexaemeron/tests/run_tests.py` | `test_parallel_worker_output_uses_only_coordinator_owned_pipes`; `test_near_cap_unicode_worker_record_fits_its_private_file` | `result-cap-composition` |
| `S2-R3-03` | Bind timing-cache read, temporary creation, replacement and cleanup to one no-follow directory. | `plugins/hexaemeron/tests/run_tests.py` | `test_timing_cache_read_refuses_a_linked_parent_outside_the_run_root`; `test_timing_cache_atomic_replace_stays_on_its_bound_directory` | `cache-path-boundary` |
| `S2-R3-04` | Translate excessive JSON nesting and numeric parse failures into stable refusals. | `plugins/hexaemeron/tests/run_tests.py` | `test_deep_json_is_a_stable_corrupt_cache_not_a_recursion_escape`; `test_existing_json_number_refusals_remain_stable` | `malformed-json` |
| `S2-R4-01` | Preserve multiple subtest failures as test evidence instead of rejecting them against top-level `testsRun`. | `plugins/hexaemeron/tests/run_tests.py` | `test_multiple_failing_subtests_remain_test_failure_evidence` | `unittest-outcomes` |
| `S2-R4-02` | Treat pipe read and close failures as scheduler evidence. | `plugins/hexaemeron/tests/run_tests.py` | `test_pipe_read_failure_is_scheduler_evidence` | `bounded-output` |
| `S2-R5-01` | Derive the worker-result cap from every bounded field and encoding reserve. | `plugins/hexaemeron/tests/run_tests.py` | `test_worker_result_limit_is_derived_from_every_bounded_field` | `result-cap-composition` |
| `S2-R5-02` | Refuse oversized numeric tokens before float conversion. | `plugins/hexaemeron/tests/run_tests.py` | `test_large_parseable_numbers_use_stable_scheduler_refusals` | `numeric-boundary` |
| `S2-R6-01` | Treat oversized timing-cache numbers as visible neutral entries. | `plugins/hexaemeron/tests/run_tests.py` | `test_large_parseable_cache_number_is_a_visible_neutral_entry` | `numeric-boundary` |
| `S2-R6-02` | Route single-worker execution through the private worker transport and bounded pipes. | `plugins/hexaemeron/tests/run_tests.py` | `test_single_worker_uses_the_private_worker_transport`; `test_single_worker_child_fd_output_is_bounded_and_replayed` | `single-worker-parity` |
| `S2-R6-03` | Bound aggregate outcome counts before cross-shard materialisation. | `plugins/hexaemeron/tests/run_tests.py` | `test_cross_shard_outcome_counts_refuse_before_aggregate_overflow`; `test_uneven_outcome_counts_at_the_sequence_limit_remain_valid` | `aggregate-accounting` |
| `S2-R7-01` | Contain aggregate refusal without rebuilding the rejected sequence. | `plugins/hexaemeron/tests/run_tests.py` | `test_public_coordinator_contains_cross_shard_aggregate_refusal` | `aggregate-accounting` |
| `S2-R7-02` | Report top-level tests and outcome events without negative inferred passes. | `plugins/hexaemeron/tests/run_tests.py` | `test_failure_event_summary_never_reports_negative_passes` | `unittest-outcomes` |
| `S2-R7-03` | Bound scheduler-error fallback to one error plus omitted count, size and digest. | `plugins/hexaemeron/tests/run_tests.py` | `test_oversized_scheduler_errors_have_a_bounded_refusal_event` | `structured-summary-bounds` |
| `S2-R7-04` | Traverse suites iteratively with cycle and incremental item limits. | `plugins/hexaemeron/tests/run_tests.py` | `test_deep_and_cyclic_suites_have_stable_manifest_boundaries`; `test_manifest_item_limit_stops_discovery_incrementally` | `discovery-boundary` |
| `S2-R8-01` | Escape test output that could forge the reserved structured-run prefix. | `plugins/hexaemeron/tests/run_tests.py` | `test_test_output_cannot_forge_the_structured_run_summary` | `report-framing` |
| `S2-R8-02` | Convert ordinary suite-iterator exceptions into bounded scheduler refusals. | `plugins/hexaemeron/tests/run_tests.py` | `test_suite_iterator_failures_are_structured_scheduler_refusals` | `discovery-boundary` |
| `S2-R8-03` | Convert ordinary `TestCase.id()` callback exceptions into bounded scheduler refusals. | `plugins/hexaemeron/tests/run_tests.py` | `test_test_id_failure_is_a_structured_scheduler_refusal` | `discovery-boundary` |
| `S2-R8-04` | Count every yielded suite item against the incremental discovery limit. | `plugins/hexaemeron/tests/run_tests.py` | `test_sparse_suite_iteration_consumes_the_item_limit` | `discovery-boundary` |

The thirteen required families are `private-result-validation`,
`structured-evidence`, `structured-summary-bounds`, `bounded-output`,
`result-cap-composition`, `cache-path-boundary`, `malformed-json`,
`unittest-outcomes`, `numeric-boundary`, `single-worker-parity`,
`aggregate-accounting`, `discovery-boundary` and `report-framing`. The machine
record rejects an unknown family, duplicate finding ID, empty guard set or a
guard not found in the current AST.

Fourth, complete rather than merely reconstruct the capability. Step 3 adds
`tests/check-map-v1.json`, `scripts/run_checks.py` and focused bounded tests.
The map declares exact ownership, named consumers, fixed argv, working
directories and ordered command groups. The planner unions requested scopes
with every actual diff surface, closes dependencies, validates the entire
graph, freezes a source snapshot and emits human and `wildcat.check-plan.v1`
plans. The executor starts no shell, holds one global slot budget, passes a
bounded allocation to nested suite runners, drains all started work, and emits
one `wildcat.check-run.v1` report.

Finally, Step 4 measures serial control against quota-aware automatic execution
on the same frozen source, publishes the observed distribution and makes the
checked runner the contributor entrypoint. The replacement study and runbook
are copied under distinct replacement names so the reconstructed first-attempt
records remain legible. An independent Warden then audits the complete fixed
tree and must record zero findings before prose, push or integration.

## 5. Risk register seed

```risk-register
artifact-substitution | A local or downloaded packet or patch differs from the published cumulative source | Hash both attachments, regenerate the path set, and compare the machine record with parsed packet and patch content before use
partial-inoculation | A path, finding, guard or family is omitted while a self-consistent local checklist passes | Require the independent bootstrap verifier to compare all eighteen paths and twenty-three findings directly with verified artifacts before product checks
current-base-conflict | A mechanically clean patch hides a semantic collision or overwrites current work | Compare current paths and decision identities by meaning, allow only the declared ADR transform, and stop on any additional conflict
signing-scope | Fixture isolation changes a real signature test or contributor signing policy | Configure only each newly created non-signature repository and run hostile plus existing signature matrices
manifest-drift | A committed test total omits tests added during audit loops | Discover a fresh ordered manifest per invocation and compare identities rather than a fixed count
assignment-loss | Missing, duplicate or foreign assignments still aggregate green | Prove the disjoint union of assignment, start and completion records before green
global-oversubscription | Nested suite workers multiply the repository executor budget | Use one shared slot authority and pass bounded child allocations to nested runners
quota-misdetection | One capacity signal exaggerates safe local concurrency | Take the minimum positive usable signal, apply conservative headroom, cap by runnable work and report the inputs
cache-authority | Timing history becomes an implicit result cache or membership source | Permit exact-ID finite durations to weight only the current manifest and test corrupt or stale data as neutral
output-loss | Pipe, truncation or descendant lifetime behavior loses evidence or hangs completion | Keep bounded coordinator-owned capture, surface drain faults, and require an explicit descendant-lifetime disposition and guard
report-forgery | Test text or a replaced path forges or overwrites structured evidence | Escape reserved prefixes and retain exclusive no-follow source-bound report creation
source-movement | A changing checkout is reported as a failed test or an accepted stale run | Execute an immutable attempt snapshot, supersede one moving attempt, and return unstable-source after bounded retry
impact-omission | A changed path or downstream consumer receives no applicable check | Validate total ownership, named dependency closure and actual-diff widening before execution
ordered-breakage | Parallel execution reorders commands whose state transitions depend on sequence | Represent ordered groups explicitly while scheduling only independent groups concurrently
audit-recursion | A new Warden finding is fixed without joining the cumulative map | Require parent-red evidence, cause fix, new guard, map extension and another independent full round
evidence-overclaim | Missing live platform or hosted-CI coverage is described as proved portability | Record synthetic versus live evidence separately and retain named evidence gaps
```

## 6. Glossary seeds

- **Published source:** the named issue comment and the two attachments after
  their bytes match the published hashes.
- **Current base:** commit
  `5489863196006d8e8b45799d74b56208cac65e4d`, from which this replacement
  controller started.
- **Archive:** the prior signed fixed tree used for provenance and content
  comparison, never as the replacement base.
- **Cumulative union:** the complete eighteen logical paths plus Step 1,
  twenty-three Step 2 mechanisms, all guards and pending Steps 3 and 4.
- **Logical source path:** the path named by the verified patch. **Target path**
  is its current-base home after an explicitly declared transform.
- **Bootstrap verifier:** the artifact-anchored checker that must pass after
  reconstruction and before any product verification command.
- **Inoculation:** a reproduced mechanism, cause-level remediation, named
  regression guard and family retained together.
- **Finding family:** one of the thirteen stable mechanism classes used to
  prove cumulative coverage across audit rounds.
- **Scope:** a contributor-declared capability boundary. **Derived scope** is
  ownership inferred from actual repository changes. The executed scope is
  their dependency-closed union.
- **Check map:** the versioned declarative ownership, command and dependency
  graph. **Plan** is its deterministic resolution for one source identity.
- **Manifest:** the fresh ordered, unique test identities discovered from one
  attempt snapshot. Its cardinality is observation, not configuration.
- **Shard:** a disjoint index subset of one manifest. **Check job** is one
  selected command or suite. Both consume the same global process budget.
- **Timing cache:** bounded, optional exact-ID duration advice used only for
  balancing the current manifest.
- **Superseded attempt:** an attempt discarded because its source moved.
  **Unstable source** is the bounded terminal state after repeated movement;
  neither is a test failure.
- **Independent clean round:** a Warden review of the complete fixed tree by an
  agent other than its implementer that records no findings.

## 7. Sources

Authoritative reconstruction sources:

- [#622 replacement comment](https://github.com/wildcat-finance/skills/issues/622#issuecomment-5423433742)
- [`622-CARRYOVER.md`](https://github.com/user-attachments/files/31458010/622-CARRYOVER.md),
  SHA-256
  `08048f48dfea9dc4bbdc08d08c40b182853c66a74d327e46bb776034c2f6e486`
- [`622-INOCULATION.patch`](https://github.com/user-attachments/files/31458011/622-INOCULATION.patch),
  SHA-256
  `108eb3a907c49e8ad99508526fd328e101f331ae343a2a9e63c5595e85541c6e`
- archive ref
  `archive/622-affected-scope-parallel-runner-attempt-1@f78f6b4c990c41629f4b77ceafe4977f016aeba1`,
  tree `7507f0e13b3c6f846adf9fe7d075a8ce0e7baa82`

Task and repository evidence:

- [#621](https://github.com/wildcat-finance/skills/issues/621) and
  [#622](https://github.com/wildcat-finance/skills/issues/622)
- Step 1 review PRs [#627](https://github.com/wildcat-finance/skills/pull/627)
  and [#626](https://github.com/wildcat-finance/skills/pull/626)
- current runner integration PRs
  [#493](https://github.com/wildcat-finance/skills/pull/493) and
  [#579](https://github.com/wildcat-finance/skills/pull/579)
- cumulative carryover precedent
  [#434](https://github.com/wildcat-finance/skills/issues/434) and
  [#513](https://github.com/wildcat-finance/skills/pull/513)
- `audit/AUDIT.md` through its fresh `audit/AUDIT_SYNOPSIS.md`,
  `plugins/hexaemeron/audit/AUDIT.md` through its fresh synopsis, the relevant
  fresh round synopses for prior runner/report work, and the archived #622
  source audit plus its generated synopsis
- current `plugins/hexaemeron/tests/run_tests.py`, root and Hexaemeron
  contracts, and current `docs/decisions/ADR-035-bind-volunteer-selection-to-an-explicit-intent-handoff.md`

External primary references:

- [Python `unittest` discovery](https://docs.python.org/3/library/unittest.html#test-discovery)
- [Python usable process count](https://docs.python.org/3/library/os.html#os.process_cpu_count)
- [pytest-xdist distribution](https://pytest-xdist.readthedocs.io/en/stable/distribution.html)
- [Bazel query language](https://bazel.build/query/language)
- [Linux cgroup v2 CPU controller](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files)
- [Git clone](https://git-scm.com/docs/git-clone) and
  [Git configuration scopes](https://git-scm.com/docs/git-config#FILES)

Discipline contracts applied rather than restated:

- `plugins/hexaemeron/skills/protasis/SKILL.md`
- `plugins/hexaemeron/skills/phylax/SKILL.md`
- `plugins/hexaemeron/skills/ephoros/SKILL.md`
- `plugins/hexaemeron/skills/metron/SKILL.md`
- `plugins/hexaemeron/skills/elenchus/SKILL.md`
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`

## 8. Signals, and the questions behind them

This capability follows Ephoros. It adds no unattended service or external
alert target; the operator console plus versioned JSON records are the durable
surfaces. Signals answer these questions:

1. **Did reconstruction use the published bytes?** Record packet and patch
   digests, archive identity, current base, logical and target path counts,
   transform IDs, finding/guard/family counts and the bootstrap verdict.
2. **What source and plan ran?** Record source snapshot, base, map digest,
   requested and derived scopes, changed paths, dependency expansions,
   selected and omitted check IDs, and a reason for each decision.
3. **Was every discovered test executed exactly once?** Record manifest digest
   and observed cardinality, assignment/start/completion sequences, per-shard
   outcomes and the final disjoint-union verdict.
4. **Was work kept within capacity?** Record available capacity signals,
   automatic or explicit budget source, effective job count, queue high-water
   mark, maximum live children, wall time and available child resource data.
5. **Did timing history stay advisory?** Record cache schema and digest,
   exact-ID hits, neutral entries, corrupt entries and resulting weight
   estimates. Never record or read a cached test verdict.
6. **Did source movement change the attempt?** Record pre-snapshot,
   post-snapshot and post-run identities, superseded attempts, the changed
   paths observed and any terminal `unstable-source` state.
7. **Why is the result not green?** Distinguish `test-failure`,
   `command-failure`, `scheduler-error`, `invalid-plan`, `snapshot-error`,
   `superseded` and `unstable-source`; preserve bounded output and validated
   partial evidence for every started job.
8. **What did audit add?** Record Warden round identity, every finding ID,
   parent-red evidence, remediation commit, guard and cumulative-map digest.
   A clean result names the full tree it reviewed.

`wildcat.check-run.v1` is written atomically only under a validated
repository-relative target. Human output begins with source and selection,
uses stable check/shard IDs for progress, and ends with one bounded structured
summary. A report refusal cannot be overwritten by a later green test line.

## 9. Boundaries, per capability

This capability follows Phylax because it reads untrusted artifacts and Git
state, parses JSON, creates snapshots, starts subprocesses, accepts paths and
writes caches and reports.

| capability | accepted input | control | refusal or safe fallback |
| --- | --- | --- | --- |
| Carryover ingestion | Explicit packet and patch files with fixed published digests | Bounded regular-file reads, SHA-256 before parse, exact table/path extraction | Digest, syntax or set mismatch stops before reconstruction |
| Inoculation record | Versioned JSON with bounded arrays and strings | Duplicate-key rejection; exact schema; compare with parsed packet/patch and current AST | Missing/extra path, finding, guard, family or undeclared transform stops before product checks |
| Scope selection | Known repeated scope IDs, optional resolvable base and fixed Git-reported paths | Exact registry membership, total non-overlapping ownership, normalized repository-relative paths, no shell | Unknown/ambiguous owner, stale command, invalid base or cycle is `invalid-plan`; nothing runs |
| Git capture | Fixed `git diff` and `git ls-files` argv | Scrub inherited Git redirection and pager/editor variables; bound output; preserve rename/deletion metadata | Malformed, oversized or changing capture supersedes or refuses the attempt |
| Snapshot creation | Tracked patch plus relevant non-ignored untracked regular files and safe symlinks | Random nonce under ignored runner-owned parent; independent clone; local unsigned synthetic commit; before/after identity | Escape, special file, apply failure or identity mismatch is `snapshot-error` or supersession |
| Command execution | Validated fixed argv and working directory from the check map | No shell; minimal environment; bounded capture; shared slot token; retain existing per-check timeouts | Missing path/executable or malformed result is command/scheduler failure; other started jobs drain |
| Worker assignment | Versioned snapshot/manifest identity plus bounded unique indices | Worker rediscovers, verifies the whole manifest and selects only local discovered objects | Digest mismatch, foreign/duplicate/out-of-range index or missing result is `scheduler-error` |
| Timing cache | Versioned local JSON with exact IDs and finite non-negative durations | Ignored bounded file; entry, depth, numeric and string limits; no-follow directory-bound atomic replace | Missing, stale, corrupt or incompatible data is a visible neutral cache miss |
| Output and reports | Child byte streams and validated repository-relative report path | Coordinator-owned bounded pipes; UTF-8 head/tail accounting; escaped reserved prefix; hardened exclusive write | Drain loss, unsafe target, forgery or replacement refuses green and preserves diagnostic evidence |
| Cleanup | Runner-created nonce directory with matching sentinel | Resolve exact parent/child, refuse symlink substitution, remove only proven-owned tree | Preserve and print an unprovable path; never widen deletion |
| Fixture signing | Fresh disposable repository owned by one non-signature fixture | Repository-local `commit.gpgsign=false` immediately after creation; explicit `cwd`; hostile sentinel and config snapshots | Signer invocation or outer/global mutation fails; signature-test fixtures retain their own policy |

No secret is required. Capacity and Git diagnostics use named allowlisted fields,
not an environment dump. Failure output retains bounded head, tail and byte
counts so diagnosis survives without unbounded memory use.

## 10. The budget, or its absence

This capability follows Metron: establish the serial control on one stable
source, make one scheduling change, repeat the same work, and keep the policy
only when the measured gain exceeds noise.

The packet records a serial suite taking roughly nine minutes and a faster
bounded parallel result on its historical tree. It also records a real
contention boundary. Those measurements justify another current-base
experiment; they do not fix a test count, process count or machine policy.

The automatic budget is the conservative minimum of positive usable CPU,
affinity and supported quota signals after headroom, capped by runnable work
and implementation safety limits. Missing optional signals are named and
ignored; no positive safe signal yields a conservative single slot. A positive
explicit override is validated and reported. Signing identity is never a
capacity input.

One root scheduler owns the process budget. A normal command consumes one
slot. An ordered group holds no extra slots between commands. A suite capable
of internal sharding receives an allocation from the same authority and must
not independently derive an additional budget while nested. The maximum
observed live-child count is acceptance evidence.

Step 4 freezes one clean source and alternates three serial-control samples
with three automatic-policy samples. Each sample records manifest digest and
cardinality, wall time, child CPU time, queue/live-child high-water marks,
available peak child memory, shard distribution and cache state. Keep the
automatic scheduling policy only when all samples execute identical manifests
and assertions, its median improvement exceeds the sum of observed median
absolute deviations, no failure class appears only under concurrency, and
resource growth stays within measured capacity. If the gain is noise, retain
the correctness and selector work but revert the unproven policy. Do not widen
a timeout to earn the measurement.

The Metron comparison keeps these commands and the frozen source constant:

```text
python3 plugins/hexaemeron/tests/run_tests.py --jobs 1
python3 plugins/hexaemeron/tests/run_tests.py
```

The selector has no fixed wall-time promise because diffs and dependency
closures vary. Its budget is exact selected coverage under the single global
process cap. Map/runner changes select a full self-audit, and `--full` remains
available for comprehensive audit and release evidence.

## 11. The fail-closed posture

This capability follows Elenchus. Failure is classified, not flattened: stable
integrity faults refuse green, ordinary test evolution creates a fresh next
manifest, and source movement supersedes an attempt rather than accusing a
test.

- A bad artifact hash, incomplete cumulative map, undeclared transform or
  absent guard stops before product verification.
- A stable unknown owner, invalid dependency graph, manifest mismatch,
  duplicate/missing execution, worker crash, lost output, unsafe path or
  unexpected success refuses green with bounded evidence.
- A genuine assertion or governed command failure is red. Other started work
  finishes so the result remains comprehensive.
- Tests added, removed or renamed between invocations are normal. The next
  fresh manifest is authoritative. If the source changes during an attempt,
  discard that attempt and retry once; repeated movement returns
  `unstable-source`, not a failed-test verdict.
- A missing, stale or corrupt timing cache is a visible neutral miss. It does
  not block execution and cannot contribute a verdict.
- An optional capacity signal may be absent. An invalid explicit override is
  rejected; a missing signal does not invent capacity.

All known carryover leads remain visible until explicitly disposed:

| lead | required disposition |
| --- | --- |
| Elenchus rejects a valid one-test report containing two failing subtest events. | Retain the separate [`elenchus-wish` #643](https://github.com/wildcat-finance/skills/issues/643); #622 must not claim universal consumer compatibility while this remains external. |
| A short-lived descendant retaining an inherited output descriptor delays coordinator drain. | Choose and guard an explicit bounded descendant-lifetime/drain policy, or report the unresolved semantic choice and withhold a completed-runner claim. |
| Automatic capacity above the current implementation safety cap was not exercised. | Keep the cap, cover signal arithmetic synthetically and describe the missing live evidence without a portability claim. |
| A live suite near the discovery item limit was not exercised. | Keep incremental synthetic guards and distinguish them from missing live-scale evidence. |
| Non-macOS and live cgroup v1/v2 capacity paths were not exercised. | Test parsers with bounded fixtures and retain the absent live-platform evidence. |
| Hosted CI did not verify the unpublished Step 2 tree. | Do not cite local results as hosted evidence; workflow expansion remains separately authorized. |
| The inherited public exit rule omits unexpected successes. | Add a focused parent-red guard and make every unexpected success non-green before final acceptance. |
| Elenchus classified changed runner code in its overlay as `passed`, not `guarded`. | Preserve independent tests-only parent-red evidence and do not upgrade the historical verdict wording. |
| Brevitas B011 conflicts with Fiat's mandatory short audit tables. | Preserve the governed audit record, run the required prose gates, and track the tooling mismatch separately rather than editing evidence away. |

Every new Warden finding follows the same loop: preserve the exact failure,
reproduce it on the parent, localise and fix the cause, add a guard, extend the
cumulative machine map, rerun the complete current tree, then request another
independent round. A later round may add tests; that is healthy drift and the
fresh manifest must include them. If the replacement run again reaches its
audit limit with findings, it emits a complete superseding
`622-CARRYOVER-2.md` and cumulative inoculation patch. The successor reconstructs
that whole union, not a delta from this conversation.

## 12. Decisions and their homes

This capability follows Hypomnema. The expensive-to-reverse selector,
snapshot, scheduling and accounting choices live in
`docs/decisions/ADR-038-select-and-schedule-repository-checks-from-one-graph.md`.
ADR-038 records the current-base collision, why #622 remains one
selector-plus-executor capability, why ownership is declarative, why workers
rediscover and select objects by canonical index, why one quota-aware global
budget governs nested work, why timing has balance-only authority and why
between-invocation drift differs from within-attempt source movement.

The reconstruction contract lives in
`tests/fixtures/issue-622-inoculation-v1.json` and
`scripts/verify_issue_622_inoculation.py`; its focused guard lives with the
Hexaemeron tests. The authoritative product graph and executor live in
`tests/check-map-v1.json` and `scripts/run_checks.py`. The self-contained
manifest/worker protocol and secure aggregate reporter remain in
`plugins/hexaemeron/tests/run_tests.py`, with versioned schema and bounds in
code docstrings and exact behavior in tests.

The reconstructed first-attempt `docs/affected-scope-test-runner/study.md` and
`runbook.md` remain historical evidence. The replacement's receipted copies
use distinct names under the same directory so they do not silently rewrite
that evidence. `AGENTS.md` becomes the human entrypoint for plan, scope, full
run, automatic allocation and explicit override. It points to the machine map
instead of maintaining a second serial catalogue. The measured consequence
lives in `docs/affected-scope-test-runner/benchmark.md`.

Audit source and synopsis stay under `audit/rounds/`. Controller receipts stay
under `.hexaemeron/`. Any further exhausted-run packet is a complete published
carryover artifact linked from #622. The Elenchus reader and prose-tooling
leads live in their correctly titled issue queues, not as hidden scope inside
#622. Shipped public prose passes Imprimatur; the machine map, tests and audit
record remain the authority for behavior and evidence.

### Amendment -- 2026-08-26

**What changed.** Current `main` contains `ReplayGuardExampleTests`, a
five-method class whose `setUpClass` raises `unittest.SkipTest` when its five
optional Lazarus imports are unavailable. Standard `unittest` records one
class-fixture skip, starts none of those five assigned methods and reports
only the other top-level tests in `testsRun`. Exact runner accounting therefore
uses two disjoint terminal dispositions: an assigned ID is either started and
completed exactly once, or `fixture-blocked` by a validated class- or
module-fixture `SkipTest` covering that discovered test object. The worker must
bind each blocked ID to its discovered fixture scope and the actual standard
skip event; a missing start, an unrecognised holder string, a non-skip fixture
error, overlap, duplicate, foreign ID or incomplete union remains a scheduler
error. Structured evidence records assigned, started, completed and
fixture-blocked IDs separately and adds an exact-accounting verdict. No field
may call a fixture-blocked ID started, completed or executed. Public
`elenchus.unittest.v1` counters retain standard `unittest` meaning and schema.

**Why.** The first reconstructed serial control discovered 1,348 unique IDs
but the worker started and completed 1,343. It exited scheduler-error after
484.234 seconds. Isolation showed the five-ID difference was exactly the
current-main class-level skip above; the direct module ran fourteen tests and
recorded one class-fixture skip. Treating those IDs as lost work rejects valid
`unittest` behavior, while pretending they ran would falsify evidence.

**Steps touched.** Step 1; Step 2; Step 3. Step 1 changes runner accounting,
structured evidence, focused guards and its decision-record clarification.
Steps 2 and 3 consume the clarified exact accounting but keep their existing
build order and interfaces.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
