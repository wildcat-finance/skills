# Study: controller currency guarantee

Assuming, unless corrected:

1. This is a generation run for Fiat. The held frontier job, [issue 363](https://github.com/wildcat-finance/skills/issues/363), is untouched. The run is pinned to `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at `fiat-v5.21.1` with 26 rows, so `done integrate` demands exactly one new valid row there. The expected identifiers are `fiat-v5.22.1` and, for the Kronos change, `kronos-v0.7.0`, but both are picked at the step that appends them, after re-reading the ledger, because concurrent runs take identifiers first.
2. Kronos is mature-but-terminal and takes generation rows; its ledger is not gated by this run's frontier pin. Both new rows retain their prior frontier revision and digest byte for byte, per `VERSIONING.md`.
3. Python 3 and the standard library remain the implementation boundary. The one new capability is a single network read at `init`, through the controller's existing bounded reader discipline: fixed argv, no shell, `GIT_TIMEOUT`, the output cap, credential prompts disabled, and no child output in any diagnosis.
4. The gate refuses only what it can prove. A pin that differs from the observed upstream head refuses; an unobservable pin or head records an explicit null and proceeds with a warning. Managed and in-repo routes never refuse.
5. The hexaemeron package version bumps from `1.5.9` so that `claude plugin update` copies this change; the bump lands on all five surfaces `tests/test_version_propagation.py` compares.
6. Every later local Fiat commit follows the permanent delivery rule: `git commit -S`, successful `git verify-commit`, and exactly one copy of each required Shoggoth trailer. The Surveyor phase creates no commit.
7. No dependency, no CI change, no state-version change. Runs recorded before this change stay loadable and verifiable without the new receipt.

## 1. Problem statement

A Fiat run is driven by whatever controller was installed when it started, and nothing in the run's evidence says which one that was. On 2026-08-24 this stopped being hypothetical on this machine: all fourteen wildcat-labs plugins were re-pinned at 17:18Z to commit `103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`, and roughly an hour later `origin/main` of `wildcat-finance/skills` stood 10 commits ahead of every pin, because Fiat and Kronos runs merge their own pull requests. `claude plugin update` reported `already at the latest version` at exit 0 while copying nothing, since it is gated on the version string in `.claude-plugin/plugin.json`, which that morning had not bumped for 12 of the 14 plugins whose bytes had changed. Only uninstall plus reinstall moves a pin. `stale_controller()` in `hexctl.py` compares ledger version strings against the possibly stale checked-in copy, warn-only on stderr, so a daisychained Kronos-to-Fiat loop executes a controller pinned before the chain started and the receipts cannot show it.

The working prototype is a controller currency guarantee with four parts:

1. A fail-closed pin-versus-upstream gate in `hexctl init`. When the running controller's recorded pin provably differs from the marketplace upstream head, `init` refuses by name, and an explicit waiver flag records the reason into the run's evidence, mirroring how a security suite is waived rather than skipped.
2. Controller provenance in the init receipt regardless of gate outcome: the controller's ledger version, the install route (`git-backed`, `managed`, or `in-repo-source`), the pinned `gitCommitSha` or an explicit null, the upstream head observed at init or an explicit null, the verdict, and any waiver reason.
3. A read-only `hexctl currency` subcommand reporting the same observation for every installed wildcat plugin, exiting 0 when nothing is behind, 3 while anything is, 1 on a refusal, so the Kronos loop gains a re-pin step at its rescan boundary: compare pins to upstream, reinstall what is behind through the host's own installer, refresh, re-resolve paths.
4. `references/plugin-currency.md` rewritten so the documented mechanism is the enforced one.

The demo path: in a hermetic fixture, an install fabricated behind its upstream head makes `init` refuse with a named error; the same `init` with the waiver flag proceeds and its receipt carries version, route, pin, observed head, verdict and reason; an in-repo checkout records `in-repo-source` with null pin and head and no refusal; `hexctl currency --json` over a fixture cache prints one row per plugin and exits 3 while one is behind. The focused proof is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
```

The repository proof is:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
```

## 2. Prior art

In the controller, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`:

- `stale_controller()` resolves its own `__file__`, reads its ledger's `Current version`, and compares it against any `plugins/*/skills/fiat/EVOLUTION.md` in the target, skipping the identity case where the target is the plugin's own source tree. It is version-string-blind in exactly the way `claude plugin update` is, and it warns rather than refuses.
- `remote_branch_tip()` is the in-controller precedent for the new read: bounded, no-shell `git ls-remote --refs origin <ref>` that accepts exactly one tab-separated full SHA with the expected ref name and refuses absent, duplicate or malformed output. The audit record for the delegation-packets run (I320-S3-R2-01, `audit/AUDIT.md`) closed on that parsing rule.
- `bounded_run`, `bounded_tool`, `bounded_tool_status` and `bounded_git` carry the reader discipline: fixed argv, no shell, `GIT_TIMEOUT` of 30 seconds, a 2 MiB output cap, and no child output in failures. `bounded_tool_status` exists for callers to whom a refusal is an answer.
- `WAIVER_PREFIX` and `is_waiver()` define the waiver pattern the gate mirrors: the `security_suite` receipt reads `"waived: <reason>"`, and a reason is the point of the string.
- `cmd_init` already refuses everything refusable before its first mutation, records the init transition with topic, base and run branch, and prints the `stale_controller` warning last. The gate joins the pre-mutation checks; the provenance joins the transition data.
- `cmd_record` already accepts a free-form `controller_version` receipt, which `references/plugin-currency.md` specifies for the case where an update cannot happen. One real run used it: the audit record at `audit/AUDIT.md` line 11977 shows a run driving installed `fiat-v5.14.1` against a repository holding `fiat-v5.15.1`, with the gap named in the receipt and the bootstrap consequence stated -- the field that run added could first be exercised by the run after the next update.

On the host, measured 2026-08-24: `~/.claude/plugins/installed_plugins.json` is `{"version", "plugins"}` with plugins keyed `<plugin>@<marketplace>`, each value a list of install records carrying `scope`, `installPath`, `version`, `installedAt` and `gitCommitSha`. The install path pattern is `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and that directory is the plugin root, so the registry sits two levels above `cache` and is derivable from the running controller's own `__file__` with no environment read. `~/.claude/plugins/marketplaces/wildcat-labs` is a full git clone whose `origin` is `https://github.com/wildcat-finance/skills.git` -- this host's marketplace was added from the public repository directly, so the private-mirror chain `plugin-currency.md` describes is a route the code must tolerate, not assume. All fourteen wildcat plugins are pinned to `08512d4ada7b1d7418e1af213be0d4b8c1494b6d` as of 18:18Z, which is also this run's starting SHA.

In the ledgers: `fiat-v4.5.1` introduced the init warning; `fiat-v4.6.1` turned the warning into the plugin-currency procedure, established the route distinction, and added the version-propagation check after Ariadne shipped `1.2.0` in two manifests and `1.1.0` in the third. That check is `tests/test_version_propagation.py`: the plugin's Claude manifest, its Codex manifest and the root marketplace listing must agree, the pinned `DELIVERY_PACKAGE_VERSIONS` map must match all three, and hexaemeron's version must also reach `.agents/plugins/marketplace.json` -- five surfaces for this plugin. `fiat-v4.7.1` added the `--frontier` row gate this run is pinned under.

The last two merged pull requests changing this area were read. [PR 585](https://github.com/wildcat-finance/skills/pull/585) (runbook amendment receipts, `fiat-v5.21.1`) carries forward issues 555, 556, 557 and 508; issue 556, dynamic target-version resolution for stale runbook literals, is adjacent and stays open -- this study answers it only by picking identifiers late. [PR 583](https://github.com/wildcat-finance/skills/pull/583) carries forward the shared `audit/AUDIT.md` overlap concern (issue 576) and two run-local deviations; none of its items is a controller-currency obligation. The audit records of the receipted-lint, delegation-packets and frontier-row-attribution runs were read for the bounded-reader and ledger-arithmetic rules cited above.

Outside the repository there is no portable pin registry to reuse: the registry file, the cache layout and the marketplace clone are Claude Code host behaviour, which is why the route detection must be observation, not convention.

## 3. Constraints and non-goals

The run starts from `main` at `08512d4ada7b1d7418e1af213be0d4b8c1494b6d`, on the run branch `fiat/controller-currency-guarantee`, in the worktree the controller created. Identifiers -- ledger versions, the ADR number, the package version -- are global but freeze locally at this sync, and concurrent runs collide on them, so each is chosen at the step that writes it after re-reading the tree, and integrate re-validates the one-new-row rule against the base.

The gate's honest contract is currency at init, recorded, not currency for the run's duration: upstream can advance mid-run and the receipt does not chase it. The bootstrap property is stated plainly wherever the change is described: this gate ships inside the artifact it gates, so it cannot govern the run that writes it; it governs every run after the next re-pin.

Non-goals: a self-updating controller (the reinstall stays with the host's installer and the agent driving it); an ancestry proof that fetches into the marketplace clone; refusing on an unknown verdict; changing `stale_controller()`'s repo-copy warning semantics; mid-run currency monitoring; publishing or syncing the private mirror; new fields in `kronos.py`'s scoreboard schema; validating receipts of runs recorded before this change.

**Always.** Both test suites before a commit; the imprimatur lint on every shipped document; the three tree lints; `git diff --check`; the signed-commit and GitHub-verification rules Fiat already enforces; regenerate the horos boundary last if any changed file is classified.

**Ask first.** Adding a dependency; any second network call from init; changing state version, receipt shape, exit-code policy or CI; reading any path outside the derived plugins root and the target.

**Never.** Echo raw `ls-remote` output, URLs with credentials, or registry bytes in a diagnosis or receipt; take the remote URL from the target repository; hand-edit a plugin cache; delete a failing test; claim a command ran when it did not.

## 4. Design options

### Option A: strengthen the procedure, change no code

Rewrite `plugin-currency.md` and the preflight step to demand the pin check. Cheapest to build, and it is the option the repository already took at `fiat-v4.6.1`; the measured 2026-08-24 failure happened under it. A procedure the controller does not enforce leaves no trace when skipped, which is the original hole. Rejected.

### Option B: route-aware observation in the controller, refusal only on proof (chosen)

One observation function resolves the controller's own `__file__`, matches it against `installPath` prefixes in the registry derived from that same path, classifies the route, reads the pin, and -- on the git-backed route only -- reads the upstream head with one bounded `git ls-remote` against the origin URL taken from the marketplace clone's own config. `cmd_init` calls it before any mutation: verdict `behind` refuses by name unless `--controller-currency-waiver '<reason>'` is passed; `current`, `no-pin` (in-repo), `managed` and `unknown` proceed; every outcome lands in the init transition and receipts. `hexctl currency` exposes the same observation for all installed wildcat plugins, and the Kronos loop's step 8 runs it at the rescan boundary and reinstalls what is behind before the next ranking. The seam between observation and process boundary is injectable, so every hostile fixture runs without a network or a real install.

The trade: init gains a network read and refuses runs that yesterday started silently, and the guarantee is only as strong as the network -- an attacker or an outage that blanks the read downgrades the verdict to `unknown`, which proceeds. The receipt keeps that visible rather than closed. This is the cheapest construction that meets the problem statement, because both the parsing rule and the waiver pattern already exist in the file the change lands in.

### Option C: ancestry proof before refusing

Fetch upstream into the marketplace clone and require `merge-base --is-ancestor <pin> <head>` before saying `behind`. Distinguishes behind from rewritten history, but init then mutates shared host cache state outside the run, adds a second network operation, and the distinction it buys is rare on a protected default branch. The verdict wording carries the residual ambiguity instead: `behind` means the pin differs from the observed head. Rejected for surface and comprehension cost.

### Option D: the controller updates itself

Have `init` shell out to `claude plugin uninstall` and `install` when behind. The controller would replace its own bytes underneath a running process, the CLI may prompt, the managed route cannot do it at all, and `plugin-currency.md` already rules that updates go through the host's installer with the agent driving. Rejected.

## 5. Risk register seed

```risk-register
upstream-read-surface | the argv of the one new git ls-remote at init | fixed argv, no shell, prompts disabled, GIT_TIMEOUT and the output cap, and no child output in any diagnosis
url-source-confusion | where the remote URL comes from | the URL is read from the marketplace clone's config under the plugins root derived from the controller's own file, and no target-repository value can reach the call
registry-hostile-input | installed_plugins.json bytes | a missing, malformed, wrong-kind or oversized registry yields route and pin unknown with a named warning, never a traceback
route-misdetection | mapping the controller file to a route | installPath prefix match decides installed, the controller's own git worktree decides in-repo, and an unmatchable path records unknown rather than guessing
verdict-honesty | behind versus unknown | a pin differing from an observed head refuses as behind, an unobservable pin or head records an explicit null and proceeds with a warning, and the two verdicts never merge
waiver-visibility | the refusal's escape hatch | a waived init records verdict behind and the reason in the receipt, and no flag silences the gate without a ledger trace
secret-echo | diagnostics and receipts from the network read | no raw ls-remote output, credentialed URL or registry value appears in any message, transition or receipt
bootstrap-limit | the run that ships the gate | every surface describing the change states it governs runs after the next re-pin, never the run that wrote it
ledger-arithmetic | the fiat and kronos generation rows | exactly one new fiat row passes the integrate gate and both rows retain their prior frontier revision and digest byte for byte
version-propagation | the five surfaces naming the hexaemeron package version | tests/test_version_propagation.py passes after the bump, including the pinned delivery map
repin-partiality | the Kronos rescan boundary | the currency report covers every installed wildcat plugin, the reinstall covers everything behind, and the next init receipt evidences the new pin
state-compat | runs recorded before this change | load_state, status and verify accept state without the new receipt, and only new inits owe it
```

The Warden should press hardest on `upstream-read-surface`, `url-source-confusion`, `verdict-honesty` and `registry-hostile-input`: the first two are the new phylax boundary, the last two are where a wrong answer recreates the silent hole with a receipt on top.

## 6. Glossary seeds

| Term | Meaning | Boundary |
| --- | --- | --- |
| Pin | The `gitCommitSha` the host registry records for an installed plugin. | Absent on the managed route; nonexistent on the in-repo route. |
| Upstream head | The default-branch SHA one bounded `ls-remote` against the marketplace origin observed at init. | An observation at one moment, not a lease for the run. |
| Route | How the running controller arrived: `git-backed`, `managed`, or `in-repo-source`. | Decided by observation of the controller's own path, never assumed. |
| Verdict | `current`, `behind`, `no-pin`, `managed`, or `unknown`. | Only `behind` refuses; `unknown` is never promoted to either side. |
| Waiver | The named reason a behind verdict was overridden at init. | Recorded evidence, not permission to stop checking. |
| Re-pin boundary | The Kronos step-8 point where pins are compared and reinstalls happen before the next ranking. | Restores currency between runs, not during one. |

## 7. Sources

- Exact start: `main` at `08512d4ada7b1d7418e1af213be0d4b8c1494b6d`; run state pins `fiat-v5.21.1`, 26 rows.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: `stale_controller`, `cmd_init`, `cmd_record`, `remote_branch_tip`, `bounded_run`, `bounded_git`, `WAIVER_PREFIX`, `is_waiver`, `LEDGER_ROW`.
- `plugins/hexaemeron/skills/fiat/references/plugin-currency.md` and `SKILL.md` preflight step 3.
- `plugins/hexaemeron/skills/VERSIONING.md`; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` rows `fiat-v4.5.1`, `fiat-v4.6.1`, `fiat-v4.7.1`; `plugins/hexaemeron/skills/kronos/EVOLUTION.md` and `SKILL.md` step 8.
- `tests/test_version_propagation.py`, `plugins/hexaemeron/tests/run_tests.py`, `plugins/hexaemeron/tests/test_hexctl.py`.
- `audit/AUDIT.md`: the `controller_version` lead at line 11977 and the I320-S3-R2 `ls-remote` parsing record.
- [PR 585](https://github.com/wildcat-finance/skills/pull/585) and [PR 583](https://github.com/wildcat-finance/skills/pull/583), the last two merged pull requests touching this area, carried-forward sections read.
- Host state measured 2026-08-24: `~/.claude/plugins/installed_plugins.json`, `~/.claude/plugins/cache/wildcat-labs/hexaemeron/1.5.9/`, `~/.claude/plugins/marketplaces/wildcat-labs` (origin `https://github.com/wildcat-finance/skills.git`, HEAD `08512d4`), fourteen plugins pinned to `08512d4`; the 17:18Z pin to `103fa90` and the 10-commit gap an hour later, from the maintainer's measurement the same day.

## 8. Signals, and the questions behind them

The controller is invoked from a terminal and does not run unattended; exit status, stderr and the receipts are the signals, and no log, metric or alert surface is added. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) stays the signal-content authority.

1. "Which controller drove this run?" The init transition and receipt carry version, route, pin, observed head, verdict and waiver, readable later from `status` and the ledger.
2. "Why did init refuse?" The named refusal on stderr states the pin, the observed head, and the two exits: re-pin through the host's installer, or pass the waiver flag with a reason.
3. "Did the loop restore currency?" `hexctl currency` exits 3 while anything is behind, and the next run's init receipt shows the pin the reinstall produced.

## 9. Boundaries, per capability

The network boundary is new: one `git ls-remote` from init, on the git-backed route only. What is worth taking at it is a spoofed or stalled answer that flips a verdict. The controls: the URL comes from the marketplace clone's config under the derived plugins root, never from the target repository or an environment variable; the call is argv-only with prompts disabled, time-capped and output-capped; anything but exactly one well-formed ref line is `unknown`, not `current` and not `behind`.

The filesystem boundary widens to two host reads: the registry and the marketplace clone config, both located relative to the controller's own resolved file. Hostile bytes at either read to `unknown` with a named warning. No path from either file is followed outside the plugins root.

The receipts boundary: provenance values are copied into state as bounded scalars -- version strings, 40-hex SHAs, route and verdict enums, one reason string -- never raw command output. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; this section feeds item 5 rather than replacing it.

## 10. The budget, or its absence

None, and here is why: no performance claim is made. Init gains at most one network call bounded by `GIT_TIMEOUT` at 30 seconds, so the worst offline cost is one timeout wait before an `unknown` verdict, stated in the docs rather than measured. If implementation acquires a performance claim, [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) defines the measurement first.

## 11. The fail-closed posture

A `behind` verdict stops `init` with exit 1 and a named refusal before any worktree, state, ledger or breadcrumb exists, the same pre-mutation position every other init refusal holds. The waiver is the only way past it, and the waiver is a recorded reason, not a silence. Unknown never refuses and never claims currency; it records nulls and warns.

Each behaviour begins as a guard in the [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) convention: build the fixture, capture the pre-fix behaviour red -- today `init` starts silently under a fabricated behind pin -- then assert the named refusal, the waiver path, the receipt fields and the unchanged tree, and prove the guard fails when the gate call is removed. Hostile fixtures cover the missing, malformed and wrong-kind registry, the timeout, the malformed `ls-remote` line, and route misdetection across all three routes.

## 12. Decisions and their homes

Expensive to reverse: init observing the network at all, the refuse-only-on-proof rule, and the verdict vocabulary in receipts. Those go in one ADR under `docs/decisions/`, its number chosen when it is written. The behaviour change lands as one `fiat` generation row and one `kronos` generation row, each retaining its frontier revision and digest byte for byte. The operating procedure lives in `references/plugin-currency.md`, rewritten to describe the enforced mechanism; `SKILL.md` preflight step 3 and the Kronos step-8 text point at it rather than restating it. The suite-wide prose cold read before integration is owed by `VERSIONING.md`, and the run-level pull request body carries what stays open. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) remains the record-placement authority.

The recommended runbook is four steps: publish the accepted study and runbook; the observation core, init gate, waiver and receipt with their tests and the fiat ledger row; the `currency` subcommand, the Kronos re-pin step and its ledger row; the documentation, manifest bump across the five version surfaces, and the demonstration from item 1.
