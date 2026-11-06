# Study: portable payload reserve and standing measurement

Task: [issue #1720](https://github.com/wildcat-finance/skills/issues/1720), `Fiat-Required: 1`, with its one comment of 2026-09-20. Run branch `fiat/1720-portable-payload-reserve-and-standing-measu`, cut from `main` at `66f52785813a8453e7c7d54f2371aa8f6e465640`.

Assuming, unless corrected:

1. The exact interpreter in `.python-version` (3.14.6), standard library only, `unittest`. No dependency is added.
2. ADR-090's cap (26,214,400 bytes) and reserve (5,242,880 bytes) are accepted policy, so a candidate that spends the reserve fails a hard gate. Section 4 records evidence that questions what the reserve protects; overturning ADR-090 is left to the user.
3. ADR-040's rule governs what ships: data the router never reads stays in the full source checkout, and the installed adapter names it. The selection between the two surviving candidates rests on this reading.
4. The security suite is waived: the run ships Python, JSON and Markdown, no Solidity.
5. Ordinary delivery. No file under `plugins/` changes, so no plugin version and no `EVOLUTION.md` row is owed. If the runbook finds it must edit a plugin file, that step owes the plugin's version rise.
6. Every measurement below was taken on a clean checkout of the starting commit on macOS (Darwin 25.5.0). Package bytes are platform independent; wall times are not.

## 1. Problem statement

**What is built.** Two things for contributors and Fiat runs that add packaged bytes to `wildcat-finance/skills`:

1. A standing measurement: one command that prints the portable package's bytes, the refusal line, the margin, the file count against its tripwire and the largest packaged paths that no named list or omission class selects, and that still answers when the tree is over the line.
2. A reserve remedy: one decided rule for what the portable router needs, so room returns without a mid-step omission.

**Why.** `scripts/portable_promise_machine.py` refuses generation above 20,971,520 bytes. Three omission classes were added in three days, each inside the step that crossed the line (run #1676 Step 4, merge `229f5856`, PR #1769). The run for #1731 then shortened packaged prose to fit, and its audit found the shortening had dropped claims. No delivery can read its room before its commit gate runs.

**Measured on `main` at the starting commit** (command and method in [section 10](#10-the-budget-or-its-absence)):

| Quantity | Value |
| --- | ---: |
| Complete package, bytes | 20,381,433 |
| Refusal line (cap 26,214,400 minus reserve 5,242,880) | 20,971,520 |
| Package margin under the line | 590,087 |
| Complete package, files | 1,550 |
| Runtime `total_bytes` in `MANIFEST.json` | 19,904,247 |
| Runtime `file_count` against the 1,600 tripwire in `tests/test_skills_sh_package.py` | 1,543, 57 below |
| `MANIFEST.json` bytes; outer files bytes | 454,859; 22,327 |
| Omission rows in `OMISSIONS` | 14 |
| Files packaged by the `plugins/**` default, not by a named list | 1,446 files, 18,254,542 bytes |

The issue said `main` had not been measured separately. These figures agree with the real `package --out` action: a walk of its output gave 1,550 files and 20,381,433 bytes, and its manifest gave 1,543 and 19,904,247.

Largest default-included paths on `main`:

| Path | Bytes |
| --- | ---: |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (operational) | 1,265,384 |
| `plugins/tabularium/examples/aave-v4-v0/events.jsonl` | 1,232,064 |
| `plugins/lazarus/examples/aave-v4-spoke-v1-release/fixture/rpc.jsonl` | 576,798 |
| `plugins/tabularium/examples/aave-v4-v0/source.json` | 461,304 |
| `plugins/lazarus/examples/aave-v4-spoke-v1-release/fixture/receipt-witness.json` | 343,966 |
| `plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` | 272,388 |
| `plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1/selection-rejections.jsonl` | 231,041 |
| `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | 177,562 |
| `plugins/alexandria/examples/usdc-interval-live-v0/staging/journals/epoch-evidence.jsonl` | 168,101 |

The two standalone Lazarus rows in the issue's table left the package in merge `229f5856`; the rest of that table stands.

**Growth.** Between `0578c19bb812ba34fcfc752dcb81e5df4b1090ae` (ADR-090 landed, 2026-09-12T20:54:17+01:00) and the starting commit (2026-09-20T08:32:06+01:00), the paths packaged today grew by 2,648,662 blob bytes across 57 first-parent commits. By directory class: `skills/` 1,851,300; `docs/` 442,147; `schemas/` 103,158; `harness/` 89,885; `examples/` 52,061; the rest 110,111. The largest single delivery, merge `86de8d18` (PR #1638), added 794,493 bytes; merge `d9b98470` (PR #1784) added 634,349. Observed: the present margin of 590,087 is smaller than the largest delivery in the window. Inferred: at 353,863 bytes a day the margin lasts under two days; the window is 7.5 days and holds two large protocol deliveries, so the rate is an upper-range reading, not a forecast.

**Working prototype.** On the delivered tree:

1. `python3 scripts/portable_promise_machine.py measure` exits 0 and prints bytes, line, margin, files against the tripwire and the largest default-included paths; `--json` prints one `portable-payload-measurement/v1` object whose figures equal a walk of `package --out`.
2. `python3 scripts/portable_promise_machine.py measure --require-margin 794493` exits 0, and exits 1 on a tree whose margin is smaller.
3. On a tree over the line, `measure` still exits 0 with a negative margin while `package` refuses, and the refusal names the margin and the `measure` action.
4. The generated package verifies in an isolated copy: `verify_runtime.py`, the installed Horos `check` and the packaged evaluation check all exit 0.
5. One measurement of the delivered tree is committed beside the study.

**Demo path.** The last runbook step runs items 1 to 4 as commands and records their output. It claims only those observations: the controller is Fiat, the source command is the generator, and the negative observations are the two refusals in items 2 and 3.

**Ownership.** The issue hands this to Protasis. Answer: no plugin skill is upgraded. The owner is the root Promise Machine distribution tooling, check-map scope `promise-machine` in `tests/check-map-v1.json`: `scripts/portable_promise_machine.py`, `tests/test_skills_sh_package.py`, `.agents/skills/promise-machine/PORTABLE.md` and the decision records. Metron's contract is cited for the budget and is not changed. A later change that makes a study read the target's declared measure would belong to Protasis's own ledger; it is listed under deferred work, not built here.

## 2. Prior art

**In this repository.**

- [ADR-040](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/docs/decisions/ADR-040-package-one-dependency-closed-portable-router.md): one dependency-closed router package; data the router never reads stays in the full checkout and the installed adapter names it. It rejected many package identities and fetching after install.
- [ADR-066](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/docs/decisions/ADR-066-publish-the-skills-sh-payload-from-its-own-repository.md): the package is published from `wildcat-finance/skills-runtime` by `distribution/skills-runtime/sync.yml`, hourly, from a clone of `main`. A change to that workflow needs a person with `workflow` scope to push it. The generated runtime is not tracked here, so `python3 scripts/portable_promise_machine.py check` exits 1 on `main`; [issue #1437](https://github.com/wildcat-finance/skills/issues/1437) owns that.
- [ADR-090](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/docs/decisions/ADR-090-omit-portable-decorative-portraits.md), answering [issue #1467](https://github.com/wildcat-finance/skills/issues/1467): portraits omitted, the reserve set, both the runtime and the complete package held to the line. Its Alternatives leave a second delivery open as a separate change.
- Drafts `docs/decisions/drafts/omit-checkpoint-authority-conformance-corpora-from-the-portable-runtime.md` (run #1676 Step 4) and `docs/decisions/drafts/keep-one-complete-lazarus-fixture-in-the-portable-runtime.md` (merge `229f5856`). Both refuse spending the reserve. The second keeps one complete Lazarus release installed for `verify`, `replay` and `verify-release`.
- `docs/main-root-suite-recovery/package-measurement.json`: a one-off recorded measurement (18,668,573 package bytes at 2026-09-12). It shows the record shape this run follows: bound to a named commit, never compared with `HEAD`.
- What is omitted today, measured on `main`: checkpoint-authority corpora 27,073,288 bytes in 64 files; Alexandria Compound v3 trees 15,859,684 in 144; `plugins/*/tests` 8,556,633 in 747; Tabularium v1 payloads 1,715,680 in 15; Lazarus duplicates 983,787 in 6; Anamnesis specimens 543,954 in 45. Five of the 14 omission rows are example-specific.
- What the router reads at run time. Observed: the portable gates are `verify_runtime.py`, the installed Horos `check`, the packaged `promise_machine.py check --only evaluation` and the `model_proxy.py conformance` demonstration; none opens a file under `plugins/*/examples/`. `tests/promise_machine_coverage.json`, `tests/promise_machine_obligations.json` and `tests/promise_machine_id_history.json` name 69 packaged paths, none under `examples/` or `docs/`. No packaged script outside `examples/`, `tests/` and `docs/` reads an example path; two mention one in a comment, and one committed design resolver under `plugins/alexandria/docs/` names the live interval example, which is a delivery record and not a router operation. `PORTABLE.md` supports exactly one installed operation on example data: Lazarus on the retained release. Packaged examples hold 3,744,470 bytes in 196 files; plugin `docs/` hold 3,499,045 in 417.

**Last two merged pull requests that changed the packager.**

- [PR #1784](https://github.com/wildcat-finance/skills/pull/1784) (run #1676, merged 2026-09-20, carries merge `229f5856`). Its carryover row `payload-margin | filed` points at #1720: carried forward as this study. Its row `limited-download-routes | none` records that a package above 1,000 files does not fit the CLI's archive routes: carried into section 4 as evidence.
- [PR #1769](https://github.com/wildcat-finance/skills/pull/1769) (run #1362, merged 2026-09-19). Row `portable-package-reserve | duplicate` points at #1720: carried forward. Row `packaged-runtime-drops-rebuild-scripts | filed` is [issue #1759](https://github.com/wildcat-finance/skills/issues/1759): stays open. The selected design does not restore those scripts; it answers the family #1759 names, packaged documents describing a path the package cannot take, once in `PORTABLE.md`. [Issue #1678](https://github.com/wildcat-finance/skills/issues/1678) is the Alexandria instance and also stays open.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check <target-root>` ran from the target root and exited 0: 99 views, every one `committed=match`. The 99 sources are the root `audit/AUDIT.md`, 93 per-run records under `audit/rounds/` and five plugin records at `plugins/{ariadne,hexaemeron,pandects,probitas,tabularium}/audit/AUDIT.md`; all are in scope because any run may have touched the packager. Only synopses were read, by pattern search across all 99 views for the packager, the package tests, the line and omissions; no source record was read. Views with relevant rows, by SHA-256:

| View | SHA-256 | Rows kept |
| --- | --- | --- |
| `audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.synopsis.md` | `067690f8e6def8e79e09b55caf8c4a77b04ecf34f5560f5b481f019aac1b763f` | S4-R1-01 medium, accepted: a repository-wide omission forced inside a step, outside its Files field. S4-R1-02 low, accepted: shipped documents name files the runtime lacks; all seven rebuild commands are repository-root-relative and none runs from the package tree. S4-R2-04 low, accepted: the amendment misattributed added bytes. |
| `audit/rounds/fiat-1676-publish-checkpoint-authority-protocol-and-r.synopsis.md` | `b6a449a7901d6c8636ba46da999cf5d21e66a1c6d31b60f34e6354689a5070a9` | S4-R1-01 low, fixed in `23f55f3439e5aa238f5b6eb2bc08c5cefcf4065f`: three passages gave package figures that named no measure. S5-R1-02 low, fixed in `a684890d10f663380a3e78a1e2ddd25f5bb1e993`: stale counts and wrong reserve arithmetic in the test comment. Step 4 `Not checked`: historical figures were not rebuilt because the generator refuses a tree that is not a Git checkout. |
| `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.synopsis.md` | `42d082a20a8f143ee7d0663b9d3c238528b647f9316487f68729781a9b5dad0a` | S1-R1-01 high, fixed and guarded in `69b3180c850d3ddd09ccfaf547b53951f6b13dd9`: `package --out` destroyed a populated directory. S2-R1-01 medium, fixed and guarded in `dda3330f8c46e4df5b14d55e886531147c4e2a83`: push credential beside cloned code. S3-R1-02 medium, not fixed, filed as #971. |
| `audit/rounds/fiat-854-stage-the-portable-sync-before-the-horos-sca.synopsis.md` | `14e96fa2a426923219a7c738aec1c739a71676f401da5ae15e51d95a6cbc47bf` | S2-R1-01 medium and S3-R1-01 low, both fixed: unconditional staging; a Solidity import form the closure check missed. |
| `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.synopsis.md` | `fb5cfd5339c2f30a9e1f1cd6d267658a26e5a19dd2ad5dc947f1159091c0f19c` | `Not checked` in both rounds: whether the headroom bounds were correctly sized. |

Those views carry no `[missing legacy field: ...]` marker on the rows above. Three findings recur across the two newest runs: package figures written by hand were wrong or named no measure. The standing measurement answers that by printing both measures.

No Protasis inventory of known failures is carried. Every packager finding above is fixed, accepted with its reason, or filed; none names a failure that must be guarded before this run's product work starts.

**Outside the repository.** The skills CLI, `vercel-labs/skills` at `7407f3893ad4dceab546ac002c3ef806e4000c73`, [`src/download-source.ts`](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/src/download-source.ts) lines 10 to 12: download 10 MiB, extracted bytes 25 MiB, archive entries 1,000, each with an environment override. One function applies all three to archive routes only.

## 3. Constraints and non-goals

**Starting ref.** `main` at `66f52785813a8453e7c7d54f2371aa8f6e465640`. Python 3.14.6 from `.python-version`. Git is required: the generator enumerates sources with `git ls-files` and refuses a tree that is not a checkout.

**Constraints.**

- The cap, the reserve and the 1,600-file tripwire keep their values.
- Source files under `plugins/` keep their bytes. Only what the generator copies changes.
- The Lazarus release under `plugins/lazarus/examples/aave-v4-spoke-v1-release/` stays installed and the byte-equality guard in `check_duplicate_fixture_payload` stays.
- Every relative Markdown link that resolves in today's package still resolves; `test_authoritative_runtime_links_close_inside_the_package` stays green.
- The committed measurement is bound to a named commit and is never compared with `HEAD`, so an unrelated packaged-byte change cannot redden it.
- `distribution/skills-runtime/sync.yml` does not change: it calls `package --out`, which keeps its interface.
- Run tests with `NO_COLOR=1`; this shell sets `FORCE_COLOR`, which reddens argparse assertions.

**Boundaries.**

- Always: the root suite and the three package suites before a commit; the Imprimatur lint on each shipped document; Phylax over any committed copy of the resolver; a fresh `measure` before quoting a package figure in prose.
- Ask first: changing the cap, the reserve or the tripwire; touching `distribution/skills-runtime/sync.yml` or any workflow; editing a file under `plugins/`; editing `AGENTS.md`, whose sentences other records quote.
- Never: shorten packaged prose to fit the line; delete a source corpus; vendor third-party source; write a package figure that names no measure; claim a command ran when it did not.

**Non-goals, deferred past the prototype.**

- A second repository or package. Compared in section 4 and not selected.
- Changing the reserve. Section 4 records the evidence; the decision stays with ADR-090's owner.
- Restoring the Tabularium v1 rebuild scripts (#1759), repairing the interval demonstrations (#1678), the `check` action on `main` (#1437) and the stale generator registry entry (#971).
- Publishing the measurement in the hourly `skills-runtime` README, and making Protasis or Fiat read a target's measure during a study. Each is a separate change with its own owner.
- A growth forecast. The measurement prints facts about one tree.

## 4. Design options

All four candidates include the standing measurement; they differ in the remedy. Figures come from simulating each rule over the starting commit with `.hexaemeron/design/resolve.py`, SHA-256 `9060bf1f6fd8a444315987b6ffcb5d7bf130f0c4855304b5f1d7d8f19d232de1`.

1. `example-payload-class`. One omission class: files under `plugins/*/examples/` that are not Markdown, except any file a packaged Markdown document links and the retained Lazarus release. It replaces the five example-specific rows. Trade: 146 demonstration files (2,545,267 bytes) leave the CLI install and stay in the source checkout; example documents will name payloads the package lacks, said once in `PORTABLE.md`. Tabularium's v0 payload (1,697,604 bytes) leaves with them, which changes the sentence in `PORTABLE.md` that says the v0 evidence remains.
2. `second-distribution`. Example and `docs/` trees that no packaged document links move to a second generated package in a second repository. Trade: most room and nothing leaves the CLI's reach, but it needs a new repository, a second manifest and verifier, a second installable identity beside the one ADR-040 allows, and a rebuild workflow only a person can push. A second package in the same repository would not help: the CLI's byte limit applies to the whole extracted archive.
3. `lower-reserve`. Reserve 2,097,152, line 24,117,248. Trade: two constants and a record; spends protection ADR-090 and two later drafts refused to spend.
4. `plugin-budgets`. The line divided per plugin. Trade: the plugin that grows is the one refused, but no room returns.

| Criterion | `example-payload-class` | `second-distribution` | `lower-reserve` | `plugin-budgets` |
| --- | ---: | ---: | ---: | ---: |
| `reserve-held`, gate, at least 5,242,880 | 5,242,880 | 5,242,880 | 2,097,152 fail | 5,242,880 |
| `delivery-room`, gate, at least 794,493 | 3,180,975 | 5,447,387 | 3,735,815 | 590,087 fail |
| `links-closed`, gate, at most 0 new breaks | 0 | 0 | 0 | 0 |
| `measure-wall-time`, gate, at most 60,000 ms | 729 | 612 | 13 | 12 |
| `margin-after`, maximise | 3,180,975 | 5,447,387 | 3,735,815 | 590,087 |
| `growth-reach`, minimise | 2,621,861 | 2,613,123 | 2,648,662 | 2,648,662 |
| `files-leaving-cli-install`, minimise | 146 | 0 | 0 | 0 |
| `human-pushed-workflows`, minimise | 0 | 1 | 0 | 0 |
| Package after, bytes and files | 17,790,545; 1,404 | 15,524,133; 1,114 | 20,381,433; 1,550 | 20,381,433; 1,550 |

`delivery-room` takes its threshold from the largest delivery observed since ADR-090. `growth-reach` replays the 2,648,662 observed growth bytes through each rule. It shows that no candidate stops growth: 70% of it is operational code under `skills/`, which no rule here can name. The selected remedy returns room for about four deliveries of the largest observed size. The durable part of this run is the measurement.

**Selection.** Two gates remove `lower-reserve` and `plugin-budgets`. The two survivors trade room and install reach against a second repository and a human-pushed workflow, so neither dominates and the rule is `user-policy`. The policy read is ADR-040's: the full source checkout is already the home of data the router never reads, and three omissions in three days applied it. Under that policy `example-payload-class` is selected. If the user prefers the second distribution, the change is one field of the record and a new lock.

**Evidence on the reserve, recorded and not acted on.** The CLI applies its 1,000-entry limit in the same function as its 25 MiB limit. The package holds 1,550 files, so the archive routes already refuse it by default, and the supported `github` route consults neither limit. Inferred: the line protects only an installer who overrides the file limit and not the byte limit. That questions what 5,242,880 bytes buys. ADR-090 is eight days old and two later drafts reaffirm it, so this study holds it as a constraint and reports the question.

**Conformance, pending.** `measure-agrees` blocks `step:3`; `class-leaks`, `installed-gates-pass` and `room-on-step-tree` (at least 794,493) block `step:4`. Resolver for each: `python3 .hexaemeron/design/resolve.py conformance --root . --reports .hexaemeron/reports --candidate example-payload-class --criterion <id>`, writing `.hexaemeron/reports/example-payload-class--<id>.json`. No cell blocks `integration`, because `main` can grow under the run before it lands.

**Module order.** Two modules, one study, because the remedy's gates are expressed in the measurement's output.

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| `measure` | The `measure` action, its JSON shape, the refusal text, the tripwire constant | none |
| `example-class` | The class rule, link-kept exceptions, `PORTABLE.md`, the decision record | `measure` |

Build order: `measure`, then `example-class`.

**The measurement interface**, fixed here because the conformance resolver reads it: `python3 scripts/portable_promise_machine.py measure [--json] [--top N] [--require-margin BYTES]`. Exit 0 when measured, including over the line; 1 when `--require-margin` is unmet or the tree cannot be read; 2 on bad usage. The JSON object has `schema` `portable-payload-measurement/v1`, `source_commit`, `tree_clean`, `cap`, `reserve`, `line`, `file_tripwire`, `package` and `runtime` objects each with `bytes`, `files` and `margin`, `manifest_bytes`, `outer_bytes`, `omission_classes`, `largest_default_included` and `kept_by_link`, the last two as lists of `path` and `bytes`. It writes nothing.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | example-payload-class
record | docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md
```

## 5. Risk register seed

```risk-register
measure-drift | the measure action beside the package action | both read one code path, so package bytes, files and margin equal a walk of package --out on the same tree
over-line-blind | the measure action on a tree above the line | it exits 0 with a negative margin and never raises the headroom refusal
refusal-text | require_byte_headroom and its callers | the refusal names bytes, line, margin and the measure action, and still refuses the first byte past the line
class-overreach | the example class predicate in _omitted | only plugins/*/examples/** matches; skills, scripts, schemas, docs and named test files are untouched
link-pullback | link-kept exceptions computed from packaged Markdown | a linked payload is kept and listed by measure; links are parsed in linear time with bounded input and no network
lazarus-retained | plugins/lazarus/examples/aave-v4-spoke-v1-release | the complete release stays packaged and the byte-equality guard still refuses a changed, missing, untracked or symlinked copy
dangling-mentions | packaged example documents naming absent payloads | PORTABLE.md names the class and directs those operations to a full checkout; no packaged prose is shortened
manifest-truth | OMISSIONS rows and EXPECTED_OMISSIONS in the package test | the manifest lists the class with its exceptions and the five replaced rows are gone from both
figure-prose | package figures in comments, PORTABLE.md and the decision record | each figure names its measure and commit and matches a fresh measure run
record-currency | the committed measurement file | it is bound to a named commit and no test compares it with HEAD
resolver-writes | committed copies of the design resolver | it writes only report files, refuses to overwrite a different report, and passes the Phylax lint
workflow-untouched | distribution/skills-runtime/sync.yml | the file keeps its bytes and the package action keeps its interface
other-suites | plugin and root suites that build the package | test_agent_instruction, test_portable_duplicate_fixture, test_portable_skills and the Hexaemeron model-proxy package test stay green
```

Audits of the last two runs landed the same fix class three times: figures in prose that named no measure. Brief each Mason with `figure-prose`.

## 6. Glossary seeds

- Line: 20,971,520 bytes, the cap minus the reserve; generation refuses the first byte past it.
- Cap: 26,214,400 bytes, the skills CLI's default extracted-bytes limit.
- Reserve: 5,242,880 bytes held below the cap by ADR-090.
- Margin: the line minus the complete package's bytes; negative when over.
- Complete package: the runtime, its `MANIFEST.json` and the outer files `package --out` writes.
- Runtime: the files under `runtime/` that the manifest lists; `total_bytes` and `file_count` describe it.
- Tripwire: the 1,600-file local limit on `file_count`.
- Default-included: packaged because it is a tracked file under `plugins/` that no omission names, not because a named list selects it.
- Example payload: a non-Markdown file under `plugins/*/examples/`.
- Link-kept: an example payload retained because a packaged Markdown document links it.
- Standing measurement: the `measure` action and its `portable-payload-measurement/v1` output.

## 7. Sources

- Issue and comment: [#1720](https://github.com/wildcat-finance/skills/issues/1720). Related: [#1467](https://github.com/wildcat-finance/skills/issues/1467), [#1759](https://github.com/wildcat-finance/skills/issues/1759), [#1678](https://github.com/wildcat-finance/skills/issues/1678), [#1437](https://github.com/wildcat-finance/skills/issues/1437), [#971](https://github.com/wildcat-finance/skills/issues/971).
- Pull requests: [#1784](https://github.com/wildcat-finance/skills/pull/1784), [#1769](https://github.com/wildcat-finance/skills/pull/1769).
- Source at the starting commit: [`scripts/portable_promise_machine.py`](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/scripts/portable_promise_machine.py), [`tests/test_skills_sh_package.py`](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/tests/test_skills_sh_package.py), [`PORTABLE.md`](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/.agents/skills/promise-machine/PORTABLE.md), [`sync.yml`](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/distribution/skills-runtime/sync.yml); also `tests/test_portable_duplicate_fixture.py`, `tests/test_portable_skills.py`, `tests/test_agent_instruction.py` and `plugins/hexaemeron/tests/test_phylax_model_proxy.py`.
- Decisions: ADR-040, ADR-066 and ADR-090 linked in section 2; the two drafts by path in section 2.
- Commits: merge `229f5856e03b9cd60c2265281696944281b35308`; `75e3a0c76faa0dfeb31f84aeff133b37ec3ad0d9` (PR #1769); growth base `0578c19bb812ba34fcfc752dcb81e5df4b1090ae`.
- Skills CLI limits: the pinned file linked in section 2.
- Run evidence under `.hexaemeron/`: `design-evidence.json`; 32 selection reports in `reports/`; `design/resolve.py`; `design/main-measurement.json`, SHA-256 `68aa491948d78473289c8864abe70af388d254691ecb5c6aa04d51369d0b8559`; `design/selection-summary.json`, SHA-256 `de1338c4849f195edaddf9dd8648a94f5da1b42918b10d800f9f227c1ee9a99c`.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal carries. One unattended path exists: the hourly rebuild in `skills-runtime`, which fails and keeps the last good package when generation refuses.

1. Why did the hourly rebuild stop publishing? Signal: the generator's refusal on the job's standard error, which after Step 2 carries bytes, line, margin and the `measure` action's name.
2. How much room does `main` have now, and which paths hold it? Signal: `measure --json` on a checkout of `main`.
3. Did a delivery change what installers receive? Signal: the `omissions` list in the published `MANIFEST.json`.

No metric, trace or alert is added: the measurement is a terminal command and the job already fails visibly. Steps 2 and 3 emit the signals above.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and controls.

- Subprocess: the measurement reuses the generator's fixed-argv `git` and Horos calls, no shell. No new command is spawned.
- Repository content as input: link-kept exceptions parse packaged Markdown. Control: one linear pattern over bounded file bytes, targets normalised and refused when they leave the tree, symlinks already refused by `_source_candidates`.
- Arguments: `--top` and `--require-margin` are non-negative integers parsed by `argparse`; `--json` writes to standard output only.
- Filesystem: `measure` writes nothing. `package --out` keeps the guards run #949 added.
- Credentials, network, dependencies, model output: none opened.
- The committed resolver copy is Python under `docs/`; it must pass the Phylax lint before Step 1 publishes it.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries.

- Byte budget: complete package at most 20,971,520 bytes. Command after Step 2: `python3 scripts/portable_promise_machine.py measure --require-margin 794493`.
- File budget: `file_count` below 1,600, printed by the same command.
- Time budget: `measure` at most 60,000 ms on a developer machine. Observed: the resolver's simulation took 12 to 729 ms per candidate, and `package --out` took 0.72 s wall.
- Baseline, recorded before any change: `python3 .hexaemeron/design/resolve.py measure --root .` on the starting commit, saved as `.hexaemeron/design/main-measurement.json`, cross-checked by `python3 scripts/portable_promise_machine.py package --out <empty directory>` and a walk of the output.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/elenchus/SKILL.md) owns triage order and the guard rule.

- Generation still refuses the first byte past the line for the runtime and for the complete package; `measure` reports and never relaxes that.
- A link-kept target that is missing, a symlink or outside the tree refuses generation.
- The Lazarus guard refuses as today.
- The resolver refuses to overwrite a report whose bytes differ.
- A design cell that fails at `step:3` or `step:4` stops the run; nothing is rewritten to pass it.
- Guard convention: every audit fix lands with a test in `tests/test_skills_sh_package.py` or the new measurement test module that fails without the fix, run as `NO_COLOR=1 python3 -m unittest tests.test_skills_sh_package tests.test_portable_duplicate_fixture tests.test_portable_skills`. The runbook names the exact Elenchus command, report format and report file per step.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record.

- Expensive to reverse: what installers of `skills-runtime` receive. Home: a new draft at `docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md`, written in Step 1 so the design bridge resolves, shipped unnumbered as the last runs shipped theirs ([issue #1782](https://github.com/wildcat-finance/skills/issues/1782)). It records the class, the five rows it replaces, the two exceptions, the refused alternatives with the figures above, and the reserve question left open.
- Expensive to reverse: the `portable-payload-measurement/v1` shape, which other runs will parse. Home: the same draft, with the field list in the generator's help text.
- Cheap to reverse, no record: the tripwire constant moving into the generator; the refusal wording.
- The installed notice lives in `.agents/skills/promise-machine/PORTABLE.md`. The committed study, runbook, design record, reports and measurement live under `docs/portable-payload-reserve/`, which is outside the package.
