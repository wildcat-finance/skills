# Study: let `done sync-run` read a private HTTPS remote

Task: [wildcat-finance/skills#2093](https://github.com/wildcat-finance/skills/issues/2093)
(`Fiat-Required: 1`). Surveyor: `fiat-2093-study-surveyor`. Target: this
repository at `main` `87142b40decb64f1c430847838ee8b5c1ab5475f`, run branch
`fiat/2093-let-done-sync-run-read-a-private-https-remo`. Every `hexctl.py:N`
below is a line of `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at that
commit. The issue's locations were taken at
`50d71a2e8c1777f8eb26db32dd8adeadb34063bd`; each one is re-derived here.

Assuming, unless corrected:

1. The fix belongs to the one seam every native remote read already shares,
   `remote_branch_tip(..., native_relation=True)` at `hexctl.py:23421`. No
   other native-relation read reaches a remote; section 2.1 settles each site
   the issue left unchecked.
2. "Authenticate the way the caller's own Git does for that one remote" means
   the native read offers the same credential helpers, in the same order, that
   the caller's Git would offer for the origin URL, taken from the caller's own
   configuration. It does not mean running the native read in the caller's
   whole environment.
3. The repository's own configuration stays inside the boundary, as it is
   today. It names `origin`, the native read already reads it, and a local
   `url.*.insteadOf` is no stronger than editing `remote.origin.url`. Global,
   system and environment-carried Git state stays outside.
4. Adding `HOME` to the remote read alone is acceptable. With
   `GIT_CONFIG_GLOBAL` held at `/dev/null`, `HOME` cannot readmit
   `~/.gitconfig` or `~/.config/git/config` (observed, section 4.3), and a
   helper such as `gh auth git-credential` needs it to find its own store (the
   2026-10-13 workaround embedded `HOME` in the helper for that reason).
5. A loopback dumb-HTTP Git server on 127.0.0.1 that demands HTTP Basic
   authentication, with a throwaway credential generated per run, stands in for
   a private GitHub remote in tests and design evidence. Nothing contacts
   github.com, and this run does not exercise a live private repository.
6. The interpreter is the `.python-version` value, 3.14.6, with stdlib
   `unittest`. Git is the platform-default `/usr/bin/git`, 2.50.1 (Apple
   Git-155).

The study proceeds on these unless corrected. Rejecting assumption 4 removes
the `home-store` helper shape and the `gh` helper the issue was filed for.
Rejecting assumption 2 in favour of the caller's whole environment selects no
candidate here, because that readmits `PATH` and `GIT_DIR`, which the audit
history below closed on purpose.

## 1. Problem statement

`done sync-run` reads the remote run-branch tip and the remote base tip with
`git ls-remote` under `_native_relation_environment()`
([`hexctl.py:4153-4168`](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L4153-L4168)).
That environment sets `PATH` to `os.defpath`, `GIT_CONFIG_GLOBAL` and
`GIT_CONFIG_SYSTEM` to `/dev/null`, `GIT_CONFIG_NOSYSTEM=1`,
`GIT_TERMINAL_PROMPT=0`, passes `SSH_AUTH_SOCK` and nothing else, so no
`HOME`. A private repository whose `origin` is an `https://github.com/` URL and
whose credential is a global `credential.https://github.com.helper` therefore
fails both reads with `remote run branch tip could not be read`
(`hexctl.py:23434`), while the same `ls-remote` succeeds in the caller's
shell. A run whose base advanced cannot receipt its sync and so cannot
integrate. On 2026-10-13 the miskatonic MR-03 run hit this and was receipted
only after a temporary repository-local helper was added around one call.

The same seam fails in more places than the issue observed. On a run whose
runbook declares `version-relations`, `done resolve-versions`, `next` at the
integrate directive and `status` in the integrate phase each make four native
remote reads, and `done integrate` makes one post-merge base read (section
2.1).

Who it is for: an operator, or the driver agent acting for one, integrating a
Fiat run on a private repository reached over HTTPS.

A working prototype means the native remote tip read behind those commands
offers the caller's credential configuration, and only that plus `HOME`, keeps
every exclusion the environment exists for, and names an authentication
refusal as one. Local relation reads keep the unchanged environment.

Demo path. The last step runs the six conformance resolvers of the design
record against the built tree from the run worktree, plus the topical test
module, and records the output. The controller is the run tree's `hexctl.py`;
the source command is `python3 .hexaemeron/design/probe.py conform ...` (one
per criterion, listed in section 4.4). Bounded positive observations: a read
whose only credential is a global-config helper returns the served tip, and
`done sync-run` receipts against that remote in the module test. Bounded
negative observations: a moved remote tip is refused, a hostile global
`url.*.insteadOf` changes nothing and the hostile endpoint sees no request, a
missing credential is refused with an authentication message carrying no child
byte, an unreachable origin keeps the plain `could not be read` refusal, and an
oversized credential configuration refuses before the remote is contacted. The
demonstration does not claim that a live private GitHub remote was read. The
installed driver controller (hexaemeron 1.6.102, `fiat-v6.85.1`) integrates
this run against the public skills repository, which needs no credential, so
this run cannot exercise its own fix at its own integration.

Success criteria, each checked by a command:

| id | Criterion | Check |
| --- | --- | --- |
| SC-1 | Acceptance 1: `done sync-run` receipts against a remote whose only credential is a global-config helper | a test whose name contains `sync_run` in `plugins/hexaemeron/tests/test_native_remote_credentials.py`; conformance cells `sync-run-module-passes` and `seam-reads-credentialed-remote` |
| SC-2 | Acceptance 2: a remote tip that differs from the supplied sync commit still refuses with `run sync commit does not match the remote run branch tip` | the same module; the moved-tip half of `seam-reads-credentialed-remote` |
| SC-3 | Acceptance 3: a hostile `url.*.insteadOf` in the caller's global config, in `~/.gitconfig`, in `~/.config/git/config` or in inherited `GIT_CONFIG_COUNT` cannot change the answer, and the hostile endpoint receives no request | the same module; `seam-reads-credentialed-remote` |
| SC-4 | An authentication failure says so; the text carries no child byte; a non-authentication failure keeps `<label> could not be read` | `authentication-refusal-fixed` |
| SC-5 | Local relation reads keep exactly today's environment | `local-reads-stay-native` |
| SC-6 | A caller credential configuration over 64 entries or 16,384 bytes refuses by name before the remote is contacted | `projection-cap-refuses` |
| SC-7 | One native remote tip read starts at most two controller children | `remote-read-children` |
| SC-8 | Repository gates stay green at every step exit | `python3 -m unittest discover -s tests`, `python3 scripts/run_checks.py --base <step base>`, `python3 plugins/hexaemeron/tests/run_tests.py`, `python3 scripts/promise_machine.py check`, `python3 scripts/plugin_release.py --base <PR base> --head HEAD` |

## 2. Prior art

### 2.1 The code at the base

The native environment, its Git and the shared reader:

- `_native_git_executable` (`hexctl.py:4145-4150`) resolves Git only from
  `os.defpath`.
- `_native_relation_environment` (`hexctl.py:4153-4168`) is the closed
  environment above. `_native_signature_environment` (`hexctl.py:4171-4187`)
  is the one precedent for widening it: it adds `HOME` and `GNUPGHOME` and a
  fixed verifier `PATH` for signature checks only.
- `_native_relation_git` (`hexctl.py:4190-4199`) runs
  `--no-replace-objects <argv>` through `bounded_tool` with that environment.
  `bounded_probe` (`hexctl.py:22672`) merges stdout and stderr and never puts
  a child byte in a diagnosis; `bounded_tool` dies with the caller's fixed
  refusal on any non-zero exit.
- `remote_branch_tip` (`hexctl.py:23421-23454`) runs
  `ls-remote --refs origin refs/heads/<branch>` through `_native_relation_git`
  when `native_relation=True` and through the caller-environment `bounded_git`
  otherwise. Its refusal on any failure is `<label> could not be read`.

Every native remote read passes through that one function. Found by
`grep -n 'remote_branch_tip(' hexctl.py`, then reading each caller:

| Line | Function | Reached by | Reads |
| --- | --- | --- | --- |
| `hexctl.py:20668`, `:20673` | `done_sync_run` | `done sync-run` | run tip, base tip |
| `hexctl.py:5427`, `:5433`, `:5501`, `:5507` | `build_version_resolution` | `done resolve-versions` (`:20960`); `next` at the integrate directive through `active_version_resolution` (`:17813`); `status` through `version_resolution_status` (`:5581`, called at `:31663`) | base and run tips, then both reread |
| `hexctl.py:21067` | `terminal_version_resolution` | `done integrate` on a relation-bearing run | post-merge base tip |

The exact-pair replay at `hexctl.py:21058` passes `exact_base` and
`exact_head` and so skips the four reads. A literal-only run reaches only the
two `done sync-run` reads.

The issue's "Not checked" sites, re-derived at the base:

- `:5222` is now `hexctl.py:5256`, `verify_local_commit(..., native_relation=True)`
  inside `_require_resolution_sync`: a local signature check through
  `_native_signature_git`. No remote.
- `:5397-5477` are now `hexctl.py:5427-5511`, the four
  `build_version_resolution` reads above. They reach the remote and fail the
  same way.
- `:10159` is now `hexctl.py:10193`, the guard commit's `verify_local_commit`
  in `_guard_commit_evidence`. Local.
- `:18757` is now `hexctl.py:18791`, `_decision_assignment_message` reading a
  commit message with `show`. Local.
- `:18894` is now `hexctl.py:18928`, `verify_local_commit` in
  `decision_assignment_receipt`. Local.

The other users of `_native_relation_environment()` are local too: the guard
object readers at `hexctl.py:9307` and `:9314`, `ls-tree` at `:18044`, the
decision-assignment allocator environment at `:18373`, the private replay
repository's `init`, `config`, `update-ref` and `status` from `:18496` to
`:18730`, and `rev-list` at `:20222`.

The SSH route with an identity loaded, settled from source: the native
environment passes `SSH_AUTH_SOCK`; Git's default `ssh` resolves from
`PATH=os.defpath`, so `/usr/bin/ssh`; `core.sshCommand`, `GIT_SSH` and
`GIT_SSH_COMMAND` from global config or the environment are excluded, which is
correct because each can substitute the transport. An agent identity therefore
authenticates the SSH route today. Key files and `~/.ssh/config` depend on
OpenSSH resolving `~` from the account's password entry rather than `$HOME`;
that is inferred from OpenSSH's documented behaviour and was not exercised,
because the fixture has no SSH server. On this machine `ssh-add -l` reports no
identities, which matches the issue. The selected design adds `HOME` to the
remote read, so an `ssh` that did consult `$HOME` would also see the right
one, and `Permission denied (publickey` is classified as an authentication
refusal.

Remote reads that already run in the caller's environment, for contrast:
`hexctl.py:19993`, `:20102`, `:20297`, `:20461`, `:20489`, `:21136` and the
`fetch` at `:23590` go through `bounded_git`; `currency_remote_head`
(`hexctl.py:7266`) runs inside the marketplace clone with
`GIT_TERMINAL_PROMPT=0`; `github_rest` (`hexctl.py:23139`) runs the caller's
`gh` for every pull-request read. None of these changes.

Test patterns to reuse: `test_version_relations.py`
`test_sync_receipt_remote_proof_ignores_inherited_git_repository` (line 1990)
drives `done_sync_run` at function level with `verify_run`,
`_integrate_directive`, `integration_revalidation_record` and
`verify_local_commit` patched; `test_resolution_remote_reads_ignore_inherited_git_repository`
(line 562) drives `build_version_resolution` under an inherited `GIT_DIR`. The
fake delivery Git in `plugins/hexaemeron/tests/hexctl_harness.py` passes every
subcommand it does not model, `config` included, to the real Git (line 584 of
that file).

### 2.2 Merged pull requests

The last two merged pull requests that changed `hexctl.py` are
[#2119](https://github.com/wildcat-finance/skills/pull/2119) (2026-11-01,
ledger rows outside the History table) and
[#2073](https://github.com/wildcat-finance/skills/pull/2073) (2026-10-04,
checkpoint criteria replay). #2119 carries
`none | none | the controller check and both row moves are whole and leave nothing for another owner`.
#2073 has no carryover block; its body leaves "published canonical acceptance"
pending for #1378, which is unrelated to remote reads and stays with #1378.

The last two merged pull requests that changed the remote read or the native
environment are [#1775](https://github.com/wildcat-finance/skills/pull/1775)
(run #1480, carried-commit refusal, merge `921438aed`) and
[#1638](https://github.com/wildcat-finance/skills/pull/1638) (run #453,
`6021e664d` "close native Git child environments"). #1775 carried seven items
(#1765, #1715 and five `none` rows on Elenchus verdicts, ledger records, skill
text, gained-range causes, the merge-step waiting-only read and cherry-pick
detection); #1638 carried #1539 to #1542. None concerns remote-read
authentication, so this run neither answers nor reopens any of them; each
stays with its filed issue or its recorded reason.

The plain-PR precedent for a Fiat generation is #2119's commit `9a2dc661f`:
hexaemeron 1.6.101 to 1.6.102, one `fiat` generation row, `metadata.version`
in `skills/fiat/SKILL.md`, and 28 files including both `plugin.json` files,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, `tests/test_phylax_model_proxy.py`, the
agent-instruction fixture, `tests/promise_machine_coverage.json`, two runtime
fixtures, `evaluation-run.json` and the Horos files.

Adjacent and not addressed:
[#868](https://github.com/wildcat-finance/skills/issues/868) (framework-24,
the integration receipt reads a branch the documented order already deleted)
concerns the same `remote_branch_tip` but a missing ref, not a credential.

### 2.3 Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root at the base and exited 0. It checked 124 sources (6
`audit/AUDIT.md` files and 118 `audit/rounds/<run>.md` files), every one
`budget=pass` and `committed=match`, so every synopsis is a verified view.

In-scope sources were chosen mechanically: every source whose text matches
`ls-remote`, `insteadof`, `GIT_CONFIG_GLOBAL`, `credential helper`,
`remote_branch_tip`, `native remote`, `remote tip`, `sync-run` or
`_native_relation` (case-insensitive). Seventeen sources match. A second scan
for private repositories, credential helpers or authentication near a remote
read found no round that accepted, deferred or recorded the limitation this
issue names.

| Source | Read | Bearing |
| --- | --- | --- |
| `audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md` | synopsis rows for Step 3 rounds 1 to 8 by grep; source lines 1670 to 1720 and 1900 to 1915 | S3-R1-01 (medium, fixed): remote relation reads used the generic environment, so an inherited `GIT_DIR` redirected base and run observations. S3-R7-01 (high, fixed in `ec2fbd73d`): inherited `GIT_DIR` supplied run and base remote tips in sync receipt construction; fix "use native remote reads". S3-R4-01 (high): a repository-local `gpg.program` forged signatures. S3-R5-01 (high): repository-local diff config hid paths. Legacy fields are `[missing legacy field: ...]` and stay unknown |
| `audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` | source line 78 | S3-R1-01 (high, open in that round, closed by #1638): the native environment copied every non-`GIT_` variable, so loader channels reached relation Git; remedy "a closed environment containing only required locale, home and verifier inputs" |
| `audit/AUDIT.md` | source lines 6670 to 6685 and 13500 to 13535 | I320-S3-R2-01: integration binds the remote run tip read with `ls-remote`. Currency risk ids `upstream-read-surface` and `url-source-confusion` held: fixed argv, prompts off, hostile target `url.insteadOf` inert because the read runs in the marketplace clone |
| `audit/rounds/fiat-1480-refuse-a-later-step-s-commits-carried-into.md` | grep lines 7, 45, 48, 79, 81, 99 | S2-R1-01 (low): extra `ls-remote` cost; leads on `status` stderr and `ls-remote` per `next`. Caller-environment reads, unchanged here |
| `audit/rounds/fiat-1888-epoch-table-split-and-release-caps.md` | grep lines 63, 82 | S1-R3-02 (low, fixed): a resolver inherited caller Git config. Lead: `GIT_CONFIG_GLOBAL=/dev/null` also drops a global `safe.directory`; not addressed here |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` | grep lines 32, 82, 117 | `GIT_CONFIG_PARAMETERS` was the remaining open configuration channel once `GIT_CONFIG_GLOBAL` was set; the projection reader strips it |
| `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.md` | grep lines 70, 74, 86, 95 | risk id `network-dependence`: one `ls-remote` per merge-step directive |
| `audit/rounds/fiat-857-framework-16-the-commit-gate-lives-in-one-cl.md` | grep lines 174, 176, 179 | the commit gate's four configuration routes (`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `$HOME/.gitconfig`, XDG); same routes this study's hostile fixture drives |
| `audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md`, `audit/rounds/fiat-774-bound-integration-revalidation-separately-fr.md` | synopsis by grep; source grep lines | sync-run aggregate and revalidation caps; no remote-read finding |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis header and grep | no match; plugin audit of 15 August 2026 |
| `audit/rounds/fiat-shoggoth-front-door-derived.md`, `fiat-888-adr-merge-recovery.md`, `fiat-1276-declare-a-held-job-s-required-inputs-in-the.md`, `fiat-1098-make-a-bound-instruction-document-editable.md`, `fiat-861-outer-checkpoint-archive-export-and-restore.md`, `fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md`, `fiat-1021-adopt-an-early-step-merge.md` (all under `audit/rounds/`) | grep match lines only | sync-run named as an allocation or repair point, or a fixture environment; no remote-read authentication finding |

Only grep-selected lines of each source and synopsis were read; no whole file
was read. `Covered`, `Not checked`, `Elenchus verdict` and `Leads not pursued`
were not reviewed beyond the lines named.

No known-failure inventory. The findings above that touch this seam
(#556 S3-R1-01, S3-R7-01, #453 S3-R1-01) are fixed and already guarded by
`test_version_relations.py` (lines 562 and 1990),
`test_hexctl.py` `test_native_git_fixture_ignores_hostile_ambient_environment`
(line 2292) and the hostile-loader cases in `test_step_branch_extensions.py`.
No audit record names an open failure this run must guard before product work,
so the study carries no inventory and the runbook carries no assignment
record. Those existing guards must stay green.

### 2.4 Outside the repository

- [gitcredentials](https://git-scm.com/docs/gitcredentials): helpers are
  tried in configuration order; once Git holds a username and password no
  further helper is tried; an empty `credential.helper` value resets the list
  collected so far. Both rules were observed in the fixture (section 4.3).
- [git-config](https://git-scm.com/docs/git-config): `GIT_CONFIG_COUNT`,
  `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>` add command-scope entries
  inherited by Git's own subprocesses, `git-remote-http` included;
  `--show-scope` labels each entry's scope. Both need Git 2.31 or later; the
  controller already uses `rev-parse --path-format=absolute` (Git 2.31) on
  every native relation read, so the floor does not move.
- [git](https://git-scm.com/docs/git): `GIT_CONFIG_GLOBAL` and
  `GIT_CONFIG_SYSTEM` replace the global and system files, XDG included.
- Apple Git reads `/Library/Developer/CommandLineTools/usr/share/git-core/gitconfig`
  as scope `unknown` (it sets `credential.helper=osxkeychain`) unless
  `GIT_CONFIG_NOSYSTEM` is set; observed here with `git config --show-scope`.
- This machine's real configuration has the shape `gh auth setup-git` writes:
  for `https://github.com` an empty helper reset followed by one `!`-prefixed
  absolute helper, in global scope. Only key names and value shapes were
  printed; no value was.

## 3. Constraints and non-goals

Starting ref: `main` `87142b40decb64f1c430847838ee8b5c1ab5475f`, the run
state's `base` and the run worktree's `HEAD`.

Toolchain: Python 3.14.6 (`.python-version`; `pyproject.toml` requires
`==3.14.*`), stdlib only; Git 2.50.1 (Apple Git-155). Run every test with
`NO_COLOR=1 FORCE_COLOR=` because this shell sets `FORCE_COLOR=3`, which
reddens argparse tests. The Hexaemeron suite needs `CHECKPOINT_COSIGN` set to
the local cosign 3.1.3 binary.

Self-hosting. The run edits the Fiat controller inside its own source tree.
The driver runs the installed controller, hexaemeron 1.6.102 (`fiat-v6.85.1`);
tests load the tree's `hexctl.py` by path. A `hexctl.py` change is a Fiat
behaviour change and owes one `fiat` generation row in
`plugins/hexaemeron/skills/fiat/EVOLUTION.md` under
`plugins/hexaemeron/skills/VERSIONING.md`. The runbook should declare one
Protasis `version-relations` block before Step 1 with the row
`fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base`,
as at least sixteen earlier runbooks do (for example
`docs/fiat-carried-step-commits/runbook.md`). Then no concrete Fiat label
token may appear anywhere else in the runbook, and the new label in
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` and `metadata.version` is
described, not spelled.

Versions. The required `invariants` job runs `scripts/plugin_release.py`, so
every step pull request that changes a path under `plugins/hexaemeron/` needs a
hexaemeron version above its own base and above every version any local or
remote ref claims. At study time (2026-11-02) the highest claim across
`refs/heads` and `refs/remotes` is 1.6.102 (`origin/main` and four branches);
re-check before each step. The surfaces are both `plugin.json` files,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, the pin
in `tests/test_version_propagation.py`, `tests/test_phylax_model_proxy.py`,
`metadata.version` in `plugins/hexaemeron/skills/fiat/SKILL.md` and
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` (`hexctl.py:488`).

Digest cascade. At the base the `hexctl.py` digest
(`83f1c56f2e0e128674ae32d9654577ff918858a689d2b0da2f9438fbaea891d2`) is pinned
only in `tests/promise_machine_coverage.json`; the fiat `SKILL.md` digest in
`tests/fixtures/agent-instruction-v1/manifest.json` and the three
`fiat-study-runbook-phase` fixtures; the fiat `EVOLUTION.md` digest in
`tests/fixtures/promise-machine/runtime/fiat-final-integration.json`;
`test_version_relations.py` in `runtime/fiat-version-resolution.json` and the
coverage register. `docs/promise-machine/obligation-gates/evaluation-run.json`
pins a whole-tree digest. `plugins/hexaemeron/skills/fiat/references/push-discipline.md`
is pinned nowhere. The step that edits these walks its own cascade, then
`scripts/portable_promise_machine.py sync` and `check`, and both Horos scans
(`--write`, then `--census --write`) after staging.

Test placement. `plugins/hexaemeron/tests/test_hexctl.py` is 262,133 bytes,
11 under the 262,144-byte read ceiling of `scripts/promise_machine.py check`.
New tests go in `plugins/hexaemeron/tests/test_native_remote_credentials.py`,
never in `test_hexctl.py`.

Step exits name the root suite and the checked runner with a base, because
`scripts/run_checks.py` with no `--base` selects nothing on a clean tree.

No Solidity: the security suite is waived for this run.

Boundaries:

- Always. Run the root suite, the Hexaemeron suite and
  `scripts/run_checks.py --base <step base>` before each commit. Lint shipped
  prose with Imprimatur. Bind test servers to 127.0.0.1 only and generate each
  test credential in the test. Start every test caller configuration with an
  empty `credential.helper` so no real keychain, `gh` or `osxkeychain` helper
  is consulted or written.
- Ask first. Adding a dependency (none is planned). Widening the remote
  environment beyond `HOME` and the credential projection, for example
  `XDG_CONFIG_HOME`, `GH_CONFIG_DIR` or `http.*` keys. Changing a receipt or
  ledger shape. Touching CI.
- Never. Read, print or store a real credential. Run a real credential helper
  in a test. Contact a host other than 127.0.0.1 in a test. Add a test to
  `test_hexctl.py`. Hand-edit state, receipts or the design record. Claim a
  private GitHub remote was read.

Non-goals, each deferred past the prototype:

- `http.*` authentication (`http.extraHeader`, proxies, `http.sslCAInfo`)
  and `~/.netrc` beyond what curl reads from `HOME` on its own.
- Helpers that need the caller's `PATH`, `XDG_CONFIG_HOME` or other variables.
  They refuse with the authentication message (measured: 4 of 6 helper shapes
  authenticate, section 4.3).
- Credential entries the caller carries in the environment
  (`GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_COUNT`); they are command scope and
  stay outside, as today.
- A global `safe.directory` (the #1888 lead) and every caller-environment
  remote read in section 2.1.
- The `ls-remote` in `plugins/hexaemeron/skills/fiat/scripts/checkpoint_clean_machine.py`
  and #868.
- A live proof against a private GitHub repository; it stays open for the
  first private-repository integration after release.

## 4. Design options

### 4.1 Candidates

1. `credential-scope-projection`. Keep the native `ls-remote`. Before it, run
   the caller's `git` (the program `bounded_git` already runs) as
   `git config --includes --show-scope -z --get-regexp '^credential\.'` with
   the caller's environment minus every `GIT_*` variable except
   `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `GIT_CONFIG_NOSYSTEM`, from the
   run worktree. Keep scopes `system`, `unknown`, `global`, `local` and
   `worktree`; drop `command`. Replay the entries in command scope through
   `GIT_CONFIG_COUNT`, preceded by one empty `credential.helper`, which clears
   what the native read collected from local config so the replay reproduces
   the caller's exact helper order. Add the caller's `HOME`. Trade: helpers run
   under `PATH=os.defpath`, so a helper found only on the caller's `PATH`
   refuses; one more child per read.
2. `github-rest-tip`. For a GitHub origin, read
   `repos/<owner>/<repo>/git/ref/heads/<branch>` through the caller's `gh`, as
   `github_rest` reads pull requests; any other origin keeps the unchanged
   native read. Trade: it authenticates with `gh`'s store rather than the
   caller's Git configuration, covers GitHub only, and readmits the caller's
   `PATH` and `gh` environment as the source of the relation answer.
3. `credential-fill-relay`. Run `git credential fill` in the caller's
   environment for the native origin's protocol and host, then hand the
   username and password to the native read through a controller-owned helper
   and two environment variables. Trade: the most faithful helper environment,
   at the cost of the credential passing through controller memory, the child
   environment and the process table, and three children per read.
4. `native-unchanged`. The baseline: today's environment and wording, with the
   operator adding a repository-local helper around one call as MR-03 did.
   Trade: no code, and the acceptance fails.

### 4.2 Criteria

Selection gates (each `boolean`, `equals true`, blocks `design-lock`):
`global-credential-read` (correctness, protasis),
`moved-tip-detected` (correctness, protasis),
`global-insteadof-inert` (correctness, phylax),
`ambient-substitution-inert` (compatibility, phylax),
`controller-holds-no-credential` (correctness, phylax),
`authentication-refusal-named` (recovery, elenchus).
Selection metrics: `child-processes-per-read` (time, metron, count,
minimise), `buffered-bytes-per-read` (space, metron, bytes, minimise),
`helper-shapes-authenticated` (compatibility, protasis, count of six,
maximise). Conformance gates, all blocking `integration`:
`seam-reads-credentialed-remote`, `sync-run-module-passes` (correctness),
`local-reads-stay-native` (compatibility), `projection-cap-refuses` (space),
`authentication-refusal-fixed` (recovery), `remote-read-children` (time,
count, at most 2).

Every selection cell runs on a fresh fixture from
`.hexaemeron/design/probe.py`: a served bare `remote.git` that answers only
HTTP Basic `fixture:<random token>`, a served `hostile.git` with other tips and
no authentication, a run worktree whose `origin` is the `remote.git` URL and
whose tracking ref is stale, and a caller environment whose only credential is
a global-config helper. The scenarios:

- `global-credential-read`: helper `"!<absolute path>"`; `gh` not logged in.
  Value: the read returns the served tip.
- `moved-tip-detected`: read, push a new served tip, read again. Value: the
  second read returns the new tip, so a sync commit equal to the first now
  differs and the comparison refuses.
- `global-insteadof-inert`: `url.<hostile>.insteadOf=<remote>` in the caller's
  global file, `~/.gitconfig` and `~/.config/git/config`. Value: the served
  tip, and zero requests at the hostile endpoint.
- `ambient-substitution-inert`: inherited `GIT_DIR` and `GIT_WORK_TREE` at a
  repository whose `origin` is hostile, inherited `GIT_CONFIG_COUNT` carrying
  the same rewrite, and a hostile directory first on `PATH` holding a `gh` that
  prints the hostile tip and a `git` that injects a wrong helper and answers
  `credential fill` with a wrong credential. Value: no hostile tip and zero
  hostile requests.
- `controller-holds-no-credential`: the token never appears in any argv,
  environment value, standard input or captured output the candidate handles.
- `authentication-refusal-named`: no helper at all. Value: the refusal names
  authentication and carries none of `could not read Username`,
  `terminal prompts`, `HTTP 401`, `fatal:`, `127.0.0.1` or the port.
- `helper-shapes-authenticated`: six caller configurations, counting served
  tips: `abs-exec` (absolute path), `bang-abs` (`!` with an absolute path),
  `bang-path` (`!` resolved on the caller's `PATH`), `named-path`
  (`git credential-<name>` on the caller's `PATH`), `home-store` (reads
  `$HOME/.fixture-credential`), `reset-order` (a wrong system helper, a global
  reset, then the right global helper).

### 4.3 Results and selection

Every report is a closed `protasis-design-report/v1` object with exit 0, under
`.hexaemeron/design/reports/selection/`, produced by
`python3 .hexaemeron/design/probe.py select --candidate <id> --criterion <id> --out <path>`
on 2026-11-02 with Python 3.14.6.

| Criterion | `credential-scope-projection` | `github-rest-tip` | `credential-fill-relay` | `native-unchanged` |
| --- | --- | --- | --- | --- |
| `global-credential-read` | pass | fail | pass | fail |
| `moved-tip-detected` | pass | fail | pass | fail |
| `global-insteadof-inert` | pass | fail | pass | fail |
| `ambient-substitution-inert` | pass | fail | pass | pass |
| `controller-holds-no-credential` | pass | pass | fail | pass |
| `authentication-refusal-named` | pass | pass | pass | fail |
| `child-processes-per-read` | 2 | 2 | 3 | 1 |
| `buffered-bytes-per-read` | 263 | 73 | 192 | 87 |
| `helper-shapes-authenticated` | 4 | 0 | 6 | 0 |

Observed facts behind the table:

- `github-rest-tip` fails the credential gates because `gh` holds no login in
  the scenario while the caller's Git does. With a `gh` login it returns the
  served tip with two children (checked separately, not a record cell). It
  fails `ambient-substitution-inert` because the `gh` first on `PATH` supplied
  the hostile tip.
- `credential-fill-relay` authenticates all six shapes and fails only
  `controller-holds-no-credential`: `git credential fill` returns the password
  to the controller, which places it in the native read's environment.
- `native-unchanged` reproduces the issue: `could not read Username ...
  terminal prompts disabled` from Git, reported as `remote run branch tip could
  not be read`.
- `credential-scope-projection` authenticates `abs-exec`, `bang-abs`,
  `home-store` and `reset-order`, and refuses `bang-path` and `named-path`,
  which need the caller's `PATH`. With the empty resets dropped from the
  replay, `reset-order` fails, so that shape measures order fidelity.
- With `HOME` pointing at a home whose `.gitconfig` and `.config/git/config`
  carry a rewrite, Git under `GIT_CONFIG_GLOBAL=/dev/null` and
  `GIT_CONFIG_NOSYSTEM=1` lists no `url.*` entry; without `GIT_CONFIG_GLOBAL`
  it lists both.
- The child counts and buffered bytes of `github-rest-tip` and
  `native-unchanged` were measured on their failing reads. The 263 bytes of
  `credential-scope-projection` include this machine's Apple
  `credential.helper=osxkeychain` entry and differ on another host.

Selection. Three candidates fail at least one selection gate and leave the
eligible set. `credential-scope-projection` is the only survivor, so the
non-dominated frontier is that one candidate and the rule is
`unique-frontier`. The record is `.hexaemeron/design-evidence.json`, SHA-256
`2dc559a0b230d436e16f215a47b612a0b03b5d0fc1d832aa2c7f0bc8b6709184`; the
Protasis checker exits 0 at `design-lock`, `step:1`, `step:2` and `step:3`, and
refuses `integration` with D008 until the conformance reports exist, as
designed. The runbook's `design-lock` block carries that digest and the
candidate `credential-scope-projection`.

The trade named: the selected design gives up helpers that rely on the
caller's `PATH` (4 of 6 shapes against the relay's 6) and adds one child per
read (2 against 1), and in return no credential byte reaches the controller and
no state the native environment excludes reaches the relation answer.

### 4.4 The chosen design

At `remote_branch_tip(..., native_relation=True)` only:

1. Projection reader. Run the caller's `git config --includes --show-scope -z
   --get-regexp '^credential\.'` through `bounded_probe` with an output cap of
   65,536 bytes, from the run worktree, with the caller's environment minus
   every `GIT_*` variable except the three configuration locators. Exit 1 with
   no output means no entries. Parse `scope NUL key LF value NUL` strictly:
   known scopes only, `command` dropped, every key starting `credential.`, at
   most 64 entries and 16,384 key and value bytes. Any start failure, timeout,
   cap, malformed framing, unknown scope, foreign key or excess refuses before
   the remote is contacted with
   `<label> could not be read: the caller's Git credential configuration could not be read`
   or `... is malformed` or `... exceeds its bound`.
2. Remote environment. `_native_relation_environment()` plus the caller's
   `HOME` when set, plus, when the projection is non-empty, `GIT_CONFIG_COUNT`
   and the key and value pairs: first `credential.helper` with an empty value,
   then every projected entry in the order Git listed it. `GIT_CONFIG_GLOBAL`
   and `GIT_CONFIG_SYSTEM` stay `/dev/null`; `PATH` stays `os.defpath`.
3. The read. `--no-replace-objects ls-remote --refs origin refs/heads/<branch>`
   with the native Git through `bounded_run`, so the status and merged output
   are available. On a non-zero exit, a fixed marker set
   (`could not read Username`, `could not read Password`,
   `Authentication failed`, `Permission denied (publickey`,
   `returned error: 401`, `returned error: 403`) yields
   `<label> could not be read: origin refused authentication, and the native read offers only the credential helpers your Git configuration names`;
   anything else keeps `<label> could not be read`. No child byte enters
   either text. The answer is parsed exactly as today.
4. Unchanged: `_native_relation_environment()`, `_native_relation_git`, every
   local relation read, every caller-environment remote read, the tip
   comparisons in `done_sync_run` and `build_version_resolution`, and every
   receipt and ledger shape. The conformance resolvers bind the names
   `remote_branch_tip`, `_native_relation_environment` and
   `_native_relation_commit`.

Study-time evidence, not shipped: a 90-line prototype of these three parts,
appended to a scratch copy of `hexctl.py` outside the repository, passed five
of the six conformance resolvers (`sync-run-module-passes` needs the test
module that does not exist yet), with `remote-read-children` reading 2. The
same resolvers against the unchanged base return false for
`seam-reads-credentialed-remote`, `projection-cap-refuses`,
`authentication-refusal-fixed` and `sync-run-module-passes`, true for
`local-reads-stay-native`, and stop with no report for `remote-read-children`
because the base read fails. No repository suite was run against the
prototype.

Conformance resolvers, run from the run worktree before the final
`done merge-step` checks `integration`:

```text
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion <criterion> --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-<criterion>.json
```

Each writes only to an `--out` path that must not exist. A copy of the probe
committed under `docs/` must stay byte-identical to the `.hexaemeron/design/`
original.

### 4.5 Step outline for the runbook

1. Scaffold. Commit copies of the study, runbook, design record, probe,
   builder and selection reports under `docs/fiat-2093-native-remote-credentials/`,
   and the decision draft named in section 12. No `plugins/` path changes, so
   no package bump.
2. Controller. The three parts of section 4.4 in `hexctl.py`; the new
   `plugins/hexaemeron/tests/test_native_remote_credentials.py` carrying the
   loopback fixture, the seam cases, one end-to-end `done sync-run` test whose
   name contains `sync_run`, one `build_version_resolution` case, and the
   no-regression case for local reads; one operator paragraph in
   `plugins/hexaemeron/skills/fiat/references/push-discipline.md`; the package
   bump on every surface, the `fiat` generation row and its cascade, all in
   this one step so the cascade is walked once.
3. Demonstrate. Run the six conformance resolvers and the module, and commit
   the output and commands to
   `docs/fiat-2093-native-remote-credentials/demonstration.md`. No `plugins/`
   path changes.

Each conformance cell is built in Step 2 and blocks `integration`, never a
`step:N`, so no cell is due before the step that builds it has pushed.

## 5. Risk register seed

```risk-register
credential-scope-only | caller configuration entries projected into the native remote read | only keys in the credential section cross; url, core, http and include entries and every command-scope entry stay out, by a test with one hostile entry of each
insteadof-global-inert | the caller's global file, HOME .gitconfig, XDG config and inherited GIT_CONFIG_COUNT | a hostile url.*.insteadOf in each leaves the served tip unchanged and the hostile endpoint receives no request
ambient-environment-inert | inherited GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_PARAMETERS, GIT_CONFIG_COUNT and loader variables | none reaches the projection reader's repository selection or the native read environment
home-admission | HOME added to the remote read only | GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM stay /dev/null so HOME readmits no file; local relation reads keep the unchanged environment by an equality test
helper-execution | caller-configured helpers running inside the native read | PATH stays os.defpath, helper output reaches Git only, and the controller never parses or keeps it
projection-parse | the caller Git's config -z --show-scope output | strict NUL framing, known scopes, the credential prefix, 64 entries, 16384 bytes and a 65536-byte child cap; malformed or oversized output refuses by name before the remote is contacted
refusal-leak | refusal text for native remote read failures | fixed text with no child byte, URL, host, port or helper output; authentication and other failures are told apart
secret-exposure | controller memory, argv, the environment the controller builds, receipts and the ledger | no credential byte enters any of them; a caller helper value that embeds a secret inline travels in the child environment as Git itself would read it, and that limit is written down
real-credential-isolation | tests and the design probe | every test caller configuration starts with an empty credential.helper and pins its global and system files, so no real keychain, gh or osxkeychain helper runs, and no socket leaves 127.0.0.1
seam-coverage | every native_relation=True remote read | sync-run, resolve-versions, next and status in the integrate phase, and the integrate post-merge read all reach remote_branch_tip and receive the same environment; no other native read reaches a remote
tip-comparison-unchanged | the comparisons in done_sync_run and build_version_resolution | a remote tip that differs from the supplied commit still refuses with the existing message
fake-git-compat | the fake delivery Git in hexctl_harness.py and existing native-remote tests | the projection's config call falls through to the real Git and the existing GIT_DIR, loader and ls-remote cases stay green
version-surface | the hexaemeron package version and the fiat ledger row | the package version exceeds the PR base and every ref's claim on all surfaces, and the generation row comes from the version-relations block
digest-cascade | fixtures pinning hexctl.py, fiat SKILL.md, EVOLUTION.md and pinned test files | the step re-pins its own cascade and the root suite, the Hexaemeron suite and promise_machine.py check pass at its exit
test-ceiling | plugins/hexaemeron/tests/test_hexctl.py at 262133 bytes | no new test lands there
killed-mid-read | a controller killed during the projection or the remote read | nothing is written before the read returns, no temporary file is created, and a rerun repeats the read
```

`killed-mid-read` holds by construction: the projection travels in the child
environment, so there is no file to leave half-written, and the commands that
use the read write state only after it returns.

## 6. Glossary seeds

- Native relation environment: the closed Git environment from
  `_native_relation_environment()` that local relation reads use unchanged.
- Native remote read: one `ls-remote` from `remote_branch_tip` with
  `native_relation=True`.
- Remote environment: the native relation environment plus `HOME` and the
  credential projection, used only by the native remote read.
- Credential projection: the caller's `credential.*` entries from every scope
  but `command`, in the caller Git's order, replayed in command scope.
- Configuration locators: `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and
  `GIT_CONFIG_NOSYSTEM`, the only `GIT_*` variables the projection reader
  keeps.
- Helper reset: an empty `credential.helper` value, which clears the helper
  list collected so far.
- Authentication refusal: the fixed refusal for a native remote read whose
  merged output carries an authentication marker.
- Loopback fixture: the served `remote.git` and `hostile.git` on 127.0.0.1 with
  a per-run token.

## 7. Sources

- Issue [#2093](https://github.com/wildcat-finance/skills/issues/2093), body
  as filed 2026-10-13, one revision.
- [`hexctl.py` at the base](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/fiat/scripts/hexctl.py),
  lines as cited.
- [`test_version_relations.py` at the base](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/tests/test_version_relations.py#L562),
  lines 562 and 1990.
- [`hexctl_harness.py` at the base](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/tests/hexctl_harness.py#L400),
  the fake delivery Git.
- [Run #556 audit record](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md#L1676),
  S3-R7-01.
- [Run #453 audit record](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md#L78),
  S3-R1-01.
- [Root audit log](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/audit/AUDIT.md#L13516),
  currency read dispositions.
- [`VERSIONING.md` at the base](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/VERSIONING.md).
- Pull requests [#2119](https://github.com/wildcat-finance/skills/pull/2119),
  [#2073](https://github.com/wildcat-finance/skills/pull/2073),
  [#1775](https://github.com/wildcat-finance/skills/pull/1775) and
  [#1638](https://github.com/wildcat-finance/skills/pull/1638).
- Git documentation: [gitcredentials](https://git-scm.com/docs/gitcredentials),
  [git-config](https://git-scm.com/docs/git-config),
  [git](https://git-scm.com/docs/git).
- Design evidence: `.hexaemeron/design-evidence.json`,
  `.hexaemeron/design/probe.py` (SHA-256
  `0e9dbe397faa4ec3ef92d33a0d8c417a9875c0a015fd401d72e6d2c78a4816df`),
  `.hexaemeron/design/build_record.py` (SHA-256
  `74f70a666ce268c4e625cdb324b5e74ebc83c61a6f3ffb8ea5a5862f21f390db`) and the
  36 reports under `.hexaemeron/design/reports/selection/`.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal carries. Fiat runs when an operator or driver calls it, so
the refusal line is the signal; this run adds no event, metric or alert.

1. "Integration stopped on a remote read: is origin refusing my credential, or
   is it unreachable?" Step 2's seam answers on every native remote read: the
   authentication refusal names authentication, anything else keeps
   `could not be read`.
2. "Did the controller read my credential configuration at all?" A projection
   that cannot be read, is malformed or exceeds its bound refuses with its own
   text before the remote is contacted. Which helpers were offered is not
   recorded, by design: helper strings never enter a receipt or the ledger, and
   the operator can list them with
   `git config --show-scope --get-regexp '^credential\.'`.
3. "Could a rewrite in my global config have steered the receipted tip?" No
   runtime signal; the answer is fixed by construction and proved by the
   `insteadof-global-inert` and `ambient-environment-inert` tests.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and the controls. Widening a trust boundary is an
ask-first item; issue #2093 asks for it, for the credential configuration
only, and this study widens it by exactly that plus `HOME`.

- The caller's configuration, read through the caller's Git. Worth taking:
  the relation answer, by smuggling a non-credential entry. Control: the
  `credential.` prefix, the scope allowlist, strict framing and the caps.
- Caller-configured helpers executing inside the native read. Worth taking:
  the run, by running a program. Control: none new is possible, because the
  caller's Git already runs these programs; `PATH` stays `os.defpath`, their
  output reaches Git only, and the caller's `git` is already the program
  `bounded_git` runs for every non-native read.
- The merged child output read for classification. Worth taking: disclosure
  through a refusal. Control: fixed markers in, fixed text out.
- The remote environment. Worth taking: substitution through inherited state.
  Control: built from the closed environment, `HOME` and controller-built
  `GIT_CONFIG_*`; the caller's own `GIT_CONFIG_*`, `GIT_DIR` and loader
  variables are never copied.
- Credential material. Worth taking: the credential. Control: it never enters
  controller memory, argv, receipts or the ledger; only helper strings travel.
- Tests and the probe. Worth taking: the operator's real credential. Control:
  loopback only, a per-run token, every caller configuration starting with an
  empty helper reset and pinned global and system files.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/metron/SKILL.md)
owns budgets. None: this run makes no performance claim. Recorded counts: a
native remote read starts 2 controller children instead of 1, so
`done sync-run` starts 4 instead of 2 and each relation-bearing
`done resolve-versions`, `next` or `status` in the integrate phase starts 8
instead of 4. Each child keeps `GIT_TIMEOUT` (30 seconds) and its output cap
(65,536 bytes for the projection, `GIT_OUTPUT_MAX` for the read). The
measuring commands are the probe's `child-processes-per-read` cell and the
`remote-read-children` conformance cell (at most 2). No wall-clock figure is
claimed, because only loopback timings exist.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns triage and the guard rule. What stops the run: an unreadable, malformed
or oversized projection (before the remote is contacted); an authentication
refusal; any other read failure; and every existing tip, parent, history and
identity refusal, unchanged. A caller with no `HOME` proceeds without it. A
caller with no credential configuration proceeds with no projection, which is
today's read. Guard convention: each fix an audit round claims lands a guard
test in `plugins/hexaemeron/tests/test_native_remote_credentials.py` (or the
module that owns the seam it fixes) that fails on the unfixed tree, through
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`. Where that runner reports an inconclusive
verdict, the round shows the counterfactual by running the guard against the
unfixed tree in a detached snapshot.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record.

1. The native remote read admits the caller's credential configuration and
   `HOME`, and nothing else, with the REST route and the credential relay
   rejected for the reasons in section 4.3. It reverses a boundary the #556
   and #453 rounds set, so it is expensive to reverse and earns a decision
   record: `docs/decisions/drafts/admit-caller-credentials-to-native-remote-reads.md`,
   numbered at the merge that lands it. Step 1 creates the draft.
2. The Fiat generation row lives in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
   bound by the runbook's `version-relations` block.
3. The operator-facing rule lives in
   `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, beside the
   `done sync-run` commands it governs.

The test layout and the refusal wording are not decisions; they live in the
code and its tests.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | credential-scope-projection
record | adr/admit-caller-credentials-to-native-remote-reads
```
