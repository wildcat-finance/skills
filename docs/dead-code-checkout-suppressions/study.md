# Study: validate the dead-code suppressions file at the checkout

Assuming, unless corrected:

- “the checkout” means the clean, tracked current commit of the target worktree. A
  dirty tracked tree has no single Git object to bind the report and suppressions
  to, so the validator refuses it rather than reading a mixture of committed and
  working-tree bytes.
- The validation universe is the existing fixed `python,repository` baseline
  analyser set. A suppression can be judged unused only against the same complete
  static report that defines its finding identity.
- Validation does not make dead-code findings fatal and does not authorise deletion.
  It checks the exception file, not the candidates it annotates.
- The target is repository Python and workflow wiring. No Solidity, chain state,
  network service, migration, or new dependency belongs to this prototype.

## 1. Problem statement

The user is the contributor changing `.dead-code/suppressions.json`; the other
consumer is the maintainer who needs the pull-request workflow to reject a bad
exception before it reaches `main`. At base
`c79d6781e2278642d1653d50671acdabb5867ef8`, the repository has a strict parser
for suppressions but no workflow command validates the file at the checkout.
`baseline --check` deliberately loads the suppression bytes from the baseline's
older source commit. The two live `report` demonstrations run no analyser and do
not load suppressions. The checked runner executes unit fixtures, not a live
checkout validation. Deleting the file, making it malformed, adding a broad or
duplicate entry, or naming a finding absent from the current static report can
therefore leave the demonstrated workflow green.

A working prototype adds one explicit, read-only checkout command. On a clean
tree it resolves the current commit, builds the fixed `python,repository` report
for that commit, reads `.dead-code/suppressions.json` as a regular file from the
same commit, and passes both to the existing closed parser. Missing, malformed,
broad, duplicate, unsorted, stale-target, mismatched-target, and unused entries
must refuse. An empty canonical entry list must pass. The command must be a named
check in the `dead-code` scope so the existing workflow invocation
`python3 scripts/run_checks.py --scope dead-code` exercises the checkout rather
than only fixtures.

The proving path is:

1. focused tests construct clean repositories for each accepted and refused case,
   including a non-empty exact suppression;
2. an integration fixture proves the dedicated command reads the current commit,
   while `baseline --check` still reads its recorded source commit;
3. the declared check-map test proves the command is owned by `dead-code` and is
   selected by `scripts/run_checks.py --scope dead-code`;
4. the live clean checkout runs the dedicated command, `baseline --check`, the
   focused dead-code suite, and the checked runner scope under Python 3.14.6; and
5. `/usr/bin/time -p` proves each analyser-bearing path stays inside the 46-second
   wall-time budget on this checkout.

## 2. Prior art

### Repository

`scripts/dead_code.py:3462-3538` already owns the useful enforcement primitive.
`parse_suppressions` accepts a closed schema and exact SHA-256 finding identities,
requires canonical sorted JSON, and rejects duplicate, broad, stale, mismatched,
or unused entries. `load_suppressions` adds bounded regular-file reading from one
named commit. `command_baseline` uses those functions at the current commit when
writing and at the recorded source commit when checking
(`scripts/dead_code.py:4123-4194`). Reuse those functions; a second validator
would create two meanings of valid.

The current operator contract says the first two report commands run no analyser
and that a later source or suppression change may leave a valid baseline behind
the checkout (`docs/promise-machine/dead-code-v1.md:8-46`). That explains why
always validating suppressions in ordinary `report` is wrong: a legitimate
non-empty file would be judged against an empty analyser result. ADR-053 keeps
candidate discovery report-only. ADR-059 makes baseline currency observable but
non-fatal. Neither prevents a malformed exception file from failing its own
checkout validator.

The check map gives `.dead-code`, the script, schemas, workflow, tests, and dead
code documents to the `dead-code` scope. Its only check is currently
`dead-code-suite`, a unit-test invocation. ADR-045 already establishes that the
check map, rather than workflow-local command duplication, is the durable owner
of scope selection.

### Organisation and merged work

The last two merged pull requests that changed this subject were read in full.

- PR [#1001](https://github.com/wildcat-finance/skills/pull/1001), merge commit
  `ec426cd0`, delivered issue #936's baseline-currency reporting. Its current
  audit source is
  `audit/rounds/fiat-936-report-dead-code-baseline-staleness-instead.md`; the
  whole-set synopsis check passed, so the committed synopsis was also usable.
  Round 1 recorded S1-R1-01 as the open low-severity checkout-suppression gap
  now tracked by #962. S1-R1-02 and S1-R1-03 were fixed and guarded. The
  informational S1-R1-04 records an inaccurate historical call-order sentence
  in already receipted run material and remains deliberately unfixable there.
  Round 2 had no findings and a null Elenchus verdict. Its not-checked inventory
  included the security suite and hosted runner; final composition supplied the
  relevant Actions evidence. It also left partial operator recovery indexing
  open, retained substitution-only refusals 7 and 8, and named #939 and #950 as
  other scopes. This run accepts S1-R1-01 by name and does not reopen the other
  items.
- PR [#929](https://github.com/wildcat-finance/skills/pull/929), merge commit
  `7e97b519`, reconciled the report-only baseline on then-current `main`. Its
  audit source is absent from the current tree, so it was read directly with
  `git show origin/fiat/437-dead-code-baseline-latest-main-reconciliatio-step-1-reconcile-and-publish-the-signed--audit:audit/rounds/fiat-437-dead-code-baseline-latest-main-reconciliatio.md`
  at audit head `80542f6b`. That round had zero findings and a null Elenchus
  verdict. It preserved 435 advisory candidates, zero suppressions, a degraded
  repository analyser, and the rule that no absence claim or deletion authority
  follows. Those limits carry forward unchanged.

The originating issue #437 audit source is also branch-only and was read directly
at audit head `102b7c1e` from
`origin/fiat/437-establish-a-report-only-dead-code-baseline-step-4-pin-the-baseline-check-suppressi--audit:audit/rounds/fiat-437-establish-a-report-only-dead-code-baseline.md`.
All of its findings are fixed or guarded. The Step 4 findings most relevant here
were S4-R1-01, which prevented a failed analyser from being baselined, and
S4-R1-02, which prevented baseline and suppression records from feeding the
repository graph. Step 4 round 2 had no findings and a null verdict. Earlier
guards for output confinement, path substitution, coverage completeness,
process cleanup, secret-bearing argv, and tool-result parsing remain required.
That audit did not check hosted CI, the security suite, or external-tool
behaviour; this Python-only prototype does not turn those unknowns into claims.

### Outside the organisation

Ruff's official RUF100 rule rejects suppression directives that no longer match
a diagnostic, and its linter documentation describes checking whether a
suppression corresponds to a violation. Vulture's official documentation
prefers explicit whitelists over broad name/decorator ignores and describes
checking whitelist syntax and existence. These are precedents for keeping an
exception attached to a current finding, not specifications for this repository.
Wildcat's exact identity, path, symbol, clean-commit, and analyser-completeness
rules remain stricter and authoritative here.

## 3. Constraints and non-goals

The exact starting ref is `main` at
`c79d6781e2278642d1653d50671acdabb5867ef8`; `HEAD`, local `main`, and
`origin/main` resolved to that same object when studied. The worktree was clean.
The required interpreter is the `.python-version` value, CPython 3.14.6, which
also matched `python3 --version`. The implementation uses only the standard
library and existing repository helpers.

Always:

- bind the report and suppression bytes to the same resolved current commit;
- require a clean tracked tree before calling that binding a checkout result;
- use `BASELINE_ANALYSERS` and the existing `load_suppressions` parser;
- refuse incomplete analyser states before accepting an absent-finding result;
- keep the command read-only and keep candidate count advisory;
- route the live validation through `tests/check-map-v1.json`; and
- retain the source-commit behaviour and summary of `baseline --check`.

Ask first:

- before changing which analysers define the baseline universe;
- before changing the suppression schema or finding identity algorithm;
- before making a candidate count, baseline currency, or degraded analyser state
  a new repository policy; and
- before adding a dependency, network lookup, generated durable artefact, or
  GitHub-side mutation.

Never:

- delete or rewrite a reported candidate;
- treat a zero from an incomplete analyser as proof of absence;
- validate a dirty working-tree suppression file against committed source;
- weaken the existing size, regular-file, symlink, confinement, or subprocess
  controls;
- silently broaden `report` so its documented no-analyser invocation rejects
  non-empty suppressions; or
- make `baseline --check` read checkout suppressions instead of the recorded
  source-commit bytes.

Non-goals are refreshing `.dead-code/baseline.json`, triaging the 435 recorded
candidates, creating a suppression, changing report or baseline schemas, adding
an expiry policy, proving external analyser semantics, changing ADR-053's
report-only policy, or modifying unrelated open work from #939 or #950.

## 4. Design options

Three constructions were compared. All three reuse the existing suppression
parser and can present a direct recovery command. The closed selection record is
`.hexaemeron/design-evidence.json`; its reports are below
`.hexaemeron/design-reports/`.

### `checkout-suppressions-command` (selected)

Add a dedicated command, for example `suppressions --check`. It performs the
clean-tree/current-commit/report/load sequence and prints a bounded success
summary. Register it as a separate check owned by the `dead-code` scope. The
trade is one new narrow CLI surface and one additional full analyser pass in CI.
It changes no existing command's meaning, gives operators a direct recovery
entrypoint, and makes the current checked-runner invocation enforce the file.

### `report-suppressions-mode`

Add an explicit suppression-checking flag to `report`, using the fixed analyser
set whenever the flag is present, and register that form in the check map. It
costs the same analyser time and writes no durable artefact. The trade is a new
mode matrix across `--json`, `--output`, `--analyser`, and `--coverage`; it also
changes the public contract of a command whose ordinary form intentionally runs
no analyser. Its compatibility count is therefore worse without a time or space
gain.

### `baseline-dual-snapshot`

Keep one public validation entrypoint by making `baseline --check` reconstruct
both the recorded source commit and the current checkout. This catches the gap,
but changes baseline check from one historical proof into two different proofs
and repeats the expensive analysers. Measured sequentially on the exact checkout,
the full live report and baseline check totalled 67.54 seconds, exceeding the
46-second ceiling. It is eliminated by the hard time gate.

The selection matrix is reproduced here for review; the JSON record and bound
reports are authoritative.

| Candidate | exact suppression contract | baseline check ms | checkout validation ms | durable bytes | changed command contracts | recovery entrypoint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `checkout-suppressions-command` | true | 34500 | 33040 | 0 | 0 | true |
| `report-suppressions-mode` | true | 34500 | 33040 | 0 | 1 | true |
| `baseline-dual-snapshot` | true | 67540 | 67540 | 0 | 1 | true |

The baseline time gate is at most 46,000 milliseconds. The comparative metrics
minimise checkout validation time, durable bytes, and changed existing command
contracts. `baseline-dual-snapshot` fails the time gate.
`checkout-suppressions-command` and `report-suppressions-mode` tie on measured
time and space, while the dedicated command changes zero existing command
contracts rather than one. The selected candidate is therefore the unique
non-dominated survivor; simplicity was not used as an unmeasured tie-breaker.

## 5. Risk register seed

Warden should enumerate these boundaries. An entry marked reviewed must cite the
guard or direct evidence; absence of a boundary may be marked not applicable
with its reason.

```risk-register
checkout-binding | the clean working tree, resolved commit, report and committed suppression bytes | one commit supplies source and suppressions and a dirty tracked tree refuses
missing-suppressions | the Git object reader at .dead-code/suppressions.json | a missing path, directory, symlink or oversized object refuses rather than becoming an empty list
stale-suppression | suppression identity, path and symbol against the current report | broad, duplicate, absent, mismatched, stale, unsorted and noncanonical entries each have a hostile guard
partial-report | analyser states before an absent-finding judgement | failed or not-available analysers cannot make an unused suppression pass and degraded behaviour remains explicit
baseline-semantics | the new checkout command beside baseline --check | the baseline checker still reads source-commit suppressions and retains its currency-only exit semantics
runtime-budget | the second full analyser pass selected by workflow wiring | both checkout validation and baseline check remain within 46000 milliseconds under the pinned measurement command
check-map-ownership | the dead-code scope and its named checks | the scope selects both unit conformance and the live checkout validator without workflow-only duplication
report-contract-drift | report's default no-analyser interface and optional modes | the implementation does not make ordinary report depend on suppressions or create flag interactions
repository-substitution | root discovery, root directory descriptor and commit reads | existing confinement, regular-file and repository-replacement guards still cover the new path
interrupted-validation | an analyser process or command interrupted before completion | no durable result is partially written and nonzero exit establishes no validation result
advisory-authority | a valid suppression file beside report-only candidates | success validates exception structure only and never authorises candidate deletion or a clean-code claim
operator-recovery | the failure message and documented rerun path | the message names the file or analyser cause and the operator can rerun one dedicated command after correction
```

## 6. Glossary seeds

`checkout validation` means one result over the clean, tracked current commit,
with report and suppression bytes read from that same commit.

`suppression` means a reviewed exception naming one exact finding identity,
path, symbol, reason, and owner; it does not remove the finding.

`unused suppression` means an entry whose exact finding identity is absent from
a complete current static report.

`stale target` means a suppression path outside the report's analysed universe.

`baseline source commit` means the immutable commit recorded in
`.dead-code/baseline.json` and reconstructed by `baseline --check`.

`baseline currency` states whether relevant paths changed after the baseline's
publication; it is reported, not gated.

`report-only` means findings are advisory and a non-zero count is successful;
contract failures still refuse.

`complete static report` means the fixed `python,repository` analyser run whose
states are eligible for suppression validation.

`live checkout check` means the named check-map command that validates committed
suppressions at the current commit rather than a unit fixture.

## 7. Sources

Repository and run evidence:

- issue [#962](https://github.com/wildcat-finance/skills/issues/962), read through
  the GitHub API on 2026-08-31;
- `scripts/dead_code.py:67-78`, `scripts/dead_code.py:3441-3538`,
  `scripts/dead_code.py:4096-4194`, and `scripts/dead_code.py:4214-4275` at
  `c79d6781e2278642d1653d50671acdabb5867ef8`;
- `.dead-code/suppressions.json`, a 61-byte canonical empty list at that commit;
- `.github/workflows/dead-code.yml:47-65`, `tests/check-map-v1.json:4-20`, and
  `tests/test_dead_code.py:2498-3048` at that commit;
- `docs/promise-machine/dead-code-v1.md`,
  `docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`,
  `docs/decisions/ADR-053-keep-dead-code-discovery-report-only.md`, and
  `docs/decisions/ADR-059-report-baseline-currency-without-failing-the-check.md`;
- PR [#1001](https://github.com/wildcat-finance/skills/pull/1001), merge
  `ec426cd0`, and current-tree source
  `audit/rounds/fiat-936-report-dead-code-baseline-staleness-instead.md`;
- PR [#929](https://github.com/wildcat-finance/skills/pull/929), merge
  `7e97b519`, and the two branch-only #437 audit sources and refs named in
  section 2;
- `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
  which exited zero before the audit views were used;
- `python3 -m unittest` over nine named `BaselineContractTests`, which passed and
  established the existing exact suppression primitive; and
- `/usr/bin/time -p` measurements: full live static report 33.04 seconds,
  existing baseline check 34.50 seconds, and their sequential combination 67.54
  seconds on the exact clean checkout with Python 3.14.6.

Outside references:

- Ruff, “unused-noqa (RUF100)”: https://docs.astral.sh/ruff/rules/unused-noqa/
- Ruff, “The linter”: https://docs.astral.sh/ruff/linter/
- Vulture official repository and whitelist guidance:
  https://github.com/jendrikseipp/vulture

## 8. Signals, and the questions behind them

These signals answer the unattended-run questions. Their event field and
cardinality contract belongs to
`plugins/hexaemeron/skills/ephoros/SKILL.md`; this study does not duplicate it.

- **Did checkout validation run, and against which commit?** The implementation
  step emits one bounded success line carrying the command identity, current
  commit, analyser states, finding count, and suppression count. A refusal goes
  to stderr and returns nonzero, so silence is not success.
- **Why did the workflow refuse?** The parser already distinguishes missing or
  irregular input, malformed/canonicality faults, stale or mismatched targets,
  unused identities, and incomplete analyser states. Tests and documentation
  keep those categories actionable without logging source contents.
- **Did the historical baseline proof change meaning?** The integration step
  captures the `published`, `currency`, and `status` lines from
  `baseline --check` and separately captures the checkout-validation summary.
  Different command identities prevent one result being mistaken for the other.
- **Did the new work exceed its budget?** The measurement step records elapsed
  wall time and exit status for the dedicated command and baseline check under
  the same pinned checkout and interpreter.

No persistent metric or network telemetry is added: the job is short-lived,
already has Actions logs, and high-cardinality finding identities belong in a
failure diagnostic rather than a metric label.

## 9. Boundaries, per capability

Boundary and control ownership stays with
`plugins/hexaemeron/skills/phylax/SKILL.md`; these are the capabilities this
design actually opens.

- **Repository selection.** The directory argument could name an unexpected
  checkout. Existing root discovery, root descriptor, clean-tree, resolved-commit,
  and replacement checks bind operations to one repository. The new command must
  use them in the same order as `command_baseline`.
- **Git object input.** Committed suppression and source bytes are untrusted
  repository content. Existing bounded Git calls, regular-file reads, maximum
  byte and path limits, duplicate-key rejection, and closed canonical JSON close
  that boundary. No working-tree fallback is allowed.
- **Analyser subprocesses and inspected source.** The fixed existing analysers
  retain list argv, timeouts, byte ceilings, process cleanup, and explicit state
  reporting. Failed or unavailable state refuses validation. The design adds no
  shell, URL, credential, or environment-secret input.
- **Filesystem output.** The selected command writes no repository artefact.
  Stdout carries one bounded summary and stderr a bounded refusal. Existing
  analyser temporary handling remains the only transient output boundary.
- **Check-map execution.** `scripts/run_checks.py` executes repository-declared
  argv. The new entry must be a literal argv with repository-root cwd, owned by
  the existing dead-code scope and covered by its map-shape tests.

There is no key-custody, network, database, smart-contract, RPC, or release-signing
capability in scope, so those Phylax boundaries are not opened by this step.

## 10. The budget, or its absence

The budget contract belongs to
`plugins/hexaemeron/skills/metron/SKILL.md`. Two wall-time ceilings apply on the
exact clean checkout with Python 3.14.6:

- `baseline --check` must remain at or below 46 seconds; its measured base is
  34.50 seconds.
- the new checkout validator must remain at or below 46 seconds; the equivalent
  fixed-analyser live report measured 33.04 seconds.

Measure the implementation with the same process and suppressed payload:

```bash
/usr/bin/time -p python3 scripts/dead_code.py suppressions --check > /dev/null
/usr/bin/time -p python3 scripts/dead_code.py baseline --check > /dev/null
```

Record `real` time and nonzero exits; run each at least once before and once after
the change under the same commit state. The design claims only budget compliance,
not a statistically significant optimisation. Persistent output has a hard
zero-byte budget because validation needs no new report file. Existing bounded
temporary analyser output is unchanged and not misreported as durable space.

## 11. The fail-closed posture

Triage and guard ownership belongs to
`plugins/hexaemeron/skills/elenchus/SKILL.md`. The command establishes success
only after clean-tree binding, complete report construction, committed regular-file
read, and full suppression parsing all finish. Any exception, timeout, signal,
missing file, malformed byte, invalid entry, unusable analyser state, repository
replacement, or check-runner failure returns nonzero and establishes no checkout
validation result. There is no partial durable result to consume.

Every repaired failure follows the parent-red/fixed-green convention: reproduce
the defect against the signed parent or a faithful temporary repository, add the
smallest guard that fails for the same causal reason, apply the fix, then run the
focused guard and full affected scope. Required hostile guards cover missing,
directory/symlink, malformed and duplicate-key files; broad, duplicate, unsorted,
stale, mismatched, and unused entries; exact non-empty and empty success;
dirty-tree and repository-substitution refusal; incomplete analyser state;
check-map selection; and preservation of baseline source-commit semantics.

## 12. Decisions and their homes

Decision-home ownership belongs to
`plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- **A dedicated checkout validator, selected through the check map.** This public
  CLI and repository-check ownership would be expensive to reverse after CI and
  operator documentation depend on it. Record it as one unnumbered ADR under
  `docs/decisions/` on the step branch, allocate the next free number against
  current `origin/main` during integration, and cite ADR-045, ADR-053, and
  ADR-059 rather than restating them. The record's slug should state the decision,
  such as `check-current-dead-code-suppressions-separately.md`.
- **Suppression validity remains exact, current, and report-only.** This is not a
  new decision: ADR-053 plus the existing schema/parser own it. The new ADR points
  there and documents only the new command/check placement.
- **Fixed analyser membership and identity.** No change is authorised, so
  `BASELINE_ANALYSERS`, the existing schema, tests, and operator guide remain its
  homes. A later change would need a separate study and record.
- **Operator procedure and recovery.** Durable commands and refusal recovery live
  in `docs/promise-machine/dead-code-v1.md`; workflow selection lives in
  `tests/check-map-v1.json`; executable interface and hostile cases live in
  `tests/test_dead_code.py`. The run study and design evidence are inputs to the
  build, not substitutes for those standing homes.
