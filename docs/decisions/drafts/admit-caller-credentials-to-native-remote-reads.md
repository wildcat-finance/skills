# Decision: Admit the caller's credential configuration to native remote reads

## Status

Accepted, 2026-11-02, for the skills#2093 study. Numberless until the integration composer assigns its number. It supersedes no decision record.

## Context

`done sync-run` reads the remote run-branch tip and the remote base tip with `git ls-remote` under `_native_relation_environment()` ([`hexctl.py:4153-4168`](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L4153-L4168)). That environment sets `PATH` to `os.defpath`, points `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at `/dev/null`, sets `GIT_CONFIG_NOSYSTEM=1` and `GIT_TERMINAL_PROMPT=0`, and passes `SSH_AUTH_SOCK` and nothing else, so no `HOME`. A private repository whose `origin` is an `https://github.com/` URL and whose credential comes from a global `credential.https://github.com.helper` fails both reads with `remote run branch tip could not be read` ([`hexctl.py:23434`](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L23434)), while the same `ls-remote` succeeds in the caller's shell. A run whose base advanced then cannot receipt its sync, so it cannot integrate. On 2026-10-13 the miskatonic MR-03 run hit this and was receipted only after a temporary repository-local helper was added around one call.

Every native remote read goes through one seam, `remote_branch_tip(..., native_relation=True)` ([`hexctl.py:23421`](https://github.com/wildcat-finance/skills/blob/87142b40decb64f1c430847838ee8b5c1ab5475f/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L23421)). On a run whose runbook declares `version-relations`, `done resolve-versions`, `next` at the integrate directive and `status` in the integrate phase each make four such reads, and `done integrate` makes one post-merge base read.

The environment is closed on purpose. In run #556, S3-R1-01 (fixed in that round) and S3-R7-01 (fixed in `ec2fbd73d`) found that an inherited `GIT_DIR` redirected the remote relation reads and supplied the run and base tips in sync receipt construction. In run #453, S3-R1-01 found that the native environment copied every non-`GIT_` variable, so loader channels reached relation Git; #1638 closed it. [skills#2093](https://github.com/wildcat-finance/skills/issues/2093) asks to widen that boundary for the credential configuration only.

## Decision

The native remote tip read admits the caller's `credential.*` configuration and `HOME`, and nothing else; every local relation read keeps today's native environment.

The change is confined to `remote_branch_tip(..., native_relation=True)`:

1. Projection. The caller's own `git`, the program `bounded_git` already runs, runs `git config --includes --show-scope -z --get-regexp '^credential\.'` from the run worktree with an output cap of 65,536 bytes. Its environment is the caller's minus every `GIT_*` variable except `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `GIT_CONFIG_NOSYSTEM`. Scopes `system`, `unknown`, `global`, `local` and `worktree` are kept and `command` is dropped. Every key starts `credential.`, with at most 64 entries and 16,384 key and value bytes. A start failure, timeout, cap, malformed framing, unknown scope, foreign key or excess refuses before the remote is contacted, naming the credential configuration as unreadable, malformed or over its bound.
2. Replay. The read runs under `_native_relation_environment()` plus the caller's `HOME` when set and, when the projection is non-empty, `GIT_CONFIG_COUNT` entries: one empty `credential.helper` first, then every projected entry in the order Git listed it. The empty reset clears the helpers the read collected from local configuration, so the replayed order is the caller's. `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` stay `/dev/null` and `PATH` stays `os.defpath`.
3. Refusal. A non-zero exit whose merged output carries a fixed authentication marker (`could not read Username`,
   `could not read Password`, `Authentication failed`, `Permission denied (publickey`, `returned error: 401`, `returned error: 403`) refuses with a fixed text naming authentication; any other failure keeps
   `<label> could not be read`. No child byte enters either text.

The repository's own configuration stays readable, as it is today; global, system and environment-carried Git state stays outside. Tip parsing, the tip comparisons in `done_sync_run` and `build_version_resolution`, and every receipt and ledger shape stay as they are.

## Alternatives

The study's probe, `docs/fiat-2093-native-remote-credentials/probe.py`, measured four candidates on 2026-11-02 against a loopback fixture: a served `remote.git` on 127.0.0.1 that answers only HTTP Basic with a per-run token, a served `hostile.git` with other tips and no authentication, and a caller whose only credential is a global-config helper. All 36 selection cells are digest-bound in `docs/fiat-2093-native-remote-credentials/design-evidence.json`.

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

- `github-rest-tip` reads `repos/<owner>/<repo>/git/ref/heads/<branch>` through the caller's `gh` for a GitHub origin. It authenticates with `gh`'s store rather than the caller's Git configuration, covers GitHub only, and readmits the caller's `PATH` and `gh` environment as the source of the relation answer. Rejected: with no `gh` login it fails the three credential gates while the caller's Git succeeds, and a `gh` first on `PATH` supplied the hostile tip, so it fails `ambient-substitution-inert`. With a `gh` login it returned the served tip with two children, checked separately and not a record cell.
- `credential-fill-relay` runs `git credential fill` in the caller's environment for the origin's protocol and host, then hands the username and password to the native read through a controller-owned helper and two environment variables. It authenticates all six helper shapes. Rejected: it fails `controller-holds-no-credential`, because the password passes through controller memory, the child environment and the process table, and it starts three children per read.
- `native-unchanged` keeps today's read and leaves the operator to add a repository-local helper around one call, as MR-03 did. Rejected: it fails the credential gates and `authentication-refusal-named`. It reproduces the issue: Git reports `could not read Username ... terminal prompts disabled`
  and the controller reports `remote run branch tip could not be read`.

Three candidates fail at least one selection gate. `credential-scope-projection` is the only survivor, so the selection rule is `unique-frontier`.

## Consequences

1. Helpers that need the caller's `PATH` refuse with the authentication text. The selected design authenticated 4 of 6 helper shapes (`abs-exec`, `bang-abs`, `home-store`, `reset-order`) and refused `bang-path` and `named-path`; the relay authenticated 6. With the empty resets dropped from the replay, `reset-order` fails, so that shape measures order fidelity.
2. A native remote read starts 2 controller children instead of 1, so `done sync-run` starts 4 instead of 2 and each relation-bearing `done resolve-versions`, `next` or `status` in the integrate phase starts 8 instead of 4. Each child keeps `GIT_TIMEOUT` (30 seconds) and its output cap. No wall-clock figure is claimed, because only loopback timings exist. The measured 263 buffered bytes include this machine's Apple `credential.helper=osxkeychain` entry and differ on another host.
3. A credential a helper returns never enters controller memory, argv, a receipt or the ledger. Only the projected `credential.*` values travel, in the child environment. One limit: a value that embeds a secret inline passes through the controller's projection and the child environment exactly as Git itself would read it. Caller-configured helpers now run inside the native read. No new control is possible there: the caller's Git already runs these programs, and it is the program `bounded_git` runs for every non-native read.
4. `HOME` does not readmit global configuration. With `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`, Git listed no `url.*` entry from a home whose `.gitconfig` and `.config/git/config` carried a rewrite; without `GIT_CONFIG_GLOBAL` it listed both. A hostile `url.*.insteadOf` in global configuration or inherited `GIT_CONFIG_COUNT` leaves the relation answer unchanged.
5. Widening further is an ask-first change. `XDG_CONFIG_HOME`, `GH_CONFIG_DIR`, `http.*` keys, `~/.netrc` beyond what curl reads from `HOME`, credential entries carried in `GIT_CONFIG_PARAMETERS` or `GIT_CONFIG_COUNT`, and a global `safe.directory` stay outside. The `ls-remote` in `checkpoint_clean_machine.py`, #868 and every caller-environment remote read are unchanged.
6. The Git floor stays at 2.31, which every native relation read already needs for `rev-parse --path-format=absolute`.
7. No live private GitHub repository was read. That proof stays open for the first private-repository integration after release.

The operator rule goes in `plugins/hexaemeron/skills/fiat/references/push-discipline.md` beside the `done sync-run` commands, and the Fiat generation row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`. Step 2 adds the controller consequences here and Step 3 the measured conformance results, each leaving the record numberless. Until integration assigns the number, the standing home is `adr/admit-caller-credentials-to-native-remote-reads`.
