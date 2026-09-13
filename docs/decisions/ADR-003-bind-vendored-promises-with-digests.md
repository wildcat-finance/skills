# ADR-003: Bind vendored promises with digests

## Status

Accepted, 2026-08-20; amended 2026-08-31. Promise Machine contract:
`promise-machine/v1`.

## Context

Five Hexaemeron skills derive from `https://github.com/pashov/skills.git` at
release tag `v28062026`. Four local instruction files are byte-identical to
their upstream paths. The top-level Fizz instruction carries a bounded local
change that selects the bundled or host-registered X-Ray skill without
installing or updating it. The earlier overlay recorded only each local
digest. It did not identify the upstream repository, resolve the release tag
to an immutable commit, or distinguish identical bytes from a local
derivative.

The Wildcat suite still needs to state what evidence it accepts from these
operations and what each result authorises. Writing that contract into an
upstream-owned instruction would obscure its provenance. An unbound note
could also survive an upstream change while describing behaviour the new
bytes no longer have.

## Decision

Hold the Wildcat declarations in the single first-party file
`plugins/hexaemeron/PROMISES.md`. Every declaration names one discovered
vendored canonical path, the HTTPS GitHub clone URI, immutable full commit,
repository-relative upstream path, upstream SHA-256, local SHA-256, and one
closed verification status. The status records whether the two byte streams
are identical or modified and must retain
`publisher-authentication-unknown`. The nine Promise Machine fields follow
that provenance block.

The repository checker recomputes each digest and rejects a missing overlay,
an extra overlay location, an unsafe or absent path, a first-party target, a
duplicate path or promise identifier, incomplete fields, uncovered vendored
skills, a mutable commit, an unsupported repository URI, an unsafe upstream
path, a strengthened publisher claim, a false byte relationship, and local
byte drift. This core check reads local committed data only.

`scripts/verify_vendored_provenance.py` is the separate upstream check. It
accepts explicit affected local paths, constructs only their immutable
`raw.githubusercontent.com` locations, uses verified HTTPS, caps total time
and response bytes, writes into fresh temporary storage, and refuses every
redirect. It compares the fetched bytes with the recorded upstream digest.
The Promise Machine core neither imports nor runs this command.

At commit `aadee2ca49cae20246af378ef791d2d4f941e237`, the Fizz Convert,
Fizz Sync, X-Ray, and Solidity Auditor bytes are identical. The top-level Fizz
bytes are recorded as modified. Neither state authenticates the upstream
publisher.

## Alternatives

- Editing vendored instructions would create an unattributed local fork and
  make upstream comparison unreliable.
- A local digest alone would not show which upstream object was reviewed or
  whether the local file was identical to it.
- Resolving a tag during the core check would make an offline conformance gate
  depend on mutable network state and a child process.
- Following redirects would let the declared GitHub identity select a
  different host after review.
- Separate overlay files beside each vendored skill would widen discovery and
  make omission and duplicate ownership harder to check.

## Consequences

An upstream or local update now fails closed until the affected identity,
bytes, relationship, and declaration are reviewed and the separate verifier
passes. The overlay remains Wildcat-authored. A modified local file stays
visible as a derivative instead of being described as byte-exact upstream
work. The digests bind bytes, not authorship or truth: executable and review
evidence must still satisfy the declaration before it authorises anything.

Rollback is all-or-nothing. Remove the overlay, its runtime binding, checker
component and tests together; do not leave an unchecked promise beside
vendored instructions.
