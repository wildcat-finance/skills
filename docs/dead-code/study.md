# Study: establish a report-only dead-code baseline

Issue [#437](https://github.com/wildcat-finance/skills/issues/437) asks for a
repository-wide candidate inventory. The run starts from `main` at
`0698092d27871031b6d5521d77f6e8d8dc5dc937`.

Assuming, unless corrected:

1. The analysed universe is the Git-tracked tree at one commit. Modified
   tracked bytes refuse a baseline; ignored Fiat state and unrelated untracked
   files are outside the universe.
2. The exact repository interpreter is Python 3.14.6 from `.python-version` and
   `pyproject.toml`. Ambient `/usr/bin/python3` is 3.9.6 and is not an allowed
   substitute.
3. `.horos/boundary.json` remains the authority for generated, vendored,
   binary, lockfile and content-addressed exclusions. This command consumes
   that evidence; it does not widen Horos into a reachability skill.
4. `tests/check-map-v1.json` and `scripts/run_checks.py` remain the authority
   for repository check ownership and execution. Coverage consumes their
   discovered commands and results rather than creating another scheduler.
5. Findings are candidates. No confidence level, static signal or coverage gap
   proves semantic uselessness or authorises deletion.
6. This is repository tooling, not a frontier advancement for Fiat, Horos,
   Metron or another skill. No `EVOLUTION.md` row is owed.

## 1. Problem statement

Build one deterministic root command for contributors and maintainers that
inventories what it analysed and reports bounded dead-code signals without
editing source. A working prototype provides equivalent text and canonical JSON
reports, a pinned baseline, checked suppressions and explicit analyser status.

Current `main` was remeasured rather than inheriting the 21 August issue counts:

- 3,015 tracked paths, including 667 Python files with 294,599 lines and 168
  Solidity files;
- 23 declared checks across 22 selected scopes in the checked impact map;
- 494 root tests under Python 3.14.6: 493 pass and one inherited isolated-copy
  test fails with `MP407` on this Darwin host;
- the historical #437 universe probe, executed from its old branch against the
  current commit, finds 1,909 analysed paths and 1,106 hard-classified
  exclusions: 978 generated, 72 content-addressed, 50 binary, three lockfiles
  and three vendored paths. It has no registered analyser and therefore
  establishes zero reachability findings, not a clean tree.

The proving demo path, from a clean checkout, is:

```bash
python3 scripts/dead_code.py report
python3 scripts/dead_code.py report --json
python3 scripts/dead_code.py baseline --check
python3 scripts/run_checks.py --scope dead-code
```

The prototype is working when both report formats carry the same ordered
findings and statuses; the universe is non-empty and commit-bound; every
finding names its analyser, object, evidence, confidence and nearest
false-positive boundary; positive fixtures exercise every signal family;
negative fixtures retain dynamic registration, CLI entry points, intentional
fixtures and Horos-classified content; malformed reports, collapsed discovery
and analyser crashes fail; existing candidate count alone does not fail; and
no command deletes or rewrites source.

## 2. Prior art

### Current repository and organisation

The current execution authority is `scripts/run_checks.py` plus
`tests/check-map-v1.json`. It already proves total path ownership, rejects
unreachable checks and stale commands, closes dependencies, executes one
immutable snapshot and emits bounded results. `scripts/dead_code.py` must be a
declared check and a consumer of that graph, not a rival scheduler.

Horos at `plugins/horos/skills/horos/scripts/horos.py` and
`.horos/boundary.json` already classify token sinks with evidence. The
Promise Machine checker, Hypomnema link checker, marketplace tests and
check-map validation already expose narrower repository-graph failures. The
new command normalises those signals and adds missing reachability analysis;
it does not copy their rules.

The last two merged pull requests that changed this subject were read in full:

- [#745, Reconstruct, check and prove the affected-scope test runner](https://github.com/wildcat-finance/skills/pull/745),
  merged 28 August 2026. It made the impact map and runner authoritative. Its
  carried Darwin failures, portable-runtime link findings, scratch-guard
  evasion forms and runner edge cases remain facts about execution, not
  dead-code findings. This run carries them as analyser statuses and invokes
  the checked runner rather than duplicating process control.
- [#732, Detach plugin suites from unrelated changes](https://github.com/wildcat-finance/skills/pull/732),
  merged 28 August 2026. It narrowed hosted workflow ownership and recorded the
  same Lazarus and Synkrisis Darwin failures. This run preserves those trigger
  boundaries. Any dead-code lane is report-only on finding count and must not
  restore every plugin workflow on every unrelated change.

The old unmerged #437 branch is evidence, not authority. Its two commits,
`6779ca2fdd1211f3b145f03135c024ac10ef1388` and
`a07436c0d4190bb2e03e29c5b121720724352f80`, are based on
`8de7a4bc910e398107ff2f54a4cf92a82e764a76` and deliver only universe
discovery, report rendering and 38 scaffold tests. The second commit correctly
extends a hard Horos directory classification to descendants without capturing
a sibling sharing the prefix; that construction carries forward. The branch's
standalone workflow, 1,512-path measurement, Python 3.11 premise, Slither
0.11.6 pin and branch-coverage deferral are stale. Its seven-step runbook never
landed and cannot govern this run.

### Audit record inventory

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
verified all 39 committed synopsis views against their authoritative sources.
The in-scope records and reading modes are:

- `audit/AUDIT.md` through fresh `audit/AUDIT_SYNOPSIS.md`, limited to root
  command, atomic-write, degraded-result and repository-graph records. The
  relevant `scripts/contributors.py` S3-R2-01 is fixed and retains one rule:
  read-only checks do not sweep old writer litter.
- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`
  through its fresh synopsis. Its findings are fixed. Its remaining CR-only
  line handling, sampled-window gaps and census-currency ideas define Horos
  recall limits; this report carries the classifier evidence without
  strengthening it.
- `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` through its
  fresh synopsis. Its product findings are fixed; the current root rerun still
  reproduces the separate Darwin `MP407` isolated-copy failure.
- all four `audit/rounds/fiat-622-*.md` sources through their fresh synopses.
  Their scheduler findings are fixed. Their unexercised high-capacity hosts,
  retained-descriptor lifetime, unexpected-success accounting, multi-subtest
  report-reader limit and scratch-guard evasion forms stay outside this
  command's ownership and are surfaced as runner evidence or status.

The remaining 32 verified sources are out of scope: they audit venue evidence,
credit laws, hook semantics, controller transitions, prose or other domain
behaviour inside the analysed tree; none defines Git universe discovery, Horos
classification, checked-run scheduling or this report format. The legacy
`plugins/hexaemeron/audit/AUDIT.md` synopsis was inspected and likewise
excluded: its controller and hook-gate findings do not govern the root runner.
No authoritative #437 audit source exists because its old branch did not land
one. No audit evidence gap blocks the study.

### Outside both repositories

- Vulture provides confidence-ranked Python dead-code candidates, including a
  high-confidence-only mode: <https://github.com/jendrikseipp/vulture>.
- Ruff F401 and F841 specify unused-import and unused-local signals and their
  suppression boundaries: <https://docs.astral.sh/ruff/rules/unused-import/>
  and <https://docs.astral.sh/ruff/rules/unused-variable/>.
- Python 3.14 `sys.monitoring` exposes line and left/right branch events without
  adding a package: <https://docs.python.org/3.14/library/sys.monitoring.html>.
- Slither names `unused-state` high-confidence and `dead-code`
  medium-confidence detectors, and can emit JSON for selected detectors:
  <https://github.com/crytic/slither/wiki/Detector-Documentation>.
- Forge exposes coverage for Foundry projects:
  <https://getfoundry.sh/forge/reference/coverage/>.

These tools produce signals, not deletion authority. Current local probes find
Forge 1.7.1 and Slither 0.11.4; absence or a different version is report data.

## 3. Constraints and non-goals

Constraints:

- exact starting ref `0698092d27871031b6d5521d77f6e8d8dc5dc937` on
  `main`;
- Python 3.14.6, standard library for the root implementation, and fixed argv
  with no shell for external tools;
- a deterministic, schema-validated, report-only command over tracked Git
  bytes, with stable analyser and suppression identities;
- current Horos and checked-runner contracts are consumed by path and version;
  generated portable runtime stays excluded under its recorded classification;
- a baseline records commit, Git tree, universe digest, analyser versions,
  statuses, finding identities and suppression digest.

Non-goals are source deletion, automatic rewriting, semantic proof of
uselessness, type checking, a dashboard, database or backup service, changing
Horos's promise, replacing the affected-scope runner, repairing the inherited
Darwin failures, and making finding count a merge gate. A future diff gate is a
separate decision after the baseline is triaged.

Boundaries in force:

- **Always:** run both the root suite and every check selected by the changed
  scope before a commit; run Imprimatur on shipped prose; record a before and
  after measurement before any speed-motivated change; regenerate Horos last.
- **Ask first:** add a dependency; change the report schema after a baseline is
  published; widen CI triggers beyond the owning workflow; change a public CLI;
  alter check ownership or a Promise Machine declaration.
- **Never:** commit credentials or signing material; import or execute a Python
  file merely to analyse it; edit vendored code; delete a failing test or source
  candidate; describe unexecuted analysis as clean; claim a command ran when it
  did not.

## 4. Design options

**A. One stdlib root command consuming Horos and the checked runner.** Git and
AST analysis discover the static universe; `sys.monitoring` records Python
line/function/branch execution through declared check commands; Slither and
Forge supply optional Solidity signals; existing graph checks contribute
machine-readable statuses. Trade: more local adapter code and lower Python
recall than dedicated packages, in exchange for one pinned implementation and
no second dependency or scheduler.

**B. One root command built around Vulture, Ruff and coverage.py.** This has
broader mature Python analysis. Trade: it adds the repository's first Python
tool dependencies, requires a lock/update policy, and still needs custom graph,
Horos, Solidity and report adapters.

**C. Widen Horos into reachability analysis.** It reuses the walk directly.
Trade: it collapses the explicit boundary between evidenced reading exclusion
and claims about unused objects, and would require a skill promise and frontier
change.

**D. Put one analyser in every plugin suite.** It keeps ownership local. Trade:
it cannot see cross-plugin imports, root manifests, generated-copy topology or
orphaned docs and fixtures, which are the issue's core gap.

**Chosen: A.** It is the lowest-comprehension construction that meets the issue
on the current tree because #745 already centralised discovery and execution,
and Python 3.14.6 now supplies branch events the old branch lacked. It trades
away Vulture/Ruff recall and coverage.py's mature arc model. Each missing signal
is named in analyser status, and the schema permits a later adapter without
rewriting finding identity.

## 5. Risk register seed

```risk-register
discovery-collapse | Git tree and Horos classification join | an empty or unexpectedly reduced universe refuses instead of producing zero findings
tree-prefix-classification | hard Horos directory entries | descendants inherit the exact parent evidence while siblings sharing the textual prefix remain analysed
analyser-absence-as-clean | every analyser status | absent, skipped, timed-out and crashed remain distinct from ran-with-zero-findings
dynamic-reference-blindness | Python import and call graph | importlib, entry points, decorators, __all__, getattr and computed paths lower confidence or retain the object
coverage-failure-as-dead | check execution under monitoring | a failing, incomplete or unselected check yields degraded coverage status and no never-executed finding
monitoring-leak | Python 3.14 sys.monitoring callbacks | tool id, callbacks and event masks are restored after every command and isolated in fixtures
untrusted-parse | tracked Python source | analysis parses bytes without import, eval or execution and reports syntax failures by path
subprocess-argv | Git, Slither, Forge and checked-runner invocations | fixed argv, no shell, bounded output, declared cwd and inherited runner timeouts
solidity-project-attribution | Foundry project discovery | each finding names one project, tool versions and build or coverage status rather than a repository-wide clean claim
repository-edge-overclaim | docs, fixtures, schemas, routers and manifests | every edge names the parser or declaration that produced it and computed references prevent high confidence
report-parity | text and JSON renderers | both formats derive from one ordered model and tests compare stable identities and counts
baseline-staleness | committed baseline | commit, tree, universe, analyser versions, statuses and suppression digest all bind or check refuses
suppression-abuse | suppression document | each narrow id has a reason, owner and still-present target; stale, broad or unused entries refuse
path-confinement | report, baseline and temporary files | no-follow descendant checks and atomic replace keep writes inside owned paths
partial-write | report and baseline publication | interrupted writes leave no accepted half-file and read-only checks never sweep unrelated litter
finding-overclaim | candidate wording and confidence | no emitted record says proved dead, safe to delete or semantically unused
```

## 6. Glossary seeds

- **Universe:** tracked paths at one commit, partitioned into analysed and
  evidence-classified exclusions.
- **Analyser:** one versioned signal source with a declared status and boundary.
- **Finding:** a stable candidate identity plus object, evidence, confidence and
  nearest false-positive boundary.
- **Coverage signal:** an observed execution relation for named checks, never a
  proof that unobserved code is unreachable.
- **Repository edge:** a named reference between a manifest, router, command,
  fixture, schema, document or generated copy and another tracked object.
- **Suppression:** a narrow, reasoned decision to retain one candidate; not a
  deletion waiver or hidden ignore pattern.
- **Baseline:** the report identity bound to one Git tree, universe and analyser
  set.
- **Degraded:** an analyser began but its evidence did not establish the
  requested signal.
- **Not available:** the named optional tool was absent before execution.

## 7. Sources

- GitHub issue #437, including its 26 August keep-but-remeasure review.
- Current `AGENTS.md`, `.python-version`, `pyproject.toml`,
  `.horos/boundary.json`, `scripts/run_checks.py`, `tests/check-map-v1.json`,
  `PROMISE_MACHINE.md` and `tests/promise_machine_coverage.json` at the starting
  ref.
- Pull requests #745 and #732, including their full bodies, files and carried
  work.
- Old branch commits `6779ca2` and `a07436c`, its committed study, runbook,
  schema, script, tests and workflow.
- The seven in-scope audit sources and verified synopsis modes listed in item 2;
  the synopsis currency command's complete 39-source output.
- The Vulture, Ruff, Python 3.14, Slither and Foundry primary documentation
  linked in item 2.
- Reproduction commands and outputs in item 1 for current counts, universe,
  check inventory, versions and root-suite status.

## 8. Signals, and the questions behind them

This command runs in terminals and CI, so Ephoros applies to the report and job
summary rather than a service dashboard.

- *Did it analyse the intended tree?* The header emits commit, tree, universe
  digest, analysed/excluded counts and each classification count.
- *Which signals actually ran?* One status per analyser emits version, command
  identity, selected check manifest, duration and one of `ran`, `not-available`,
  `degraded` or `failed` with reason.
- *What changed from the baseline?* Comparison emits added, resolved,
  suppressed and stale-suppression identities by analyser and path.
- *Did candidates block development?* The terminal status distinguishes a
  green report with findings from a failed report contract; CI publishes the
  count but gates only malformed, crashed or collapsed analysis.

## 9. Boundaries, per capability

Phylax governs the controls cited here.

- **Tracked-source read:** contributor-controlled bytes can exhaust or confuse
  parsers. Use bounded regular-file reads from the recorded tree, never import
  analysed Python, reject unsafe paths and retain per-file parse errors.
- **Check execution:** repository tests execute arbitrary project code. Delegate
  selection, snapshotting, timeouts, process groups and result accounting to
  `scripts/run_checks.py`; consume its bounded record.
- **External Solidity tools:** Slither and Forge execute compilers and project
  configuration. Use fixed argv, declared project cwd, version capture and
  existing timeouts; absence is visible and a crash is not zero findings.
- **Classification and manifests:** malformed JSON can erase the universe or
  invent graph edges. Use duplicate-key rejection, closed shapes, exact schema
  versions and a non-empty floor before analysis.
- **Artefact writes:** symlink swaps and interruption can escape or corrupt a
  baseline. Use confined no-follow paths, stable rereads, same-directory atomic
  replacement and product-specific temporary prefixes.

## 10. The budget, or its absence

The static Python plus repository-graph report should finish within 60 seconds
on a warm checkout at the starting ref. Record at least three runs before and
after any speed-motivated change using the same interpreter and tree:

```bash
/usr/bin/time -p python3 scripts/dead_code.py report --analyser python,repository --json
```

This follows Metron; the recorded median and spread decide keep or revert.
Coverage and Solidity have no aggregate speed budget because they execute the
declared suites and optional toolchains. Their existing per-check timeouts and
the report's measured durations are still required. No performance conclusion
may be drawn across different manifests, commits or tool versions.

## 11. The fail-closed posture

Elenchus governs any failure worked during implementation. The report refuses
on a dirty tracked tree, unsafe path, malformed or stale Horos boundary,
duplicate-key or wrong-schema input, empty/collapsed universe, analyser crash,
missing required status, report-schema failure, text/JSON identity mismatch or
unsafe write. `baseline --check` additionally refuses changed commit, tree,
universe, analyser version/status or suppression digest.

An optional tool absent before execution is `not-available`, not a crash. A
check failure or incomplete monitoring run is `degraded` and contributes no
absence finding. Existing candidate count never changes the exit status by
itself.

Every implementation or audit fix follows the guard convention: preserve the
smallest reproducer, show the focused test red on the exact parent bytes, fix
the cause, then show the same test green and run the affected scope. If the
failure cannot be reproduced, record `inconclusive`; do not guess at a fix.

## 12. Decisions and their homes

Hypomnema governs the records.

- The expensive decision is a report-only root capability that consumes Horos
  classification and the checked runner without changing either promise. Put
  it in the next free `docs/decisions/ADR-*.md`, chosen when the step begins so
  concurrent work cannot collide.
- The finding, analyser-status, baseline and suppression shapes live in schemas
  under `schemas/`; the schemas are the normative records and prose links to
  them instead of restating fields.
- Capability and operator documentation lives under
  `docs/promise-machine/dead-code-v1.md`; the study and runbook receive durable
  copies under `docs/dead-code/`.
- Current baseline bytes live under `.dead-code/` and name their generating
  command. A later diff gate requires a new ADR and issue; it is not smuggled
  into a suppression or workflow threshold.
