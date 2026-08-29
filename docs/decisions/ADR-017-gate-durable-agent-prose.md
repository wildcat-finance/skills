# ADR-017: Gate durable agent prose before publication

## Status

Accepted, 2026-08-24.

## Context

Sapheneia shaped the agent's session replies but had no bounded operation for
prose that outlives the session. Fiat audit records, GitHub issue submissions,
and GitHub issue comments can therefore keep process narration or lose visible
working state unless each owning workflow supplies its own rule.

The three surfaces have different required structures. Audit records belong to
Fiat's audit contract. Issue titles and bodies belong to one of the four queues
in [ADR-009](ADR-009-four-issue-queues-and-their-titles.md). Comments belong to
the workflow that posts them. One common template would erase those
differences.

The repository also has no central command for issue and comment publication.
A local instruction can govern its agents, but it cannot make GitHub refuse a
human or external tool that skips the instruction. Open issue #421 owns a
generic executable Sapheneia pre-send checker; this decision does not implement
it.

## Decision

Sapheneia owns a second promise, `sapheneia-durable-record-shape`, for one
agent-authored audit record, one GitHub issue title and body, or one GitHub
issue comment. The operation freezes the protected evidence inventory and
required host structure, then removes only claim-neutral connective or process
prose. It does not activate session-wide response shaping and does not rewrite
an existing record.

Repository agents prepare issue submissions and comments in this order:

1. freeze the queue format, host structure, and protected evidence inventory;
2. apply the bounded Sapheneia operation;
3. run Imprimatur and clear its reported defects;
4. apply Vulgate to the surface only and compare content with the source; and
5. run Imprimatur again on the exact bytes to be published.

The second Imprimatur run matters because Vulgate changes bytes after the first
run. A failed check, changed queue prefix or body opening, missing protected
item, or content mismatch blocks publication by a compliant agent. GitHub is
not the enforcer.

Fiat may record an exact declaration that an audit candidate crossed the
Sapheneia operation. That receipt establishes the declaration, not semantic
correctness of the prose. The controller change belongs to the next runbook
step and remains separate from this contract decision.

## Alternatives

- **Use instructions without a Sapheneia promise.** This leaves the canonical
  skill unable to say what an audit, issue, or comment pass preserves.
- **Wrap every GitHub publication command.** This adds credentials, network
  calls, and bypass paths while taking over work already held by #421.
- **Use one terse template for all records.** This conflicts with the audit
  schema, the four issue queues, and comments owned by other workflows.
- **Rewrite existing records.** This would change append-only evidence and
  historical issue context. The rule is prospective.

## Consequences

Agents have one bounded contract for preserving evidence while shortening the
three named durable surfaces. Session activation stays explicit. Issue and
comment publication gains a fixed Sapheneia, Imprimatur, Vulgate, Imprimatur
sequence without claiming a GitHub-side gate.

The semantic Sapheneia and Vulgate checks remain model-checked. Imprimatur can
check only the exact bytes it receives. A later executable checker, GitHub App,
or publication wrapper needs its own promise, credentials boundary, and
evidence; this decision supplies none of them.
