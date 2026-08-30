## Step 1, round 1 -- 2026-08-30T06:34:53Z

Audit schema: fiat-audit-round/v2

Covered: generator-output-escape=reviewed; suite-coverage-loss=reviewed; authored-file-loss=reviewed; publish-unverified=not-applicable; stale-destination=not-applicable; workflow-drift=not-applicable; token-scope=not-applicable; broken-install-window=not-applicable

Not checked: the five not-applicable concerns all sit on the destination repository and its scheduled job, which step 2 builds. Nothing in this step publishes, schedules or holds a token. Also not checked: whether a package this generator writes installs through the skills CLI. The generated tree verifies itself offline here; no `npx skills add` was run against a published repository, and step 2 owns that proof.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `scripts/portable_promise_machine.py` | `package --out` called `shutil.rmtree` on whatever stood at the destination before writing, so naming a populated directory destroyed its contents and exited 0. Driven against a throwaway tree holding one file: the file was gone and the command reported success. The four refusals already driven covered paths that should be rejected, not a directory that should be left alone, and the phylax lint exited 0 on the file both before and after. | fixed and guarded in 69b3180c850d3ddd09ccfaf547b53951f6b13dd9 |
| S1-R1-02 | low | `scripts/portable_promise_machine.py` | `_checked_output` carried `parent.resolve() != parent`, comparing an already-resolved path against its own resolution. The branch could never be taken, and it read as a symlink guard that was not one. | removed in the same commit |

Leads not pursued: the marker test treats any directory carrying `.agents/skills/promise-machine/runtime/MANIFEST.json` as one this generator wrote, so a directory a person assembled with that path inside it would still be cleared; the manifest is a generated artefact nobody writes by hand, and the alternative is a sentinel file that adds a path with no other purpose. `_package_bytes` reads every source into memory before writing, holding about 21 MB at once; that is bounded by the payload the generator already builds the same way in `expected_files`, and no caller streams it. The generated `README.md` names the source commit but nothing signs it, so a package cannot prove which commit it came from against a hostile publisher; the destination is written only by its own job, and proving publisher authenticity is outside this run and outside ADR-040's boundary. The three lints exit 0 and the runner contract reports 741 of 741, up from the 740 on the step branch by the guard this round adds.

## Step 1, round 2 -- 2026-08-30T06:38:00Z

Audit schema: fiat-audit-round/v2

Covered: generator-output-escape=reviewed; suite-coverage-loss=reviewed; authored-file-loss=reviewed; publish-unverified=not-applicable; stale-destination=not-applicable; workflow-drift=not-applicable; token-scope=not-applicable; broken-install-window=not-applicable

Not checked: the same boundaries as round 1. The five destination concerns remain step 2's, and no `npx skills add` was run against a published repository in this round either, so what the skills CLI does with a generated package is still unestablished here.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's three leads stand unchanged and for the same reasons. Round 1's fix was re-driven rather than reread, and so were the two guards beside it. Three mutations were driven against the fixed tree and each failed, naming its case: disabling the manifest-marker test failed one case, disabling the symlink test failed two, and disabling the non-directory test failed one. The module was restored byte-for-byte after each and `git status` reports it unmodified. `generator-output-escape` is therefore reviewed against driven failures rather than against a reading. The three lints exit 0 and the runner contract reports 741 of 741.

## Step 2, round 1 -- 2026-08-30T06:50:42Z

Audit schema: fiat-audit-round/v2

Covered: token-scope=reviewed; publish-unverified=reviewed; workflow-drift=reviewed; stale-destination=reviewed; broken-install-window=reviewed; generator-output-escape=reviewed; authored-file-loss=not-applicable; suite-coverage-loss=not-applicable

Not checked: whether the scheduled job runs green. Its drift step compares the destination's workflow against `source/distribution/skills-runtime/sync.yml` cloned from `main`, and that canonical copy reaches `main` only when this run integrates, so a dispatch before then fails by design. No scheduled or dispatched run has therefore been observed. Also not checked: the published `README.md` names the step-2 branch commit it was generated from rather than a commit on `main`; that is the commit that built it, and the first post-merge rebuild replaces it.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `distribution/skills-runtime/sync.yml` | `actions/checkout@v4` persists a push-capable token in `.git/config` by default. The job then executes `portable_promise_machine.py` from a clone of a different repository, so code under execution sat beside a credential able to push to the destination. The source is the same organisation and public, so this is reach the job did not need rather than an observed compromise. | fixed and guarded in dda3330f8c46e4df5b14d55e886531147c4e2a83 |
| S2-R1-02 | low | `distribution/skills-runtime/sync.yml` | The commit message extracted the source SHA from the generated `README.md` with `sed`. A non-match yielded an empty value and committed `Rebuild from wildcat-finance/skills@`, recording a rebuild of nothing identifiable as a success. | fixed in the same commit |

Leads not pursued: the job trusts whatever `portable_promise_machine.py` the cloned source carries, which is the same trust boundary as the repository itself and is not narrowed by pinning a commit, because the point of the job is to track the tip. `cp -R "/package/." .` copies over a tree the preceding `find` already emptied of everything but `.git`, `.github` and `source`, so a file dropped from the package is removed rather than left behind; that ordering is load-bearing and untested, and testing it needs a runner. The published package carries no signature, so it cannot prove which commit produced it against a hostile publisher; the destination is written only by its own job, and publisher authenticity sits outside ADR-040's boundary and this run. The three lints exit 0 and the runner contract reports 742 of 742.

## Step 2, round 2 -- 2026-08-30T06:53:22Z

Audit schema: fiat-audit-round/v2

Covered: token-scope=reviewed; publish-unverified=reviewed; workflow-drift=reviewed; stale-destination=reviewed; broken-install-window=reviewed; generator-output-escape=reviewed; authored-file-loss=not-applicable; suite-coverage-loss=not-applicable

Not checked: the same two boundaries as round 1. No scheduled or dispatched run of the destination job has been observed, because its drift step reads a canonical copy that reaches `main` only at integration. The published `README.md` still names the step-2 branch commit that built it.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's three leads stand unchanged and for the same reasons. Round 1's fixes were re-driven rather than reread. Four mutations were driven against the fixed workflow and each failed exactly one case: restoring credential persistence, removing the explicit push token, removing the empty-SHA refusal, and replacing the repository guard with `if: true`. A fifth attempt in the same batch did not mutate the file at all, because the shell quoting around the guard string broke before the replacement ran; it was redriven on its own and is the fourth result above, so the batch's apparent pass for it established nothing and is not counted. The file was restored byte-for-byte after each and `git status` reports it unmodified. The three lints exit 0 and the runner contract reports 742 of 742.

## Step 3, round 1 -- 2026-08-30T11:43:13Z

Audit schema: fiat-audit-round/v2

Covered: authored-file-loss=reviewed; broken-install-window=reviewed; suite-coverage-loss=reviewed; stale-destination=reviewed; generator-output-escape=not-applicable; publish-unverified=not-applicable; workflow-drift=not-applicable; token-scope=not-applicable

Not checked: whether the published package stays current once this stack merges. The destination job has never completed a publish; its only dispatch, run 33309124188, stopped at the drift guard because the canonical workflow copy is not yet on `main`. Also not checked: whether `npx skills add` against the destination still succeeds after this step, since nothing in step 3 changes the published package.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | `INSTALL.md` | The new pointer to the publication guide read `./skills-runtime-publication.md`, but `INSTALL.md` sits at the repository root and the guide is under `docs/`, so the link resolved to nothing. The root suite passed while it was broken; `hypomnema` caught it. | fixed in 3b9ce1e15ddd127af8c50347e6565b3393e88649 |
| S3-R1-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `GENERATOR_AGGREGATE_REGISTRY` registers `promise-machine-portable-runtime-v1` against the prefix `.agents/skills/promise-machine/runtime/` and the command `python3 scripts/portable_promise_machine.py check`. This step empties that prefix, so the entry names a directory the repository no longer carries and a command that exits non-zero on a clean checkout. The entry is dormant rather than broken, because the aggregate engages only when a revalidation surface holds paths under its prefix and no tracked path does. | not fixed here; filed as [#971](https://github.com/wildcat-finance/skills/issues/971) |

Leads not pursued: S3-R1-02 was left rather than fixed because this runbook does not cover `plugins/hexaemeron/skills/fiat/`, an edit to `hexctl.py` cascades into its digest bindings, and the controller that executes is the installed plugin copy rather than the tree's, so an edit here would change no behaviour until the plugin is re-released. Historical records naming the removed paths were left intact: `docs/skills-sh-payload-siting-study.md`, ADR-054, the \#940 audit rounds and `plugins/probitas/docs/morpho-midnight-fixed-maturity-runbook.md` all describe a tree that was true when they were written, and rewriting a durable record to match a later tree would be worse than the staleness. `scripts/portable_promise_machine.py check` now fails on a clean checkout by design, because there is nothing in-tree to check; `sync` still writes the runtime for local use and the directory is ignored. The three lints exit 0 on the fixed tree, `repo_contract.py` still resolves `ROUTER` and `CODEX_MARKETPLACE`, `plugins.sapheneia.tests.test_sapheneia` passes 6 of 6, and the root suite reports 740 of 740 with the payload absent.

## Step 3, round 2 -- 2026-08-30T11:45:19Z

Audit schema: fiat-audit-round/v2

Covered: authored-file-loss=reviewed; broken-install-window=reviewed; suite-coverage-loss=reviewed; stale-destination=reviewed; generator-output-escape=not-applicable; publish-unverified=not-applicable; workflow-drift=not-applicable; token-scope=not-applicable

Not checked: the same two boundaries as round 1. The destination job has still completed no publish, and step 3 changes nothing about the published package, so no fresh install was driven against it in this round.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's leads stand unchanged, and S3-R1-02 remains open against [#971](https://github.com/wildcat-finance/skills/issues/971) for the reasons recorded there. Round 1's fix was re-driven rather than reread, and so were the two guards beside it. Three mutations were driven against the fixed tree and each failed exactly one case: adding the removed manifest back to the expected tracked set, removing the runtime directory from `.gitignore`, and restoring the old install command in `README.md`. Every file was restored byte-for-byte afterwards and `git status` reports the tree clean. The runner contract reports 740 of 740 with the payload absent.
