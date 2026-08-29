# Study: bind the integrate gate to the sync receipt's recorded base head

Assuming, unless corrected:

1. This is a generation run for Fiat. The held frontier job, [issue 363](https://github.com/wildcat-finance/skills/issues/363), is untouched. The run is pinned to `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at `fiat-v5.24.1` with 29 rows (state sha256 `19ed2bc967d1e9ec310e0d0fdb5c3df26ea065486c2fdba5442569209db4da03`), so `done integrate` demands exactly one new valid row there. The expected identifier is `fiat-v5.25.1`, picked at the step that appends it after re-reading the ledger, because concurrent runs take identifiers first. The row retains the frontier revision `state-shape-validation` and its digest byte for byte, and `SKILL.md` frontmatter moves with it.
2. Python 3 and the standard library remain the implementation boundary. No dependency, no CI change, no state-version change, and no new capability: the fix re-points an argument to a bounded read the controller already performs.
3. The hexaemeron package version moves from `1.6.0` to `1.6.1` on all five surfaces `tests/test_version_propagation.py` compares, so `claude plugin update` copies the fix. Patch rather than minor: this restores behaviour a shipped row already promised, and PR 607's carried-forward lead says the minor-versus-patch choice is unpoliced, so the modest reading is taken and recorded here.
4. This run executes under the installed `fiat-v5.24.1` controller, which carries the defect being fixed. The bootstrap consequence is stated in item 3 of this study.
5. Every later local commit follows the permanent delivery rule: `git commit -S`, `git verify-commit`, one copy of each required Shoggoth trailer. The Surveyor phase creates no commit.
6. The tracked copies of this study and the runbook go to `docs/fiat-integrate-receipt-binding-study.md` and `docs/fiat-integrate-receipt-binding-runbook.md`, following the parent run's placement.

## 1. Problem statement

`done integrate` computes its published-row subtraction as `base_ledger_versions(args.dir, recorded_sync.get("base_commit"), frontier["ledger"])` (`hexctl.py:3925` at the starting SHA), while `done_sync_run` records the merged base tip under `"base_head"` (`hexctl.py:3855`). No sync receipt anywhere carries a `base_commit` key, so the getter always passes `None`, `base_ledger_versions` returns the empty set by design, and the subtraction introduced for [skills#466](https://github.com/wildcat-finance/skills/issues/466) at `fiat-v5.16.1` has never engaged on any run. The failure is silent until it is terminal: the controller-currency run (run branch `fiat/controller-currency-guarantee`) absorbed the base's `fiat-v5.22.1` and `fiat-v5.23.1` rows byte for byte in its one receipted sync (merge `8a6b4d6f651fb63fe200996acc328c17bcc05b46`, base tip `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, three green revalidation checks), appended its own `fiat-v5.24.1`, and was refused at its final receipt with "gained 3 history row(s)" after [PR 607](https://github.com/wildcat-finance/skills/pull/607) had already merged and verified. That run is halted with this reason on its ledger. Every concurrent-frontier run that absorbs published rows in a sync is refused the same way, which is the exact second-of-two-runs fault `fiat-v5.16.1` exists to prevent. [Issue 608](https://github.com/wildcat-finance/skills/issues/608) is the authoritative defect statement, and this run closes it at integrate.

The working prototype is the binding, guarded: the receipt key is named once, in a shared module-level constant both `done_sync_run` and `done_integrate` use, so the writer and the reader cannot disagree again; and a regression suite drives the controller-currency topology end to end through the CLI -- a frontier-pinned run whose one receipted sync absorbs published base rows, plus one own row -- and requires `done integrate` to pass with `receipts.integrate.frontier_subtracted_rows` naming the absorbed versions. That suite fails on the current tree and would have caught the defect at `fiat-v5.16.1`.

The focused proof:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl_frontier_receipt -v
```

The repository proof:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
```

## 2. Prior art

In the controller, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at `c4650f02`:

- `done_sync_run` (line 3751) validates `--base-commit` against the remote base tip and the sync merge's second parent, then writes the receipt keys `commit`, `base`, `starting_base`, `base_head`, `parents`, `github_verified`, `product_evidence`, `revalidation`. The first sync receipt writer ever shipped (merged in `334aa98e`, 2026-08-21) stored exactly `commit`, `base_head`, `parents`, `github_verified`; later commits (`123a380a`, `9db8a350`, `2693dfcb`) added the other keys. `base_head` has been the base-tip key in every receipt any shipped controller wrote.
- `done_integrate` (line 3896) derives `published` from the recorded sync (line 3924), feeds it to `frontier_close_fault`, and records `frontier_subtracted_rows` in the terminal receipt (line 3989). The reader was introduced in `332c58e8` (2026-08-24), three days after the writer, asking for `base_commit`.
- `base_ledger_versions` (line 1698) refuses a non-commit argument with `COMMIT_RE` and returns the empty set, silently and by design: "an unreadable or unparsable blob returns the empty set, which leaves the gate on its older and stricter arithmetic". The fail-closed side is correct and stays; the defect is that the healthy side never receives the evidence.

The git-history question this study had to settle: whether any shipped writer ever stored `base_commit`, which decides whether the fix needs a fallback for archived states. It did not. A fixed-string sweep for the literal dict key `"base_commit":` over every blob of `hexctl.py` in every commit on every ref (74 commits touch the file; `git log --all`) finds none. `git blame` agrees: the writer line `"base_head": base_tip` predates the reader by three days. The halted run's live state confirms the shipped shape -- its sync receipt carries exactly the eight keys above, `base_head` equal to `0f835d5f...`, and `revalidation.base_after` holding the same SHA. A plain key correction therefore suffices; no archived state anywhere needs a fallback.

How the defect survived three gates is the lesson the fix construction answers. The `fiat-v5.16.1` study asserted the key as fact in its prior art -- "`done_sync_run` already records the exact remote base commit the run merged, in `state["integrate"]["sync"]["base_commit"]`" (`plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md:59`) -- and the implementation followed the study. The twelve unit tests in `FrontierRowAttributionTests` (`test_hexctl.py:5397`) pass `published` directly or call `base_ledger_versions` with a real SHA, so they prove the arithmetic and the fallback while bypassing the receipt; all twelve pass today (re-run for this study) with the wiring broken. The audit record (`audit/AUDIT.md`, "Fiat frontier row attribution", lines 11931 and 11994) dispositioned `base-read-failure` clean by testing the fallback three ways, and its "Leads not pursued" recorded that the run shipping the field could not exercise it -- the installed controller predated it -- so "a run under a controller carrying `fiat-v5.16.1` is the first that can". The first run that could was the parent, and it halted. This is the third iteration of the same gate's lesson: [skills#443](https://github.com/wildcat-finance/skills/issues/443) fixed the anchor, skills#466 fixed what is counted after it, and this run fixes where the evidence is read from.

The last two merged pull requests changing the controller were read. [PR 607](https://github.com/wildcat-finance/skills/pull/607) (controller currency, `fiat-v5.24.1`): its carried-forward items are currency-scoped and stay open, except the minor-versus-patch lead, which assumption 3 answers by example; the halt itself postdates that PR's body, so issue 608 and the halted ledger carry it, not the pull request. [PR 602](https://github.com/wildcat-finance/skills/pull/602) (bound step merge, `fiat-v5.23.1`): its retarget-drift lead is open and is not this run's subject. The per-run audit records `audit/rounds/fiat-576-*.md` and `audit/rounds/fiat-594-*.md` were read; neither carries an integrate-arithmetic lead.

In the tests: `HexctlCase` (`test_hexctl.py:108`) drives the CLI with a real origin checkout plus fake delivery tools (`fake_refs`, `fake_parents`, `FAKE_GIT_DIFF_PATHS`), and `prepare_run_sync`, `write_integration_revalidation` and `write_run_pr` already carry a run from sync to integrate. `FrontierRowAttributionTests` already commits a ledger in the fixture repository and reads it back with real `git show` through `base_ledger_versions`, so the end-to-end regression needs no new fixture machinery, only the join. `test_hexctl_currency.py` is the file-boundary precedent: `test_hexctl.py` is cited as authored law by the Promise Machine, whose bounded read refuses a contract over 262,144 bytes, and the file stands at 251,357.

## 3. Constraints and non-goals

The run starts from `main` at `c4650f02a979e859ce36374779eac9cd70744288`, on run branch `fiat/608-bind-the-integrate-gate-to-the-sync-receipt`, in the worktree the controller created. Identifiers -- the ledger version and the package version -- are global but freeze locally at a sync, so each is chosen at the step that writes it after re-reading the tree.

The bootstrap property applies to this run exactly as it did to the parent: the fix ships inside the controller it fixes, so it cannot govern this run's own integrate. The running `fiat-v5.24.1` controller carries the broken reader; if the base publishes fiat ledger rows mid-run and this run's one permitted sync absorbs them, this run is refused at integrate the same way and recovers by the same halt-resume route. The run is short and the window is small, so the likelihood is low, but the risk is named rather than assumed away.

The audit record home changed since the parent run: `init` now derives a per-run file ([skills#576](https://github.com/wildcat-finance/skills/issues/576), ADR-025), and this run's state names it -- `audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md`. `audit/AUDIT.md` keeps its bytes and takes no new rounds.

Non-goals:

- Recovering the halted controller-currency run. That happens after this run integrates and the fleet re-pins: the operator resumes the run in its own clone (`hexctl resume`), re-runs `done integrate --pr-url https://github.com/wildcat-finance/skills/pull/607 --merge-commit c4650f02a979e859ce36374779eac9cd70744288`, and only then deletes its branches, because integrate reads the remote run branch tip. The remote branch still stands at the sync commit `8a6b4d6f` (verified by `ls-remote` for this study), so the receipt can be written under the fixed controller. It is out of this run's exit criteria because the receipt lives in that run's state, in that run's clone, under the operator; this run only makes the fixed controller installable.
- Renaming the receipt key or reshaping the receipt. `base_head` is the shipped shape; the halted run's receipt is already on disk with it.
- Changing `base_ledger_versions`' fail-closed contract. An unreadable blob or a missing key still subtracts nothing.
- Superseding the halted run's sync instead of fixing the reader. Supersession requires a new signed merge that moves the remote tip, and PR 607 has already merged against tip `8a6b4d6f`; `done integrate` checks the pull request head against that tip, so a writer-side repair strands the run permanently.
- Touching the kronos or any other ledger, the retarget-drift lead from PR 602, or issue 556's dynamic literals.

**Always.** Both test suites before a commit; the imprimatur lint on every shipped document; the three tree lints; `git diff --check`; the signed-commit and GitHub-verification rules Fiat already enforces; refresh the six `hexctl.py` digest pins in `tests/promise_machine_coverage.json` with any controller byte change; regenerate the horos boundary last and only on drift.

**Ask first.** Adding a dependency; changing the receipt shape, state version, exit-code policy or CI; adding bytes to `test_hexctl.py` beyond its bounded-read headroom.

**Never.** Run `hexctl` against this repository from inside the delivery steps except as the controller directs; edit the halted run's clone or state; delete a failing test; claim a command ran when it did not.

## 4. Design options

### Option A: read `base_head` outright

Change the reader to `recorded_sync.get("base_head")`. The smallest edit, and the history shows no fallback is needed. The trade: the key name keeps living twice, seventy lines apart, and the two sites drifted once already -- the reader was written three days after the writer, from a study assertion nobody measured. A future receipt reshape can recreate the fault, and only the regression suite would notice. Rejected in favour of removing the drift class rather than watching for it.

### Option B: fallback chain

Read `base_head`, fall back to `base_commit`. The fallback's second branch is unreachable in every state that exists -- the blob sweep proves no writer ever produced the key -- so it is dead code in a gate, and it teaches the next reader that such states exist. Rejected.

### Option C: one shared constant for writer and reader (chosen)

A module-level `SYNC_BASE_HEAD_KEY = "base_head"` beside the controller's other receipt constants; `done_sync_run` writes the dict with it and `done_integrate` reads with it. The trade: a dict literal with a variable key reads one step less directly at each site. What it buys is that the defect class becomes unrepresentable -- the two sites cannot name different keys -- and the constant gives the regression suite a stable handle. After a fault that survived a study assertion, twelve unit tests and a clean audit disposition, and surfaced only on the first live run able to exercise it, prevention is the cheapest construction that meets the problem statement.

### Option D: the writer records `base_commit` beside `base_head`

Fixes future engagement and duplicates one SHA under two names in every receipt from now on. Decisive against it: the halted run's receipt is already written with the old shape, its sync cannot be re-run (one permitted sync; supersession moves the remote tip PR 607's merge check pins), so a writer-side fix leaves the demonstrated failure unrecoverable. Rejected.

## 5. Risk register seed

```risk-register
receipt-key-drift | the key name shared by the sync receipt writer and the integrate reader | one constant names the key, both sites use it, and the end-to-end regression fails if either site stops consuming it
ledger-arithmetic | the one-new-row gate this run is itself pinned under | exactly one new fiat row passes frontier_close_fault against the 29-row pin, retaining the frontier revision and digest byte for byte
version-propagation | the five surfaces naming the hexaemeron package version | tests/test_version_propagation.py passes after the 1.6.1 move, including the pinned delivery map
state-compat | states whose sync receipts predate this change | every shipped receipt carries base_head, verified across all 74 hexctl.py blobs; a receipt missing the key still reads as the empty set and keeps the stricter arithmetic, with a regression asserting it
bootstrap-limit | this run's own integrate under the unfixed 5.24.1 controller | the risk and its halt-resume recovery are stated here and in the pull request body, and the run syncs only if the base forces it
digest-pin-refresh | the six hexctl.py sha256 pins in tests/promise_machine_coverage.json | scripts/promise_machine.py check passes after the pins are refreshed for the changed controller bytes
test-cap | the Promise Machine's 262,144-byte bounded read over test_hexctl.py | the new suite lands in its own module importing the shared harness, and test_hexctl.py stays under the cap
```

The Warden should press hardest on `receipt-key-drift` and `state-compat`: the first is the defect class itself, and the second is where an over-eager fix could break the exact receipt the recovery depends on. The audit rounds will waive the bundled Solidity suite for the same recorded reason the attribution run did: the steps change a Python controller and its tests.

## 6. Glossary seeds

| Term | Meaning | Boundary |
| --- | --- | --- |
| Sync receipt | The `integrate.sync` record `done_sync_run` writes: the merge, its parents, the base tip, product evidence and revalidation. | Written at most once, superseded only by a new signed merge. |
| Base head | The exact remote base tip the sync merged, validated against the remote and the merge's second parent, stored under `base_head`. | The only evidence separating this run's rows from published ones. |
| Published set | The row versions the base ledger already carried at the recorded base head, read back by `base_ledger_versions`. | Empty on any read failure, which keeps the stricter arithmetic. |
| Receipt join | The point where `done_integrate` feeds the sync receipt's base head into the published-set read. | The seam that drifted; the shared constant now names it once. |
| Frontier pin | The ledger, row count, sha256 and init-time version a run is charged against. | This run: 29 rows at `fiat-v5.24.1`. |
| Subtraction | Discounting published rows so a run is charged for its own rows and no others. | Visible afterwards in `receipts.integrate.frontier_subtracted_rows`. |
| Bootstrap limit | A controller fix governs runs under the next re-pin, never the run that ships it. | Named per surface; it is why the parent halted after its own merge. |

## 7. Sources

- Exact start: `main` at `c4650f02a979e859ce36374779eac9cd70744288`; run state pins `fiat-v5.24.1`, 29 rows; task issue [skills#608](https://github.com/wildcat-finance/skills/issues/608), closed at integrate.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: `done_sync_run` (3751, writer dict at 3851), `done_integrate` (3896, reader at 3924, receipt at 3989), `base_ledger_versions` (1698), `frontier_close_fault` (1756), `frontier_rows_after_anchor`, `frontier_subtracted_rows`, `COMMIT_RE`.
- History: writer key first shipped in `334aa98e` (2026-08-21); reader introduced in `332c58e8` (2026-08-24, `fiat-v5.16.1`); `git blame` on both lines; fixed-string sweep for `"base_commit":` over all 74 `hexctl.py` blobs on every ref, zero hits.
- The halted run, measured live for this study: `/Users/c0rtexzer0/Documents/GitHub/skills-fiat-controller-currency/tmp/fiat/fiat-controller-currency-guarantee/.hexaemeron/state.json` -- sync keys as listed above, `base_head` `0f835d5f...`, halt reason naming this defect; remote branch `fiat/controller-currency-guarantee` at `8a6b4d6f` via `ls-remote`.
- `plugins/hexaemeron/docs/fiat-frontier-row-attribution/study.md` (the wrong-key assertion at line 59) and `runbook.md`; `audit/AUDIT.md` lines 11931 and 11994; `audit/rounds/fiat-576-*.md` and `fiat-594-*.md`.
- [PR 607](https://github.com/wildcat-finance/skills/pull/607) and [PR 602](https://github.com/wildcat-finance/skills/pull/602), the last two merged pull requests touching the controller, carried-forward sections read.
- `plugins/hexaemeron/skills/VERSIONING.md`; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` rows `fiat-v5.16.1` and `fiat-v5.24.1`; `plugins/hexaemeron/skills/fiat/references/audit-loop.md`; `tests/test_version_propagation.py`; `tests/promise_machine_coverage.json` (six `hexctl.py` pins, currently `58e56fd1...`); `plugins/hexaemeron/tests/test_hexctl.py`, `test_hexctl_currency.py`, `run_tests.py`; `docs/fiat-controller-currency-study.md` and `-runbook.md` for placement and register.

## 8. Signals, and the questions behind them

The controller runs from a terminal; exit status, refusal text and receipts are the signals, and no log, metric or alert surface is added. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) stays the signal-content authority.

1. "Did the subtraction engage on this integrate?" `receipts.integrate.frontier_subtracted_rows` lists the exact discounted versions, and an empty list means nothing was published, not that the read failed silently -- the regression pins the difference.
2. "Why was an integrate refused?" The fault string names the rows gained "after subtracting N already published in the recorded base", and with the fix that count comes from the recorded base head rather than a key that never existed.
3. "Which base did the gate read?" `integrate.sync.base_head` in state and `status`, the same SHA the sync receipt validated against the remote.

## 9. Boundaries, per capability

None open, and here is why: the change re-points an argument to a read that already exists. `base_ledger_versions` keeps its `bounded_run` discipline -- fixed argv, no shell, output cap, empty set on any failure -- and the value now reaching it is `base_head`, which `done_sync_run` validated against the observed remote base tip and the sync merge's second parent before writing, and which state-edit laundering checks already guard. What is worth taking at the seam is a forged base head that excuses foreign rows, and the control is that the receipt cannot be written without the remote agreeing nor edited without the receipt chain refusing. [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules; this section feeds item 5 rather than replacing it.

## 10. The budget, or its absence

None, and here is why: no performance claim is made. The fix reads one dict key instead of another and the regression suite adds ordinary unit-test time. If implementation acquires a performance claim, [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) defines the measurement first.

## 11. The fail-closed posture

The gate's posture does not change; the fix makes the recorded evidence reach it. A missing or malformed key still reads as the empty set and the older, stricter arithmetic; a refusal still halts the run with the reason on its ledger. Each new behaviour begins as a guard in the [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) convention: build the controller-currency topology in fixture, capture the pre-fix behaviour red -- today `done integrate` refuses with "gained 3 history row(s)" against a receipt whose `base_head` names a base carrying both published rows -- then assert the pass, the subtracted-rows receipt, the key-set pin on the sync receipt, and the empty-set fallback for a receipt without the key, and prove the guards fail against the unfixed reader.

## 12. Decisions and their homes

No new ADR, and here is why: the expensive decision -- subtract published rows using the sync's recorded base -- was made at `fiat-v5.16.1` and its record stands in the attribution study and ledger row; this run corrects the read to match that record. The homes: the shared constant carries a comment naming both consumers; the tracked study and runbook copies land in `docs/`; the `fiat-v5.25.1` ledger row and `SKILL.md` frontmatter carry the behaviour change; issue 608 closes at integrate; the pull request body carries the recovery contract for the halted run and anything left open. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) remains the record-placement authority.

The recommended runbook is three steps: publish the accepted study and runbook; the shared-constant fix with the regression module `plugins/hexaemeron/tests/test_hexctl_frontier_receipt.py`, the six refreshed digest pins, and the `fiat-v5.25.1` row with matching frontmatter; the `1.6.1` package move across the five version surfaces and the demonstration from item 1.
