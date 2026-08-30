# Pull-request identity gate study

Assuming, unless corrected:

1. Issue #893 authorises the repository workflow, required-check, and review
   rules needed to reject governed work attributed to a runtime host.
2. This branch starts from the signed head of pull request #964 at
   `b3f7de8742f4e69a61a7ae969e23b73d728e9473`. Nothing from this study may be
   published until `main` equals that commit.
3. Ruleset `21830871` requires the current-base `invariants` and `plugins`
   contexts. Organization ruleset `16257211` requires a pull request but no
   approval. Ruleset `16257446` requires signatures and does not classify the
   author or committer.
4. The host sets in Fiat and `scripts/contributors.py` are the current
   executable interpretation of ADR-016. They are a known-host refusal set,
   not a claim that every future host name is already known.
5. Publication is by `laurenceday`; governed commits remain authored by
   Shoggoth and are signed with `B83B60AE16F5DD1A`.

## 1. Problem statement

GitHub's signed-commit rule establishes that GitHub accepts a signature on a
commit. It does not establish that the author or committer fields name the
contributing actor. Issue #893 carries the concrete counterexample: commit
`a597c21` was signed by a cloud-managed key and reported as verified while both
identity fields named Claude. With no required review, the same runtime host
can open and merge the pull request that carries it.

Success has two separately visible parts. Every pull request to `main` receives
one stable `identity` result produced by policy bytes from the protected base.
That result is green only when the pull-request login and every commit outside
the exact base reject no known host author, committer, co-author, or generated
byline. After that context is proved on an exact canary head, the repository
rules require it alongside `invariants` and `plugins`. The pull-request rule
then requires one approving review.

## 2. Prior art

ADR-016 classifies runtime hosts as execution metadata rather than authors.
ADR-052 separates the Shoggoth author from an explicitly authorised human
publisher, signer, and repository account. Fiat enforces both rules inside a
receipted run, and `scripts/contributors.py` carries the same three host sets
for repository-wide contributor classification. Tests already refuse drift
between those copies.

That controller gate is not a branch gate. A contributor can bypass Fiat, and
GitHub does not inspect the identity fields as part of `required_signatures`.
The new check therefore reuses the existing host-set semantics but runs at the
protected repository boundary.

GitHub documents `pull_request_target` as privileged base-context execution,
with `GITHUB_SHA` set to the last commit on the default branch, and warns
against checking out and executing untrusted pull-request code. It separately
requires a required status to succeed on the latest pull-request head. The
base-owned job therefore publishes one commit status to the event's validated
head SHA. The context is not added to the live ruleset until a canary proves
that exact association and source.

## 3. Constraints and non-goals

The workflow is unconditional for pull requests to `main` and has no path
filter. Its job and future required context are both named `identity`. It runs
with `contents: read` and the single additional `statuses: write` permission
needed to mark the validated event head pending, then success or failure. It
persists no checkout credential, references no repository secret, and has a
short timeout. Candidate commits are fetched from the fixed public repository
URL into a bare repository under the runner's temporary directory. The
pull-request tree is never checked out. Python imports and the executable
script come only from the exact base SHA checked out as the workflow workspace.

The workflow passes event values through environment variables rather than
interpolating them into shell source. The pull-request number is checked as
decimal before it enters the fixed `refs/pull/<number>/head` fetch. The policy
script validates full object identifiers, refuses a shallow object database,
disables replacement objects and inherited Git configuration, bounds the
commit count, each commit object's bytes, total bytes, command time, and output,
and reads commit objects only. It never runs a hook, build, dependency, or file
from the candidate.

The gate refuses known host names, addresses, GitHub logins, co-author trailers,
and generated-by lines using the same policy as Fiat. A Shoggoth author must be
the exact `Shoggoth <shoggoth@wildcat.finance>` identity and must carry exactly
one canonical co-author trailer and one `Wildcat-Origin: shoggoth` trailer. A
non-host human author is allowed without those Shoggoth trailers. The gate does
not infer whether a human publisher had authority, prove that an unfamiliar
future model name is human, or turn a signature into authorship evidence.
Those claims remain outside the available evidence.

Always: test the policy against every role and every commit in a range; prove
the workflow never executes candidate bytes; run the root suite, complete
plugin graph, policy lints, Promise Machine checks, Horos, and signature
verification; read each live ruleset before and after mutation. Ask first:
adding a bypass actor, weakening the host set, accepting an unknown payload
shape, or reducing the approval count after enforcement. Never: run candidate
code under `pull_request_target`, make a path-filtered required job, add the
required context before a head-bound canary, or treat the approval as proof of
authorship.

## 4. Design options

**A. Extend the signed-commit rule.** GitHub's rule has no author-policy input.
It cannot express ADR-016. Rejected.

**B. Run a normal `pull_request` workflow from the candidate merge ref.** This
attaches naturally to the pull request, but the pull request can alter the
workflow or script that decides whether it passes. Read-only credentials do
not make self-modifying policy trustworthy. Rejected.

**C. Run `pull_request_target`, check out the candidate, and execute its policy
script.** The workflow definition comes from the base, but the deciding code
does not. This is the unsafe checkout-and-execute shape GitHub warns about.
Rejected.

**D. Run base-owned policy over candidate commit objects in a bare repository.**
Chosen. The candidate supplies data only. No candidate tree becomes a working
directory or Python import root, and the script has fixed, bounded Git reads.
Because the native job belongs to the base SHA, the job uses `statuses: write`
only to publish `identity` against the validated event head. It posts pending
before any fallible checkout or fetch and resolves the status to success only
when the evaluation step succeeded; cancellation or publication failure leaves
the head pending. The trade is a two-stage bootstrap: merge the workflow before
it can run, then prove its exact-head status with a signed canary before changing
the ruleset.

## 5. Risk register seed

```risk-register
self-modified-policy | the pull request changes the gate that judges it | workflow and script are checked out from the exact base SHA as the workspace
candidate-execution | a hook import build or dependency runs from the pull request | candidate exists only as bounded commit objects in a bare repository
script-injection | event text enters shell source | expressions populate environment values and the only ref component is decimal-validated
partial-range | a shallow fetch hides an earlier host-authored commit | policy refuses shallow repositories and checks every commit in base..head under a count cap
replacement-object | Git replacement refs change the object inspected | policy sets GIT_NO_REPLACE_OBJECTS and uses a fresh bare repository
oversized-commit | attacker-controlled messages exhaust runner memory or logs | per-object total-byte commit-count output and timeout ceilings refuse first
policy-drift | Fiat contributors and the branch gate classify different hosts | root tests compare every host set and shared regex with the canonical controller
unknown-host | a future runtime name is not in the known set | no universal claim is made and policy extension remains fail-closed maintenance
missing-context | the base workflow cannot publish against the PR head | status is posted to the validated event head and a signed canary must prove it before ruleset mutation
false-green | an earlier step fails before the result is published | pending is posted first and only the evaluation step's success outcome selects success
publication-authority | candidate input redirects the writable status request | repository endpoint and context are fixed by base bytes and the head is full-lowercase-SHA validated
context-wedge | the ruleset requires a check that cannot run | bootstrap merges first and canary evidence gates the ruleset write
sole-party-merge | the author opens and merges the same pull request | organization pull-request rule requires one approving review after bootstrap
ruleset-drift | a narrow live edit drops signatures checks or conditions | mutate fresh full documents preserve every other field and read back immediately
```

## 6. Glossary seeds

Base-owned policy: workflow and script bytes read from the protected target
branch rather than from the proposed change.

Candidate object database: a bare Git repository that holds commit data for
inspection and has no checked-out candidate files.

Host identity: a name, address, login, co-author, or generated-by attribution
that the repository's ADR-016 policy classifies as a runtime rather than a
contributing actor.

Exact-head canary: a signed, public pull request used only to prove that the
`identity` context is produced by GitHub Actions for that pull request's current
head SHA before the context becomes required.

## 7. Sources

- Issue [#893](https://github.com/wildcat-finance/skills/issues/893).
- `SHOGGOTH.md`, ADR-016, ADR-018, and ADR-052.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and
  `scripts/contributors.py`.
- Live rulesets `16257211`, `16257446`, and `21830871`, read before design.
- GitHub's [secure `pull_request_target` guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
  [workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
  [commit-status API reference](https://docs.github.com/en/rest/commits/statuses),
  and [required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## 8. Signals, and the questions behind them

Ephoros applies. A green run prints the schema, exact base and head, validated
pull-request login, and commit count without printing addresses. A refusal
names the commit and identity role that failed. The explicit status links the
immutable Actions run and records pending, success, or failure. The canary
record must show the context name, GitHub Actions creator, and exact head SHA.
Post-write ruleset reads answer which
contexts, strictness, approval count, merge methods, and bypass actors now
control `main`.

## 9. Boundaries, per capability

Phylax applies. The GitHub event and candidate Git objects are hostile inputs.
The workflow has no write permission beyond commit statuses, no repository
secret, cache, candidate checkout, or candidate dependency installation. Its
status endpoint, context, remote URL, ref prefixes, argv, policy path, and
Python version source are fixed by base-owned bytes. The status target is a
full lowercase SHA from the event. The script reads only commit objects under
explicit shape and size limits. The candidate cannot alter an import because
the bare repository is never on `sys.path`.

## 10. The budget, or its absence

No performance improvement is claimed. The gate reads commit metadata rather
than trees or blobs and refuses more than 1,024 commits, more than 128 KiB in
one commit object, or more than 8 MiB across the range. Each Git command has a
ten-second timeout and the Actions job has a five-minute timeout. The normal
case is a handful of commit objects and should finish before the existing root
or plugin checks.

## 11. The fail-closed posture

Elenchus applies. A malformed identity, invalid UTF-8, absent object, shallow
history, host role, oversized range, command failure, timeout, mismatched event
head, missing status, wrong status creator, or ruleset readback mismatch is red
or blocks the next transition. The workflow does not downgrade an unreadable
identity to unknown. A canary whose context cannot be proved against its exact
head leaves the live required-check set unchanged.

## 12. Decisions and their homes

Hypomnema places the durable choice in
`docs/decisions/ADR-058-require-base-owned-identity-and-human-review.md`.
`scripts/check_commit_identity.py` owns the bounded commit-object policy,
`.github/workflows/identity.yml` owns hosted execution, and root tests own
policy parity plus workflow immutability. This study and the runbook remain in
`docs/pr-identity-gate/`. GitHub owns commit statuses and rulesets; exact API
readbacks are their receipts rather than a second repository configuration.
