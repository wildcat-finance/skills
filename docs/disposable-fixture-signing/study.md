# Study: isolate disposable fixture signing

Task issue: [wildcat-finance/skills#621](https://github.com/wildcat-finance/skills/issues/621),
"framework-19: disposable Git fixtures inherit contributor signing and stall on
pinentry". Base ref `main` at `f5d94a5f27168e6c0faecd43eee426f6ee892cdc`.

Assuming, unless corrected:

1. The interpreter is the exact patch in `.python-version`, 3.14.6, which
   `pyproject.toml` pins as `==3.14.*`. On the operator machine bare `python3`
   is 3.12.13 and the pinned interpreter is `/Users/kethcode/.local/bin/python3.14`.
2. Git 2.54.0, the version on the operator machine. Config precedence and the
   `GIT_CONFIG_GLOBAL` variable behave as measured in section 2.
3. Stdlib `unittest`, no pytest. Every affected suite is discovered or run by
   the commands AGENTS.md lists under "Suites".
4. This run ships no Solidity, so the vendored security suite is waived and
   recorded as waived. The waiver does not excuse the mechanical lints.
5. The rule is applied to test fixtures only. No product code, contributor
   configuration, key, or Fiat signing policy is touched.

## 1. Problem statement

Tests across four suites build throwaway Git repositories and commit into them.
None of those repositories declares a signing policy, so each inherits the
contributor's global `commit.gpgsign`. The fixture history is not evidence about
signatures; it exists so a scanner, a checker or a controller has a tree to read.
Letting the contributor's signing configuration decide whether that tree can be
built makes a test's result depend on a setting the test has no opinion about.

The fault has two forms, and which one a contributor sees depends on the signing
format they use.

On a contributor signing with GPG, the fixture commit invokes `gpg` and pinentry.
A non-interactive run waits for a prompt nobody answers and fails before reaching
the assertion. That is the form issue #621 recorded, measured at revision
`e4d1f5677fa1`: the root suite took 188.38 seconds with three fixture commits
failing after pinentry waits, against 6.91 seconds for the same 118 tests under a
measurement-only override.

On a contributor signing with SSH, there is no pinentry and no stall. The commit
succeeds in about 20 milliseconds and is signed with the contributor's real key.
That is the form on the machine this run executes on, and it is measured in
section 2 rather than assumed. It is quieter and no less wrong: throwaway history
in a temporary directory carries a real personal signature, and every fixture
commit reaches for a key it has no reason to touch.

**Who this is for.** A contributor running the suites locally, and any agent
running them unattended. Today both must remember a per-invocation override; the
repository's own #377 runbook makes that override mandatory on every suite command
it lists.

**What a working prototype means here.** Every disposable repository declares
`commit.gpgsign=false` in its own local config before its first commit, so the
result of a fixture commit is the same for a contributor who signs with GPG, signs
with SSH, or does not sign at all. Repositories whose subject is signature
verification keep their existing matrices untouched.

**The demo path that proves it.** With a hostile global configuration supplied as
a file, containing `commit.gpgsign=true` and a signing program that appends to a
sentinel and exits non-zero:

```bash
GIT_CONFIG_GLOBAL=<hostile> GIT_CONFIG_SYSTEM=/dev/null \
  python3 -m unittest discover -s tests
GIT_CONFIG_GLOBAL=<hostile> GIT_CONFIG_SYSTEM=/dev/null \
  python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
GIT_CONFIG_GLOBAL=<hostile> GIT_CONFIG_SYSTEM=/dev/null \
  python3 plugins/hexaemeron/tests/run_tests.py
GIT_CONFIG_GLOBAL=<hostile> GIT_CONFIG_SYSTEM=/dev/null \
  python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
```

All four exit 0 and the sentinel file stays empty. Before the change, the first
three fail. That pairing is the success criterion: an exit code and an empty file,
both checkable without judgement.

## 2. Prior art

### The same fix, built once already and left unmerged

An earlier combined run for issue #622 produced commit
`b1ce1c013a296196c267cd42cd1fa2403bdacab4`, carried by open PR #627 with a
zero-finding audit in open PR #626. Neither is merged; both remain open against a
run branch, and that branch is three days stale against a main that has moved
roughly seventy merged pull requests since. This run rebuilds on current main
rather than reviving it.

That commit is worth reading for two things it got right and one it got wrong.

Its **mechanism** is `git config --local commit.gpgsign false` against the fixture
repository, immediately after `git init`. Judged on the merits below, that
mechanism is correct and this study adopts it.

Its **scope rule** is: a newly created disposable repository that commits
non-signature fixture history is in scope; a repository that never commits is not;
a test whose subject is signing or signature verification is excluded unless its
matrix explicitly requires a neutral control. Re-derived against today's tree in
section 3, that rule holds and is adopted.

Its **inventory** no longer matches the tree, in both directions. It patched
`plugins/hexaemeron/tests/test_hexctl.py:1366` and `:1388`, which do not need the
change: both re-initialise a repository that `HexctlCase.setUp` already built
through `make_origin_checkout`, and that helper has carried
`["config", "commit.gpgsign", "false"]` at line 55 since before this run began. A
re-init preserves local config, so those two edits were redundant. It also patched
two `test_kronos_scoreboard.py` sites the issue never named, which is a real
finding this study keeps.

Its **rejected alternative** was a process-wide `GIT_CONFIG_*` or
`git -c commit.gpgsign=false` override around all tests, refused because a broad
override can invalidate signature tests and still leaves unmanaged fixtures to
contributor behaviour. Section 4 re-derives that refusal and agrees, and section 2
adds a measured reason the prior run did not record.

Finally, that commit bundles `docs/affected-scope-test-runner/{study,runbook}.md`
and an ADR selecting and scheduling repository checks from one graph. Those belong
to issue #622, not to #621. See the non-goals in section 3.

### What the last two merged pull requests on this subject left open

Both belong to the issue #377 run, and both are merged.

**PR #658**, "Commit the marker-self-exclusion study and runbook where the
repository keeps them", commit `8942785d`. Its study records the host condition in
`plugins/horos/docs/marker-self-exclusion/study.md:163-174`: this machine sets
`commit.gpgsign=true` globally, the test helpers drop repository-pointing
variables without neutralising signing, and every suite that commits in a
temporary repository hangs on gpg in a non-interactive session. It then defers the
real fix in as many words: "making the helpers self-sufficient is a repo-wide test
change and stays an ask-first item for the maintainer."

That deferred item is issue #621. This study carries it forward as its whole
content rather than refusing it.

**PR #663**, "Demonstrate the fixed boundary at the run head", commits `9f91455d`
and `186a7193`. It applied the deferred workaround as a standing convention: the
#377 runbook requires `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign
GIT_CONFIG_VALUE_0=false` on every suite command, written `<sign-off>` for brevity,
and the round record in `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`
repeats that prefix through its demo transcript.

Carried forward: once this change lands, that prefix stops being required. Retiring
it is a named deliverable in section 12, not a side effect.

### A measured correction to how the regression must be built

The issue's required shape says a regression "supplies a temporary global Git
config with signing enabled and a signing program that records or fails if
invoked". How that hostile configuration is supplied decides whether the
regression means anything. Measured on the operator machine, git 2.54.0, with one
failing signer that appends to a sentinel on every invocation:

| hostile config supplied via | fixture sets local `gpgsign=false` | commit rc | signer invocations |
| --- | --- | --- | --- |
| `GIT_CONFIG_COUNT` / `KEY_n` / `VALUE_n` | yes | 128 | 1 |
| `GIT_CONFIG_GLOBAL` file | no | 128 | 1 |
| `GIT_CONFIG_GLOBAL` file | yes | 0 | 0 |

The environment triple carries the same precedence as `git -c`, which outranks
repository-local config. Supplied that way, a fixture that correctly sets local
`commit.gpgsign=false` still invokes the signer and still fails. The fix is fine;
the injection is wrong, because the triple does not model what a contributor's
`~/.gitconfig` actually is. Only the middle and bottom rows describe the real
fault and the real fix.

The same precedence fact explains why the repository's existing `<sign-off>`
workaround works at all: it forces signing off from above local config. The
property that makes it a usable workaround is exactly the property that makes it
unusable as a hostile injection, and unsafe as a permanent mechanism.

### Two forms of the fault, measured here

On the operator machine `commit.gpgsign=true`, `gpg.format=ssh`, and
`user.signingkey` is an SSH public key. A disposable repository built the way the
fixtures build one produced a commit whose `%G?` is `G`, a good signature by the
contributor's key. The same repository with local `commit.gpgsign=false` produced
`%G?` of `N`. Per-commit cost over three samples of twenty commits each: 25.6,
25.5 and 25.5 milliseconds signed, against 20.3, 20.5 and 20.1 unsigned.

So on this host the defect does not stall. It attaches a real signing identity to
throwaway history and spends about five milliseconds per fixture commit doing it.
Section 10 takes that seriously rather than promising a stall this environment
cannot produce.

### The in-repository exemplar

`plugins/hexaemeron/skills/kronos/scripts/kronos.py:574` already passes
`-c commit.gpgsign=false` when the Kronos scoreboard commits into its own durable
worktree, and `plugins/hexaemeron/tests/test_hexctl.py:55` and
`plugins/hexaemeron/tests/test_fiat_skill.py:1458` already set the config on their
fixtures. The rule is not new to the repository; it is applied in three places and
missing from ten.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 from the target root, with `committed=match` on every pair. A verified
synopsis is therefore the normal reading view for the sources below.

| In-scope source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`, budget pass |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`, budget pass |
| `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md` | the source directly | its synopsis flattens the demo transcript to one line; the `<sign-off>` prefix convention this study retires is legible only in the source |

No finding in either synopsis concerns disposable fixture signing. The #377 round
record is the only audit source that touches the subject, and what it carries is
the workaround, not a finding: its step-4 demo transcript runs every suite command
under the `GIT_CONFIG` prefix and records the counts obtained that way.

`plugins/horos` and `plugins/hermes` have no `audit/AUDIT.md`. Both suites are
in scope for the fix and neither has an audit record to carry forward; that is an
absence in the tree, not an unread source.

No finding id, `Covered`, `Not checked`, `Elenchus verdict` or `Leads not pursued`
entry from any source above is dropped by this study. The root synopsis carries
`[missing legacy field: ...]` markers on pre-schema rounds; those remain unknown
and are not reconstructed here.

### Outside this repository

`git-config(1)` for the `commit.gpgsign`, `gpg.format`, `gpg.program` and
`gpg.ssh.program` keys and for the four configuration scopes; `git(1)` for
`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and the `GIT_CONFIG_COUNT` triple. No
third-party package is added or needed.

## 2b. Current-tree inventory

Built by reading the tree at `f5d94a5f`, not from the issue's list. The issue was
filed against revision `e4d1f5677fa1` and its line numbers have all moved; one of
its seven named paths is already handled and two files it never named are in scope.

**In scope: creates a disposable repository, commits into it, declares no signing
policy.** Ten sites in six files.

| # | Site | Construction | First commit |
| --- | --- | --- | --- |
| 1 | `tests/test_boundary_currency.py:166` | `GuardMutationTests.setUp` | `:170` |
| 2 | `plugins/hermes/skills/hermes/scripts/test_hermes.py:173` | `HarnessFixture.setUp` | `:177` |
| 3 | `plugins/hexaemeron/tests/test_elenchus_checker.py:114` | `Fixture.__init__` | `Fixture.commit`, `:133` |
| 4 | `plugins/hexaemeron/tests/test_kronos_scoreboard.py:664` | `DurableHomeTest.make_scope` | `:668` |
| 5 | `plugins/hexaemeron/tests/test_kronos_scoreboard.py:759` | `clone` in `test_extra_blobs_in_the_state_ref_are_ignored` | `:764` |
| 6 | `plugins/horos/tests/test_scoped_entry.py:64` | `ScopedEntryTests.setUp` | `:73` |
| 7 | `plugins/horos/tests/test_demonstration.py:53` | `DemonstrationTests.setUp` | `:55` |
| 8 | `plugins/horos/tests/test_universe.py:56` | `UniverseTests.setUp` | `:61` |
| 9 | `plugins/horos/tests/test_universe.py:134` | `BindingDirectoryTests.setUp` | `:144`, in test bodies |
| 10 | `plugins/horos/tests/test_universe.py:195` | `CandidateBindingTests.setUp` | `:199` |

Site 5 is a `git clone`, not a `git init`. The rule is therefore stated as
"immediately after the disposable repository comes into existence", whichever verb
created it.

**Already carries the rule.** `plugins/hexaemeron/tests/test_hexctl.py:55` in
`make_origin_checkout`, and `plugins/hexaemeron/tests/test_fiat_skill.py:1458`.
Both write `["config", "commit.gpgsign", "false"]` without an explicit scope flag.
`git config` writes to the repository-local file by default when run inside a
repository, so both are correct today; both are candidates for the `--local`
hardening in section 4, and neither is a defect.

**Covered by inheritance, no change needed.** `test_hexctl.py:1366` and `:1388`
re-initialise the repository `make_origin_checkout` already configured. Verified
by reading `HexctlCase.setUp:134` and `OriginCheckoutMixin.target:82-84`. The prior
run patched both; this run does not.

**Out of scope: creates a repository but never commits into it.**
`tests/test_boundary_currency.py:140` (index-isolation test, `add` only),
`plugins/horos/tests/test_scoped_entry.py:140` (symlink refusal),
`plugins/hexaemeron/tests/test_hexctl.py:5218` (worktree-path validator) and
`:5468` (worktree add), and the three bare repositories at
`test_kronos_scoreboard.py:642`, `:834` and `:910`, which receive pushes and take
no local commit. `plugins/horos/tests/test_universe.py:247` adds a linked worktree,
which shares the fixture repository's config file, so site 8's entry covers it.

**Excluded: the subject is signing.** `plugins/hexaemeron/tests/test_issue_429_recovery.py`
asserts a `gpgsig` header and runs `git verify-commit` against the real repository,
and deliberately builds an unsigned commit with `-c commit.gpgsign=false` at
`:490-491` to assert the refusal message. Its signed, unsigned and refusal legs
stay exactly as they are. In `plugins/hexaemeron/tests/test_hexctl.py`, the
signature classes are `TestCommitVerification`, `GitHubSignerDiagnosis`,
`RewrittenStackRefusal` and the fake-git `verify-commit` handler at `:448-459`;
they drive a fake git and build no repository. The exclusion is class-scoped, not
file-scoped, because the same file also holds in-scope construction sites.

**No shared helper exists.** There is no `conftest.py` in the tree and no shared
git helper module. The three horos modules each carry a byte-identical
`def git(root, *args)`; the root suite has a richer `git`/`git_env` pair at
`tests/test_boundary_currency.py:76-101`; Kronos and the Elenchus checker have
per-class methods; Hermes has six inline `subprocess.run` calls and no helper at
all. Ten sites reduce to six edit points, one per chokepoint.

## 3. Constraints and non-goals

**Starting ref.** `main` at `f5d94a5f27168e6c0faecd43eee426f6ee892cdc`.

**Toolchain.** Python 3.14.6, the exact patch in `.python-version`, resolved on
the operator machine as `/Users/kethcode/.local/bin/python3.14`; bare `python3`
there is 3.12.13 and must not be substituted. Git 2.54.0. The Hexaemeron suite
needs Node 26 on this host: host `node` is v22.22.3 and
`plugins/hexaemeron/tests/test_elenchus_checker.py` runs `node --version` and a
`node:test` emitter, so that suite runs inside
`npx --yes --package=node@26.6.0 --call '...'`.

**Runner commands, verified against AGENTS.md lines 178, 183, 184 and 186 at this
ref.** All four the prior run named are real and current:

```bash
python3 -m unittest discover -s tests
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
```

`.github/workflows/repo.yml:46` runs the first of those in CI. No workflow runs the
Hermes, Hexaemeron or Horos suites, so those three are contributor-local today.

**The hostile configuration must be supplied as a file through
`GIT_CONFIG_GLOBAL`,** with `GIT_CONFIG_SYSTEM=/dev/null` alongside it. It must not
be supplied through the `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` /
`GIT_CONFIG_VALUE_n` triple. The measurement in section 2 shows the triple
outranks repository-local config, so a regression built on it reports a correct fix
as broken. This constraint is written here so that the runbook cannot get it wrong
and a later reader does not simplify it back to the triple.

**Ruled out by the user and by the issue's own boundary.** No signing gate anywhere
is weakened. Contributor and Fiat signing policy is untouched. The repository's own
commits keep their signing requirements. No test writes to global Git config, to
the checked-out repository's local config, or to any contributor key. No preferred
contributor identity is selected and no local key becomes a marketplace default.

**Non-goals.**

- The affected-scope test runner is issue #622's subject and is out of scope here.
  The prior commit bundled `docs/affected-scope-test-runner/{study,runbook}.md` and
  an ADR selecting and scheduling repository checks from one graph; none of that is
  rebuilt by this run. The boundary is: #621 changes what a disposable repository
  declares about signing, and nothing about which tests get selected or scheduled.
- Deduplicating the three byte-identical horos `git()` helpers into one module is a
  refactor with its own risk, and PR #732 moved the repository toward keeping
  plugin suites detached rather than coupled. The rule is applied at each helper.
- Issue #547, making the real-repository commit gate survive clones, stays separate.
- No new dependency. No CI workflow is added for the three uncovered suites.

**Boundaries for the build.**

- **Always.** The four suite commands above before a commit, under the pinned
  interpreter. The imprimatur and brevitas lints on every shipped document. The
  phylax, ephoros and hypomnema tree lints. A recorded before and after for any
  timing claim.
- **Ask first.** Adding a repository-level test runner surface (see the open
  question in section 12). Changing any assertion or count in a
  signature-verification test. Touching CI. Editing `AGENTS.md`.
- **Never.** Commit key material. Disable signing for product commits. Delete or
  skip a failing test to make a suite pass. Supply the hostile configuration
  through the `GIT_CONFIG_*` triple. Claim a suite ran when it did not.

## 4. Design options

**Option A: declare the policy on each disposable repository, at creation.**
Immediately after `git init` or `git clone` brings the repository into existence,
run `git config --local commit.gpgsign false` against it. Applied at the six
chokepoints identified in section 2b, which covers all ten sites.

The trade: the rule is written at six chokepoints, and a construction site added
later can forget it. Closed by the guard in section 11 rather than by discipline.

**Option B: one shared cross-plugin helper.** A module exporting
`init_disposable(path)` that every suite imports.

The trade: it creates an import edge from `plugins/hermes/skills/hermes/scripts/`
and `plugins/horos/tests/` to a root module. Each plugin is packaged and
distributed on its own, and `test_hermes.py` ships inside the Hermes skill
directory, so a root import would break plugin independence. PR #732 moved the
repository the other way. Rejected.

**Option C: teach each module's existing `git()` wrapper to notice.** The wrapper
detects an `init` argument and chains a second call.

The trade: behaviour hidden inside a generic pass-through, where a reader of the
call site sees `git(root, "init", "-q")` and nothing else. Three of the six
chokepoints have no such wrapper, so coverage is partial anyway. Rejected, though
its useful half survives in Option A: where a chokepoint is a helper, the line goes
in the helper.

**Option D: a process-wide or runner-wide override.** `GIT_CONFIG_*` in the
environment, or `git -c commit.gpgsign=false` wrapped around every suite.

This is what the repository does today as a manual workaround, and the trade is
measured rather than argued. The override sits at `git -c` precedence, above
repository-local config, so no test can opt back into signing for its own purpose.
A signature-verification fixture that deliberately wants signing on would be
silently defeated, and the failure would look like a signing bug rather than a
configuration one. It also protects nothing the moment somebody runs a single test
without the prefix, which is the common case. Rejected, and this run additionally
retires the existing workaround rather than promoting it.

**Chosen: Option A.**

It is the cheapest to comprehend: the declaration sits next to the `git init` it
protects, so a reader sees the whole rule in one place, with no import graph, no
wrapper magic and no environment precedence to reason about. It is the only option
that leaves a signature-verification test free to set its own policy, because
repository-local config is the layer tests can still override. It matches the
mechanism already used at three places in this repository, so it adds no new idea.

What it trades away: a single point of control. Ten sites become six edit points
and any eleventh site is a future omission. That is a real cost and section 11
pays it with an enumerating behavioural guard rather than accepting it.

**Hardening carried with the choice.** The two sites that already declare the
policy write `["config", "commit.gpgsign", "false"]` with no scope flag. That is
correct today because `git config` defaults to the local file inside a repository.
Both become `--local` so the scope is stated rather than inferred, and both move to
immediately after creation so the ordering rule is uniform across all twelve sites.

## 5. Risk register seed

The concern this register exists for is not that the one-line change is hard. It is
that a regression which looks green can be green for the wrong reason: a hostile
configuration that is not hostile, a signer that is never reached because the test
never commits, or an injection whose precedence hides the very thing it claims to
prove. Ids below are cited by round records.

```risk-register
injection-precedence | how the regression supplies the hostile global config | a GIT_CONFIG_GLOBAL file is used and the GIT_CONFIG_COUNT triple is absent from the regression
vacuous-regression | the hostile-config harness | a negative control commits without the local policy and is observed to fail and to invoke the signer
config-scope-escape | the cwd or -C target of each git config call | every call names its fixture repository explicitly and cannot fall through to the outer checkout
contributor-config-mutation | the contributor's global config, keyring, and the checked-out repository's local config | no test writes outside its own temporary directory, checked before and after the suite
signature-test-weakening | test_issue_429_recovery.py and the signing classes of test_hexctl.py | their assertions and case counts are unchanged, and the unsigned and invalid-signature legs still fail when the code under test stops refusing
format-coverage | the gpg.format the hostile signer declares | the regression covers openpgp via gpg.program and ssh via gpg.ssh.program, plus an unsigned control
missed-construction-site | a disposable repository added after this change | the guard fails when a covered suite commits under the hostile configuration, so a new unguarded site is caught by the suite rather than by a contributor
clone-and-worktree-paths | repositories created by clone or worktree add rather than init | the rule is applied at creation whichever verb created it, and a linked worktree is shown to share the config it inherits
skip-instead-of-fail | the regression's own preconditions | it fails rather than skips when git is unavailable or the hostile config cannot be written, because a silent skip reads as a pass
sentinel-leak | the sentinel file and signer script the hostile harness writes | both live inside the test's own temporary directory and are removed with it
subprocess-argv | the argv of the git and suite calls the regression adds | fixed argv, no shell, and a phylax pragma with a reason where the linter asks
measurement-honesty | the recorded before and after in section 10 | the record names the host and signing configuration the samples came from, and reports a delta inside variance as inside variance
```

## 6. Glossary seeds

- **Disposable repository.** A Git repository a test creates in a temporary
  directory, commits fixture history into, and deletes when the test ends.
- **Fixture history.** Commits made only so something has a tree to read. Their
  signatures are never the subject of an assertion.
- **Construction site.** The exact line where a disposable repository comes into
  existence, by `git init`, `git clone` or `git worktree add`.
- **Chokepoint.** A helper or setup method through which several construction sites
  pass, so one edit covers all of them.
- **Hostile configuration.** A temporary global Git config with signing on and a
  signing program that records every invocation and exits non-zero.
- **Sentinel.** The file the hostile signing program appends to. Empty means the
  signer was never reached.
- **Negative control.** A commit deliberately made without the local policy, to
  show the hostile configuration is genuinely hostile.
- **Signature-subject test.** A test whose assertions are about signatures. Excluded
  from the rule.
- **The `<sign-off>` prefix.** The `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign
  GIT_CONFIG_VALUE_0=false` workaround the #377 runbook requires on every suite
  command. Retired by this change.

## 7. Sources

- Issue #621, `gh issue view 621 --repo wildcat-finance/skills`. Original filing is
  the specification; the `wave-atlas-review` block is routing guidance.
- Commit `b1ce1c013a296196c267cd42cd1fa2403bdacab4`, the prior run's implementation.
  Open PRs #627 and #626 carry it and its audit.
- `plugins/horos/docs/marker-self-exclusion/study.md:163-174` and
  `plugins/horos/docs/marker-self-exclusion/runbook.md:9-14`, the recorded host
  condition and the deferral that became this issue. Merged as PR #658.
- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`, the demo
  transcript carrying the `<sign-off>` prefix. Merged as PR #663.
- `AGENTS.md:169-194`, the interpreter rule and the suite commands.
- `.github/workflows/repo.yml:46`, the one suite CI runs.
- `plugins/hexaemeron/skills/kronos/scripts/kronos.py:574`, the in-repository
  exemplar.
- `plugins/hexaemeron/skills/elenchus/SKILL.md:284-300`, the runner contract and the
  three accepted report formats.
- `plugins/hexaemeron/tests/run_tests.py:26,118`, the `elenchus.unittest.v1` emitter.
- `git-config(1)` and `git(1)` for scope precedence and the `GIT_CONFIG_*` variables.
- Measurements in section 2 were taken on this host on 2026-08-28 at base
  `f5d94a5f`; the commands are reproduced in section 10.

## 8. Signals, and the questions behind them

This is a test-fixture change, not an unattended service, so there is no metrics or
tracing surface and none is added. There is still an on-call reader: the
contributor or agent staring at a red suite at three in the morning. The
observable surface is exit codes and assertion messages, and the questions worth
answering with them are these.

1. **"Did my suite fail because of my change, or because of my signing setup?"**
   Today that question is unanswerable from the output: a pinentry stall looks like
   a hang and a signer failure looks like a git error. The guard added in section 11
   answers it directly, because it is the only test that fails when the cause is
   signing, and its failure message names `commit.gpgsign` and the sentinel path.

2. **"Was the signer actually reached?"** The sentinel file is the answer, and it is
   a file rather than a log line so it survives the process. The guard reports its
   contents on failure rather than only its emptiness, so the reader sees which
   invocation happened, not merely that one did.

3. **"Is this test green for the right reason?"** The negative control answers it.
   Its assertion message states that the hostile configuration failed to be hostile,
   which is a different sentence from the fix being broken and points at a different
   repair.

4. **"Did a fixture commit get signed with my key?"** Answered by `%G?` on the
   fixture head, which the guard asserts is `N` rather than only asserting the
   commit succeeded. A commit that succeeds and is signed still fails the rule.

Which steps emit these: the step that adds the guard emits all four; the steps that
apply the rule extend the enumeration the first question relies on. No other step
emits a signal, because no other step changes behaviour anyone observes at runtime.

`plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a signal must carry.

## 9. Boundaries, per capability

Three boundaries open here, all inside the test process, and all opened by the
regression rather than by the fix.

**Writing and executing a signing program.** The hostile harness writes an
executable script to disk and git executes it. What is worth taking: the ability to
observe whether signing was attempted, which no assertion on the commit alone can
establish. The control: the script is written into the test's own temporary
directory with a fixed body containing no interpolated caller input, it is invoked
only by git through a config value the test wrote, and the directory is removed on
teardown. It is never placed on `PATH`.

**Supplying a global configuration through the environment.** `GIT_CONFIG_GLOBAL`
and `GIT_CONFIG_SYSTEM` redirect git away from the contributor's real files. What is
worth taking: it is the only way to model an inherited configuration without
touching the contributor's own. The control: both variables are set on the child
process only, never on `os.environ` of the test process, so a failure mid-test
cannot leave the contributor's git pointed at a temporary file. The paths are
absolute and inside the test's temporary directory.

**Spawning suites as subprocesses.** The guard runs representative tests from other
suites under the hostile configuration. What is worth taking: it proves the rule
behaviourally without importing across plugin boundaries. The control: fixed argv
built from repository-relative paths, no shell, a bounded timeout so a
reintroduced pinentry stall fails the guard instead of hanging it, and the
interpreter taken from `sys.executable` rather than resolved from `PATH`.

Nothing here reads untrusted input, holds secret material, opens a network
connection, or adds a dependency. The one filesystem write outside a temporary
directory would be a scope escape, and `config-scope-escape` in section 5 is the
register entry for it.

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls.

## 10. The budget, or its absence

There is a budget, and acceptance item 4 requires it: three same-command before and
after samples recording wall time and spread, with the improvement exceeding the
measured variance. It needs care, because the honest answer depends on which
machine asks.

On a GPG contributor the before does not finish at all, so a wall-clock comparison
is not measuring a speedup, it is measuring the difference between failing and
working. The issue's 188.38 seconds against 6.91 is that difference, recorded at
revision `e4d1f5677fa1` on a machine this run does not have. This study does not
re-claim those figures.

On this host, signing with SSH, there is no stall to remove. Section 2 measured the
whole effect: about 5.2 milliseconds per fixture commit. Across the handful of
fixture commits in a suite that is tens of milliseconds against suite times measured
in seconds and minutes, which is inside noise. Promising a suite-level speedup here
would be a claim the environment cannot support.

So the budget is recorded at two levels, and both are measurable here.

**M1, the construction path, where the claim lives.** Twenty fixture commits in a
disposable repository, three samples per arm, signed against locally overridden:

```bash
# per arm: git init; git config user.name/user.email; optionally
# git config --local commit.gpgsign false; then twenty add-and-commit cycles,
# wall time divided by twenty.
```

Recorded at base `f5d94a5f` on 2026-08-28: 25.6, 25.5, 25.5 ms/commit signed;
20.3, 20.5, 20.1 ms/commit unsigned. Spread within an arm is at most 0.4 ms; the
improvement is 5.2 ms. The improvement exceeds the variance by more than an order
of magnitude, which is what item 4 asks for, and it is a real before and after taken
on the machine that runs this delivery.

**M2, the four suites, recorded for completeness and reported honestly.** Three
samples of each suite command before and after, under the contributor's real
configuration, with the host and its `commit.gpgsign`, `gpg.format` and
`user.signingkey` recorded beside the numbers. The expected result on this host is a
delta inside variance, and the record says so if that is what happens. A suite-level
speedup is not claimed and item 4 is not satisfied from M2.

**The correctness result that carries acceptance items 1 and 5** is not a timing
result at all: under the hostile configuration the four suite commands exit 0 and
the sentinel stays empty, where three of the four fail before the change. That is
the demo path in section 1, and it is the same on every host regardless of signing
format.

`plugins/hexaemeron/skills/metron/SKILL.md` owns what a budget carries and how it
is checked.

## 11. The fail-closed posture

**What stops the run.** Any of the four suite commands returning non-zero under the
hostile configuration. A non-empty sentinel. A fixture head whose `%G?` is anything
other than `N`. The negative control passing, which means the hostile configuration
is not hostile and every other result in the run is uninformative. Any evidence that
the contributor's global config, the checked-out repository's local config, or a key
changed during a suite run.

**What must not stop the run quietly.** A skip. The existing fixtures guard
themselves with `unittest.skipIf(GIT is None, ...)`, which is right for a suite that
cannot run without git; it is wrong for this guard, because a guard that skips when
it cannot build its hostile configuration reports as a pass and reads as evidence.
The guard fails in that case and says which precondition was missing.

**The guard convention.** One guard test that fails without the fix, named for what
it protects rather than for the issue number, living beside the tests it constrains.
Its shape, in the order the assertions run:

1. Build the hostile configuration as a `GIT_CONFIG_GLOBAL` file with signing on and
   a recording, failing signer, across three arms: `gpg.format=openpgp` with
   `gpg.program`, `gpg.format=ssh` with `gpg.ssh.program`, and an unsigned control.
2. Negative control: construct a disposable repository without the local policy and
   assert the commit fails and the sentinel records an invocation. This is what makes
   the rest of the test mean something.
3. Positive case: construct one the way the fixtures do, with the policy, and assert
   the commit succeeds, the sentinel is empty, and `%G?` is `N`.
4. Enumeration: run one representative test from each covered suite as a bounded
   subprocess under the hostile configuration, and assert exit 0 and an empty
   sentinel. This is the assertion that fails when a new construction site forgets
   the rule, and the assertion that makes each apply-the-rule step fail on its own
   parent commit.

Step 4 is what ties the guard to Elenchus's mechanical rule: a step that applies the
rule to a suite also extends the enumeration to that suite, so the changed test file
applied to the parent fails there and passes on the fix.

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order and the guard
rule.

## 12. Decisions and their homes

Three decisions here are expensive to reverse, in the sense that reversing them
later means re-editing every construction site or re-reading every round record.

**The scope rule.** Which disposable repositories get the policy, and which are
excluded because their subject is signing. This governs every future test that
creates a repository, and getting it wrong in either direction is costly: too narrow
and the fault returns, too wide and a signature test is silently defeated. Home: a
new decision record, `docs/decisions/ADR-045-declare-signing-policy-on-disposable-git-fixtures.md`.
ADR-044 is the current highest at this ref. The record carries the rule, the three
rejected options from section 4 with the measured reason for rejecting D, and the
`GIT_CONFIG_GLOBAL` constraint from section 3.

**The mechanism and its layer.** That the policy is repository-local rather than
process-wide, so a test can still opt back in. This is the property that keeps the
signature suites working, and it is not obvious from reading any single call site.
Home: the same ADR, plus a comment at the chokepoints saying why the line is there
rather than what it does. The prior run's comment at
`tests/test_boundary_currency.py` is a good model: fixture history is not signing
evidence, so inherited signing must not decide whether the repository can be built.

**Retiring the `<sign-off>` prefix.** Once the rule holds, the workaround the #377
runbook makes mandatory is no longer needed, and leaving it in place would teach
every later runbook to keep using an override that outranks local config. Home: the
study and runbook copies committed under `docs/disposable-fixture-signing/`,
following the `docs/<topic>/{study,runbook}.md` pattern that
`docs/elenchus-rpc-boundary-fixtures/` and `docs/ariadne-state-fixture-predicate/`
already use. The #377 documents are not edited: they recorded a true host condition
at their own ref, and the ADR is what supersedes them.

Not earning a record: the individual line at each of the ten sites, and the `--local`
hardening at the two that already declare the policy. Both are direct consequences
of the ADR and a record per site would be noise.

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a record
and where each one belongs.

### One question the repository could not settle

Where the guard lives changes the runbook's every `Tests` field, so it is a design
question rather than a detail, and it is asked rather than guessed.

The guard belongs in the repository-wide invariant suite, `tests/`, because the rule
is repository-wide and because `.github/workflows/repo.yml` runs that suite on every
pull request, which is the only way the rule gets enforced for contributors other
than the one who wrote it. The guard is meaningful in CI even though CI configures no
signing, because it supplies its own hostile configuration.

The cost is that the root suite has no `elenchus.unittest.v1` emitter. The four
`tests/emit_*_report.py` files are human-readable printers, not Elenchus runners, so
a step whose changed test file is in `tests/` has no `{report}` command to declare.
Adding `tests/run_tests.py`, modelled on `plugins/hexaemeron/tests/run_tests.py`,
would close that and is roughly ninety lines. It is also a new repository runner
surface, which section 3 puts under ask-first.

**The question: may this run add `tests/run_tests.py` so the guard can live in the
CI-covered root suite?** If yes, every step declares
`python3 tests/run_tests.py --elenchus-report {report}` with format
`unittest-json-v1`. If no, the guard goes to
`plugins/hexaemeron/tests/test_disposable_fixture_signing.py`, every step declares
the existing `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
and the rule is not enforced in CI. Both are buildable; the first is better and costs
one file.
