# Study: distinguish Wave, frontier and maintenance volunteer intent

Assuming, unless corrected:

1. Issue [#447](https://github.com/wildcat-finance/skills/issues/447) remains a design-only delivery. Completion means one accepted, repository-standing decision with worked cases; it does not mean an executable selector exists.
2. The current contributor front door supersedes the issue's 22 August 2026 earliest-Wave proposal. `wave` means selection through the Wave Atlas's dependency-clear issue pool, not ordering milestone titles and taking the earliest one.
3. A named issue is a fourth, overriding intent kind rather than a hidden inference inside one of the three lanes.
4. The launcher records the requested intent before candidate search. Selection stays with the component that owns each candidate universe. Fiat may bind the resulting handoff, but it does not rank issues, read every frontier, or invent maintenance scope.
5. This run changes no canonical skill, external service, issue metadata, frontier or package version. Any later implementation is separately scoped and authorised.
6. The exact starting ref is `main` at `ab611eb96a6a9bddecb57bff2416641296e0a21e`. The observed local tools are Python 3.9.6 and Git 2.54.0.
7. The whole-set audit synopsis check exited zero before this study. Verified synopses are used as views; authoritative legacy source ranges are read where the synopsis marks fields missing.

These readings govern the study unless corrected. None changes the build order, so no question blocks the design record.

## 1. Problem statement

The repository needs one durable decision that prevents a friendly offer such as “help evolve you” from silently choosing among three different candidate universes:

- the Wave Atlas's open, dependency-clear GitHub issue pool;
- governed skill frontiers ranked by Kronos; and
- a caller-supplied maintenance job with one bounded output.

The users are external contributors choosing work, maintainers checking whether work is already claimed, selector owners producing the choice, and Fiat consuming a chosen job. The defect is not that any one selector ranks badly. The defect is that natural-language wording can cross the boundary between selectors without an explicit record of which universe was searched.

This run's working prototype is a cross-repository ADR, not a command. It must define:

1. a closed `wildcat-volunteer-intent/v1` handoff with `named-issue`, `wave`, `frontier` and `maintenance` cases, plus a producer-side receipt proving which case was fixed before candidate search;
2. the producer, candidate evidence, selected subject, claim state, consumer and refusal for each case;
3. named-issue precedence and the rule that Fiat binds but never selects; and
4. a public claim and recovery rule that works for a contributor without repository write permission.

The proving demo path is the ADR's `Worked intent cases` section. A reviewer follows one example per case and reaches exactly one selector or refusal without interpreting words such as “evolve”, ordering a Wave suffix, or granting a GitHub write. The repository proves the artefacts are structurally and mechanically admissible with:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/volunteer-intent-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/volunteer-intent-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions docs/volunteer-intent-study.md docs/volunteer-intent-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/<volunteer-intent-adr>.md docs/volunteer-intent-study.md docs/volunteer-intent-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/<volunteer-intent-adr>.md
python3 -m unittest discover -s tests
```

Success also requires the decision to answer the issue's hostile cases without implementing them: an empty issue pool refuses; a stale or mismatched snapshot refuses; an already-claimed issue refuses; a mature frontier refuses; maintenance without a bounded output refuses; and non-integer Wave suffixes remain opaque milestone text rather than ordering input.

## 2. Prior art

### Repository

The original study, `docs/how-to-help-shoggoth-study.md`, proposed `wave`, `frontier` and `maintenance` lanes and filed #447 as the standing home for the unresolved decision. Its dated Wave 3 census is historical evidence, not a current selector input. `docs/how-to-help-shoggoth.md` and the root `README.md` now send an external contributor to the Atlas, say the contributor does not choose a Wave, and describe the Atlas rule as a random open issue from the full pool whose recorded hard dependencies are closed.

`docs/decisions/ADR-014-reallocate-the-live-wave-atlas-from-a-complete-census.md` makes GitHub milestones the Wave assignment source and says the public endpoint is a draw from dependency-clear issues, not a claim that Wave order is a hard dependency. It also says allocation freshness must be re-established rather than inferred from a compiled site. `AGENTS.md` keeps Wave issues, held frontier jobs, skill wishes and framework observations as distinct queues. None authorises a cross-queue inference.

Fiat already accepts a validated `--task-issue` URL at initialization, binds its positive terminal issue number into run and step branch identity, and refuses later replacement. That establishes issue continuity after selection; it does not establish why the issue was selected. Kronos already owns frontier selection. Its scoreboard records the complete allowed candidate universe, held-job digests, four-axis scores, tie-break and selected job; rank-only records do not launch Fiat. Mature, parked, vendored and out-of-scope skills remain refused. A common handoff should consume those facts rather than duplicate their rules.

The last two merged pull requests that changed volunteer allocation semantics were read before drawing the options:

- [PR #528](https://github.com/wildcat-finance/skills/pull/528), merged as `6c98a728a9f8ee25f4eed70b7032dc10f836eb17`, replaced the earlier lane-first contributor route with “ask the Atlas for a number”, separated checked bootstraps from local harnesses, and made the contributor front door one random dependency-clear issue pool. It carried no explicit intent packet or early public-claim mechanism.
- [PR #506](https://github.com/wildcat-finance/skills/pull/506), merged as `367e9662384bb29ea94576d270ab86744f3326a2`, removed prose that implied a particular Atlas read path. It carried [issue #505](https://github.com/wildcat-finance/skills/issues/505) for freshness and exclusion evidence. #505 is still open and stays out of this delivery.

[PR #596](https://github.com/wildcat-finance/skills/pull/596) was also inspected because it is the latest public collective-map rewrite. It changed catalogue and routing prose but did not change volunteer selection, claim or handoff semantics. The earlier [PR #452](https://github.com/wildcat-finance/skills/pull/452), merged as `e4bf336ae100fc57aaff5e20deef3e1ea4615730`, remains relevant because its `Carried forward` section explicitly assigns the lane grammar, intent handoff, public claim, census trigger and Wave-suffix question to #447. This run accepts or displaces each item below:

- lane grammar and handoff: carried into the chosen typed handoff;
- public claim: settled as a contributor-authored structured issue comment with explicit release recovery;
- census trigger: refused here by name because #505 owns Atlas freshness and exclusion evidence;
- Wave-suffix ordering: displaced because current Wave selection does not order milestone names; titles remain opaque source metadata.

### Organisation and live operating surfaces

The Shoggoth Interceptor was read at public commit `23f9761a849980eecb89a0bd6fdcabba19d52c61`. Its `CLAUDE.md`, `README.md`, `bin/shoggoth.py` and `bin/console.py` show a read-only issue path, a roster excluding assigned work and branch or pull-request trails, local ranking receipts, configured target resolution and Fiat dispatch. It has no volunteer lane and no issue-write path. Its existing ranking rules stay intact.

The live Atlas `GET /api/job?all=true` response was read twice. The observed `wildcat-wave-job/v2` response reported `generated_at` `2026-08-26T00:21:58.461Z`, a 600-second cache, first a live read and then a cache read, 92 eligible jobs and no open issue without a Wave. Those are recorded observations, not permanent backlog facts. The response now exposes `generated_at`, `read_from`, `cache_seconds` and `open_issues_without_a_wave`, so part of #505 appears live; #505 remains open, the Atlas repository was not accessible through the supplied GitHub credential, and this study does not claim the issue is delivered. A selected `/api/job` response still carries a count rather than a digest of the exact candidate set. A second `all=true` request cannot prove it saw the same set the selection used, so the future handoff needs a same-read candidate digest.

### Audit records

The sole in-scope audit source is authoritative `audit/AUDIT.md`; the verified normal view is `audit/AUDIT_SYNOPSIS.md`, whose header binds source SHA-256 `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`. A search across every verified root, run and plugin synopsis found no other audit source about volunteer intent, Wave selection, task-issue selection or maintenance lanes. The relevant synopsis rows mark `audit-schema`, `Covered`, `Not checked` and `Elenchus verdict` as missing legacy fields, so those values remain unknown. The authoritative source ranges were read to retain finding ids and statuses:

- `I438-S2-R1-01`, medium, was open when Fiat accepted relative, hostless, non-HTTP and control-bearing task-issue strings. It was fixed in `63861895b98585cf597ae1fb3a2ec749ae3c9ef7`; the hostile URL cases and no-state-on-refusal guard remain the named evidence.
- `SCG-S1-R1-01`, medium, was fixed by filing #447 as the standing design home. This delivery must replace that open discussion with a standing ADR rather than leave the choice in a run artefact.
- `SCG-S1-R1-02`, low, was fixed by scoping Hypomnema to the changed documents. Its lead had no code regression because the checker was not defective; this run carries the same changed-document invocation boundary.
- `SCG-S2-R1-01`, medium, and `SCG-S2-R1-02`, low, were fixed by preserving the then-current earliest-open-Wave rule and removing a self-staling count. PR #528 later displaced the former for the public contributor front door. The latter still governs: record a digest and timestamp, never a prose count presented as durable truth. The follow-up round was clean and `Leads not pursued: none`.

No finding is reopened. The design preserves the fixed parser boundary, retires #447's missing standing record, keeps legacy fields unknown, and carries #505 rather than absorbing it.

### Outside both

GitHub's own documentation says [assignees clarify who is working, but assignment requires repository write access](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users). That makes assignment a poor canonical signal for an external contributor. GitHub also says a [linked branch or pull request shows that a fix is in progress](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue), while [draft pull requests expose work in progress without making it mergeable](https://docs.github.com/en/pull-requests/reference/pull-requests). Those are strong corroborating trails, but they appear only after a branch and at least one commit exist. A structured issue comment is the earliest public surface an external contributor can author without repository write permission; it therefore wins as the claim record, subject to explicit authority and recovery below.

## 3. Constraints and non-goals

- Starting ref: `main` at `ab611eb96a6a9bddecb57bff2416641296e0a21e`; one existing repository, no new package or scaffold.
- Toolchain: Python 3.9.6 standard-library tests, Git 2.54.0, the bundled Protasis, Hypomnema, Imprimatur and Brevitas commands, and the root unittest suite. No dependency, network client, CI or schema runtime is added.
- Deliverable boundary: committed study, runbook and one numbered ADR with worked examples. The exact ADR number is the next unused number observed when the implementation step starts; a concurrent record must not be overwritten.
- Exact issue boundary: this run does not implement a command, alter Wave metadata, reopen a skill frontier, grant issue-write authority or replace the Shoggoth Interceptor's ranking rules. It also does not close #505 or claim its private repository state.
- One module, `intent-decision`: the ADR, its source study/runbook and their checks can ship and be verified together. There is no separately shippable runtime capability to decompose.

Always: preserve source URLs and observation times; run both Protasis modes, the changed-prose lints, Hypomnema and the root suite; keep named issue, candidate digest and claim state distinct. Ask first: any controller or selector implementation, external-repository change, dependency, CI change, GitHub issue comment, assignment, label or milestone mutation. Never: infer frontier intent from prose, parse Wave suffixes for priority, auto-write a claim, move a held frontier for this design, store raw issue bodies or prompts in the handoff, weaken an existing roster exclusion, or claim a command or remote state was checked when it was not.

## 4. Design options

### Option A: put `/fiat volunteer` inside Fiat

Fiat would parse natural language or a `--lane` flag, gather every candidate universe and then initialize itself. This gives one obvious command. It also makes the delivery controller own issue allocation, frontier ranking and maintenance scoping, duplicates Atlas and Kronos rules, and turns an issue-read failure into controller policy. Rejected because the easy spelling hides the largest boundary.

### Option B: lane-owned selection with one typed handoff

The caller chooses `named-issue`, `wave`, `frontier` or `maintenance`. The owning selector emits a closed `wildcat-volunteer-intent/v1` handoff from the exact candidate evidence it used. Fiat validates and binds that handoff at initialization but never selects. A public contributor front door may default a bare volunteer offer to `wave` because that policy is explicit there; direct Fiat invocation does not infer a lane.

This adds one small cross-component schema and adapters at producer boundaries. It preserves existing selectors, records why a universe was searched and lets Fiat check that its task issue matches the selected subject. Chosen because it is the lowest-comprehension design that does not collapse three owners into Fiat.

The producer and Fiat each retain one side of a bounded handoff; conversation state is never authoritative. Before any candidate read, the launcher writes an immutable request receipt in its producer-owned launch state containing the schema, intent kind, producer, observation time and canonical request digest. After the lane owner selects or refuses, it seals the complete canonical JSON handoff around that exact request digest and its same-read selection evidence. Fiat initialization validates those bytes, copies them to `.hexaemeron/volunteer-intent.json` in the run worktree and binds their SHA-256 into controller state before accepting the selected task. A missing producer receipt, changed request digest or Fiat copy mismatch refuses without creating run state. The producer copy explains why that universe was searched; the Fiat copy makes the delivered branch replayable.

The handoff is a closed tagged union:

- `named-issue`: one canonical issue URL, a normalized singleton issue snapshot and its digest;
- `wave`: the Atlas source identity, one same-read normalized candidate-set digest and count, generation/read metadata and a selected member;
- `frontier`: the Kronos scoreboard record identity, full candidate digest, selected held-job digest and maturity/park state;
- `maintenance`: one bounded output descriptor, target repository and scope digest; there is no ranked candidate set to pretend exists.

Common fields bind schema, intent kind, producer, observation time, evidence class, selected subject, claim state, consumer and the Promise Machine boundary. Raw issue bodies, comments, prompts and model reasoning do not enter the packet. A named issue always wins and must equal Fiat's task-issue receipt. Repository mutation or publication from maintenance requires a named issue before Fiat starts; a read-only local report may remain issue-free and need not invoke Fiat.

The handoff requires same-read selection evidence on every `wave` request; it does not introduce a periodic full-issue census or an age/count trigger. Atlas source freshness and dropped-issue evidence remain #505's decision. Wave milestone names, including suffixed names such as `5b` and `9b`, are opaque metadata and are never ordered by this selector.

The canonical early public claim is a contributor-authored issue comment carrying a version marker, intent digest, authenticated author as claimant and active state. No agent posts it without exact comment authority and the repository's publication gates. There is no clock-based auto-expiry: a resumed Fiat run can legitimately outlive a guessed lease, and silent expiry would authorise duplicate work. Recovery is an explicit release comment by the claimant or a maintainer, bound to the original comment URL and intent digest. An edited, malformed or conflicting claim refuses selection until a maintainer resolves it. Assignment, issue-number branches and linked draft or ordinary pull requests corroborate the claim and remain independent safety refusals under existing roster rules; the design weakens none of them.

### Option C: GitHub state alone

Treat assignment, branch or pull-request presence as both intent and selection evidence. This is inspectable and reuses the current roster, but assignment requires write access, branches and pull requests arrive late, and none says whether the contributor asked for Wave, frontier or maintenance work. Rejected because it records work state after selection, not the selection boundary itself.

### Option D: keep natural-language inference

Let “evolve”, “help”, “next” or similar text choose the nearest selector. It adds no schema and feels frictionless. The same phrase can choose a different universe after documentation or routing prose changes, cannot be replayed deterministically and is the defect #447 records. Rejected.

The chosen trade is a small protocol and explicit release action in exchange for deterministic ownership, replayable evidence and no new central selector. It deliberately trades automatic abandonment expiry for maintainer-visible recovery rather than risking two live Fiat runs on one issue.

## 5. Risk register seed

```risk-register
lane-inference | the conversational front door before a selector is chosen | bare help defaults only at the documented Atlas front door and direct Fiat never infers frontier or maintenance intent
preselection-intent | the producer boundary before any candidate read | an immutable producer receipt fixes schema intent kind and request digest before the lane owner searches
named-issue-precedence | the handoff union and Fiat task-issue receipt | a canonical issue URL overrides lane input and the same URL and number reach branch identity and closure
candidate-snapshot-drift | the remote issue or frontier set used for selection | the producer records normalized same-read bytes or their digest count source and observation time before choosing
split-read-race | an Atlas selection followed by a separate all-jobs request | a selected response carries the digest of the exact set used rather than borrowing evidence from a later request
snapshot-membership | the selected subject against the recorded candidate set | validation refuses a selection absent from the normalized set or carrying a mismatched digest
frontier-maturity | the Kronos-to-Fiat handoff | current ledger maturity park and held-job digest gates are preserved and rechecked before dispatch
maintenance-scope | caller-supplied upkeep with no candidate universe | one repository output and scope digest are required and public mutation additionally requires a named issue
claim-authority | the public issue-comment boundary | no automated comment occurs without exact authority publication gates and byte readback
claim-spoofing | untrusted comment authors bodies edits and competing claims | the claim binds GitHub author comment URL intent digest and state while malformed or conflicting active records refuse
claim-abandonment | a volunteer who starts and does not finish | claimant or maintainer posts an explicit digest-bound release and no guessed clock silently frees the issue
legacy-roster-safety | assignment branch and pull-request exclusions | existing exclusions remain refusals even when the canonical early claim comment is absent or released
public-overclaim | an ADR that can be mistaken for a shipped command | every example is labelled design-only and no README or launcher claims the packet is live
```

Warden must enumerate every id. A design-only round may mark runtime exercise not applicable, but it must still check that the ADR states the future refusal and does not imply implementation.

## 6. Glossary seeds

- **Volunteer intent:** the caller's explicit choice of one selection kind before candidate search.
- **Intent handoff:** the closed, digest-bound record a selector gives Fiat; it records selection evidence but grants no publication authority.
- **Named issue:** one canonical GitHub issue URL that overrides lane selection and becomes Fiat's task issue.
- **Wave lane:** the Wave Atlas's dependency-clear GitHub issue candidate universe; it does not mean choosing or ordering a Wave title.
- **Frontier lane:** the eligible governed held jobs Kronos ranks from current evolution ledgers.
- **Maintenance lane:** one caller-bounded output that does not claim a skill frontier advance.
- **Candidate snapshot:** normalized identifiers and eligibility facts, or their digest, from the same read used to choose.
- **Claim:** the structured public issue comment saying a contributor has begun the selected issue.
- **Corroboration:** assignment, issue-number branch or linked pull request evidence consistent with an active claim; existing safety exclusions still apply without it.
- **Release:** an explicit claimant- or maintainer-authored comment that ends one claim by URL and intent digest.

## 7. Sources

- `AGENTS.md`, `PROMISE_MACHINE.md`, `.agents/skills/promise-machine/SKILL.md`, `SHOGGOTH.md` and `.horos/boundary.json` at `ab611eb96a6a9bddecb57bff2416641296e0a21e`.
- `plugins/hexaemeron/AGENTS.md`; `plugins/hexaemeron/agents/surveyor.md`; and the complete Protasis, Phylax, Ephoros, Metron, Elenchus and Hypomnema contracts at the starting ref.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/kronos/SKILL.md` and `plugins/hexaemeron/skills/kronos/EVOLUTION.md` at the starting ref.
- `docs/how-to-help-shoggoth-study.md`, `docs/how-to-help-shoggoth-runbook.md`, `docs/how-to-help-shoggoth.md`, `docs/decisions/ADR-014-reallocate-the-live-wave-atlas-from-a-complete-census.md`, `README.md` and `scripts/build_contributor_guide.py`.
- Authoritative `audit/AUDIT.md`, read directly for the `Fiat task-issue branch names` and `Shoggoth contributor guide` ranges; verified view `audit/AUDIT_SYNOPSIS.md`, source SHA-256 `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`; whole-set synopsis check exit 0.
- [Issue #447](https://github.com/wildcat-finance/skills/issues/447), [issue #505](https://github.com/wildcat-finance/skills/issues/505), [PR #452](https://github.com/wildcat-finance/skills/pull/452), [PR #506](https://github.com/wildcat-finance/skills/pull/506), [PR #528](https://github.com/wildcat-finance/skills/pull/528) and [PR #596](https://github.com/wildcat-finance/skills/pull/596), read from GitHub on 25 August 2026.
- Shoggoth Interceptor `README.md`, `CLAUDE.md`, `bin/shoggoth.py` and `bin/console.py` at public commit [`23f9761a849980eecb89a0bd6fdcabba19d52c61`](https://github.com/laurenceday/shoggoth-interceptor/commit/23f9761a849980eecb89a0bd6fdcabba19d52c61).
- Live Wave Atlas [`GET /api/job`](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job) and [`GET /api/job?all=true`](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job?all=true), observed on 25 August 2026; the response's own generation time is recorded in section 2.
- GitHub Docs: [assigning issues and pull requests](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users), [linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue), and [draft pull requests](https://docs.github.com/en/pull-requests/reference/pull-requests).

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns the signal contract. This design-only delivery adds no unattended path, so it emits no runtime event, metric, trace or alert.

A later implementation must first answer four operator questions: Which intent kind and producer chose the path? Which exact candidate digest was searched? Did the selected subject remain eligible and unclaimed at Fiat initialization? If selection refused, which field or current-state check caused it? The intent handoff and Fiat initialization receipt are the bounded records for those answers; a future unattended selector must take their event and correlation shape through Ephoros rather than invent it in this ADR.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary review. This run reads public GitHub and Atlas state and writes documentation only. It introduces no executable input, credential, subprocess, dependency or write path.

The design names future boundaries without claiming their controls exist:

- Atlas or GitHub candidate data: worth taking selection integrity and availability; close with a capped closed schema, canonical URLs, normalized same-read digest, source identity and current-state recheck.
- Kronos records: worth taking frontier eligibility and held-job identity; close by consuming its validated scoreboard and rechecking ledger digest, maturity and park state rather than reparsing prose.
- Maintenance text: worth taking filesystem and publication scope; close with one normalized repository/output descriptor and reject free-form paths, shell text or unbounded outcomes.
- Issue comments: worth taking roster availability and write authority; treat bodies as hostile data, bind author/id/digest, cap parsing, require exact publication authority for writes and preserve assignments/branches/pull requests as independent refusals.
- Fiat handoff input: worth taking controller state and branch identity; validate before state creation, bind the packet digest once and refuse later replacement or selected-issue mismatch.

No credential, raw prompt, issue body or comment body belongs in the durable packet.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns performance evidence. No performance change, service or runtime path ships, so there is no performance budget and no Metron command for this delivery. Document length is controlled by Brevitas, not treated as a speed measurement. A future live selector may need a latency and cache-staleness budget, but setting one without a baseline here would violate Metron.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure work. The decision says a future consumer stops before Fiat state creation on an absent or unknown intent kind, malformed packet, candidate digest mismatch, selected subject outside the snapshot, named-issue mismatch, stale current-state check, active claim, mature or parked frontier, unbounded maintenance output or missing comment authority. It does not fall through to another lane.

For this design-only run, a failed Protasis, Hypomnema, Imprimatur, Brevitas or root-suite command blocks the documentation receipt and is rerun after the source is corrected. For later implementation, each observed failure gets the narrowest fixture that reproduces it, a guard seen failing on the unfixed parent and passing on the fix, then the focused and full suites under Elenchus's runner convention. No test is weakened to make a lane pass.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns record placement. The expensive-to-reverse choice is the boundary between lane-owned selection and Fiat consumption, including named-issue precedence, exact snapshot evidence and explicit claim recovery. It cuts across the repository, Atlas and Interceptor, so its standing home is the next unused numbered ADR under `docs/decisions/`. The ADR carries the rejected unified-Fiat, GitHub-only and natural-language designs and the worked cases. It resolves the open design home that `SCG-S1-R1-01` created in #447; the issue may close only after the ADR merges.

The committed `docs/volunteer-intent-study.md` and `docs/volunteer-intent-runbook.md` remain source and delivery records, not a second standing decision. A future Fiat consumer change records its implementation reason in Fiat's `EVOLUTION.md`; a Kronos handoff adapter records its generation in Kronos's ledger without reopening or advancing its mature frontier. Atlas and Interceptor changes belong in their own repositories and records. ADR-014 remains authoritative for Wave allocation, and #505 remains the separate home for Atlas freshness and dropped-issue evidence.

### Amendment -- 2026-08-25

**What changed.** The sealed `wildcat-volunteer-intent/v1` handoff binds an immutable claim requirement, not mutable claim state. After an issue-backed handoff is sealed, the authorised contributor publishes the active claim comment citing that handoff's SHA-256. The producer then emits a separate `wildcat-volunteer-claim-evidence/v1` record that binds the handoff digest, comment URL and id, authenticated author, exact comment-body digest, observed active state and observation time. Fiat validates the handoff and claim-evidence bytes together, rechecks the live comment, copies them separately to `.hexaemeron/volunteer-intent.json` and `.hexaemeron/volunteer-claim.json`, and binds both SHA-256 digests before creating run state. A release remains a later external record and never mutates either retained input.

**Why.** Audit finding `S1-R1-01` in `audit/rounds/fiat-447-distinguish-wave-frontier-and-maintenance-vo.md` showed that putting claim state inside the sealed handoff made the active comment either impossible to digest-bind or immediately stale, because that comment must cite the already sealed handoff digest.

**Steps touched.** Step 1's ADR decision and committed study copy.

**Still holding.** Step 1: entry holds; exit holds.
