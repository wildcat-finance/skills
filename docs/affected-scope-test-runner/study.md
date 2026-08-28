# Study: disposable fixture signing and an affected-scope parallel check runner

Starting revision: `e2200b6a04bbf639c3d5ec37f01a7aa63ce58f16` (`main`).

Assumptions:

- Issues [#621](https://github.com/wildcat-finance/skills/issues/621) and [#622](https://github.com/wildcat-finance/skills/issues/622), including every comment visible on 2026-08-25, are the authority for this packet. #622 owns both affected-scope selection and the bounded parallel executor. #621 is a prerequisite delivered in the same packet.
- The current Hexaemeron test tree is byte-identical to the tree measured at `1efec4de762e3b30c1d677371643c0e5e12667ed`; the repository has advanced only in other surfaces. A fresh discovery at the starting revision found 1,167 ordered, unique test IDs with manifest SHA-256 `ab3e1505b10675155e2348117985fe4b338b6895fe6936363236ca2f12c78d2a`. Those values are baseline evidence, never scheduler inputs or acceptance constants.
- A test set may legitimately grow, shrink or rename between audit loops. Each invocation therefore owns a newly discovered content snapshot and manifest. Drift between invocations is normal. A source change during an invocation supersedes that attempt and causes a bounded retry; it is not reported as a failed test.
- A declared scope is a request for coverage, not permission to ignore changed files outside it. The plan is the union of declared scopes and scopes derived from committed, staged, unstaged and non-ignored untracked paths. Any widening is printed.
- The runner remains Python-standard-library and Git based. New third-party runtime dependencies, changes to hosted CI, and Solidity product changes require separate authority.
- Contributor signing configuration is arbitrary. Correctness cannot depend on a particular key, signer, account, hostname or interactive pinentry.

## 1. Problem statement

The repository currently has two coupled sources of avoidable test latency.

First, several tests create disposable Git repositories and commit fixture history without setting repository-local signing policy. Those repositories inherit a contributor's global `commit.gpgsign`, `user.signingkey` and `gpg.program`. On a machine that signs by default, a throwaway commit may open pinentry, wait for an unavailable signer or fail before the test reaches the behavior it is meant to exercise. This is an isolation fault, not a reason to weaken signing on the real checkout. Current-tree inspection found the unfixed pattern in:

- `tests/test_boundary_currency.py`;
- `plugins/hermes/skills/hermes/scripts/test_hermes.py`;
- `plugins/hexaemeron/tests/test_elenchus_checker.py`;
- `plugins/hexaemeron/tests/test_kronos_scoreboard.py`; and
- `plugins/horos/tests/test_demonstration.py`, `test_scoped_entry.py` and `test_universe.py`.

`plugins/hexaemeron/tests/test_fiat_skill.py` and the main `test_hexctl.py` fixture already set local signing off. `test_issue_429_recovery.py` deliberately tests signed and unsigned evidence and must not be blanket-neutralised. The current code, rather than an old line list, decides the final inventory.

Second, `AGENTS.md` is a serial command catalogue. It states that changed areas should be checked, but it provides neither an executable ownership map nor a scheduler. A contributor or Fiat phase therefore tends to run every skill suite even when the changed surface and its downstream consumers are known. The largest current suite is then executed in one process. The replacement measurement on #622 records a roughly nine-minute serial Hexaemeron baseline and a large safe gain under bounded parallel execution. It also records repeatable failures once contention becomes too high. The answer is not a larger timeout: selection, concurrency and result accounting must become explicit.

Success means all of the following are true:

1. Every non-signature disposable repository that makes a fixture commit sets `commit.gpgsign=false` in that repository immediately after `git init` and before its first commit. A hostile inherited Git configuration cannot invoke its sentinel signer. The outer checkout, global Git config and contributor keys are unchanged.
2. One checked declarative map resolves declared scopes plus actual changed paths to the applicable suites, lints and ordered command groups, including named downstream consumers. It produces both a human plan and a versioned JSON plan. Unknown ownership, malformed entries, missing commands and dependency cycles refuse execution.
3. #622 includes a real bounded executor. Independent check jobs run concurrently, and the Hexaemeron unittest suite is split across processes using fresh discovery. The total number of live child processes never exceeds one global budget.
4. The default budget is derived from usable CPU and quota signals with conservative headroom; `--jobs` provides an explicit positive override. The final job count is capped by runnable work, so a small manifest creates no empty shards. Signing state has no bearing on that calculation.
5. Each invocation freezes an ordered, unique manifest `M` from its source snapshot, records `N = |M|`, and assigns the disjoint union of `M` to workers. Every worker rediscovers the same snapshot, verifies the manifest digest, selects test objects from that discovery and preserves canonical order. The coordinator proves exact executed-once coverage before reporting green.
6. The design supports dynamically generated IDs, including the current IDs containing `<locals>`, without trying to import those IDs by dotted name. Added, removed and renamed tests work on the next invocation without changing a constant or increasing the process count by themselves.
7. Timing history may balance work only. It cannot select tests, suppress execution or cache a pass verdict. New or renamed IDs are neutral, removed IDs are ignored, and a corrupt or incompatible cache is a visible cache miss rather than a suite failure.
8. A stable missing, duplicate, unexecuted or multiply executed assignment is a scheduler error. A mid-attempt source change supersedes and retries once; repeated change yields `unstable-source`, not a test verdict. All genuine test failures are retained and reported after the remaining assigned work finishes.
9. The existing positional and `--elenchus-report` interfaces and their secure no-follow, exclusive-create, source-binding behavior remain compatible. Direct invocation of the copied, self-contained Hexaemeron runner still works.
10. Three serial and three automatically budgeted samples on one frozen revision contain the same IDs and assertions. The automatically budgeted median must improve by more than the combined observed run-to-run spread without introducing a new failure class or unacceptable peak-memory growth.

## 2. Prior art

The useful prior art is local and already carries constraints that this delivery must preserve.

- `plugins/hexaemeron/tests/run_tests.py` performs canonical sorted unittest discovery and owns the Elenchus report. PRs [#487](https://github.com/wildcat-finance/skills/pull/487) and [#577](https://github.com/wildcat-finance/skills/pull/577) hardened that report against symlink and replacement attacks, bound it to the source run, and retained the positional path form. The new coordinator/worker modes must feed one aggregate result through the same reporter; workers never write the receipt themselves.
- `plugins/hexaemeron/tests/test_elenchus_checker.py` copies `run_tests.py` by itself and executes the copy. That is a compatibility contract: the Hexaemeron discovery, partition and worker implementation stays self-contained rather than importing a new root-only package.
- PR [#537](https://github.com/wildcat-finance/skills/pull/537) made the root boundary fixture clear inherited `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE`. Repository-local signing neutralisation extends that isolation without undoing it. PR [#455](https://github.com/wildcat-finance/skills/pull/455) added the earlier report fixture and carries no competing signing design.
- PRs [#571](https://github.com/wildcat-finance/skills/pull/571) and [#253](https://github.com/wildcat-finance/skills/pull/253) are the last two merged changes to the Kronos scoreboard fixture. The durable-home production path deliberately makes unsigned throwaway state commits, but its test helper still inherits signing. That distinction remains explicit.
- PRs [#463](https://github.com/wildcat-finance/skills/pull/463) and [#263](https://github.com/wildcat-finance/skills/pull/263) are the last two merged changes to the current Horos fixture surface. #263 carried the absence of a Horos CI workflow; this packet does not silently add one.
- PRs [#359](https://github.com/wildcat-finance/skills/pull/359) and [#358](https://github.com/wildcat-finance/skills/pull/358) are the last two merged changes to the Hermes test script. Its audit history is especially relevant: inheriting a `TestCase` through a helper once duplicated fourteen cases. That was corrected by using a non-collectable mixin. Exact discovered and executed counts are therefore correctness evidence, not cosmetic output.
- PRs [#619](https://github.com/wildcat-finance/skills/pull/619) and [#615](https://github.com/wildcat-finance/skills/pull/615) are the last two merged changes to `test_hexctl.py`. Existing local signing isolation stays in place. Their unrelated carried issues and resource warnings do not enter this packet.
- The current `janus.yml`, `lazarus.yml` and `pandects.yml` path filters and command sequences are partial ownership-map precedents. They show that local plugin paths, root contracts, Python suites, dependency setup and ordered Forge commands differ by capability. They are evidence for the checked map, not a second authority to copy indefinitely.
- `audit/AUDIT.md` records the Hermes duplicate-collection correction, the Horos scoped-entry delivery, the secure Elenchus reporter rounds and the Kronos durable-home work. `plugins/hexaemeron/audit/AUDIT.md` records historical plugin review but no open product finding that replaces #621 or #622. Hermes and Horos have no separate plugin-local audit log in the current tree.
- Python's `unittest.TestLoader.discover` is suitable for creating the canonical suite in each worker. It is not sufficient to pass the resulting dynamic IDs back to `python -m unittest`; #622's prototype demonstrated why selection must use objects from rediscovery.
- Python's usable CPU interfaces, process affinity and Linux CPU-controller quota files provide bounded local signals. None alone is universal, so the calculation takes the minimum positive available capacity and reports which signals contributed.
- A separate disposable local clone is established Git machinery for an immutable working snapshot while preserving history. It also gives the snapshot its own Git config, avoiding mutation of the source checkout's shared config.

The inspected merged PRs contain no unfinished signing or runner product change to adopt. Their relevant carried work is compatibility: secure reporting, Git-environment isolation, exact collection accounting and explicit CI boundaries. Other carried findings remain outside this packet.

## 3. Constraints and non-goals

Always:

- derive a new source identity, impact plan and test manifest for every invocation;
- combine declared scope with actual changed paths and explain every selected check and dependency expansion;
- configure signing only inside a disposable repository that this test or snapshot creator just initialised or cloned;
- preserve suite assertions, individual timeouts, canonical order within a shard and all failure output;
- keep one global process budget across suite jobs, shards and ordered command groups;
- bind reports to the stable source snapshot, map digest, manifest digest and actual execution record;
- run the checks selected for every changed surface before a step can exit green; and
- measure performance on one frozen revision with identical manifests and assertions.

Ask first:

- before adding a dependency, changing a hosted workflow, creating a new remote cache or service, or changing the public Elenchus report schema;
- before treating a previously independent plugin as a downstream consumer or removing a declared dependency edge; and
- before altering a signature-verification fixture, a production signing policy or the Promise Machine contract.

Never:

- change global Git config, the source checkout's local config, a contributor's signer program or any signing key;
- inject a process-wide signing override that can conceal a signature test;
- hard-code a discovered test total or a default worker total;
- use prior pass results to skip a test, or let timing-cache contents affect membership or verdicts;
- drop assertions, increase a timeout to mask contention, fail fast and lose later failures, or call a partial manifest green;
- execute an unowned changed path, a cyclic plan or an unverifiable assignment;
- describe source churn during an attempt as a test failure;
- clean an unresolved or unowned filesystem path; or
- modify Solidity in this packet.

Non-goals:

- Remote result caching, distributed execution and a hosted scheduler are not being built.
- The runner does not infer semantic dependency from imports at runtime. Maintainers own a reviewed declarative graph whose completeness is mechanically checked against the repository's registered scopes and tracked paths.
- This delivery does not replace GitHub Actions, add missing plugin workflows, change external branch protection or make one developer machine's concurrency policy universal.
- It does not optimise individual test bodies or weaken test isolation. A slow test remains a real test and an observed contention failure remains evidence for headroom.
- It does not make all existing suite entrypoints disappear. Direct commands remain usable; `scripts/run_checks.py` becomes the canonical selection and orchestration entrypoint documented by `AGENTS.md`.
- Pandects and Janus Solidity commands are represented and tested as ordered plan capabilities, but this no-Solidity packet does not edit their contracts or harnesses.

## 4. Design options

### Option A: blanket signing override and a faster serial catalogue

Set `GIT_CONFIG_*` or `git -c commit.gpgsign=false` around all tests, add path advice to `AGENTS.md`, and leave suite execution serial. This is small but wrong. A broad override can invalidate signature tests, contributor behavior still determines unmanaged fixtures, advice is not an executable impact map, and the dominant suite remains slow. Reject.

### Option B: changed-file selector plus dotted unittest IDs

Add a selector, divide the discovered ID strings and launch `python -m unittest <id>`. This is also insufficient. Current discovery contains dynamically generated IDs with `<locals>` that are not importable names. It does not prove each worker saw the same manifest, and separate suite launchers can oversubscribe the machine. Reject.

### Option C: one static manifest and fixed shards

Record the current IDs or count in source and allocate permanent ranges. It benchmarks easily but becomes stale as tests are added, removed or renamed during audit loops. It turns healthy change into an administrative failure and can silently miss new work. Reject.

### Option D: checked impact graph, immutable per-attempt snapshot and one bounded executor

Choose this option. It has three coupled parts and is delivered as one #622 capability with #621 first.

#### Disposable repository isolation

Immediately after each applicable `git init`, execute `git config --local commit.gpgsign false` using the fixture repository as `cwd`, before any commit. Keep the setting next to repository construction rather than hiding it in a process-wide test harness. Reuse an existing local helper only within a file when it already owns repository construction; do not introduce a cross-plugin dependency solely to save one line.

The final inventory is semantic: a newly created disposable repo that commits non-signature fixture history is in scope; a repo that never commits is not; a test whose subject is signing or signature verification is excluded unless its own matrix explicitly requires a neutral control. The hostile regression supplies inherited `commit.gpgsign=true`, a nonexistent key and a recording signer that exits nonzero. Passing requires the intended fixture assertions and an untouched sentinel log, not merely absence of a hang.

#### Checked impact map and interface

Add `tests/check-map-v1.json` as the single declarative catalogue and `scripts/run_checks.py` as its validator, planner and executor. The JSON uses duplicate-key rejection and the version `wildcat.check-map.v1`. It contains:

- registered scope IDs for root and every marketplace skill;
- non-overlapping ownership rules, each with an ID, repository-relative path patterns and one or more named owning scopes;
- suite definitions with stable IDs, fixed argv arrays, working directories, expected source paths and a kind of `command`, `unittest-discovery`, `hexaemeron-unittest` or `ordered-group`;
- named dependency edges from a changed contract or handoff surface to its consumers;
- lint and documentation capabilities selected by their governed path surfaces; and
- ordered groups for commands such as `forge build` followed by `forge test`.

Validation enumerates tracked files plus relevant non-ignored untracked files. Every path must match exactly one ownership rule; a shared rule names all its owners rather than overlapping another rule. It rejects unknown scope or suite IDs, duplicate IDs, absolute or escaping paths, shell strings in place of argv, absent executables or governed source paths, missing owners, self-edges, cycles, an incomplete marketplace/plugin registry, and stale suite commands. A change to the map, planner, runner or their tests selects the complete map self-audit and full check catalogue.

The CLI is:

```text
python3 scripts/run_checks.py [--scope SCOPE ...] [--base REF] [--full]
    [--plan] [--format human|json] [--jobs POSITIVE_INT]
    [--json-report REPOSITORY_RELATIVE_PATH]
```

`--scope` is repeatable. `--base` defaults only when Git provides an unambiguous merge base; otherwise the planner asks for it. Actual changes are the union of `git diff <base>...HEAD`, `git diff HEAD`, rename/deletion metadata, and `git ls-files --others --exclude-standard`. With no declared scope and no changed path, the runner refuses an ambiguous empty plan and points to `--full`. `--plan` performs validation and emits the plan without running it. Human output gives the reason for every check; JSON uses `wildcat.check-plan.v1` and includes source identity, map digest, requested/derived scopes, expansions, jobs and ordered edges.

Examples fixed by acceptance tests include:

- a Probitas-local implementation change selects the Probitas Python suite, not Alexandria or Tabularium; editing their handoff contract selects the named consumers;
- a Hexctl-only change selects the complete Hexaemeron controller suite but no unrelated plugin suite;
- Promise Machine or marketplace contract changes fan out to every registered consumer;
- Pandects source selects its Python checks and the ordered Forge build/test group;
- a Janus harness change selects its Python and ordered harness checks;
- prose selects the applicable Imprimatur, Brevitas and Hypomnema checks without inventing unrelated test dependencies; and
- an unknown new top-level path refuses execution until its ownership is declared.

After implementation, these examples are planned again from the actual diff. The implementation does not rely on the design-time path list.

#### Stable source snapshot

Before discovery, the root runner records a source identity from the starting commit, base, map bytes, `git diff --binary HEAD`, untracked path list and their content digests. It creates a nonce directory below ignored `tmp/check-runner/snapshots/`, verifies a sentinel identifying that directory as runner-owned, makes a separate local clone of the source repository, checks out the starting commit, applies the tracked overlay, copies non-ignored untracked files without following escaping symlinks, and commits the overlay as a local synthetic snapshot. The clone sets its own repository-local identity and `commit.gpgsign=false`; it never changes the source checkout's config. The snapshot report records the original identity and synthetic commit.

The source identity is read again after snapshot creation and after execution. A mismatch discards the attempt's verdict and starts one new snapshot. A second changing attempt exits with the distinct status `unstable-source`. The next user invocation is free to discover the new tests. Stable source churn is therefore neither ignored nor mislabeled as a failed test.

Cleanup resolves the candidate path, requires both the exact snapshot parent and sentinel, and removes only the runner-owned clone. If either check fails, it preserves the directory and reports it. No wildcard, unresolved environment variable or source-repository path is a cleanup target.

#### One bounded executor and fresh test manifests

Extend the self-contained `plugins/hexaemeron/tests/run_tests.py` with coordinator and private worker modes while preserving its existing direct and report-path forms. Direct use becomes:

```text
python3 plugins/hexaemeron/tests/run_tests.py [--jobs POSITIVE_INT]
    [--elenchus-report PATH | PATH]
```

The coordinator discovers `test_*.py` in canonical order, flattens the suite, rejects duplicate IDs, and writes ordered manifest `M`, its SHA-256 and `N`. Assignments contain manifest indices, not dotted import names. Each worker independently rediscovers the same snapshot, recomputes the ordered digest, refuses a mismatch, selects the already discovered test objects at its assigned indices and runs them in index order. This retains support for generated IDs.

The root executor uses the same private manifest/assignment protocol for Hexaemeron shards and launches all other suite or ordered-group jobs itself. It owns one queue and one subprocess slot counter, so nested coordinators cannot multiply the budget. An ordered group occupies one slot and starts its next command only after the preceding command succeeds; independent groups and suites may proceed in other slots. All started jobs drain. Buffered output is replayed in deterministic plan/shard order and the final report retains every failure.

Usable capacity is the minimum positive value available from Python's usable process count, process affinity, cgroup v2 `cpu.max`, cgroup v1 quota/period and `os.cpu_count()` fallback. The automatic policy reserves `max(1, ceil(usable / 3))` of machines with more than one usable CPU and uses the remainder; a one-CPU environment uses one. An explicit positive `--jobs` replaces the automatic policy but remains subject to process availability and safety validation. For a manifest or runnable graph of size `N`, `J = min(budget, N)` and no empty shard is created. The report names the capacity signals, budget source, effective `J`, queue high-water mark and maximum observed live children.

`tmp/check-runner/timings-v1.json` is an optional, ignored, size-bounded, atomically replaced `wildcat.test-timings.v1` cache. Only prior durations for exact IDs help a deterministic longest-processing-time partitioner balance shards; ties resolve by canonical index. Unknown IDs get the current median estimate, removed IDs disappear on bounded rewrite, and schema/digest corruption produces counted neutral entries. Membership comes only from current discovery. Results come only from current execution.

The coordinator proves before launch that shard indices are an exact disjoint union of `0..N-1`, then proves from worker result records that every assigned ID started and completed exactly once. A stable digest mismatch, missing result, duplicate execution, unexecuted assignment or unknown result is `scheduler-error`, never green. `N` changing on a later invocation is expected and reported.

## 5. Risk register seed

```risk-register
fixture-signing-scope | A broad override could conceal the signature behavior under test | Run the hostile inherited-config matrix and the existing signed and unsigned evidence matrix while checking the sentinel and outer configs
source-config-mutation | A linked worktree or inherited Git command could mutate the contributor checkout | Use an independent disposable clone and compare source and global config before and after the run
impact-map-omission | A new or shared path could escape every applicable check | Enumerate tracked plus relevant untracked paths and reject zero or ambiguous ownership matches
dependency-cycle | A mistaken consumer edge could recurse or produce unstable selection | Validate the graph with an explicit cycle fixture and deterministic topological order
manifest-bootstrap | A map or runner change could validate itself with only a partial plan | Make map runner and planner paths select the full catalogue and test that rule from a hostile map fixture
snapshot-drift | Tests added during an audit loop could mix two source states in one verdict | Bind each attempt to a snapshot and supersede then retry when the source identity changes
snapshot-copy-boundary | Untracked symlinks or path traversal could copy or remove data outside the owned snapshot | Reject escaping paths require a sentinel and resolve both copy and cleanup targets beneath the fixed ignored parent
dynamic-test-identity | Generated unittest IDs cannot be re-imported as dotted names | Assign canonical indices and select objects from worker-local rediscovery after digest verification
shard-accounting | A missing duplicate or unexecuted test could still look green | Prove the assignment union before launch and reconcile exact started and completed IDs after every worker returns
global-process-budget | Nested suite runners could exceed the selected capacity | Give the root executor the only slot counter and expose Hexaemeron workers rather than nesting its coordinator
timing-cache-authority | Stale timing history could become an accidental result cache | Test cache corruption additions removals and renames while deriving membership and verdicts only from the current run
subprocess-output | Concurrent output could interleave hide failures or grow without bound | Capture per job with a cap retain overflow metadata and replay every result in stable plan order
report-compatibility | Parallelisation could bypass the hardened Elenchus report contract | Re-run positional flag symlink replacement source-binding and copied-runner regressions against the aggregate coordinator result
timing-sensitive-contention | Excess concurrency could turn an existing short timeout into a false product failure | Keep conservative quota-aware headroom measure repeated samples and retain the timeout as an acceptance signal
fixture-collection-count | Helper refactoring could duplicate or omit unittest cases | Compare ordered unique manifests and exact executed-once records before and after every refactor
ordered-command-breakage | Forge test or another dependent command could start before its build gate | Represent dependencies as ordered groups and exercise them with recording fake commands under concurrent load
unstable-source-label | Continuous editing could be reported as a red suite | Give superseded attempts and unstable-source their own structured states and never convert them to test failures
```

## 6. Glossary seeds

- **Affected scope:** the union of explicitly declared scope and ownership inferred from every actual changed path, closed over named downstream dependencies.
- **Automatic budget:** the conservative process limit derived from the minimum usable CPU/quota signal after headroom. It is not a repository constant.
- **Canonical order:** the deterministic order obtained by flattening one fresh `unittest` discovery over the snapshot.
- **Changed path:** a committed, staged, unstaged, renamed, deleted or non-ignored untracked path relative to the selected base and current worktree.
- **Check map:** the reviewed, versioned ownership, suite and dependency graph in `tests/check-map-v1.json`.
- **Content snapshot:** the independent disposable clone and synthetic local commit containing exactly the source state assigned to one attempt.
- **Declared scope:** a repeatable user/controller input naming intended coverage. It can widen a plan but cannot hide an actual change.
- **Disposable repository:** a repository created solely inside a test or runner-owned temporary boundary and never used as delivery evidence.
- **Executed-once proof:** equality between the frozen manifest and the disjoint union of completed worker records, with no missing or duplicate ID.
- **Manifest (`M`):** the fresh ordered unique test-ID list discovered from a content snapshot; `N` is its current length.
- **Neutral timing:** the estimate assigned to a test with no reusable exact-ID duration. It carries no result meaning.
- **Ordered group:** commands that must run sequentially with respect to one another while unrelated jobs may run concurrently.
- **Scheduler error:** a stable failure of discovery, assignment, worker identity or result accounting. It is distinct from a test failure.
- **Source identity:** the digests and Git coordinates that bind a plan, snapshot, manifest and report to one input state.
- **Superseded attempt:** an attempt whose source changed while it was being prepared or run. Its test output is retained as diagnostic evidence but cannot decide green or red.
- **Unstable source:** the terminal non-test state after the bounded automatic retry also observes source change.

## 7. Sources

Primary issue and measurement record:

- [Issue #621 and body: disposable Git fixtures inherit contributor signing](https://github.com/wildcat-finance/skills/issues/621)
- [#621 replacement hostile-config and timing baseline](https://github.com/wildcat-finance/skills/issues/621#issuecomment-5416138775)
- [Issue #622 and body: changed scope chooses checks](https://github.com/wildcat-finance/skills/issues/622)
- [#622 replacement full-suite and corrected concurrency measurements](https://github.com/wildcat-finance/skills/issues/622#issuecomment-5416139004)
- [#622 fresh-manifest, drift and accounting clarification](https://github.com/wildcat-finance/skills/issues/622#issuecomment-5416248981)

Current source at `e2200b6a04bbf639c3d5ec37f01a7aa63ce58f16`:

- `AGENTS.md`, `PROMISE_MACHINE.md` and `.agents/skills/promise-machine/SKILL.md`
- `plugins/hexaemeron/AGENTS.md`
- `plugins/hexaemeron/tests/run_tests.py`
- `plugins/hexaemeron/tests/test_run_observation_binding.py`
- `plugins/hexaemeron/tests/test_elenchus_checker.py`
- every current file containing both disposable `git init` and fixture `git commit`, including the ten files inventoried in item 1
- `.github/workflows/janus.yml`, `.github/workflows/lazarus.yml` and `.github/workflows/pandects.yml`
- `audit/AUDIT.md`, `plugins/hexaemeron/audit/AUDIT.md`, `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` and its synopsis

Merged history inspected for the in-scope surfaces:

- runner/report: [#577](https://github.com/wildcat-finance/skills/pull/577), [#487](https://github.com/wildcat-finance/skills/pull/487) and the copied-runner association in [#488](https://github.com/wildcat-finance/skills/pull/488)
- root boundary fixture: [#537](https://github.com/wildcat-finance/skills/pull/537) and [#455](https://github.com/wildcat-finance/skills/pull/455)
- Hexctl fixture: [#619](https://github.com/wildcat-finance/skills/pull/619) and [#615](https://github.com/wildcat-finance/skills/pull/615)
- Kronos fixture: [#571](https://github.com/wildcat-finance/skills/pull/571) and [#253](https://github.com/wildcat-finance/skills/pull/253)
- Horos fixtures: [#463](https://github.com/wildcat-finance/skills/pull/463) and [#263](https://github.com/wildcat-finance/skills/pull/263)
- Hermes test script: [#359](https://github.com/wildcat-finance/skills/pull/359) and [#358](https://github.com/wildcat-finance/skills/pull/358)

Discipline contracts applied rather than restated:

- `plugins/hexaemeron/skills/protasis/SKILL.md`
- `plugins/hexaemeron/skills/phylax/SKILL.md`
- `plugins/hexaemeron/skills/ephoros/SKILL.md`
- `plugins/hexaemeron/skills/metron/SKILL.md`
- `plugins/hexaemeron/skills/elenchus/SKILL.md`
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`

External primary references:

- [Python `unittest` discovery documentation](https://docs.python.org/3/library/unittest.html#test-discovery)
- [Python process CPU-count documentation](https://docs.python.org/3/library/os.html#os.process_cpu_count)
- [Linux cgroup v2 CPU controller documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files)
- [Git clone documentation](https://git-scm.com/docs/git-clone)
- [Git config scope documentation](https://git-scm.com/docs/git-config#FILES)

## 8. Signals, and the questions behind them

This capability follows `plugins/hexaemeron/skills/ephoros/SKILL.md`. There is no unattended service or external alert target; the operator is the local contributor or CI job, and the human console plus a versioned JSON report are the durable surfaces.

The signals answer these on-call questions:

1. **What source and plan actually ran?** Record source/base/snapshot identity, map digest, requested and derived scopes, changed paths, dependency expansions, selected and omitted check IDs, and the reason for each selection.
2. **Was work complete?** Record each test manifest digest, current `N`, unique count, assignment ranges, per-shard counts, started/completed IDs, the final disjoint-union verdict and every command exit.
3. **Was the machine oversubscribed?** Record capacity signals, automatic or explicit budget source, effective `J`, queue high-water mark, maximum observed live children, per-job wall time and available peak child RSS.
4. **Did historical data affect only balance?** Record cache schema/digest, exact-ID hits, neutral entries, ignored removals, corrupt-entry count and final shard estimates. Never record or read a cached verdict.
5. **Did the source move?** Record pre-snapshot, post-snapshot and post-run identities, every superseded attempt, the changed paths observed and final `unstable-source` status where applicable.
6. **Why is the run not green?** Distinguish `test-failure`, `command-failure`, `scheduler-error`, `invalid-plan`, `snapshot-error`, `superseded` and `unstable-source`; include stable, bounded output for every failed job.
7. **Did signing isolation hold?** The regression records the hostile fixture setup and sentinel result without logging secrets, key material or environment contents.

`wildcat.check-run.v1` is written atomically only beneath a caller-named repository-relative path. Normal output begins with the snapshot and selected checks, reports progress by stable check/shard ID, then ends with one summary carrying the exact status vocabulary above. A report-path or cleanup refusal is visible and cannot be overwritten by a green test summary.

## 9. Boundaries, per capability

This capability follows `plugins/hexaemeron/skills/phylax/SKILL.md` because it parses a manifest, reads Git state, starts subprocesses, handles hostile inherited Git configuration, copies untracked paths and writes caches/reports.

| Capability | Accepted input | Boundary and control | Refusal or safe fallback |
| --- | --- | --- | --- |
| Scope selection | Known repeated scope IDs, an optional resolvable base, and repository paths reported by fixed Git argv | Strict JSON with duplicate-key rejection; exact registry membership; path normalisation under repository root; no shell | Unknown scope/base/path ownership, overlap, cycle or stale command is `invalid-plan`; nothing runs |
| Git change capture | `git diff` and `git ls-files` output from the named source checkout | Scrub inherited `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and unsafe pager/editor variables; fixed argv; bounded stdout/stderr | Malformed, oversized or changing capture supersedes or refuses the attempt |
| Snapshot creation | Tracked patch plus non-ignored untracked regular files/safe symlinks | Random nonce below a fixed ignored parent; independent clone; local unsigned synthetic commit; before/after digest; no network | Escaping path, special file, failed patch or identity mismatch produces `snapshot-error` or supersession |
| Command execution | Fixed argv and cwd from the validated map | No shell; minimal inherited environment; bounded capture; one global slot token; existing command timeouts unchanged | Missing executable/path or malformed output is a command/scheduler error, with all other started jobs drained |
| Worker assignment | Versioned assignment with snapshot and manifest digest plus bounded unique indices | Worker rediscovers, verifies full digest and indexes only local discovered objects | Digest mismatch, out-of-range/duplicate index or missing result is `scheduler-error` |
| Timing cache | Versioned local JSON of exact IDs and finite non-negative durations | Ignored directory; file-size, entry-count, number and string bounds; atomic replace; mode prevents unintended readers where supported | Missing, corrupt or incompatible data becomes neutral timing and is reported; execution continues |
| Reports | Caller-provided repository-relative path or existing hardened Elenchus path | Resolve under allowed root; reject symlinks/non-regular parents; exclusive/no-follow create where already required; size-bound job output | Refuse unsafe target and preserve diagnostic state; never claim a report was written |
| Cleanup | Runner-created nonce directory with matching sentinel | Resolve exact parent and child, reject symlink substitution, delete only owned tree | Preserve and print the path when ownership cannot be proved |
| Git signing fixture | Fresh disposable repository owned by the individual fixture | `git config --local commit.gpgsign false` immediately after initialisation; explicit cwd; compare sentinel/config afterward | Any signer invocation or outer/global config change fails the regression |

No secrets are required. Environment reports use an allowlist of signal names and derived numeric values, never a dump. Output caps retain the head and tail plus byte counts so a failure remains diagnosable without allowing an unbounded child to exhaust memory.

## 10. The budget, or its absence

This performance change follows `plugins/hexaemeron/skills/metron/SKILL.md`: baseline first, same command and snapshot, repeated samples, and a keep/revert decision against observed spread.

The replacement #622 comment is the historical baseline: on the unchanged Hexaemeron tree, serial discovery/execution averaged 519.243 seconds. Its green bounded samples cut wall time by about 84% to 89%, while higher contention repeatedly changed a short transport-timeout branch into failure. #621 separately records that deterministic hostile signing failure becomes a passing isolated class when repository-local policy is set. These numbers motivate the work; none is a permanent machine budget.

At implementation time, freeze one clean snapshot at the starting revision and record three samples of each exact command:

```text
python3 plugins/hexaemeron/tests/run_tests.py --jobs 1
python3 plugins/hexaemeron/tests/run_tests.py
```

The direct runner's structured summary records snapshot identity, manifest digest, `N`, effective `J`, wall time, child CPU time, peak child RSS where the platform exposes it, shard distribution and cache use. The first command is the serial control; the second exercises the automatic quota-aware policy. Run order alternates to reduce warm-cache bias. The hostile signing regression is measured separately because eliminating an external signer wait is a correctness result, not a comparable suite-speed sample.

Keep the scheduler only when:

- all six samples discover and execute the same ordered IDs exactly once and every assertion remains unchanged;
- the automatic median wall time improves on the serial median by more than the sum of their median absolute deviations;
- no timeout, scheduler, source-stability or report-security failure appears only under concurrency;
- peak memory and process high-water marks remain within the measured machine capacity and are reported, not guessed; and
- a one-job plan's added planning/snapshot overhead does not exceed the observed serial run spread without a documented reason.

If the gain is inside noise, retain the correctness and selector work but revert the unproven scheduling policy. If contention reproduces the known transport failure, reduce the automatic policy or improve isolation and repeat; do not change that test's timeout. Explicit `--jobs` remains an operator control, not evidence that a default is safe.

The selector has no absolute wall-time promise because selected graphs and machines differ. Its budget is exact coverage under one global process cap. A full scheduled audit remains available through `--full` and is required to audit the impact map itself.

## 11. The fail-closed posture

This capability follows `plugins/hexaemeron/skills/elenchus/SKILL.md`: preserve the observed failure, reproduce it deterministically, fix the cause and leave a guard that is red without the fix.

The posture is selective rather than treating every kind of drift as failure:

- A stable unknown owner, invalid dependency graph, manifest mismatch, duplicate assignment, missing/unexecuted result, worker crash or unsafe report/snapshot path refuses green. The output states `invalid-plan`, `scheduler-error` or `snapshot-error` and preserves evidence.
- A test assertion or governed command failure is red and named as such. Other already-started jobs finish so the record remains comprehensive.
- A test added, removed or renamed before a later invocation is ordinary evolution. Fresh discovery makes the new manifest authoritative. No old total is expected.
- A source change during an attempt supersedes that attempt. One automatic retry is allowed. Repeated change returns `unstable-source`; it does not accuse a test of failing and does not reuse the discarded verdict.
- A missing, stale or corrupt timing cache is a reported miss. It never blocks tests and never supplies a verdict.
- Missing optional CPU/quota signals fall back to the minimum remaining positive signal and report the fallback. An invalid explicit override is rejected before launch.

Required red/green guards are:

1. Run the currently affected disposable fixture classes with inherited `commit.gpgsign=true`, a missing signing key and a recording signer that exits nonzero. They fail or invoke the sentinel on the parent revision and pass with no invocation after local isolation. Existing signature-positive and signature-negative cases remain unchanged.
2. Feed the planner local-plugin, shared-contract, test-infrastructure, Hexctl, Pandects, Janus, prose, unknown-owner, missing-owner and cyclic-map fixtures. The parent has no executable plan; the product returns the exact expected graph or refusal.
3. Discover a suite containing generated `<locals>` IDs, add a test, remove one, rename one, run with `N` below the budget, corrupt the timing cache, and force stale worker discovery. Only the stable accounting violations are scheduler errors.
4. Inject duplicate, missing and unexecuted assignments and a worker that returns an unknown ID. None may produce green.
5. Change source once during a controlled run and then continuously. The first run is superseded and retried; the second exits `unstable-source` without a failed-test label.
6. Reproduce the issue's contention-sensitive transport branch under a deliberately excessive explicit budget. Preserve the timeout and use the result to check automatic headroom; do not convert it into a product fix in this packet.
7. Re-run every existing secure-report regression, including copied-runner, positional path, flag path, symlink, replacement and source-binding cases.

The final full selected run must be clean on a stable snapshot. A residual environment failure is reported with its exact class and rerun evidence; an isolated pass does not rewrite a failed full-suite record.

## 12. Decisions and their homes

This delivery follows `plugins/hexaemeron/skills/hypomnema/SKILL.md`. The impact graph, snapshot boundary and scheduler accounting are cross-cutting and expensive to reverse, so implementation writes the next free numbered ADR under `docs/decisions/`. The ADR records:

- why #622 is one selector-plus-executor capability rather than two drifting tools;
- why repository ownership is declarative and mechanically complete rather than inferred from imports;
- why workers rediscover and select by canonical index instead of receiving dotted IDs;
- why one global process budget and conservative quota-aware headroom were chosen after the measured contention boundary;
- why timing data has balance-only authority;
- why per-attempt source changes supersede and retry while between-invocation test drift is normal; and
- why an independent disposable clone is used instead of mutating the source checkout or a linked worktree's shared config.

The authoritative machine homes are `tests/check-map-v1.json`, `scripts/run_checks.py`, and the self-contained worker protocol in `plugins/hexaemeron/tests/run_tests.py`. Schema and protocol docstrings state their version, input bounds, status vocabulary and compatibility obligations. Tests are the home for exact selection, accounting, hostile config, drift and security examples.

`AGENTS.md` becomes the human entrypoint: it explains the planner/executor commands, how to request scope/full coverage, how automatic versus explicit jobs work, and that the JSON map is canonical. It no longer maintains a second hand-copied suite catalogue. Plugin `AGENTS.md` files need change only if they currently duplicate a command that becomes false.

Short comments beside fixture construction explain the non-obvious reason for repository-local signing isolation where the hostile regression would otherwise be surprising. They do not discuss any contributor's key. The secure Elenchus report compatibility stays in its existing code/tests rather than being redescribed elsewhere.

The completed Fiat study, runbook, audit rounds and receipts remain in their governed `.hexaemeron` and `audit/` homes. No decision is recorded in a cache, console-only message or issue comment alone. Shipped prose passes Imprimatur; no Brevitas gate applies to this completeness-oriented specification.
