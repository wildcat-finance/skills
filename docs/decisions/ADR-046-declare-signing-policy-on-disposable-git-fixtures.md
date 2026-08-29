# ADR-046: Declare the signing policy on disposable Git fixtures

## Status

Accepted, 2026-08-28. This record fixes the rule selected for issue
[#621](https://github.com/wildcat-finance/skills/issues/621).

The number is 046 rather than 045. ADR-045 was free when the study named it and
went to `docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`,
issue [#622](https://github.com/wildcat-finance/skills/issues/622)'s decision,
which reached `origin/main` while this delivery was building. A reader who finds
the rule described at 046 and the study still naming 045 has found a base that
moved under a run, not a missing record.

This record supersedes `plugins/horos/docs/marker-self-exclusion/runbook.md` on
the subject of fixture signing. That document is not edited. It recorded a true
condition of one host at its own ref, and the workaround it made mandatory is
retired below rather than corrected in place.

## Context

Tests across four suites build throwaway Git repositories and commit into them.
At `f5d94a5f`, ten such sites in seven files declared no signing policy, so each
inherited the contributor's global `commit.gpgsign`. Fixture history is not
evidence about signatures. It exists so a scanner, a checker or a controller has
a tree to read, and letting a contributor's signing configuration decide whether
that tree can be built makes a test's result depend on a setting the test has no
opinion about.

The fault takes two forms and the contributor's signing format picks which one
they see. On GPG the fixture commit invokes `gpg` and pinentry, and a
non-interactive run waits for a prompt nobody answers. That is the form issue
#621 recorded at revision `e4d1f5677fa1`: 188.38 seconds for the root suite with
three fixture commits failing after pinentry waits, against 6.91 seconds for the
same 118 tests under a measurement-only override.

On SSH there is no pinentry and no stall. The commit succeeds and is signed with
the contributor's real key. Measured on the delivery host at the run head, over
three samples of twenty commits each: 21.3, 21.6 and 21.3 ms per commit signed,
against 16.6, 16.9 and 16.8 unsigned. Within-arm spread is at most 0.3 ms and the
improvement is 4.6 ms. The quiet form costs about five milliseconds per fixture
commit and attaches a real personal signature to history that is deleted when the
test ends.

Two sites already carried the rule at `f5d94a5f`, and
`plugins/hexaemeron/skills/kronos/scripts/kronos.py:574` already passes
`-c commit.gpgsign=false` when the Kronos scoreboard commits into its own durable
worktree. The mechanism was applied in three places and missing from ten.

## Decision

Every disposable repository declares its own signing policy. Immediately after
`git init`, `git clone` or `git worktree add` brings the repository into
existence, and before anything commits into it, run
`git config --local commit.gpgsign false` against that repository. The scope flag
is written rather than inferred, even though `git config` already defaults to the
local file inside a repository.

A test whose assertions are about signatures is excluded and keeps its existing
matrices untouched. The exclusion is scoped to the class, not to the file,
because one file holds both kinds: `plugins/hexaemeron/tests/test_issue_429_recovery.py`
asserts a `gpgsig` header and runs `git verify-commit` against the real
repository, and in `plugins/hexaemeron/tests/test_hexctl.py` the signature
classes are `TestCommitVerification`, `GitHubSignerDiagnosis` and
`RewrittenStackRefusal`, while the same file also creates fixtures that fall
under the rule. A repository that is created but never committed into needs no
declaration.

Two inheritance facts decide where the declaration goes, and both were measured
during this delivery rather than reasoned about. A clone inherits no local
configuration from its source, so it is its own construction site and needs its
own declaration. A linked worktree shares the config file of the repository it
was added from, reads `commit.gpgsign=false` there, commits at exit code 0 and
leaves the sentinel empty, so it needs no second declaration.

The policy is repository-local, which is the property that keeps the signature
suites working. A test that wants signing on for its own purpose can still set
it, because repository-local config is the layer a test can override.

A guard for this rule supplies its hostile configuration as a file through
`GIT_CONFIG_GLOBAL`, with `GIT_CONFIG_SYSTEM=/dev/null` beside it, and drops
`GIT_CONFIG_COUNT` and `GIT_CONFIG_PARAMETERS` from the environment it hands a
fixture. Both of those carry `git -c` precedence, which outranks repository-local
config, so a correct fix reports as broken under either. Measured against git
2.54.0 with a signer that appends to a sentinel and exits non-zero:

| hostile config supplied via | fixture declares local `gpgsign=false` | commit rc | signer invocations |
| --- | --- | --- | --- |
| `GIT_CONFIG_COUNT` / `KEY_n` / `VALUE_n` | yes | 128 | 1 |
| `GIT_CONFIG_PARAMETERS` | yes | 128 | 1 |
| `GIT_CONFIG_GLOBAL` file | no | 128 | 1 |
| `GIT_CONFIG_GLOBAL` file | yes | 0 | 0 |

`GIT_CONFIG_PARAMETERS` needs the explicit mention because nobody types it. Git
converts its own `-c` into that variable and hands it to every process it spawns:
a pre-commit hook run under `git -c some.key=somevalue` sees
`GIT_CONFIG_PARAMETERS` set while `GIT_CONFIG_COUNT` is unset. An inherited value
carrying `commit.gpgsign=false` would force every fixture unsigned however it was
built, and a guard would pass with no construction site having declared anything.

`%G?` answers whether a signature verifies, not whether one is present. Under a
configuration that names no `gpg.ssh.allowedSignersFile`, git cannot verify an
SSH signature and answers `N`, the same letter a genuinely unsigned commit gets;
a commit carrying a `gpgsig -----BEGIN SSH SIGNATURE-----` header reads `N`
there. A check that wants to know whether a fixture commit was signed reads the
object's `gpgsig` header. A check that wants to know whether a signature is good
reads `%G?` and must supply a verifier.

The `<sign-off>` prefix is retired. Issue #377's runbook made
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`
mandatory on every suite command it listed, and the round record repeats it
through its demo transcript. Once the rule above holds, no suite command needs
it. Later runbooks do not carry it forward, because the precedence that makes it
work as a workaround is the same precedence that makes it unsafe as a permanent
mechanism.

## Alternatives

One shared cross-plugin helper exporting `init_disposable(path)` that every suite
imports. This would give a single edit point, but it creates an import edge from
`plugins/hermes/skills/hermes/scripts/` and `plugins/horos/tests/` to a root
module. Each plugin is packaged and distributed on its own and `test_hermes.py`
ships inside the Hermes skill directory, so a root import would break plugin
independence, which pull request #732 moved the repository away from. Rejected.

Teach each module's existing `git()` wrapper to notice an `init` argument and
chain a second call. This hides behaviour inside a generic pass-through, where a
reader of `git(root, "init", "-q")` sees nothing of the rule, and three of the
six chokepoints have no such wrapper, so coverage would be partial anyway.
Rejected. Its useful half survives: where a chokepoint is a helper, the
declaration goes in the helper.

A process-wide or runner-wide override, either `GIT_CONFIG_*` in the environment
or `git -c commit.gpgsign=false` wrapped around every suite command. This is what
the repository did as a manual workaround, and the measurement above is the
reason for refusing to promote it: the override sits at `git -c` precedence,
above repository-local config, so no test can opt back into signing for its own
purpose. A signature-verification fixture that deliberately wants signing on
would be silently defeated and the failure would read as a signing bug rather
than a configuration one. It also protects nothing the moment somebody runs a
single test without the prefix. Rejected.

## Consequences

A fixture commit costs the same for a contributor who signs with GPG, signs with
SSH, or does not sign at all, and throwaway history stops carrying a personal
signature. On a GPG host this turns three failing tests into passing ones; on an
SSH host it returns about 4.6 ms per fixture commit, which is inside noise at
suite scale and is not a suite-level speedup claim.

Ten sites became ten edit points, one per chokepoint across seven files, and a
single point of control is what the choice trades away. An eleventh construction
site added later can forget the declaration. Part of that cost is paid by
`tests/test_disposable_fixture_signing.py`, which runs one representative test
from each of the four suites under the hostile configuration and fails when that
representative's fixture reaches the signer. The cover is partial by design and
the extent was measured: removing the declaration from five of the ten sites
fails the guard, and removing it from the other five does not, because no
registered representative exercises them. A new site is caught when a
representative's path reaches it and by review otherwise.

The rule governs every future test that creates a repository, and getting the
scope wrong is expensive in both directions: too narrow and the fault returns at
the next new fixture, too wide and a signature test is defeated without saying
so. Widening or narrowing it means re-editing every construction site, which is
why the boundary is written here rather than inferred from the call sites.

The individual line at each site and the `--local` hardening at the two sites
that already declared the policy earn no record of their own. Both follow from
this one, and a record per site would be noise.
