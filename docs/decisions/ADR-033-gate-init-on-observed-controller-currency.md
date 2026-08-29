# ADR-033: Gate init on observed controller currency

## Status

Proposed, 2026-08-24. Recorded for the controller currency guarantee
delivery ([study](../fiat-controller-currency-study.md),
[runbook](../fiat-controller-currency-runbook.md)), which holds the three
decisions below expensive to reverse.

## Context

A Fiat run is driven by whatever controller was installed when it started,
and until this change nothing in the run's evidence said which one that was.
On 2026-08-24 all fourteen wildcat-labs plugins were re-pinned at 17:18Z, and
an hour later `origin/main` stood 10 commits ahead of every pin, because Fiat
and Kronos runs merge their own pull requests. `claude plugin update`
reported `already at the latest version` at exit 0 while copying nothing,
since it compares version strings that had not bumped. The controller's own
`stale_controller()` warning compares version strings against a possibly
stale checked-in copy and cannot see the gap either. A daisychained loop
therefore executes a controller pinned before the chain started, silently.

Three choices behind the fix would be expensive to reverse once receipts
depend on them: whether `init` may read the network at all, what evidence a
refusal requires, and what vocabulary the recorded verdict uses.

## Decision

**Init observes the network.** `hexctl init` makes one bounded `git
ls-remote` from inside the marketplace clone, on the git-backed route only,
under the controller's existing reader discipline: fixed argv, no shell,
credential prompts disabled, the `GIT_TIMEOUT` cap and the output cap. The
remote is named as `origin`, so only the clone's own configuration under the
plugins root derived from the controller's resolved file decides where the
read goes; no target-repository or environment value reaches the call, and
no URL, raw child output or registry byte appears in any diagnosis,
transition or receipt. Managed and in-repo routes read nothing remote.

**Refusal only on proof.** `init` refuses, with exit 1 and before any
worktree, state, ledger or breadcrumb exists, exactly when the recorded pin
and an observed upstream head both exist and differ. Everything the
observation cannot prove -- a missing or hostile registry, an unreadable
clone HEAD, a timeout, a malformed remote answer -- reads as `unknown`,
warns by name on stderr, and proceeds with explicit nulls recorded. The one
way past a proven `behind` is `--controller-currency-waiver '<reason>'`,
which records the reason into the init transition and receipt; an empty
reason is refused.

**The verdict vocabulary.** Every init transition and receipt carries the
controller's ledger version, its route (`git-backed`, `managed`,
`in-repo-source`, or `unknown` when the observation could not classify it),
the pin or null, the observed head or null, the waiver reason or null, and
one verdict from a closed set: `current`, `behind`, `no-pin`, `managed`,
`unknown`. `behind` means the pin differs from the head observed at init,
carrying the residual ambiguity of a rewritten branch rather than hiding it.
`unknown` is never promoted to either side. Runs recorded before this change
stay loadable and verifiable without the new receipt.

## Alternatives

- **Strengthen the procedure, change no code.** The repository already took
  this option once, and the measured 2026-08-24 failure happened under it: a
  procedure the controller does not enforce leaves no trace when skipped.
  Rejected.
- **Ancestry proof before refusing.** Fetching upstream into the marketplace
  clone and requiring `merge-base --is-ancestor` would distinguish behind
  from rewritten history, but init would then mutate shared host cache state
  outside the run and add a second network operation for a distinction that
  is rare on a protected default branch. Rejected; the verdict wording
  carries the ambiguity instead.
- **The controller updates itself.** Shelling out to the host installer from
  `init` would replace the controller's own bytes underneath a running
  process, may prompt, and cannot work on the managed route. Rejected;
  re-pinning stays with the host's installer and the agent driving it.
- **Refuse on `unknown`.** Fail-closed against outages as well as staleness,
  but an attacker or an outage that blanks one read could then stop every
  run on the host. Rejected; `unknown` proceeds with the gap recorded and
  named, which keeps the degradation visible without handing it a veto.

## Consequences

`init` gains at most one network wait bounded by `GIT_TIMEOUT`, and runs
that yesterday started silently on a stale pin now stop with the pin, the
observed head and the two exits stated. The guarantee is only as strong as
the network: a blanked read downgrades to `unknown` and proceeds, so the
receipt, not the refusal, is the durable evidence in that case.

The gate ships inside the artefact it gates, so it cannot govern the run
that writes it; it governs every run after the next re-pin. The waiver is
recorded evidence rather than a silence, and a receipt field that later
proves wrong points at the observation that produced it, because every value
is either observed or an explicit null.
