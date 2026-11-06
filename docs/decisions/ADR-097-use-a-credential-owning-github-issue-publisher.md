# ADR-097: Use a credential-owning GitHub issue publisher

## Status

Accepted, 2026-09-12.

Stable identity: `adr/use-a-credential-owning-github-issue-publisher`.

This decision covers the issue #925 component prototype. Installing it on a
live host remains a separate privileged transition.

## Context

`wildcat-finance/skills` requires agent-authored issue prose to pass one
ordered Sapheneia, Imprimatur, Vulgate, Imprimatur sequence before publication.
GitHub does not enforce that sequence. The current local App helper lets any
process that can read the App PEM mint an installation token and call the issue
endpoint directly.

Issue #855 is the reproduced specimen. Its authoring trace moved from a local
candidate to an App token and GitHub issue POST without evidence from any of
the four prose passes. Adding checks to one helper would leave the PEM,
sourceable token variables, and token-only route under the same process
identity.

The authority boundary must own the check. A request that fails before that
boundary must have no route to the credential or issue mutation.

## Decision

Use the selected `isolated-publisher` design: one credential-owning service for
GitHub issue creation. On macOS, run it as a dedicated non-login account
through a system LaunchDaemon. Only that identity may read the App PEM. Agents
receive group access to one Unix socket and no key access.

The service accepts one closed, bounded, versioned request. It checks the queue
prefix, body opening, host structure, protected inventory, ordered record
subjects, and digest continuity. Sapheneia and Vulgate remain recorded
judgements. The service reruns pinned Imprimatur over the shaped candidate and
exact final candidate.

Only after admission may the service sign an App JWT, exchange it for a token
narrowed to `wildcat-finance/skills` and `issues:write`, and make one issue
POST. It retains the final title and body in memory from the final check through
the POST. The client supplies no path that can be reopened. A confirmed create
is never retried automatically.

The component uses one length-prefixed request on a fixed Unix socket. The
client checks socket type, owner, group, and mode; the server rejects root and
its own service identity as callers. The signer fixes the executable,
arguments, service-owned PEM path, stdin, output ceiling, and timeout. The
HTTPS transport fixes TLS validation, GitHub host, installation, repository,
API version, routes, methods, response ceilings, and redirect refusal.

An uncertain POST returns `create-indeterminate` with the request digest and no
retry. A confirmed create becomes `published` only after authenticated and
anonymous reads match its number, canonical URL, title, and body. Otherwise it
returns `created-but-unverified`. Fixed, content-free events and the terminal
result retain attempt counts and cleanup state without prose, credentials,
headers, response bodies, or raw errors.

The client receives a content-free result. It never receives a JWT,
installation token, PEM bytes, header, raw response, or general HTTP
capability. The sourceable token-variable and token-only helper contracts are
not part of the replacement interface.

## Alternatives

### Add checks to the shell helper

Rejected. A same-identity caller can source the helper, invoke another route,
or read the PEM and mint directly.

### Watch `fw51.md`

Rejected. The policy would attach to one mutable path rather than issue
authority. Inline content, another file, or a direct API call bypasses it, and
file observation creates ordering races.

### Run a same-UID broker

Rejected as the live boundary. It improves protocol testability but leaves the
agent able to read the key, inspect or replace the process, and mint outside
the protocol.

### Use a shared remote gateway

Deferred. It adds remote authentication, multi-tenant state, availability, an
administrative API, and network exposure before one local boundary has been
proved.

## Consequences

The issue-publication operation becomes small enough to test as a closed
component. Missing, failed, reordered, or mismatched prose evidence refuses
before signer access. One process identity owns the App credential and the
last executable gate.

Deployment costs one privileged account, group, key move, socket, and
LaunchDaemon installation. Repository tests can prove the component and
deployment verifier. They cannot prove that a particular Mac applied those
predicates. A live-isolation claim requires a separately observed host
receipt; Step 1 establishes neither live deployment nor live isolation.
Step 2 establishes those component paths with injected signer, transport,
filesystem, peer, and clock doubles, plus a local socket-pair check of the
macOS peer-credential ABI. It makes no live GitHub call, reads no real PEM, and
still establishes neither live deployment nor live isolation.

Root and administrators remain outside the promise. Sapheneia and Vulgate
records remain checked records of judgement rather than semantic proof.
Version 1 covers issue creation in `wildcat-finance/skills` only. Pull requests,
comments, edits, closure, and the zero-check problem in #855 remain separate.
