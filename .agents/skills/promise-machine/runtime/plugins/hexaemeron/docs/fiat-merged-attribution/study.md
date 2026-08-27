# Study: preserve external contributor attribution through Fiat integration

Issue: [skills#466](https://github.com/wildcat-finance/skills/issues/466).
Target skill: Fiat, on the generation axis. The held frontier job
([skills#363](https://github.com/wildcat-finance/skills/issues/363)) is not
touched.

Assuming, unless corrected:

1. Python 3.12 or later and stdlib `unittest`, matching the rest of the
   controller. No new dependency: `hexctl.py` stays stdlib-only.
2. The run starts from `191f2ce1d60abb8068887095a8c39fb4341f0be6` on `main`,
   the merge of [PR #518](https://github.com/wildcat-finance/skills/pull/518).
3. `wildcat-finance/skills` is public, so a pushed commit's author name and
   email are already published in the repository. The privacy rule in the
   issue therefore constrains what `.hexaemeron` stores, not what git holds.
4. GitHub owns the contributor list and computes it on its own schedule. No
   receipt in this run can guarantee an entry appears there.
5. The repository keeps all three merge methods enabled. This run does not
   change repository settings.
6. Fiat runs under a person at a terminal. Nothing here ships an unattended
   process.

## 1. Problem statement

Fiat verifies that its own commits carry a valid signature, the two exact
provenance trailers, and no runtime-host author, co-author or byline. It does
not record who the author was, and it does not check that the identity survived
the merge into the base. The README tells a contributor that a completed job
merged with their authorship intact adds them to the contributor list
automatically, and nothing in the controller establishes the antecedent.

Build the missing binding, for two readers. An external contributor who takes a
queue issue and wants the merged work to leave them visible. A maintainer who
has to tell, from the record, whether it did.

A working prototype here means three things:

- `done push` records a bounded attribution record for the exact verified
  range: the GitHub account each commit is linked to, or an explicit null, plus
  a digest that identifies the author without publishing the address.
- `done integrate` refuses unless every identity recorded across the run is
  still attributable from the recorded merge commit, and records the mechanism
  that preserved it.
- The README and the contributor guide say what that evidence establishes and
  name the GitHub-side conditions the repository cannot control.

Demo path: replay `plugins/hexaemeron/docs/fiat-merged-attribution/proof.md`
in a clean checkout. It drives a run whose step commits carry an external
author, shows the push receipt holding that identity, shows the integration
receipt recording it preserved, and shows a rewritten merge refusing the
receipt.

## 2. Prior art

**In this repository.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
already holds the whole mechanism this work extends.
`verify_local_commit` reads the author with `git show -s --format=%an%x00%ae`,
passes it to `is_host_identity`, and discards it.
`inspect_pull_request` reads `author.login`, rejects the logins in
`HOST_PR_LOGINS`, and records url, head, base, head SHA, state and merge SHA.
`verify_github_commits` performs `GET repos/{repo}/commits/{sha}` for every
SHA in the exact pushed range and keeps only the SHA once verification reports
`verified: true` with `reason: valid`. That response already carries the linked
account, the author name and email, and the commit message. The evidence this
issue asks for is fetched today and thrown away.

`done_merge_step` is the precedent for re-establishing evidence later: when a
push receipt is missing or stale it re-resolves the remote branch tip, verifies
the local range again, and stores the result as `effective_push` rather than
rewriting the older receipt. Binding attribution at merge time fits the same
shape.

**The last two merged pull requests that changed Fiat.**
[PR #511](https://github.com/wildcat-finance/skills/pull/511) made the
controller reject known runtime-host authors, co-authors, pull-request accounts
and generated-by bylines, and recorded
[ADR-016](https://github.com/wildcat-finance/skills/blob/main/docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md).
It was a direct pull request, not a stacked Fiat run, and carried no
`## Carried forward` section. Its ADR states the gap this run closes: the rule
is prospective, and Fiat "fail[s] closed on the known host identities they can
inspect" -- a deny list, with nothing recorded about the identity that passed.
[PR #490](https://github.com/wildcat-finance/skills/pull/490) added the
Elenchus verdict receipt. Its run-level pull request,
[PR #493](https://github.com/wildcat-finance/skills/pull/493), carried four
items forward: issues 429, 453, 369 and 363. None concerns attribution, and
none is answered or displaced here. Issue 363 stays Fiat's held frontier job.

[PR #518](https://github.com/wildcat-finance/skills/pull/518) rewrote the
README and contributor guide two hours before this run started. It replaced the
stop-at-a-checkpoint promise with the current rule that an external contributor
must finish the run locally. It left the contributor-list sentence at
`README.md:60` untouched, and that sentence is what item 5 of the issue is
about.

**Concurrent work that depends on this run.**
[skills#515](https://github.com/wildcat-finance/skills/issues/515) names 466
as its dependency, "which makes the authorship evidence exist", and its
boundary states that it "does not change how #466 binds authorship at
integration time". A run for it is already in flight ahead of its dependency,
with three open stacked pull requests, 516, 519 and 520. Its diff against
`main` adds `CONTRIBUTORS.md`, `scripts/contributors.py`, its own tests, and a
`<!-- contributors:start -->` thanks block at the end of `README.md`. It does
not touch the contributor-list sentence at `README.md:60`, and it does not
touch `docs/how-to-help-shoggoth.md`, so the two runs edit different text in
the same two files. Its observation also settles a design question for this
one: it reports one human split across `dave@wildcat.finance` and a GitHub
noreply address, appearing twice in `git log` and once in GitHub's contributor
API. An email is therefore the wrong key for an identity, and the resolved
account is the right one.

**Audit records for Fiat.** `audit/AUDIT.md` holds the rounds for the
delegation-packets run that installed this machinery, the state-shape run, the
worktree run, the study-amendment run and the Elenchus verdict run. The
delegation-packets closing round records that the bounded signing review found
no gap in "owned local ranges, intermediate commit enumeration, branch-tip
checks, exact trailer counts, local signature checks, remote repository
identity, pushed PR topology, step-merge topology, input validation, resource
caps, no-shell execution or secret-safe refusals", and closes with "Further
leads: none". Its post-push merge incident is the origin of the merge-time
repair path. Two earlier Imprimatur rounds disclaim "model authorship beyond
the declared provenance rule" as outside their frontier. The Shoggoth
contributor guide rounds closed a risk id called `contributor-attribution`, but
that concerned the accuracy of the guide's account of PR #445 rather than any
controller evidence. No open audit lead covers merged authorship, so this run
opens the subject rather than resuming it.

**Outside.** GitHub's commits REST endpoint returns `author` as the linked user
account, or `null` when it cannot match the commit author email to an account,
alongside `commit.author.name` and `commit.author.email`. That null is the
mechanical form of the failure the issue calls an unlinked author identity.
`Co-authored-by:` trailers are how a second identity travels on one commit, and
the controller already parses them with `COAUTHOR_RE`. The repository currently
permits merge commits, squash merges and rebase merges; a squash replaces the
range with one new commit and a rebase rewrites every SHA, so neither leaves
the recorded commits reachable from the base.

## 3. Constraints and non-goals

Starting ref `191f2ce1d60abb8068887095a8c39fb4341f0be6` on `main`. Python 3.12
or later, stdlib only. Every new external read goes through the existing
bounded argv-only `bounded_git` and `bounded_gh` readers, which cap output,
forbid a shell and discard raw signature material. New state lives inside the
version-1 container spine `load_state` already validates.

The issue rules out recording private account data in `.hexaemeron`. It also
rules out inferring a real-world identity, creating a payment or membership
programme, and letting recognition weaken any signing, review, test or
integration gate.

Non-goals for this prototype:

- No change to repository merge settings, branch protection or GitHub
  configuration.
- No rewrite of historical commits or existing pull requests. ADR-016 already
  settled that the rule is prospective, and this run inherits that.
- No query of `GET /repos/{owner}/{repo}/contributors`, and no claim about what
  that list shows. Section 4 explains the rejection.
- No regeneration of `docs/pdf/how-to-help-shoggoth.pdf`. It is a hand-designed
  six-page artefact built outside the repository, and the guide paragraph this
  run adds is new text rather than a contradiction of what the PDF already
  says. Carried forward.
- No extension of `HOST_IDENTITY_NAMES`. Naming future hosts is a separate
  maintenance job.
- No `CONTRIBUTORS.md`, no README thanks block and no scheduled refresh. Those
  belong to [skills#515](https://github.com/wildcat-finance/skills/issues/515),
  which consumes this run's evidence.

## 4. Design options

**A. Record GitHub's own linkage at push, and check the merged state at
integrate.** Extend the bounded GitHub reader to return a closed attribution
record per SHA: the linked account login or an explicit null, the author name,
a SHA-256 digest of the lowercased author email, and the co-author identities
parsed from the message. Record it on the push receipt beside the verified
SHAs. At `done integrate`, require every identity recorded across the run to
remain attributable from the recorded merge commit, by one of two mechanisms:
the commit that carried it is an ancestor of the merge SHA, or the identity
appears as author or `Co-authored-by` of the merge commit itself. Record which
mechanism held. Refuse otherwise, naming the identity and the fault.
Trade: the refusal lands after the merge has happened, so it stops the claim
rather than the action, and recovery is a halt and a maintainer decision.

**B. Refuse the merge method up front.** Read the repository's merge settings
at `init` and refuse to run unless merge commits are permitted.
Trade: cheap, and it establishes nothing. Settings say what is possible, not
what a maintainer clicked, and a contributor cannot change the settings of a
repository they do not administer.

**C. Store the full author identity and compare literally.** Keep the name and
email on the receipt and compare strings.
Trade: the simplest comparison, and it writes an account email into
`.hexaemeron`, which the issue rules out. A `users.noreply` address is not less
private for being obscure.

**D. Ask GitHub whether the account is in the contributors list.** Query
`GET /repos/{owner}/{repo}/contributors` after the merge and require the login
to appear.
Trade: it looks like the strongest evidence and is the weakest. That list is
computed asynchronously and cached, so a query immediately after a merge
reports the state before it. A gate that fails for timing reasons gets
bypassed, and a bypassed gate is worse than none.

**Chosen: A, with one part of B.** A is the only option that binds the merged
state rather than an intention, a setting or a cache, and it needs no new API
surface: the fields come from a response the controller already fetches for
every verified SHA. From B it takes the useful half without the refusal -- the
`integrate` directive names the merge method that preserves attribution, so the
operator is told before the merge instead of refused after it.

Within A, the resolved account is the identity and the email digest only
corroborates it. Issue 515 found one person holding two author emails and one
GitHub account, so two digests can name one contributor while one account
cannot name two. A recorded login therefore matches on the login; a digest
carries the comparison only where the account is `null` and there is nothing
else to compare.

What A trades away is prevention. Fiat cannot stop a maintainer choosing Squash, so it
guarantees only that a run cannot be recorded as complete while claiming an
attribution the base does not carry.

## 5. Risk register seed

The audit loop should look hardest at the new untrusted fields and at the
distance between what the receipt records and what the README says. Two
concerns deserve prose beyond their line. First, `author: null` is the ordinary
case for a contributor whose commit email is not on their account, so the
control is that null is recorded as null and never coerced into a truthy
placeholder; a refusal has to be able to say "this commit is not linked to any
account" without inventing one. Second, the commit message is attacker-
influenceable text, and the trailer parser is the one place a crafted line
could add an identity the signer never claimed.

```risk-register
attribution-null-login | the GitHub commit payload's author field | an unlinked author records explicit null, never a truthy placeholder, and the refusal names the commit
attribution-private-email | state and ledger bytes under .hexaemeron | no author email, account email or display-name-plus-email pair is stored; only a digest and a public login
attribution-unbounded-field | the GitHub JSON reader | every newly read field is type-checked and length-capped before it is recorded, and a malformed or oversized payload refuses
attribution-coauthor-parse | the commit message trailer parser | a crafted trailer cannot inject a second identity, evade the host-identity check or duplicate a recorded one
attribution-rewritten-merge | the base after a squash or rebase merge | a merge that dropped a recorded identity refuses the integration receipt rather than recording it as preserved
attribution-overclaim | the README and contributor guide statement | the published text claims only what the receipt establishes and names the GitHub-side conditions the repository does not control
attribution-ancestor-check | the local merge-base --is-ancestor reader | argv-only with no shell, and a nonzero exit is read as not-an-ancestor only when the call itself ran
attribution-state-shape | the version-1 state container spine | new receipt containers validate under the existing load_state contract rather than beside it
```

## 6. Glossary seeds

- **Attribution record.** The closed per-commit structure this run adds to a
  receipt: linked login or null, author name, author email digest, roles.
- **Linked account.** The GitHub account the commits endpoint returns in
  `author`, matched from the commit author email. Null when unmatched. The
  primary key for an identity, because one person may hold several emails and
  one account.
- **Email digest.** SHA-256 of the lowercased, stripped author email.
  Corroboration, and the only comparison available when the account is null.
- **Preserved merge.** A merge after which a recorded commit is still an
  ancestor of the base tip.
- **Rewritten merge.** A squash or rebase merge, after which it is not.
- **Host identity.** A runtime or model account, per ADR-016. Never an author.

## 7. Sources

- [skills#466](https://github.com/wildcat-finance/skills/issues/466), the
  observation this run answers.
- [skills#515](https://github.com/wildcat-finance/skills/issues/515) and its
  open stack, 516, 519 and 520, read for the dependency it declares on this
  run and for its split-identity finding.
- `docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md` and
  `ADR-011`.
- Merged pull requests 511, 493, 490 and 518, read in full for what each
  carried forward.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
  `2ae7f06cef8eaad8f01b4d2511550e5043d40b6fd5d75c6a875a19b039258f7c`.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`.
- `plugins/hexaemeron/skills/VERSIONING.md`, for the generation axis.
- `audit/AUDIT.md`, the Fiat rounds between the delegation-packets run and the
  Elenchus verdict run.
- `README.md:57-61`, the statement item 5 of the issue is about.
- GitHub REST: `GET /repos/{owner}/{repo}/commits/{ref}`, for the `author`
  linkage and `commit.author` fields.
- `gh api repos/wildcat-finance/skills`, for the enabled merge methods.

## 8. Signals, and the questions behind them

Fiat runs under a person at a terminal, so there is no pager and no unattended
process. The receipts and the hash-chained ledger are the record somebody reads
afterwards, and three questions have to be answerable from them.

- *Did this contributor's authorship reach the base?* The integration receipt's
  attribution block, read through `hexctl status` and `hexctl verify`. Step 3.
- *Which identity did this run publish under, step by step?* The push receipt's
  attribution list. Step 2.
- *Why did integrate refuse?* The refusal names the identity and which of the
  faults it found, and the ledger holds the event. Steps 2 and 3.

[ephoros](../../skills/ephoros/SKILL.md) owns what those emissions must carry. No new
metric, log sink or alert: a controller command that exits non-zero with a
named reason is the emission here.

## 9. Boundaries, per capability

[phylax](../../skills/phylax/SKILL.md) owns the boundary list and the controls; this
names the four boundaries the run opens and feeds them to item 5.

- **New GitHub JSON fields** (step 2). Worth taking: the linked account and the
  author identity. Control: closed shapes, explicit type checks, length caps,
  and refusal before any state or ledger mutation. `attribution-unbounded-field`,
  `attribution-null-login`.
- **Commit message trailers** (step 2). Worth taking: a second identity on one
  commit. Control: the existing `COAUTHOR_RE` full-match parse, the existing
  host-identity check applied to every parsed identity, and a bounded count.
  `attribution-coauthor-parse`.
- **A new local git read** (step 3). Worth taking: whether a recorded commit is
  an ancestor of the merge. Control: `bounded_git`, argv-only, no shell, and a
  nonzero exit distinguished from a failed call.
  `attribution-ancestor-check`.
- **Persisted state** (steps 2 and 3). Worth taking: an identity comparable
  across phases. Control: digest and public login only, inside the version-1
  container spine. `attribution-private-email`, `attribution-state-shape`.

## 10. The budget, or its absence

None, and no performance claim is made. The push-phase attribution adds no
request: it reads fields from the response `verify_github_commits` already
fetches per SHA. Integrate adds at most one `merge-base --is-ancestor` per
recorded commit, bounded by the existing `GIT_PATHS_MAX` cap on a range.
[metron](../../skills/metron/SKILL.md) owns budgets, and it also forbids a
speed-motivated change without a recorded before and after, so no step in this
runbook may make one.

## 11. The fail-closed posture

A malformed, absent or ambiguous attribution field refuses the receipt before
any state or ledger mutation, in the manner every other Fiat gate already
uses: name the exact fault, change nothing. At integrate, a recorded identity
that cannot be found on the merged base refuses the receipt and the run halts
with the blocker on the ledger rather than recording a preserved claim.

[elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard rule.
Every fix in this run lands with a regression that fails against the unfixed
controller and passes after it, in
`plugins/hexaemeron/tests/test_hexctl.py`. The runner contract each step
carries is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
writing an `elenchus.unittest.v1` report.

## 12. Decisions and their homes

[hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record and
where each lives.

- **ADR-017**, `docs/decisions/`, written in step 1: the stored attribution
  shape is a digest and a public login rather than an email, and the claim is
  bound at the receipt rather than by gating the merge method. Both are
  expensive to reverse: the first is a persisted state format that later
  receipts read, the second is a published gate other runs depend on.
- **The EVOLUTION row**, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, in
  step 4: one generation entry, `fiat-v5.14.1`, retaining the
  `state-shape-validation` revision, its digest and the held issue 363 target
  byte for byte.
- **The public statement**, `README.md` and `docs/how-to-help-shoggoth.md`, in
  step 4: what the evidence establishes and what GitHub controls.
- **The promise boundary**, the Fiat `SKILL.md` Promise Machine contract, in
  step 4: `fiat-final-integration` gains the attribution evidence and states
  plainly that it does not establish that GitHub will list the contributor.

Nothing else in this run is expensive enough to reverse to earn its own record.

## Boundaries the study must state

**Always.** Both suites before any implement receipt:
`python3 -m unittest discover -s tests` and
`python3 plugins/hexaemeron/tests/run_tests.py`. The Imprimatur lint on every
shipped document, then the Vulgate mask. The Protasis checker on the study and
the runbook. `python3 scripts/promise_machine.py check` after any change to
`hexctl.py`, with the three `fiat-*` runtime digests in
`tests/promise_machine_coverage.json` refreshed in the same step. A Horos
rescan after any docs change.

**Ask first.** Adding a dependency. Changing the shape of an existing recorded
receipt field rather than adding one. Touching CI. Changing repository merge
settings or branch protection. Extending `HOST_IDENTITY_NAMES`. Regenerating
the printable PDF.

**Never.** Store an author or account email in `.hexaemeron`. Weaken the
signature, trailer, GitHub-verification, review or test gates to let an
attribution check pass. Rewrite a historical commit or an existing pull
request. Claim the contributor list will update. Delete a failing test to make
a suite pass. Claim a command ran when it did not.

### Amendment -- 2026-08-24

**What changed.** Six corrections to step 4, all forced by work that landed on
`main` after this run's steps began. The ledger row is `fiat-v5.15.1`, not
`fiat-v5.14.1`, because the Sapheneia audit-record run took `fiat-v5.14.1` on
`main` at `8e2a9cd`. The decision record is
`docs/decisions/ADR-018-bind-merged-authorship-to-the-integration-receipt.md`,
not ADR-017, because the same run took `ADR-017-gate-durable-agent-prose.md`;
step 4 renames the file this run already committed and updates every reference
to it. Hexaemeron moves to `1.5.8` in all three manifests, not `1.5.7`, which
is now the version on `main`; `tests/test_version_propagation.py` moves with
it, and `tests/test_evolution_contract.py` moves from `fiat-v5.14.1` and
`ADR-017` to `fiat-v5.15.1` and `ADR-018`. Every audit round from step 3 round
2 onward declares `--audit-filter sapheneia:sapheneia` and has its record
shaped by the bounded Sapheneia durable-record pass before append, because the
controller governing this run now refuses a round without that declaration.
Item 3's non-goal about the printable PDF is withdrawn: `main` at `6c98a72`
added `scripts/build_contributor_guide.py`, which generates
`docs/pdf/how-to-help-shoggoth.pdf`, so step 4 regenerates it with that script
rather than recording an absence. And the prose baseline moved: the claim to
correct now reads that if the result is merged with your human authorship
intact, GitHub includes you in the repository's contributor history, at
`README.md` lines 73 to 75.

**Why.** Three runs merged into `main` between this run's step 1 and step 4.
Two of them took the version number and the ADR number this run had reserved,
one changed the audit-round receipt contract under a live run, and one rewrote
both prose files step 4 has to edit. None of it changes the design in item 4 or
the decision in item 12; all of it changes names, numbers and one non-goal.
Step 4 is authored on this run's older prose baseline, because a step branch
cannot merge `main`: the signed-range gate would refuse `main`'s commits, which
do not carry this run's provenance trailers. The correction therefore reaches
the current text in the one permitted `sync-run` merge at integrate, and that
resolution is part of the integration rather than of step 4.

**Steps touched.** Step 4, in its exit, its files and its tests.

**Still holding.** Step 4: entry holds; exit holds.
