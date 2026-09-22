# Decision: Omit example payloads from the portable runtime

## Status

Proposed, 2026-09-20, for issue #1720. This draft awaits the governed
implementation. It changes no cap, reserve or numbered record.

## Context

At the starting commit `66f52785813a8453e7c7d54f2371aa8f6e465640` the complete
portable package measured 20,381,433 bytes against a 20,971,520-byte line (the
26,214,400-byte skills CLI cap minus a 5,242,880-byte reserve set by ADR-090),
a margin of 590,087 bytes. That margin is smaller than the largest single
delivery observed since ADR-090 landed (794,493 bytes, merge `86de8d18`). Three
omission classes were already added in three days inside the step that crossed
the line (run #1676 Step 4, merge `229f5856`), and the run for #1731 shortened
packaged prose to fit, which its audit found had dropped claims.

`OMISSIONS` in `scripts/portable_promise_machine.py` holds 14 rows. Five are
example-specific:

1. `plugins/lazarus/examples/aave-v4-spoke-v1/{anchors.jsonl,header.json,plan.json,proofs.jsonl,receipt-witness.json,rpc.jsonl}`
2. `plugins/alexandria/examples/compound-v3-phase0-v0/input/**`
3. `plugins/alexandria/examples/compound-v3-phase0-v0/release/**`
4. `plugins/alexandria/examples/compound-v3-phase0-v0/source/**`
5. `plugins/tabularium/examples/*-v1/{source.json,capture.json,coverage.json,events.jsonl,rebuild.py}`

Observed: what the router reads at run time never opens a file under
`plugins/*/examples/`; `PORTABLE.md` supports exactly one installed operation
on example data, Lazarus on the retained release. The full source checkout is
already the declared home for data the router never reads (ADR-040), and these
five rows apply that reading one payload family at a time.

## Decision

Replace the five rows above with one class, `example-payload-class`: omit
every file under `plugins/*/examples/` that is not Markdown from the generated
portable runtime.

Two exceptions. First, a file a packaged Markdown document links stays
packaged and is listed by `measure` as kept by link, so a document that names
a payload the runtime carries does not go stale. Second, the retained Lazarus
release under `plugins/lazarus/examples/aave-v4-spoke-v1-release/` stays
packaged whole; its byte-equality guard against the standalone
`aave-v4-spoke-v1` fixture (`docs/decisions/drafts/keep-one-complete-lazarus-fixture-in-the-portable-runtime.md`)
is unchanged.

The standing `measure` action's JSON object uses schema
`portable-payload-measurement/v1`, with fields `schema`, `source_commit`,
`tree_clean`, `cap`, `reserve`, `line`, `file_tripwire`, a `package` object and
a `runtime` object each carrying `bytes`, `files` and `margin`,
`manifest_bytes`, `outer_bytes`, `omission_classes`, `largest_default_included`
and `kept_by_link`, the last two as lists of `path` and `bytes`. This shape is
expensive to reverse once other runs parse it, so it is recorded here beside
the generator's help text.

## Composition with the Wildcat interval draft

`main` added `docs/decisions/drafts/keep-wildcat-interval-demonstration-payloads-in-full-checkouts.md`
after this design was locked. It omits the direct JSON files and pre-plan
probes of `plugins/alexandria/examples/wildcat-v1-interval-v0/` and
`wildcat-v2-interval-v0/`, and keeps their documents and Python entrypoints.
Its row is retained unchanged. The example class omits the two unlinked
`demo.py` entrypoints as well (26,498 bytes), because that draft's own
consequences state they must be run from a full checkout, so a packaged copy
cannot run from the package. Their `README.md` documents stay packaged.
This extends that draft rather than amending it; its bytes are unchanged.

## Alternatives

Figures below come from simulating each rule over the starting commit
`66f52785813a8453e7c7d54f2371aa8f6e465640` with `.hexaemeron/design/resolve.py`
(SHA-256 `9060bf1f6fd8a444315987b6ffcb5d7bf130f0c4855304b5f1d7d8f19d232de1`).

- `second-distribution`. Move example and `docs/` trees that no packaged
  document links to a second generated package in a second repository.
  Reserve held 5,242,880 bytes, delivery room 5,447,387 bytes, 0 new broken
  links, wall time 612 ms, package after 15,524,133 bytes across 1,114 files,
  0 files leaving the CLI install. Refused: it needs a new repository, a
  second manifest and verifier, a second installable identity beside the one
  ADR-040 allows, and a rebuild workflow only a person with `workflow` scope
  can push (1 human-pushed workflow against a gate of 0).
- `lower-reserve`. Reserve 2,097,152 bytes, line 24,117,248 bytes. Delivery
  room 3,735,815 bytes, 0 new broken links, wall time 13 ms, package after
  20,381,433 bytes across 1,550 files, unchanged. Refused: it fails the
  reserve-held gate (at least 5,242,880 bytes) outright, spending protection
  ADR-090 set and two later drafts have since reaffirmed.
- `plugin-budgets`. Divide the line per plugin. Reserve held 5,242,880 bytes,
  delivery room 590,087 bytes, 0 new broken links, wall time 12 ms, package
  after 20,381,433 bytes across 1,550 files, unchanged. Refused: it fails the
  delivery-room gate (at least 794,493 bytes); the plugin that grows next is
  the one refused, and no room returns to any plugin.

## Consequences

146 demonstration files, 2,545,267 bytes, leave the skills CLI install and
stay in the source checkout; example documents will name payloads the package
lacks, said once in `PORTABLE.md`. Tabularium's v0 payload, 1,697,604 bytes,
leaves with them, which changes the `PORTABLE.md` sentence that says the v0
evidence remains. The runtime manifest lists the class with its two
exceptions, and the five replaced rows leave both `OMISSIONS` and
`EXPECTED_OMISSIONS` in `tests/test_skills_sh_package.py`.

Left open for ADR-090's owner: the skills CLI applies its 1,000-entry archive
limit in the same function as its 25 MiB extracted-bytes limit. The package
already holds 1,550 files, so the archive routes refuse it by default before
either byte limit is reached, and the supported `github` install route
consults neither limit. That reserved margin protects only an installer who
overrides the CLI's file limit but not its byte limit, which questions what
the 5,242,880-byte reserve (ADR-090) buys. This draft records the question and
changes no cap, reserve or numbered record; ADR-040 and ADR-090 keep their
bytes.
