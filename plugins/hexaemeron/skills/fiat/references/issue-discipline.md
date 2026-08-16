# Issue discipline

The issue is a precondition for the step, and the yardstick while working
it. It describes the PR before the PR exists.

## Structure

Exactly these sections, in this order (template:
[assets/issue-body.md](../assets/issue-body.md)):

```markdown
## Description
## TODO
## Acceptance Criteria
## User Value / Need
```

`Description` is prose: current state, intended change, boundaries. The
other three are checklists. `TODO` holds concrete implementation moves.
`Acceptance Criteria` holds observable, testable outcomes -- each box a
thing a reviewer could verify from the pushed state. `User Value / Need`
names who benefits and what problem goes away; a box per claim keeps it
honest. No placeholders, no invented facts.

## Routing

Create the issue with `gh issue create` from the bundled template
(`assets/issue-body.md`), apply `origin:ai` in that same create command,
and reconcile by editing the issue body with `gh` after the push. Before
receipting the issue phase, read the issue back from GitHub and confirm that
the label and `<!-- wildcat-origin: shoggoth -->` body marker both persisted.

## Provenance

Every issue, sub-issue, commit and pull request created by Fiat is AI-origin.
Stamp each one before the event reaches GitHub:

- Issues and sub-issues: apply the `origin:ai` label at creation and keep
  `<!-- wildcat-origin: shoggoth -->` in the body.
- Commits: end the message, after a blank line, with both exact trailers:

  ```text
  Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
  Wildcat-Origin: shoggoth
  ```

- Pull requests: apply `origin:ai` in `gh pr create` and keep
  `<!-- wildcat-origin: shoggoth -->` in the body passed to that command.
  Read the pull request back from GitHub and confirm both markers before
  receipting the push phase.

Extra labels are additive. Do not remove or rename either provenance marker.
Do not add them to a pre-existing human issue, commit or pull request merely
because Fiat later resumes or continues work around it.

## Sub-issues

Permitted only when a topic is bound to the step so tightly that a separate
top-level issue would confuse a reader, or when work discovered mid-step is
genuinely separable (its own acceptance criteria, sequencing, or delivery
timing). Same four sections. Attach through the native sub-issue
relationship, keep the parent as the step's issue of record, and never tick
a parent box merely because a sub-issue now exists. Record each one on the
receipt with `--subissue-url`.

## Delivery trail

- Branch: `issue-<n>-<slug>` where conventions allow.
- Commits: `Refs #<n>` plus both exact Shoggoth trailers.
- PR body: reference the issue prominently and retain the hidden Shoggoth
  marker. `Closes #<n>` only when the merge alone satisfies every acceptance
  criterion; otherwise `Refs #<n>`.

## Reconciliation (push phase)

After the PR is pushed, reread the issue body and compare every unchecked
box against the pushed state. Tick a box only when that state satisfies it, with
citable evidence -- partial, unverified, review-dependent, and merge-dependent
items stay unchecked. All boxes ticked: close the issue. Any box unticked:
leave it open. The push receipt refuses a state that breaks either rule:

```text
hexctl done push --pr-url <url> --checkboxes 6/6 --issue-state closed
hexctl done push --pr-url <url> --checkboxes 4/6 --issue-state open
```

Then tick the epic's box for this step.
