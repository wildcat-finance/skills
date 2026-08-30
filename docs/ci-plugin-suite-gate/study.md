# Complete plugin suite gate study

Assuming, unless corrected:

1. Issue #889 authorises the workflow and repository-ruleset changes needed to
   make the complete plugin test graph a merge gate.
2. The starting ref is `main` at
   `4fe374dd33d43b86d800abe9240d62e09ed7d395`.
3. The repository currently contains sixteen plugin directories, not the
   fourteen present when #889 was filed.
4. The live `Required CI` ruleset already requires the root `invariants` check,
   but does not require any plugin suite and does not require a current-base
   result.
5. Publication is by `laurenceday`; governed commits remain authored by
   Shoggoth and are signed with `B83B60AE16F5DD1A`.

## 1. Problem statement

The repository has one declarative check graph and a bounded executor, but the
hosted merge gate runs only the root suite. Separate path-filtered workflows
cover Janus, Lazarus, Pandects and Synkrisis. Alexandria, Ariadne, Berean,
Brevitas, Hermes, Hexaemeron, Homologia, Horos, Lemma, Probitas, Sapheneia and
Tabularium can therefore regress while the required check stays green.

The current complete graph is not green in a fresh checkout. Homologia is not
owned by the graph. Hexaemeron regression fixtures depend on a filesystem
limit, evolving append-only evidence or unreachable historical Git objects
rather than the property they mean to guard. Checkpoint JSON also has a byte
ceiling but no structural depth ceiling. A hosted gate must repair those faults
rather than omit the affected tests.

Success is one unconditional GitHub Actions job named `plugins` that invokes
the repository-owned full graph, runs all sixteen plugin suites and every
declared shared lint or Solidity check, and reports failure for any incomplete
or failed check. The live ruleset must then require both `invariants` and
`plugins`, with current-base checking enabled and no bypass added.

## 2. Prior art

ADR-045 created `tests/check-map-v1.json` and `scripts/run_checks.py` as the
single ownership, dependency and execution graph. Its final boundary expressly
left hosted CI unchanged. The root `repo.yml` workflow later made `invariants`
unconditional because a required path-filtered job can be absent and wedge a
pull request. That same reasoning applies to the plugin gate.

The current path-filtered plugin workflows remain useful diagnostics, but none
is a complete graph and none is required. The live repository ruleset named
`Required CI` now requires `invariants`; that is a partial improvement since the
issue snapshot, not evidence that plugin suites gate a merge.

The fresh-base Hexaemeron run discovered 1,989 tests. It exposed five causes:
Homologia's missing graph entry; a macOS fixture that exceeds the host path
limit before reaching Fiat's own path ceiling; an exact-equality assertion over
an audit file whose pinned bytes remain an append-only prefix; an incident
fixture whose named commits are absent from fresh clones; and a JSON decoder
whose result depends on the interpreter's recursion behaviour. These are the
baseline defects this delivery owns.

The first complete-graph runs exposed further portability boundaries: a root
Git-index test treated timestamp movement as staged-content movement;
Synkrisis read macOS maximum resident set size as kibibytes rather than bytes;
an old Lazarus scaffold test rejected the newer unfiltered root workflows; the
audit synopsis walked concurrent ignored `tmp/` reports; and the issue-429
release proof compared a historical generator digest with the evolving current
generator. Each repair preserves the intended evidence and adds a focused
guard for the newly observed failure.

## 3. Constraints and non-goals

The workflow uses the existing graph and fixed argv executor. It does not grow
a second list of plugin commands. It runs on every pull request and every push
to `main`, without a path filter, so the required status is always produced.
The job has read-only repository permissions. It checks out full Git history
because the Hexaemeron suite verifies historical signed release objects, then
uses the pinned Python version, the Lazarus lock file and Foundry because those
are dependencies already named by the complete graph.

The graph must account for every current plugin directory, including Homologia.
Historical regressions remain meaningful in a fresh clone: a fixture may retain
the incident's counts and topology, but cannot require an unreachable object.
The issue-429 audit guard must preserve the exact pinned base bytes while
permitting later append-only audit records, and its release proof must bind the
generator digest recorded by that historical release rather than today's
generator. The checkpoint reader gains an explicit JSON nesting ceiling under
its existing byte ceiling. The published Goldfinch v1 producer stays
byte-identical: its descriptor-stage tests execute on hosted Ubuntu and report
an explicit capability skip only on a host, such as macOS, that cannot expose a
traversable process file-descriptor path; every other Lazarus test still runs.
The controller change advances Fiat's generation and the installable
Hexaemeron patch version without moving Fiat's held frontier.

This work does not remove the existing path-specific workflows, weaken any
suite, add a bypass actor, or claim that a GitHub Actions result proves a human
review. Issue #893 owns authorship and approval policy. The ruleset is not
tightened until the pull request has produced a successful `plugins` context,
because requiring a context that has never existed can wedge delivery.

Always: run the full local graph, the workflow contract tests, Promise Machine
checks, applicable prose and boundary lints, and signature verification before
publication. Ask first: reducing a suite, removing an existing workflow, adding
a bypass actor or changing the required-check names. Never: mark an omitted
check, incomplete run or scheduler error green; hide a platform skip that
hosted CI does not exercise; interpolate pull-request data into a shell command;
or update the live ruleset before the hosted context exists.

## 4. Design options

**A. Add twelve more path-filtered workflows.** This mirrors the current
partial arrangement but duplicates the check graph, can leave required
contexts absent, and makes new plugins easy to miss. Rejected.

**B. Put every plugin command directly in one workflow.** This produces one
gate, but creates a second command registry that will drift from ADR-045.
Rejected.

**C. Run `scripts/run_checks.py --full` in one unconditional workflow and
require its `plugins` job.** Chosen. The existing graph remains the source of
truth, the executor proves the complete plan and terminal dispositions, and one
stable check name can be required for every pull request.

**D. Replace `invariants` with the new full gate.** The complete graph already
contains the root suite, but removing the established gate during this repair
would broaden the migration and discard a separately visible root result.
Deferred. Both contexts remain required.

The chosen trade is duplicated root-suite execution between `invariants` and
`plugins`. That cost buys a stable migration and two independently visible
contracts. A later measured change may consolidate them after ruleset and
workflow evidence exists.

## 5. Risk register seed

```risk-register
missing-plugin | a new plugin is not entered in the check graph | root contract test compares plugin directories scopes checks and owners
absent-required-context | a path filter suppresses the required job | plugins workflow has no path filter and runs on every pull request
stale-command-list | workflow commands diverge from local commands | workflow invokes the one declarative full graph rather than listing suites
incomplete-green | a worker or suite disappears before a verdict | run_checks requires one terminal result for every selected check
dependency-drift | hosted Python or Foundry differs from the declared project | workflow reads .python-version installs the Lazarus lock and records Foundry setup
missing-history | a shallow Actions checkout omits signed objects required by release proofs | aggregate checkout uses fetch-depth zero and its workflow contract pins that setting
fixture-host-dependence | a regression passes only in one old checkout or filesystem | fixtures use controller-relative limits append-only prefixes and self-contained topology
decoder-exhaustion | bounded bytes still create unbounded nesting | checkpoint JSON refuses depth above a fixed ceiling before decoding
ruleset-wedge | a required context is named before Actions can produce it | update the ruleset only after plugins succeeds on the pull request
stale-base-green | a pull request is green only against an older base | enable strict required status checks in the live ruleset
secret-expansion | pull-request text reaches a shell or credential | fixed workflow argv read-only permissions and no untrusted interpolation
```

## 6. Glossary seeds

Complete graph: every declared repository check selected by
`scripts/run_checks.py --full`, including plugin suites, shared lints and
ordered Solidity checks.

Required context: the exact GitHub status-check name a repository ruleset waits
for before permitting a merge.

Current-base checking: the ruleset condition that requires the pull request to
be tested against the current protected-branch tip.

Structural fixture: a self-contained reconstruction that preserves the
incident's tested counts, overlap and ownership relations without relying on
unreachable repository objects.

## 7. Sources

- Issue [#889](https://github.com/wildcat-finance/skills/issues/889).
- `docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`.
- `tests/check-map-v1.json`, `scripts/run_checks.py` and their contract tests.
- `.github/workflows/repo.yml` and the existing plugin workflows.
- Live repository-ruleset response for ruleset `21830871`, read before design.
- The fresh-base Hexaemeron run and the five targeted failing cases named in
  section 2.

## 8. Signals, and the questions behind them

Ephoros applies to the hosted gate. The Actions job answers which commit and
event ran, whether setup completed, which graph checks ran, and whether the
aggregate result was green. `run_checks.py` writes a bounded JSON report as an
Actions artefact even on failure, so a maintainer can distinguish assertion
failure, missing executable, timeout, scheduler error and not-started work.
The live ruleset readback answers which exact contexts and strictness setting
now control `main`.

## 9. Boundaries, per capability

Phylax applies. The workflow consumes repository bytes and GitHub event state,
but passes no event text to a command. Actions are pinned by major version in
the repository's existing style, permissions are `contents: read`, dependency
installation uses the committed Lazarus lock, and Foundry installation uses the
same supported installer already used by the Solidity workflows. The local
executor retains fixed argv, bounded output and process-budget rules.

## 10. The budget, or its absence

The complete Hexaemeron baseline took roughly 144 seconds on the local machine.
No performance improvement is claimed. ADR-045's executor derives a bounded
CPU budget and runs independent checks concurrently; the workflow delegates to
that measured mechanism. Actions timeouts bound setup and execution. Any later
attempt to reduce hosted cost must retain the same graph and prove equivalent
coverage before changing this gate.

## 11. The fail-closed posture

Elenchus applies to each observed baseline defect. The parent behaviour must
reproduce the relevant failure, and the repaired case must pass without
weakening the underlying claim. The aggregate job exits non-zero when setup,
planning, any selected check, report creation or terminal-accounting fails. A
missing executable is failure, not a skip. The ruleset is read back after the
write and publication stops if either required context or strictness differs.

## 12. Decisions and their homes

Hypomnema places the hosted-gate decision in
`docs/decisions/ADR-053-require-the-complete-plugin-graph.md`. The executable
graph remains `tests/check-map-v1.json`; workflow procedure lives in
`.github/workflows/plugins.yml`; graph and workflow invariants live in tests;
the checkpoint depth boundary lives beside the other Fiat checkpoint ceilings;
and historical fixture qualifications stay with their tests. The study and
runbook remain under `docs/ci-plugin-suite-gate/`. The live ruleset is external
state and is captured by exact post-write readback rather than represented as a
repository file.
