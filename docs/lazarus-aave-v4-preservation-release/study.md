# The first end-to-end Aave v4 preservation release

## Assumptions

Assuming, unless corrected:

1. The starting ref is `main` at `382fdc0`, and the run lands there through one
   integration branch.
2. Lazarus keeps its four pinned runtime dependencies and adds none. Ariadne is
   standard library only and stays that way, so nothing here may make Ariadne
   import Lazarus.
3. Python 3.11 upward, `unittest` rather than `pytest`, matching Lazarus's
   existing suite of 144 tests.
4. Lazarus reaches no network in this run. Every command added here reads a
   directory that already exists.
5. The Aave v4 fixture at `plugins/lazarus/examples/aave-v4-spoke-v0` is the
   subject. It was captured on 2026-08-16 and is checked in; nothing here
   re-captures it.
6. A preservation release is a directory somebody can archive and check later
   without either tool's authors, so its checkable content matters more than
   the convenience of producing it.

## Problem statement

Lazarus's held job:

> Bind a Lazarus fixture through an Ariadne state-fixture predicate in the first
> end-to-end Aave v4 preservation release without upgrading recorded RPC
> evidence into proof-backed state.

The two halves already exist separately. Lazarus captures, verifies and replays
a fixture. Ariadne registers a state-fixture predicate and reads a Lazarus
fixture into a statement. Nothing binds them, and the clause about not upgrading
evidence is the reason that matters.

**The gap, reproduced before this run started.** Take the shipped Aave v4
fixture. Edit one field of its manifest so `evidence_counts` reads six
proof-backed and zero recorded-RPC where the records on disk hold two and four.
Recompute the fixture digest so the manifest is fully self-consistent: canonical
bytes, correct digest, every component digest unchanged and right.

| Command | Exit | Says |
| --- | --- | --- |
| `lazarus verify` | 1 | `manifest evidence counts disagree with fixture records` |
| `ariadne capture-state-fixture` | 0 | wrote the statement |
| `ariadne verify` | 0 | `check evidence: pass -- 6 proof_backed, 1 header_bound, 0 recorded_rpc` |

Four recorded RPC responses presented as proof-backed state, in a statement that
verifies clean. The two tools trust different things. Lazarus recomputes the
counts from the proof and RPC records and refuses a manifest that disagrees.
Ariadne reads the counts from the manifest, deliberately: recomputing them would
mean reimplementing Lazarus's judgement about which records were checked against
the state root, and a capture that arrived at a larger number would perform the
upgrade itself.

Both choices are right on their own. The hole is that nothing runs both.

**What is being built.** A release path in Lazarus that produces a preservation
release: the fixture, the Ariadne statement over it, and a release document
binding the two. The binding is checked against Lazarus's own verification
report rather than against the manifest, so a statement that overstates the
fixture is refused where the overstatement is detectable.

**For whom.** Somebody archiving a fixture who wants a stranger, years later and
without either tool's authors, to be able to check that the statement beside it
describes that fixture and does not claim more than it holds.

**A working prototype means** the demo path below runs offline from the
repository root and exits 0:

```bash
python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/aave-v4-spoke-v0
python3 plugins/ariadne/scripts/ariadne.py capture-state-fixture \
  --fixture plugins/lazarus/examples/aave-v4-spoke-v0 --name aave-v4-spoke-v0 \
  --capture-tool lazarus --capture-command python3 \
  --first-capture-reason '<why there is no earlier capture>' --out statement.json
python3 plugins/lazarus/scripts/lazarus.py release \
  plugins/lazarus/examples/aave-v4-spoke-v0 --statement statement.json --out release/
python3 plugins/lazarus/scripts/lazarus.py verify-release release/
```

and the check that proves it is the negative one: the same path over the
tampered manifest above fails at `release`, naming the count that disagrees.

## Prior art

**In this plugin.** `scripts/lazarus.py` offers `validate`, `build-manifest`,
`verify`, `capture` and `replay`. `lazarus_lib/verifier.py` returns the report
this run binds against: `fixture_digest`, `block_hash`, `evidence_counts`, and
per-class detail including `header_bound.canonical_chain_claim: False`.
`lazarus_lib/manifest.py` holds `fixture_digest()`, the canonical-encoding check
and the component digest checks. `lazarus_lib/canonical.py` gives sorted-key,
no-space JSON with a trailing newline and refuses duplicate keys and numbers as
strings. `lazarus_lib/schemas.py` registers five document types by
`(kind, version)` with the SHA-256 of each schema file, and `validate schemas`
checks those digests. `lazarus_lib/paths.py` confines a relative path inside a
root. 144 tests pass on `main`.

**In the sibling plugin.** Ariadne registers
`https://ariadne.wildcat.finance/state-fixture/v1` with gates 2 and 5, an
evidence check and a replay check, and ships `capture-state-fixture`, which
reads a Lazarus fixture into a statement. Its evidence check refuses a
proof-backed count above zero with no `state_root`. Its documented boundary says
plainly that it does not cross-check the counts against the components, which is
the sentence this run acts on from the other side.

**Elsewhere in the marketplace.** The Aave v4 market and transaction in the
fixture were selected from the first row of Tabularium's checked-in Aave v4
release. Alexandria preserves lending-data archives. Neither is touched here.

**Outside.** in-toto Statement v1 and DSSE are the statement formats Ariadne
uses. EIP-1186 is the account and storage proof format Lazarus verifies.
EIP-1898 supplies the block-hash selectors capture prefers.

## Constraints and non-goals

**Constraints.**

- The starting ref is `main` at `382fdc0`.
- Lazarus's four pinned dependencies stay as they are. No new runtime
  dependency, and `requirements.txt` and `requirements.lock` do not move.
- Ariadne must not gain a dependency on Lazarus in either direction of import.
- Everything added here reads a directory that already exists and reaches no
  network.
- A new document type registers in `schemas.py` with its file digest, like the
  five already there.

**Non-goals.**

- Re-capturing the Aave v4 fixture. It is checked in and this run reads it.
- Making Lazarus produce an Ariadne statement. That would duplicate the
  predicate, which is the drift both plugins exist to avoid.
- Signing. Neither tool holds a key, and `cosign` owns that boundary.
- Establishing that the pinned block is canonical. Neither tool re-derives a
  chain, and the release records that rather than resolving it.
- A release format that describes more than one fixture.

## Design options

**A. Lazarus shells out to Ariadne.** `release` runs
`ariadne capture-state-fixture` itself and checks what comes back. One command
for the operator. It adds a subprocess boundary, a path to a sibling plugin that
an installed-standalone Lazarus does not have, and a release whose content
depends on which Ariadne happened to be on disk when it ran.

**B. Lazarus imports Ariadne.** Ariadne is standard library only, so the
dependency is harmless in package terms. It still needs a path into a sibling
plugin, and it couples two release cycles: an Ariadne change could break a
Lazarus command with no Lazarus change to point at.

**C. Lazarus checks a statement it is handed.** `release` takes the fixture and
an already-written statement, verifies the fixture itself, and refuses a
statement that disagrees with the verified report. Two commands in a documented
order. No import, no subprocess, no path to a sibling plugin. The operator sees
which tool refused and why.

**D. Lazarus writes the statement itself.** Refused outright. It would mean a
second implementation of the predicate, and the first thing to drift would be
the evidence classes, which is the exact failure this job is about.

**Picked: C.** It is the cheapest to comprehend and the only one where neither
plugin can reach into the other. It also puts the check where the prohibition
lives: Lazarus's own skill is what forbids describing recorded evidence as
proof-backed, so Lazarus is where a statement that does so should be refused.

**The trade.** The operator runs two commands rather than one, and the order
matters. The release document and the plugin's own prose have to make that
order obvious, and a `release` run against a statement for a different fixture
has to say so in one line rather than producing a confusing diff.

## Risk register seed

- **The upgrade this job names.** A statement claiming more proof-backed records
  than the fixture holds. The check must compare against the verified report,
  never against the manifest, because the manifest is the thing that can lie.
- **Partial writes.** A release directory half-written and read later as
  complete. Lazarus's capture already finalises atomically; the release path
  must too, and a killed run must leave nothing rather than something.
- **Untrusted input.** The statement arrives from outside. It is JSON somebody
  else wrote, so it gets the same treatment the manifest gets: bounded read, no
  `NaN`, no duplicate keys, confined paths, and a refusal rather than a
  traceback.
- **Path handling.** A component path in the statement, or an `--out` that
  resolves inside the fixture. A release that wrote into its own subject would
  change what it was describing while describing it.
- **The bool-is-an-int trap.** Five appearances across this marketplace so far.
  A count of `true` is an integer in Python and one record if nothing looks.
- **Cross-plugin drift.** The three class names live in both plugins now. A
  rename in one is a silent disagreement unless a test reads them from the
  other, as Ariadne's suite already does in that direction.
- **A release read years later.** `verify-release` is the part that has to work
  when nobody remembers how it was made, so it reads only what the release
  contains and never the tools that made it.

## Glossary seeds

- **Preservation release.** A fixture, a statement over it, and a document
  binding the two, in one directory somebody can archive.
- **The verified report.** What `lazarus verify` returns after recomputing the
  counts from the records, as distinct from what the manifest claims.
- **Proof-backed.** Checked against the pinned block's state root through
  EIP-1186.
- **Header-bound.** Tied to the captured header without a trie proof.
- **Recorded RPC.** A response an endpoint gave, preserved and not proved.
- **The upgrade.** Describing evidence of one class as evidence of a stronger
  one. The thing this release refuses.
- **Canonical bytes.** Sorted keys, no spaces, one trailing newline, no
  duplicate keys and no numbers carried as strings.

## Boundaries

**Always.**

- Both suites before a commit: Lazarus's 144 and the repository's 24. Ariadne's
  632 whenever anything it owns is touched.
- The imprimatur lint on every shipped document.
- The three bundled lints in every audit round, recorded as exits on the round.
- A recorded measurement before any change made for speed.

**Ask first.**

- Adding a runtime dependency to either plugin.
- Changing an existing schema's bytes, which moves its registered digest.
- Changing what `verify` reports, which other things read.
- Touching CI.

**Never.**

- Commit an RPC credential or key material.
- Re-implement Ariadne's predicate inside Lazarus.
- Describe recorded RPC evidence as proof-backed, in code, in a document, or in
  an example.
- Claim a command ran when it did not.
- Edit the checked-in Aave v4 fixture's captured bytes.

## Sources

- `plugins/lazarus/skills/lazarus/SKILL.md` and `EVOLUTION.md`, for the held job
  and the three evidence classes.
- `plugins/lazarus/scripts/lazarus_lib/verifier.py:79-101`, for the recomputed
  counts and the refusal when the manifest disagrees.
- `plugins/lazarus/scripts/lazarus_lib/manifest.py:46-56,134-140`, for
  `fixture_digest()` and the canonical-encoding check.
- `plugins/lazarus/examples/aave-v4-spoke-v0/README.md`, for the fixture's
  provenance and its existing demonstration.
- `plugins/ariadne/docs/capturing-a-state-fixture.md`, for what the capture
  reads and the boundary it states about not cross-checking the counts.
- `plugins/ariadne/scripts/ariadne_lib/predicates/state_fixture.py`, for the
  evidence check and the class names.
- The reproduction above, run against a copy of the shipped fixture before this
  run began.
