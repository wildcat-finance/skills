# Study: make Goldfinch fixture generation work on macOS

Assumptions fixed before the design:

- The user is the Wildcat contributor invoking Fiat for open issue #881. The target is this clean run only; a predecessor directory was declared corrupt and deleted, so none of its product bytes or claims is evidence here.
- “OS-provided root aliases such as `/var`” means the exact macOS root aliases `/var -> private/var`, `/tmp -> private/tmp`, and `/etc -> private/etc`, checked at the time of use. It does not mean resolving a general symlink chain.
- The exact supported interpreter is Python 3.14.6. Python 3.13.15 is historical reproduction evidence, not a second supported target and not authority to change the pin.
- The existing Goldfinch fixture and release bytes are outputs to reproduce, not files to regenerate in this repair.
- There is no remaining ambiguity that changes the design. If a future macOS release changes a root alias, the safe result is a named refusal until that alias contract is studied again.

## 1. Problem statement

Lazarus's Goldfinch v1 producer is supposed to rebuild a checked fixture offline. On macOS it creates and pins the private stage correctly, then `_descriptor_directory` tries to turn the open directory back into `/proc/self/fd/<fd>/fixture` or `/dev/fd/<fd>/fixture`. Neither path reaches the child on this Darwin host, so the producer exits 1 with `refused: platform cannot anchor fixture stage`. The skip at `plugins/lazarus/tests/test_goldfinch.py:67-70` hides the builder and its race guards on the platform that needs them.

The release writer has the opposite problem. Its descriptor-relative statement walk correctly refuses every symlinked parent, but macOS's ordinary temporary directory is below lexical `/var`, which is a system root symlink to `private/var`. `_read_statement` therefore rejects a valid statement before reaching the user-controlled part of the path.

A working prototype means both defects are repaired without converting either operation to path-only authority. The stage remains rooted in its already-open directory descriptor; each component read, manifest write, verification, atomic no-replace publish, rollback, and cleanup remains relative to pinned descriptors. The statement reader admits only the exact verified macOS root aliases above, then resumes its existing `O_DIRECTORY | O_NOFOLLOW` walk for every remaining parent and `O_NOFOLLOW | O_NONBLOCK` for the final regular file. Linux keeps its current lexical no-follow walk.

The proving path is:

1. Run the exact supported interpreter with `TMPDIR=/private/tmp` and build to a new path. Exit 0 and byte-for-byte equality with `plugins/lazarus/examples/goldfinch-v1` are required.
2. Copy the checked statement to Python's default macOS `TemporaryDirectory`, call `write_release`, and verify the produced release. Exit 0 is required.
3. Run the hostile parent-symlink, parent-identity, no-replace, rollback, and bounded-cleanup guards without the descriptor-path skip.
4. Run `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}` under exact Python 3.14.6; the report must be closed `unittest-json-v1`, complete, and green.
5. Preserve the Linux Lazarus job and add either the issue-authorised macOS job or an equivalently durable Darwin runner that executes both regressions.

Current reproductions at `0987aa37f5110501b2c7a440f42370f81d58afe5`:

```text
TMPDIR=/private/tmp PYTHONPATH=plugins/lazarus uv run --no-project --python 3.14.6 --with-requirements plugins/lazarus/requirements.lock python plugins/lazarus/examples/goldfinch-v1/demo.py build-fixture --out /private/tmp/fiat881-surveyor-goldfinch-v1
exit 1: refused: platform cannot anchor fixture stage

PYTHONPATH=plugins/lazarus/scripts uv run --no-project --python 3.14.6 --with-requirements plugins/lazarus/requirements.lock python -c '<copy checked statement into tempfile.TemporaryDirectory; call write_release>'
exit 1: PathError: statement path contains a symlink or non-directory: /var/folders/.../statement.json
```

One earlier probe used `PYTHONPATH=plugins/lazarus` for `lazarus_lib.release` and exited 1 with `ModuleNotFoundError`; it was a probe setup error, not product evidence. The corrected command above establishes the defect.

## 2. Prior art

Repository code already contains most of the required mechanism. `demo.py:182-446` opens directories with no-follow flags, checks device and inode identity, writes new components with `O_EXCL`, walks cleanup through descriptors with count and depth bounds, and uses Linux `renameat2` or Darwin `renameatx_np(RENAME_EXCL)` for atomic no-replace publication. `lazarus_lib/paths.py` already performs descriptor-relative confined reads and writes, but its whole-tree listing and public roots are path-shaped. The missing join is an explicit descriptor-root form for those existing manifest and verifier helpers. `release.py:393-470` already supplies one bounded, stable, nonblocking read after its parent walk; only the verified system-root-alias entry needs to change.

The last two merged pull requests that changed the subject paths were read from the local merge commits because both GitHub pull endpoints returned HTTP 404:

- Merge `4296f9f0b3eb03926d9b5b03258246dcab8c13ec` (PR #718), second parent `21fbe2b583bf247b1e58a93e456ba7715207d32d`, pinned Python 3.14.6 and adjusted Python 3.14 path inspection semantics. It changed `demo.py` and `test_goldfinch.py` but did not repair either macOS path defect. Carry forward the exact pin and the issue's finding that both failures predate it; refuse any pin change here.
- Merge `68039a8756e60c7aae97439d1cce616c09986a24` (PR #666), second parent `82c1b7123a3cc10b8ce875ba915cd703fb147d19`, removed an orphaned cross-plugin assertion from `test_goldfinch.py`. Carry forward its plugin boundary: do not restore cross-plugin test ownership or move this repair outside Lazarus without a checked shared contract.

The complete audit-synopsis set was checked with `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`, exit 0. The in-scope records were then read for their path and recovery findings:

- `audit/AUDIT.md`, Goldfinch preservation release rounds at lines 3119-3725, requires dangling-symlink refusal, one-read statement binding, stable bytes, owner-only staging, no partial output, and nested-symlink refusal. Its accepted final empty-directory rename race is bounded and is not reopened by this issue.
- `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md` and its checked synopsis carry S4-R1-04 (one bounded stable final statement descriptor), S4-R3-03 (no-follow every parent), S5-R5-01 (pin parent and stage descriptors through publication and rollback), S5-R7-01 (descriptor-bounded cleanup must not delete a replacement), and S5-R7-02 (bounded path-error surface). These controls are mandatory. The final audit explicitly left hosted CI unchecked; issue #881 now owns the Darwin regression evidence.
- `audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md` and its synopsis carry atomic finalisation, bounded resources, and release compatibility. Their provider and secret leads are outside this offline path repair.
- `audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md` and its synopsis contain no open fixture-stage or statement-path work. Its replay and RPC boundaries are refused from this repair.

Organisation boundary: Lazarus owns fixture preservation and release reading. Ariadne consumes the resulting statement/release evidence but does not own filesystem traversal, so no Ariadne change is selected. The Lazarus evolution ledger's open empty-block receipt frontier is unrelated and must not advance.

Outside the repository and organisation, macOS 26.5's `open(2)` manual defines `openat` relative to a directory descriptor and documents `O_DIRECTORY`, `O_NOFOLLOW`, `O_NOFOLLOW_ANY`, and `O_RESOLVE_BENEATH`; `rename(2)` documents descriptor-relative `renameatx_np` and `RENAME_EXCL`. Python 3.14.6 on this host reports `os.open`, `os.stat`, and `os.rename` in `os.supports_dir_fd`, and `os.scandir` in `os.supports_fd`. Host inspection records `/var`, `/tmp`, and `/etc` as root-owned symlinks to `private/var`, `private/tmp`, and `private/etc`; `tempfile.gettempdir()` is `/var/folders/2l/ft_wrtys7tj88xf2pkdjcflw0000gn/T`. These are platform observations, not permission to accept another alias.

## 3. Constraints and non-goals

The exact start is clean branch `fiat/881-macos-path-repair-clean-run` at `0987aa37f5110501b2c7a440f42370f81d58afe5`; issue base `7e449ba35e1519d28b33f06225c4c4137b548a23` is an ancestor. Toolchain: Darwin 25.5.0 arm64, `.python-version` 3.14.6, `pyproject.toml` `requires-python ==3.14.*`, `uv 0.12.5`, and `plugins/lazarus/requirements.lock`.

Always:

- Keep the stage descriptor authoritative from creation through manifest construction, verification, publication, rollback, and cleanup. Duplicate a caller-owned descriptor before a helper takes ownership; never close the caller's descriptor implicitly.
- Preserve component-count, byte, depth, identity, regular-file, stable-read, no-follow, no-replace, and offline limits.
- Check a macOS root alias lexically and by exact link text and target identity; after that one root transition, open every remaining component relative to a descriptor with no-follow flags.
- Keep all existing path-root APIs and fixture formats compatible. The checked Goldfinch v0/v1 fixture, statement, release, and manifest bytes remain unchanged.
- Make macOS regression tests execute rather than skip, and keep the Linux suite green under the exact pin.

The issue explicitly authorises the smallest `.github/workflows/lazarus.yml` change needed for a macOS regression job if the durable runner is CI. Adding another workflow, changing permissions, changing unrelated matrices, or changing release automation still requires separate authority.

Non-goals and refusals:

- No Python pin, dependency, schema, evidence class, package version, skill version, evolution frontier, or producer argv change.
- No `Path.resolve()` of arbitrary statement ancestors, no general symlink allowlist, no path-only stage bridge, and no `shutil.copytree` staging fallback.
- No network capture, fixture regeneration, release restamping, Ariadne change, shared Promise Machine change, issue publication, branch publication, or controller receipt during study.
- No promise for non-macOS root aliases. On Linux and other systems, the existing no-follow root walk remains the contract.

## 4. Design options

The closed selection record is `.hexaemeron/design-evidence.json`; its ten reports are under `.hexaemeron/design-reports/`. It covers exactly one criterion for each required concern. `descriptor-root-alias` is the unique frontier.

### Candidate `descriptor-root-alias`: selected

Teach Lazarus's confinement helpers an explicit descriptor root. A helper duplicates the supplied directory descriptor, walks and lists with `openat`-style `dir_fd` calls and `os.scandir(fd)`, and closes only its duplicate. `component_claim`, `build_manifest`, `write_manifest`, and `verify_fixture` then consume the already-open `fixture_fd`; `_descriptor_directory` and the test skip disappear. Path-root callers retain their existing behavior through the same confined implementation.

For statements, retain the absolute descriptor walk. On Darwin only, if the first lexical component is exactly `var`, `tmp`, or `etc`, require the root entry to be a symlink whose link text is exactly `private/<name>`, open `private` and `<name>` beneath the root with no-follow directory flags, compare the opened target identity with the system alias target, and recheck the alias before continuing. Any mismatch refuses. All later components use the existing no-follow walk.

Trade: more confinement code must understand a descriptor root, so the implementation has more internal test surface. In exchange, there is no path materialisation, no path buffer, and renamed-path attacks cannot redirect the pinned stage.

### Candidate `canonical-path-reentry`: rejected

Use Darwin `fcntl(F_GETPATH)` to materialise the open stage, then call the existing path-based manifest and verifier functions. Resolve the statement path before `_read_statement` so `/var` becomes `/private/var`.

Trade: this is the smaller edit and the host mechanism exists, but it changes authority from an open inode to a namespace string. The design probes show a renamed directory name can be replaced and the materialised path then reads the replacement. General `Path.resolve()` also accepts a user-controlled symlinked parent. It therefore fails the compatibility and recovery hard gates even though it could make the happy paths pass.

Selection results: both candidates pass `host-mechanism`; the selected candidate passes `symlink-boundary` and `rename-recovery`, while path re-entry fails both. The selected candidate also uses zero pathname materialisations and zero path-buffer bytes; path re-entry uses one and 1,024 bytes. `unique-frontier` therefore selects `descriptor-root-alias` without a policy tie-break.

## 5. Risk register seed

```risk-register
stage-path-reentry | a pinned stage becomes a replaceable namespace path before manifest or verification | remove the descriptor-path bridge and prove every stage helper receives the open fixture descriptor
descriptor-ownership | a helper closes or mutates the caller-owned fixture descriptor | duplicate at the helper boundary and test caller descriptor identity and usability after success and refusal
alias-overreach | normalising macOS temporary paths silently accepts a user-controlled symlink ancestor | admit only exact Darwin root names and exact private targets, then keep no-follow for every remaining component
alias-drift | the root alias or its target changes between validation and open | bind link text and opened target identity and recheck before reading the statement
parent-identity | output parent replacement redirects writes or publication | retain existing device and inode rechecks around every source read, write, verification, and finalisation boundary
atomic-no-replace | a competitor at the destination is overwritten | retain renameat2 or renameatx_np exclusive publication and prove the competitor survives
rollback-cleanup | refusal deletes an unowned replacement or leaves a claimed-clean stage | retain quarantined descriptor cleanup with entry and depth bounds and guarded visible failure
test-skip | macOS reports green while the builder and race guards never execute | remove the traversable-descriptor-path skip and require zero unexpected skips in the structured runner
linux-drift | Darwin alias support changes ordinary Linux no-follow behavior | keep the current Linux workflow and run the complete Lazarus suite on both operating systems
fixture-byte-drift | a path repair changes the shipped fixture or release | rebuild to a fresh directory and compare every file byte-for-byte without editing checked artefacts
```

## 6. Glossary seeds

- **Descriptor root:** an already-open directory descriptor that is the authority for a confined tree operation.
- **Path materialisation:** converting an open descriptor back to a filesystem pathname, such as `F_GETPATH` or `/proc/self/fd`.
- **System root alias:** one exact root-level macOS symlink, verified as `/var`, `/tmp`, or `/etc` to its matching `private/*` target.
- **User-controlled ancestor:** any path component below the admitted system root transition; it remains subject to no-follow.
- **Identity:** the `(st_dev, st_ino)` pair used to prove an opened or named directory is still the intended inode.
- **No-replace publication:** one atomic rename that refuses when the destination name already exists.
- **Anchored cleanup:** bounded removal performed relative to open directory descriptors after inode rechecks.
- **Darwin regression runner:** exact Python 3.14.6 execution on macOS that runs both defects and emits durable structured results.

## 7. Sources

- Live issue `https://github.com/wildcat-finance/skills/issues/881`, read 2026-08-31; title, body, acceptance, and boundary. Its pull references #718 and #666 were unavailable through GitHub API (HTTP 404), so no remote body or comment was inferred.
- Git start `0987aa37f5110501b2c7a440f42370f81d58afe5`; local merge commits `4296f9f0b3eb03926d9b5b03258246dcab8c13ec` and `68039a8756e60c7aae97439d1cce616c09986a24`, including their second-parent diffs and commit bodies.
- `plugins/lazarus/examples/goldfinch-v1/demo.py:148-446` and `:449-644`; current identity, descriptor, cleanup, no-replace, path bridge, and build flow.
- `plugins/lazarus/tests/test_goldfinch.py:40-70` and the builder race tests; current platform skip and guarded invariants.
- `plugins/lazarus/scripts/lazarus_lib/paths.py`; current confined read/write primitives and path-only whole-tree listing.
- `plugins/lazarus/scripts/lazarus_lib/release.py:393-470`; current statement descriptor walk and bounded stable read.
- `.github/workflows/lazarus.yml` and `plugins/lazarus/tests/test_scaffold.py:304-369`; current Linux-only workflow and its pinned shell/toolchain contract.
- `plugins/lazarus/skills/lazarus/EVOLUTION.md`; current `lazarus-v2.2.0` and unrelated `empty-block-receipt-witnesses` frontier.
- `audit/AUDIT.md:3119-3725`; `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md`; and the fiat-386 and fiat-387 audit records and checked synopses named in item 2. `audit_synopsis.py --check .` exited 0 before reliance.
- Local macOS 26.5 manual pages `open(2)`, `rename(2)`, and `hier(7)`; Python 3.14.6 `os.supports_dir_fd`, `os.supports_fd`, `tempfile.gettempdir()`, and direct `stat`/`readlink` observations recorded by the design probes.
- `.hexaemeron/design-evidence.json` and `.hexaemeron/design-reports/*.json`; complete checked candidate matrix and exact selection commands.

## 8. Signals, and the questions behind them

There is no long-running service and no production telemetry to add. The required signals are build and test records because they answer the operator's actual questions:

- Did the builder execute on Darwin rather than skip? Record OS, architecture, exact Python, test count, skip count, exit, and Elenchus report digest.
- Did it reproduce the fixture? Record the rebuilt fixture digest plus a byte-for-byte tree comparison result; never infer equality from exit 0 alone.
- Did the default temporary statement path work? Record the lexical first component (`var`, without the private suffix), the exact accepted alias class, release verification exit, and no raw statement bytes.
- Did a hostile or changed path fail safely? Existing bounded `refused:` errors remain the public signal; guards must assert the destination, competitor, source, and displaced owned stage after refusal.
- Did Linux remain compatible? The existing Lazarus workflow and aggregate shard must both report green on the same commit as the Darwin result.

The macOS job or equivalent runner is the correlation boundary: one commit SHA joins interpreter, host, regression tests, complete suite, and fixture comparison. Do not add per-component metrics or filesystem paths to normal CLI output; they do not answer an on-call question and could expose private temporary names.

## 9. Boundaries, per capability

Phylax applies because both operations consume caller-controlled filesystem names.

- The output name may be hostile. Open and retain the parent descriptor, create stage entries with exclusive relative operations, check inode identity, and publish only with atomic no-replace.
- The source fixture is trusted only by its pinned digest and per-component claims. Read each source component once through confined descriptors and recheck the output parent around it.
- A caller-owned descriptor is a capability, not an integer pathname. Duplicate it before confined traversal; reject non-directory descriptors; never use `/proc`, `/dev/fd`, `F_GETPATH`, current working directory, or a mutable path to recover authority.
- The macOS root alias is OS-owned but still checked. Exact name, exact relative link target, root position, platform, target directory type, and target identity are all required. No nested alias or user-created symlink inherits this exception.
- The statement final component stays a bounded, stable, nonblocking regular-file descriptor. Parsed JSON and binding logic receive exactly the bytes read from it.
- Cleanup may remove only the stage inode it owns, through bounded descriptors. Identity disagreement or inability to clear is a visible failure, not permission to recurse through a name.
- CI receives no secrets or network authority. Fixture generation and verification remain offline.

## 10. The budget, or its absence

No wall-clock performance claim is made. The current command fails before a valid baseline can complete, the repair adds no network operation or data class, and fixture size is unchanged; inventing a latency target would not protect acceptance.

The bounded resource contract still holds: no extra whole-tree copy, no unbounded symlink resolution, no new traversal beyond the existing 8,192-entry and fixture byte caps, and only short-lived duplicated directory descriptors. The design-time Metron proxies are the checked `path-materialisations` and `path-buffer` reports: selected values are 0 and 0 bytes. If implementation introduces a measurable alternative, the exact same build command must be measured before and after on the same host with `/usr/bin/time -l`, but a timing comparison is not an entry gate for this repair.

## 11. The fail-closed posture

Every unsupported or changed condition refuses before publication: missing descriptor APIs, wrong descriptor type, alias mismatch, non-Darwin alias request, symlink below the admitted root, identity drift, oversize or unstable statement, existing destination, unavailable exclusive rename, cleanup identity drift, and incomplete test evidence. A recognized `/var` must not become a fallback to `resolve`; if its checked form differs, it is refused.

Elenchus guards are red on the exact base before repair and green after it. Extend `test_goldfinch.py` with an unskipped macOS build that compares every fixture file; extend `test_release.py` with the default `TemporaryDirectory` success case and exact hostile non-root symlink refusals; preserve all current parent-swap, write-swap, finalisation, no-replace, rollback, and cleanup guards. The source-owned command is:

```text
python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}
```

The report is `unittest-json-v1`. A valid report names the exact command and Python, is complete, records zero failures/errors/unexpected successes, and makes skips visible. The focused regressions must also be copied to the base for the Elenchus comparison; inability to make them fail for the named macOS causes is an inconclusive guard, not a pass.

## 12. Decisions and their homes

The selected candidate and rejected path-reentry alternative live immutably in `.hexaemeron/design-evidence.json` and its reports. That record is the design authority; this prose explains it.

The descriptor-root ownership rule belongs beside the confinement implementation in `plugins/lazarus/scripts/lazarus_lib/paths.py`, with executable ownership and rename guards in `plugins/lazarus/tests/test_paths.py` and `test_goldfinch.py`. A short code comment must explain why a descriptor is duplicated and why path materialisation would lose authority; comments should not restate mechanics.

The exact Darwin root-alias allowlist is an operator-visible security policy. Its home is the statement-walk helper in `release.py`, its hostile and valid cases in `test_release.py`, and the public preservation-release guide if the accepted path surface is documented there. Any future alias addition changes the trust boundary and requires a new decision, not a data-only edit.

The durable Darwin execution home is the existing Lazarus workflow if CI is used, with the workflow-shape assertion in `test_scaffold.py`; no new workflow is warranted. Fixture and release byte pins remain in their existing tests and artefacts.

No new ADR is required: the choice is local to Lazarus, reversible without a wire-format migration, and already held by the study plus checked design record. If a later change exports descriptor roots as a shared cross-plugin contract, Hypomnema must require an ADR at that boundary before code moves.

### Amendment -- 2026-08-31

**What changed.** `plugins/lazarus/examples/goldfinch-v1/demo.py` is both the builder that must change and a digest-bound component of the checked Goldfinch fixture and preservation release. Step 1 may update that canonical component and must rebuild every directly derived manifest and release binding in place under the same existing version. Every preserved source component other than the two checked `demo.py` copies remains byte-identical; there is no version bump, superseded copy, or retained bad artefact.
**Why.** Keeping the old digest bytes would require keeping the failing pseudo-FD builder, while changing the builder without rebuilding its bindings makes the checked fixture invalid. Digest-sealed evidence must describe the corrected same-version bytes rather than retain a known-bad prior state.
**Steps touched.** Step 1's Exit and Files; Step 3's Entry.
**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit holds. Step 3: entry broken; exit holds.
