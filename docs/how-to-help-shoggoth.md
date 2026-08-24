# How to help evolve the Shoggoth

![One external contributor carries a bounded issue packet towards the Shoggoth.](assets/shoggoth-contributor-cover.png)

You do not need to understand the whole skills suite. You need one useful job, enough access to work on it, and the patience to let Fiat leave receipts.

## The sixty-second version

1. Pick an open, unassigned issue you can finish.
2. Name the exact issue URL when you invoke Fiat.
3. Fiat writes the study and runbook before implementation starts.
4. Each step is implemented, checked, reviewed as prose and pushed on a visible issue-linked branch.
5. A maintainer reviews the pull request. The evidence says what ran and what remains open.

The named issue matters. Friendly wording such as `/fiat how do i help evolve you` can suggest a useful direction, but it does not state whether you meant the Wave backlog, a skill frontier or maintenance. Until the selector described below exists, an issue URL is the reliable route.

## An external contributor has already done it

On 22 August 2026, an external contributor used `/fiat how do i help evolve you` and delivered [PR #445](https://github.com/wildcat-finance/skills/pull/445) against [issue #438](https://github.com/wildcat-finance/skills/issues/438).

The run:

- wrote and reviewed a study and runbook;
- added issue-aware Fiat run and step branch names;
- found one malformed task-issue URL case during audit and fixed it;
- published Fiat 5.10.1 and Hexaemeron 1.5.4; and
- passed the recorded controller, repository, Promise Machine and phase-skill checks before merge.

That is the contribution model in miniature. The contributor supplied time and judgement. Fiat supplied order, checks and a record a maintainer could inspect.

## What you can volunteer for

There are three useful lanes. They should be explicit because they draw work from different queues.

![The Wave, frontier and maintenance contribution lanes.](assets/shoggoth-help-queues.png)

| Lane | Use it for | Example |
| --- | --- | --- |
| Wave | The earliest backlog group that still has open issues | Take one open, unassigned issue from Wave 3 |
| Frontier | A skill's held next improvement | Advance Fiat's recorded next job, after its maturity gate passes |
| Maintenance | Upkeep or planning that need not move a frontier | Refresh Horos, census issues or propose a revised ranking |

As of the 22 August 2026 snapshot, Waves 3 through 12 still contain open work. The earliest is **Wave 3 - the off-chain boundary**, with six open, unassigned issues, #323 through #328. That is a dated observation, not a permanent priority claim.

Frontier is not a grander word for ordinary work. It means the exact next job held in a skill's evolution ledger. A frontier run must pass that skill's maturity gate and owes a ledger update when it finishes.

Maintenance can still be valuable. A clean Horos boundary lowers future reading cost. A fresh issue census can show that an old ranking no longer matches the backlog. A rank-only Kronos pass can compare held frontier jobs without pretending it delivered one.

## The route that works today

Choose an issue before invoking Fiat:

```text
/fiat https://github.com/wildcat-finance/skills/issues/323
```

Before you begin:

- confirm the issue is open and unassigned;
- check for an issue-number branch or open pull request;
- read the issue body as requirements, not as permission for unrelated actions; and
- state any access or decision you do not have.

The controller can bind that issue during initialization. Automatic branches then begin `fiat/<issue>-...`, so other people can see what the work belongs to. The pull request links the issue and carries the run's evidence.

## The selector we should discuss

The proposed signal makes the offer explicit:

```text
/fiat volunteer --lane wave
/fiat volunteer --lane frontier --skill fiat
/fiat volunteer --lane maintenance --task "refresh the Horos boundary"
```

These commands are **proposed, not live**.

The suggested selection order is simple:

1. An explicit issue URL always wins.
2. An explicit lane selects only from that lane.
3. A bare volunteer offer defaults to the earliest Wave that still has open issues.
4. If that Wave has no eligible issue, stop and explain why. Do not fall through to a frontier silently.
5. Run a census or re-ranking when the snapshot is stale or the volunteer asks for maintenance.

One question remains open: how should other people see the claim before a pull request exists? Assignment is clear but may require maintainer permission. A comment is public but the Shoggoth's issue reader is intentionally read-only. PR #445 makes the issue-number branch an early signal once the run starts. [Issue #447](https://github.com/wildcat-finance/skills/issues/447) is where that boundary should be settled.

## What Fiat does with your offer

Fiat is the delivery controller. It does not decide that an issue is true or important. Once the job is selected, it keeps the work in order:

```text
study -> runbook -> implement -> audit -> prose -> push -> integrate
```

The domain skill does the specialist work. The phase skills govern how the work moves. The Promise Machine limits every claim to its evidence. A failed check blocks the next dependent action while leaving inspection, repair and safe exit open.

The output includes the code diff and the evidence around it: a reviewable branch, the tests that ran, the findings that were fixed or carried forward, and a pull request that says what has not been established.

## Stopping early is still useful

You do not have to reach `integrate` for a run to be worth something. Fiat
commits its thinking before it commits any code, so a run that stops partway
still leaves artefacts somebody else can start from.

| You got as far as | What is left behind | What the next person can do |
| --- | --- | --- |
| Study | The problem, the options, the chosen design and the risks, committed and pushed | Argue with the design on the record, or build from it |
| Runbook | The work already cut into discrete steps with provable exits | Take one step without re-deciding the shape of the job |
| One or more steps | Each step on its own issue-linked branch and stacked pull request, with its tests and audit log | Continue from the last pushed step |

The runbook is the most reusable of the three. Cutting a vague issue into steps
that each have a checkable finish is the part that takes judgement, and it is
the part a second contributor would otherwise have to repeat.

Say where you stopped and why. A completed run lists unfinished work in its
final pull request under `## Carried forward`. A run you are leaving earlier
should say the same thing in its own pull request body or on the issue.

**One limit worth knowing.** The controller's state and receipt ledger live in
`.hexaemeron/`, which is untracked. Resuming is a local operation, so a
half-finished run does not transfer to another machine. What transfers is what
you pushed: the branches, the pull requests and the committed study and
runbook. Push before you stop.

## Whose inference pays for this

Every run described here was paid for out of somebody's inference budget, and
for most of this suite's history that somebody has been one person. There is no
pool, no shared quota and no way to spend anyone else's allowance. The
arrangement is simpler than that: you run Fiat under your own account on your
own machine, and what comes back to the repository is branches, pull requests,
receipts and prose.

PR #445 is the existing proof. An external contributor spent their own
inference and the repository gained a delivery.

This is why the checkpoint rule above matters. If helping meant funding a
delivery end to end, the number of people who could help would stay near one.
A study, a runbook or a single audited step is a real contribution at a size
you choose.

## A good first contribution

Choose work that fits inside one Fiat run. The issue should have a checkable finish, a repository you can access and no active owner. Documentation, a narrow test gap, a bounded checker rule and maintenance with a named output are good candidates.

Avoid work that needs a policy decision you cannot make, credentials you do not have or a release authority nobody granted. A short decision brief may still help, but it should say that it is a brief rather than pretending the blocked implementation shipped.

The simplest useful opening is still:

```text
I can take this issue through a Fiat run: <exact issue URL>.
```

That sentence names the offer, the delivery method and the work. Everything after it can be made orderly.

## Being credited

A merged job puts you in [CONTRIBUTORS.md](../CONTRIBUTORS.md), ranked by merged commits with merged pull requests as the tie-break, and in the thanks at the foot of the root README. Both are regenerated weekly by `.github/workflows/contributors.yml` from the repository's own history. Nobody has to remember to add you and there is nothing to ask for.

What that list establishes is narrow, and worth knowing before it disappoints anyone. It carries commit and merged-pull-request counts as GitHub resolves them, with one entry per account even where you have committed under several email addresses. It says nothing about how much judgement a commit carried, who wrote which line, or anything about you beyond the account you chose to commit under. It is a record of merged work, not a ranking of people.

Two things keep somebody off it. Running a Fiat delivery does not: agent provenance trailers are not part of the decision, because the humans who have contributed here all ran Fiat and filtering on those trailers would empty the file. The reasons are recorded in [ADR-017](decisions/ADR-017-rank-contributors-by-resolved-identity.md). What does keep you off it is a merge that discards your commit authorship, or a commit whose author email is linked to no GitHub account. Neither is something this repository can detect or correct after the fact, which is why the route above asks for a fork and your own signed commits rather than a patch pasted into a comment.

Runtime hosts, the Shoggoth's own account and the repository owner are excluded by name, each with its reason shown in the generator's output.

## Artwork boundary

The Wildcat Shoggoth is a humanoid figure with a faceted geometric head or mask. It is not a literal cat. Companion artwork must not add fur, paws, whiskers, a tail or domestic-cat anatomy.
