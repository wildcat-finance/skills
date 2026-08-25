# ADR-035: Select and schedule repository checks from one graph

## Status

Accepted, 2026-08-25.

## Context

The repository lists its checks as serial commands in `AGENTS.md`. That list
does not say which changed paths own a check, which other scopes consume the
changed surface, or which independent commands may run together. Contributors
therefore tend to run unrelated suites, while the largest Python suite still
runs in one process.

The same test tree creates disposable Git repositories for fixture history.
Those repositories inherited contributor signing configuration, even though
their commits are neither release evidence nor signature test subjects. A
default signer could prompt, stall or fail before the intended assertion ran.

Test discovery is not static. Audit work can add, remove or rename tests, and
some current IDs are generated dynamically and cannot be imported as dotted
names. Source may also change while a local run is in flight. A scheduler must
separate ordinary change between invocations from a changed source during one
attempt, and it must prove that a green result covers the exact tests it found.

## Decision

Use one versioned, declarative graph for repository ownership, checks and named
downstream dependencies. A single runner will combine requested scope with all
actual changed paths, close that set over the graph, take an independent
disposable snapshot, and execute the resulting plan under one process budget.
The graph must account for every governed path mechanically. It will not infer
ownership from runtime imports.

Each attempt discovers a fresh ordered test manifest from its snapshot.
Workers rediscover that same snapshot, verify the complete manifest identity,
and select already discovered test objects by canonical index. The coordinator
must prove that assignments are disjoint and that every discovered test
started and completed exactly once before it can report green. A later
invocation may have a different manifest without error. A source change during
an attempt supersedes that attempt and permits one fresh retry; repeated change
ends as `unstable-source`, not as a failed test.

The runner will derive a conservative default budget from available CPU and
quota signals and accept a positive explicit override. One global counter
covers suite processes, shards and ordered command groups. Timing history may
balance the current manifest only. It cannot select a test, suppress execution
or retain a pass verdict.

Snapshot repositories and non-signature test fixtures set repository-local
`commit.gpgsign=false` immediately after creation and before their first
commit. Signature-verification fixtures keep their existing signed, unsigned
and invalid-signature cases. The source checkout, global Git configuration and
contributor keys remain outside this boundary.

## Alternatives

- Set a process-wide signing override and keep the serial command list. This
  could hide a signature-verification defect, leaves fixture construction
  dependent on unmanaged sites, and does not address suite scheduling.
- Select changed files and pass divided dotted IDs to `python -m unittest`.
  Generated IDs are not importable names, separate launchers can exceed the
  intended process limit, and the scheme cannot prove that workers discovered
  the same tests.
- Commit one fixed manifest and permanent shards. Test changes would require
  scheduler maintenance, and new tests could be omitted by stale membership.
- Infer ownership from imports. Imports do not express prose checks, ordered
  build commands, shared contracts or every downstream consumer, so the
  inferred graph would be incomplete without a reviewable place to state the
  missing edges.
- Use the source checkout or a linked worktree as the execution snapshot.
  Either permits source movement during the attempt, and linked worktrees share
  repository configuration with the checkout they came from.

## Consequences

Maintainers gain one reviewable place to update ownership and dependencies.
Unknown or multiply owned paths, stale commands, dependency cycles, manifest
mismatches and incomplete execution refuse green. New, removed and renamed
tests need no scheduler constant; the fresh manifest is authoritative for its
own invocation.

Snapshot creation and worker rediscovery add work before assertions begin, and
the declarative graph becomes a maintained interface. In return, reports can
name the source, plan, capacity, assignments and exact execution record that
produced a verdict. Timing data remains disposable scheduling advice.

Disposable fixture commits no longer invoke contributor signers. This does not
weaken signed delivery commits or signature-verification tests. Hosted CI,
third-party dependencies and existing direct suite entrypoints remain
unchanged by this decision.
