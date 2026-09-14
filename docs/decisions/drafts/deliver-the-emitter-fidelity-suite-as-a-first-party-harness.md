# Decision: Deliver the emitter-fidelity suite as a first-party harness

## Status

Proposed, 2026-09-14. It takes its `ADR-NNN` number from the decision allocator
when it merges, and is cited elsewhere by its stable slug,
`deliver-the-emitter-fidelity-suite-as-a-first-party-harness`. It supersedes
nothing.

## Context

Twenty-seven event emitters in `wildcat-finance/v2-protocol` build their logs by
hand in assembly rather than through the compiler's `emit`. Nothing checks that
what they write matches what the corresponding `event` declaration says a log
of that event looks like: the topic count, topic0, the indexed values in
declaration order, and the ABI-encoded data region. An emitter and its
declaration can drift apart while every test in the protocol repository still
passes, because those tests read the emitters' own output.

A suite that proves the correspondence needs a home in this repository, an
oracle that is not the code under test, and a way to hold the protocol source
it compiles. Each is expensive to reverse.

Two facts constrain the home. The Fizz skill tree is vendored:
`ADR-005-vendor-the-pashov-suite-whole-and-ungoverned` keeps it upstream-owned
and byte-for-byte unmodified, so it cannot hold first-party Solidity. And a home
that no declared check builds executes nothing; this repository builds exactly
two Foundry roots, `plugins/janus/harness/` and `plugins/pandects/`.

One fact constrains the source. Deliveries like this one will need many target
repositories. A copy of each inside this repository would grow every size limit
the repository and its packaged runtime answer to, and the packaged runtime
already sits close to its byte cap.

## Decision

**The suite is a first-party Foundry root at `plugins/hexaemeron/harness/`,** in
the shape `plugins/janus/harness/` already has, with its own workflow and its
own entries in `tests/check-map-v1.json`.

### The oracle is declaration-derived

**Each expected log comes from the `event` declaration, through a mirror-emit
reference contract.** The reference imports the declaring interface and
redeclares nothing; it emits each event through high-level `emit`, so the
compiler derives topic0, the topic count, the indexed positions and the data
encoding. A differential case calls the emitter and the reference with the same
arguments and compares the two recorded logs field by field. No expected
topic0, topic count, indexed position or data offset is read from or
transcribed out of the emitter files.

### The protocol source is fetched at a pinned commit, never copied here

**This repository holds the protocol source by identity only.**
`plugins/hexaemeron/harness/PROVENANCE.json` names the repository, the commit
`f5a26146987926f4811b72a795d662813dedfe85`, and the path, size and SHA-256 of
each of the eleven files the harness compiles. `fetch_protocol.py` materialises
them under `src/vendor/`, which is ignored, and refuses any file whose bytes
differ from the record. The harness's forge checks and its workflow fetch before
they build.

Re-pinning to a later protocol commit means changing the commit and the digests
together, in a change a reviewer can see, and re-running the suite against the
new bytes. A source that is not public at a pinned commit, or too large to fetch
file by file, is stored outside this repository and named the same way.

### No version is incremented

**This delivery increments no skill version.** Fizz keeps no frontier ledger: it
has a `VERSION` file containing `1` and no `EVOLUTION.md`, and no Hexaemeron
plugin-level ledger exists.

## Alternatives

- **The generator, template and reference inside the Fizz skill tree.**
  Rejected: `ADR-005-vendor-the-pashov-suite-whole-and-ungoverned` keeps that
  tree unmodified.
- **Specification only here, with the suite delivered to the protocol
  repository.** Rejected: nothing in this repository could run it.
- **A Foundry project under `plugins/hexaemeron/tests/fixtures/`.** Rejected: no
  declared check compiles a Foundry root of that shape.
- **A copy of the protocol source inside the harness.** Built first and
  withdrawn before merge. It carried 46,799 bytes for one target, and repeating
  it for every target this kind of delivery will need does not fit the
  repository's limits.
- **An oracle transcribed from the emitters.** Rejected: it makes the code under
  test its own authority, so every case passes by construction.

## Consequences

**A new emitter must pair by name or the suite fails.** Every `emit_<EventName>`
free function in the fetched emitter files has to have exactly one case, and
`plugins/hexaemeron/tests/test_harness_pairing.py` fails on a missing, extra or
duplicated one.

**Building the harness needs the network, or a local clone.** `fetch_protocol.py`
reads `raw.githubusercontent.com` at the pinned commit, or a local clone through
`--from-git`. Until it has run, the Python tests that read the source skip, and
the forge checks refuse to build.

**The pin has to be moved deliberately.** Once the protocol moves, the pinned
commit names something older, and nothing here moves it automatically.
