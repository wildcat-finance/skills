# The state-fixture predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

Type URIs:

- `https://ariadne.wildcat.finance/state-fixture/v1`
- `https://ariadne.wildcat.finance/state-fixture/v2`

A state fixture is the finite part of historical chain state an application test
needs, captured so the test survives the archive endpoint that served it. Lazarus
produces them. This predicate is how one gets published with evidence a stranger
can check.

The thing it exists to refuse is a fixture that claims more than its producer did.
Version 1 records three classes of evidence. Version 2 adds
`receipt_trie_proved`, bound to `receipts_root`. A statement that shifts a count
between the classes, drops a class, or lets one root grant the other's proof turns
recorded data into stronger evidence without anybody having to say so.

## The fields

**`chain`** -- the pin: `chain_id`, `block_number`, `block_hash`, and
`state_root` where there is one. The first three together, because any one alone
leaves a reader guessing: a block number without a hash does not say which of two
blocks at that height, and a hash without a chain does not say which chain.

`state_root` is required by what the statement claims rather than by its shape. A
capture that recorded a header and some responses and proved nothing against the
trie has no use for one, and refusing it would refuse an honest fixture. A capture
claiming proof-backed records needs one, and the evidence check below is where
that is enforced -- deliberately, so the rule reaches statements gate 2 accepts
rather than only ones it has already refused.

Both numbers are integers. A Lazarus manifest writes them as hex quantity strings,
which is right on the wire and wrong to compare: `"0xc7da16" < "0x2"` is true,
because that orders text. The capture path converts and this predicate refuses the
wire form rather than ordering it as a string.

Version 2 may also carry `receipts_root`. A positive
`receipt_trie_proved` count requires it. This rule is independent of
`proof_backed`: `receipts_root` grants no state-trie authority, and `state_root`
grants no receipt-trie authority.

**`capture`** -- `tool`, `tool_version`, `command`, `parameters_digest`. A fixture
is only as reproducible as the thing that wrote it, and a tool name with a version
does not say what it was told to do.

Version 2 requires one printable ASCII graphic in every machine-read name and
command word. Unicode may surround that character. This gives the JSON Schema and
Python predicate one exact visibility rule instead of letting an invisible format,
control or private-use string pass one reader and fail another. Component names
and in-toto subject names must also be unique after NFC normalisation, matching the
release reader even when a statement did not come from Ariadne's capture command.
All version-2 predicate gate lines are fixed and value-free on both success and
failure, so an untrusted identifier cannot become an unbounded terminal or log line.

**`fixture_subjects`** -- one per component file: `name`, `path`, `digest`,
`bytes`. Each digest has to be a subject of the statement, so the predicate cannot
describe files the statement does not cover. Paths are fixture-relative; an
absolute one, or one carrying a `..` segment, describes a file the fixture does
not hold. In version 2 every path segment also contains one printable ASCII
graphic. A segment such as `\u200b` names a POSIX file but nothing a reader can see.

**`evidence`** -- the versioned counts, spelled as Lazarus spells them in its
manifest schemas:

| Class | Authority | Means |
| --- | --- | --- |
| `proof_backed` | `state_root` | Checked against the pinned block's state root |
| `header_bound` | Header | Tied to the captured header, without a trie proof |
| `recorded_rpc` | None | A response an endpoint gave, recorded and not proved |
| `receipt_trie_proved` | `receipts_root` | Version 2 only: scoped consensus receipt and log-projection relations proved against `receipts_root` |

**`replay`** -- `reaches_network` and `canonical_chain_claim`. Both versions
record them as false. Version 2 also records `provider_independence_claim` as
false and requires `commands` to be empty, because its verification boundary is
local files only.

**`deltas`** -- the comparison against an earlier capture of the same block. Both
sides carry a `name` and a `digest`. The one section is `components`. A first
capture carries `"baseline": null` with a `reason`.

**`claims`** and **`commands`** -- the core blocks, checked by gates 1, 3 and 6
like any other predicate's.

## The two gates it owns

**Gate 2, the environment is recoverable.** The pin and the capture record above,
in full, plus every component digest being a subject of the statement. The message
names what is missing rather than saying the record is incomplete.

**Gate 5, deltas name both sides.** A comparison fails when either side cannot be
identified by digest. The current side is checked whenever it is present, on a
first capture as much as on a comparison. That branch went unchecked on the
Solidity release predicate until the run that added this type closed it.

## The two checks each version owns

**The evidence check.** Every versioned class key is present, each a non-negative
whole number, and neither proved class is counted without its own root.

A class left out is the quietest of the three failures. It reads as nothing of
that kind having been captured, when what happened is that nobody said. So the key
is required and a fixture that proved nothing writes a zero.

A count of `true` is refused. Python makes `True` an integer, so a check that only
asked whether the value was a number would read a producer's mistake as one
proof-backed record.

The state rule requires `state_root` for a positive `proof_backed` count. Version
2 independently requires `receipts_root` for a positive
`receipt_trie_proved` count. A fixture can satisfy either rule while failing the
other; neither root or count supplies evidence for the other relation.

Gate 2 does not require the root, which is what lets this rule do work. An earlier
draft required it there, and the rule became unreachable: every statement it would
have refused had already failed gate 2, so it read as the safeguard this type
exists for while guarding nothing. Writing the conformance fixture is what
surfaced that, because the fixture could not breach the check alone.

**The replay check.** `reaches_network` false, because a replay that falls back to
an endpoint is not a fixture, and the endpoint is the thing a fixture exists to
outlive. `canonical_chain_claim` false, because a block hash and a state root pin
a block, not its place in a chain nothing here re-derived.

Both fields have to be present. `False` is the value, not the default: a producer
who left the key out has not made the decision the field records.

Version 2 applies the same rule to `provider_independence_claim`. Matching source
labels are operator-selected metadata, not proof that independent providers
supplied the records. Version 2 also refuses an executable command; its replay is
local-file verification only.

## What this predicate does not establish

Worth stating plainly, because a clean verify is narrower than it looks.

It does not establish that the pinned block is canonical. Nothing in Ariadne or
Lazarus re-derives a chain, and `canonical_chain_claim` being false is the record
of that rather than a formality.

Version 2 does not establish provider independence. Its
`provider_independence_claim` is false even when recorded source labels differ.

It does not check the proofs. It checks that a count of proof-backed records has a
state root behind it. Whether those proofs verify is Lazarus's own `verify`, and a
statement records the result as a claim like any other.

Nor does it cross-check the counts against the components. A statement claiming one
proof-backed record while listing no proofs file verifies, because this predicate
reads a statement and not a fixture directory. Reading the two together is what the
capture path does, and a statement it wrote carries counts taken from the manifest
rather than from its caller.

It does not upgrade recorded evidence. A `recorded_rpc` count is a count of
responses somebody wrote down. No gate here makes one stronger, and the split
exists so that nobody reading the statement can be misled into thinking one did.

`receipt_trie_proved` does not attribute transaction hashes. It covers only the
scoped consensus receipt and log-projection relations proved by Lazarus.
Transaction hashes and RPC decorations remain recorded data outside that proof.

## The published schema

[`schemas/state-fixture-v1.json`](../schemas/state-fixture-v1.json) and
[`schemas/state-fixture-v2.json`](../schemas/state-fixture-v2.json) describe the
two shapes for another producer to read. Drift tests hold both to the field tables
in the module, so a field added to one and not the other fails the suite.

The schema expresses more of the rules than an earlier draft of it did. Draft
2020-12 has `if`/`then`, so the conditional state-root rule is in there: a
`proof_backed` count above zero makes `state_root` required. A component path that
would leave the fixture, or whose segment contains no printable ASCII graphic, is
refused by a pattern rather than left to the verifier. The same shared shape covers
version-2 capture and delta names. Tests hold the schema and verifier to the same
verdict over hand-written shapes and the shipped conformance fixtures.

Two rules are beyond the predicate schema, rather than beyond this schema. It
cannot see whether a component digest also appears in the statement's `subject`
array, and it cannot compare the names in that outer array after NFC
normalisation. The component-coverage and duplicate-subject-name fixtures record
those two verifier refusals explicitly. Tests name both exceptions, so another
schema/verifier disagreement cannot appear quietly.

The other thing a schema cannot express is the reason. It can refuse an all-zero
state root with a pattern and it cannot say that the value identifies nothing, and a
producer reading a pattern mismatch learns less than one reading a gate line. So
both ship, and the verifier is the one that explains itself.

## Running it

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-state-fixture.json
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-state-fixture-v2.json
```

Both exit 0. The version 1 fixture uses the digests, byte counts and evidence
counts Lazarus wrote for `plugins/lazarus/examples/goldfinch-v0`. The version 2
fixture carries a receipt witness rooted at
`0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e`.
