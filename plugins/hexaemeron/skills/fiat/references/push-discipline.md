# Push discipline

The pushed branch and pull request are the delivery trail. Fiat does not
create or require a GitHub issue.

## Branches and commits

- Branch as `step-<n>-<slug>` where repository conventions allow.
- Keep commits scoped to the current runbook step.
- Preserve the target repository's required commit format and checks.
- End every Fiat-created commit message, after a blank line, with both exact
  provenance trailers:

  ```text
  Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
  Wildcat-Origin: shoggoth
  ```

## Pull request

Push the branch, then open a pull request using the title and body prepared in
the prose phase. The body states what changed, why, where the audit record
lives, and how to run the proof. Do not invent an issue reference. Include one
only when the user independently supplied a relevant issue.

Before opening the pull request, make sure the target repository has the
`origin:ai` label. Append `<!-- wildcat-origin: shoggoth -->` to the prepared
body, then apply `origin:ai` in the same `gh pr create` command. Read the pull
request back from GitHub and confirm that both markers persisted before
receipting the push phase.

Extra labels are additive. Do not remove or rename either provenance marker.
Do not amend a pre-existing human commit or relabel a pre-existing human pull
request merely because Fiat later resumes work around it.

Verify the pull request URL after creation. Never merge it and never
force-push over another person's work.

## Receipt

```text
hexctl done push --pr-url <url>
```
