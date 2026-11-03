# Demonstration: the credentialed native remote read

This is the conformance evidence for [skills#2093](https://github.com/wildcat-finance/skills/issues/2093): the six cells the design record leaves pending for `credential-scope-projection`, each blocking integration. The decision they support is `adr/admit-caller-credentials-to-native-remote-reads`.

## What ran

On 2026-11-03, between 09:38 and 09:39 UTC, each resolver ran once from the root of the run worktree, with the interpreter `.python-version` pins, at `0ee28a3591c40d6f4cf80ab9a4cfec7ee91559f4`. That is the Step 2 head; Step 3 changes no product file.

```bash
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion seam-reads-credentialed-remote --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-seam-reads-credentialed-remote.json
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion sync-run-module-passes --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-sync-run-module-passes.json
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion local-reads-stay-native --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-local-reads-stay-native.json
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion projection-cap-refuses --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-projection-cap-refuses.json
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion authentication-refusal-fixed --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-authentication-refusal-fixed.json
python3 .hexaemeron/design/probe.py conform --candidate credential-scope-projection --criterion remote-read-children --root . --out .hexaemeron/design/reports/conformance/credential-scope-projection-remote-read-children.json
```

Each exited 0. None was retried and no report was replaced; the probe opens its report for exclusive creation and refuses an existing path.

The probe, `.hexaemeron/design/probe.py`, is byte-identical to `docs/fiat-2093-native-remote-credentials/probe.py` (SHA-256 `0e9dbe397faa4ec3ef92d33a0d8c417a9875c0a015fd401d72e6d2c78a4816df`). It loads the controller in this tree, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (SHA-256 `bb9c96062ab5e7b2bb180f4f1e812cd39c2c699b2cb90eecd4554ba97e7004ef`, 1,365,545 bytes), and calls its functions in process. The init-pinned 1.6.102 controller that drives this run did not run. The fixture's caller `git` and the native Git both resolved to `/usr/bin/git`, `git version 2.50.1 (Apple Git-155)`.

Each resolver builds a fresh fixture and removes it afterwards: a bare `remote.git` served over plain HTTP on 127.0.0.1 that answers only HTTP Basic `fixture:<token>`, with a random token per fixture; a served `hostile.git` with other tips and no authentication; a run worktree whose `origin` is the `remote.git` URL and whose tracking ref is stale; and a caller environment with its own `HOME` and its own global and system configuration files. The global file opens with an empty `credential.helper` reset. By default its only credential is a `"!<absolute path>"` helper scoped to the loopback URL: a shell script that prints the token.

## Results

| Criterion | Value | Gate | Report SHA-256 |
| --- | --- | --- | --- |
| `seam-reads-credentialed-remote` | `true` | equals `true` | `37931fd1f9b2b8b9732b265e11cffe86d59aba1c6fa1eebb6ef04a795b6f2e5e` |
| `sync-run-module-passes` | `true` | equals `true` | `8331967188d62a37e3e3a20cb05a1859de217c5d4b6dc8219fa2149539be24cd` |
| `local-reads-stay-native` | `true` | equals `true` | `dbae540cbdc0e11a807c293c09dd6b93d6ad938b686b7dbb988680987e113068` |
| `projection-cap-refuses` | `true` | equals `true` | `a70cfcacfec9adadec702ea608cf3baadc7142bf4c9440488e32db021a35de90` |
| `authentication-refusal-fixed` | `true` | equals `true` | `66ae4cf5bd84543c98ddce23ce8f6bc9d7837a642e67f2cfb2442085e9bd904b` |
| `remote-read-children` | `2` | at most `2` | `2ecea795a7c7c41a1dee45e29e84f513c0dda792efd339b6ec2b2b9c7def1c81` |

Each report is one closed `protasis-design-report/v1` object holding its command, exit 0 and value. `docs/fiat-2093-native-remote-credentials/reports/conformance/` holds copies equal to the bytes the resolvers wrote, under the same names. With the six reports in place, this printed `clean`, exited 0 and consumed the six digests above:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration
```

It ran from the installed Hexaemeron 1.6.102 copy of the checker, byte-identical to the one in this tree.

## What each cell observed

- `seam-reads-credentialed-remote`. The caller also inherits `GIT_DIR` at a repository whose `origin` is the hostile URL, and `GIT_CONFIG_COUNT` carrying `url.<hostile>.insteadOf` set to the remote URL; the same rewrite sits in its global file, `~/.gitconfig` and `~/.config/git/config`. `remote_branch_tip(work, "run", native_relation=True)` read once, the served branch moved to a new commit, and it read again. True: the first read returned the served tip, the second the new tip, and the hostile endpoint received no request.
- `sync-run-module-passes`. It runs `python3 -m unittest discover -v -s plugins/hexaemeron/tests -p test_native_remote_credentials.py` from the root, with `FORCE_COLOR` and `CLICOLOR_FORCE` removed and `NO_COLOR=1`. True: exit 0, an `OK` line and a test whose name contains `sync_run`. The module drives `done_sync_run` (`test_sync_run_receipts`, `test_sync_run_refusals`) and `build_version_resolution` (`test_resolution_reads`) through the seam. Run once more directly, it ran 7 tests, `OK`.
- `local-reads-stay-native`. The caller carries `GIT_CONFIG_COUNT` with `core.hooksPath`. The probe kept the environment `_native_relation_environment()` returned and the environment of every `subprocess.Popen` the controller started for `_native_relation_commit(work, "HEAD", ...)`. True: no environment held a key outside the eight native keys and `SSH_AUTH_SOCK`, which the fixture caller did not set, and each had `PATH` equal to `os.defpath`, `GIT_CONFIG_GLOBAL` equal to `/dev/null` and no `HOME`.
- `projection-cap-refuses`. The caller's global file adds 65 `[credential "https://cap-<n>.example.invalid"]` sections to the reset and the helper. True: no tip, a refusal naming the credential configuration, and no request at the served remote. This crosses only the 64-entry bound; the module's `over the byte bound` and `over the output cap` cases cross the 16,384-byte and 65,536-byte bounds.
- `authentication-refusal-fixed`. The caller has no helper beyond the empty reset. True: the refusal names authentication and carries none of `could not read Username`, `terminal prompts`, `Authentication failed`, `HTTP 401`, `Bad credentials`, `fatal:`, `127.0.0.1` or the port;
  with `origin` at `http://127.0.0.1:9/fixture/closed.git`, the refusal reads `could not be read` and does not name authentication.
- `remote-read-children`. The probe counted the controller's `subprocess.Popen` calls during one read that returned the served tip: 2, the caller Git's `git config` projection and the native `ls-remote`. Processes Git starts itself, such as its HTTP transport and the credential helper, are outside that count. No timing was taken, and nothing beyond the count is claimed.

## The read under test

At `0ee28a35`, `remote_branch_tip(..., native_relation=True)` (`hexctl.py:23615`) is the only caller of `_native_remote_git` (`:4350`), which calls `_caller_credential_projection` (`:4253`) and then `_native_remote_environment` (`:4327`). The native callers are `done_sync_run` (`:20834`, `:20839`), `build_version_resolution` (`:5593`, `:5599`, `:5667`, `:5673`) and `terminal_version_resolution` (`:21233`). Four resolvers call `remote_branch_tip` directly and `local-reads-stay-native` makes no remote read; only the module reaches it through `done_sync_run` and `build_version_resolution`.

The tip is parsed from Git's standard output alone. Standard error goes to a sink that is only matched against the six fixed authentication markers. The projection also parses standard output alone and drops standard error; its 65,536-byte cap covers both streams, beside its 64-entry and 16,384-byte bounds. The native read's own cap is `GIT_OUTPUT_MAX`, 2,097,152 bytes.

None of the six cells measures credential exposure. The fixture's token appears only in a helper's output. A configuration value that embeds a secret inline, such as a helper string carrying a token, passes through the controller's projection and the read's environment exactly as Git reads it.

## What the loopback remote does not prove

- No live private GitHub repository was read. The remote is plain HTTP on 127.0.0.1 with a fixture token, so TLS, the `github.com` host and GitHub's authentication responses were not exercised. This run is driven by the init-pinned 1.6.102 controller against a public origin, so its own remote reads do not exercise the change either.
- No real `gh` helper ran. Every helper that ran is a fixture shell script. Each caller configuration names its own global and system files, so a helper installed in the developer's own `~/.gitconfig`, such as `gh auth git-credential`, is never read. Its empty `credential.helper` reset clears `osxkeychain`, which Apple Git's own Command Line Tools configuration names in `unknown` scope, read before the system and global files.
- SSH was not exercised; the fixture has no SSH server. The study's SSH reasoning in section 2.1 comes from source and OpenSSH's documentation.
- `terminal_version_resolution` has no test driving its read. The tests that call it, in `plugins/hexaemeron/tests/test_version_relations.py`, mock `remote_branch_tip` or refuse before it, and no resolver calls it. Its post-merge base read at `hexctl.py:21233` passes `native_relation=True` to the same `remote_branch_tip` the other two callers reach. Those tests were found by searching the test trees for the function's name.
- Controller tests still read the developer's real Git configuration. A test that reaches the native remote read under the ambient environment runs the projection against the developer's own `credential.*` entries, so a valueless key there changes its result (audit finding S2-R1-04). [skills#2150](https://github.com/wildcat-finance/skills/issues/2150) carries that isolation. The resolvers and the module build their own caller configuration.
- The Hexaemeron runner caps its test-id manifest. At this head `plugins/hexaemeron/tests/run_tests.py` refuses a manifest above 409,600 bytes (`MAX_MANIFEST_BYTES`, `run_tests.py:77`). Step 2 measured 409,121 bytes for 4091 ids, so the credential cases run as subtests of seven methods. [skills#1971](https://github.com/wildcat-finance/skills/issues/1971) tracked the cap; [skills#2146](https://github.com/wildcat-finance/skills/pull/2146) raised it to 1,048,576 bytes on `main` in `9cce3bb2`, which this branch does not contain.
