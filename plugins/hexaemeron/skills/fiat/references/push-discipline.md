# Push discipline

The pushed branch, merged pull request, and closed task issue are the delivery
trail. Fiat does not create an issue unless the user or a higher-priority
target-repository rule requires one. If one exists, record it as
`task_issue` and close it before the terminal receipt.

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

## Pull request and closure

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

Verify the pull request URL after creation. Wait for required checks, convert
the PR from draft if necessary, then merge it using the repository's permitted
merge method. Enable auto-merge when checks are still running and the host
supports it. Never force-push over another person's work and never bypass a
required review or failing gate.

After merge, verify the merge commit and delete the remote task branch where
repository policy permits. If a `task_issue` receipt exists, close that exact
issue with a short comment linking the merged PR. A plan or implementation is
not complete while its own branch, PR, or issue is awaiting routine agent
action.

If GitHub rejects the push or merge, a required independent approval cannot be
self-supplied, or an external gate fails, record `hexctl halt --reason ...`
with the exact blocker. Do not call the run complete.

## Receipt

```text
hexctl done push --pr-url <url> --head-commit <sha> --merge-commit <sha> \
  [--closed-issue-url <url>]
```
