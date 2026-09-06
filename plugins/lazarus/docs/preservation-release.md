<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Receipt witnesses reconstruct receiptsRoot offline and prove one scoped receipt payload plus its consensus-log projection; transaction hashes and unrelated RPC results remain recorded evidence, while empty blocks still have no receipt-witness representation.
<!-- marketplace-context:end -->

# Preservation releases

A fixture proves things about itself. A release is what you hand somebody else:
the fixture, a statement about it that somebody else wrote, and a document
binding the two, written only if the fixture verifies and the statement survives
being held to that verification.

The historical manifest-v1 example is at
[`examples/aave-v4-spoke-v0-release/`](../examples/aave-v4-spoke-v0-release). The
receipt-aware manifest-v2 example is at
[`examples/aave-v4-spoke-v1-release/`](../examples/aave-v4-spoke-v1-release). Read
either one back with no network:

```bash
python3 plugins/lazarus/scripts/lazarus.py verify-release \
  plugins/lazarus/examples/aave-v4-spoke-v0-release

python3 plugins/lazarus/scripts/lazarus.py verify-release \
  plugins/lazarus/examples/aave-v4-spoke-v1-release
```

## The gap this closes

Lazarus recomputes the three manifest-v1 evidence counts, or all four
manifest-v2 counts including `receipt_trie_proved`, from the proof and RPC
records and refuses a manifest that disagrees with them. Ariadne reads those
counts from the manifest and does not re-derive them, deliberately: re-deriving would mean
reimplementing Lazarus's judgement about which records were checked against the
state root, and a capture that arrived at a larger number would perform exactly
the upgrade it exists to prevent.

Both choices are right on their own, and between them sits a gap neither tool can
close alone. Edit one integer in a manifest, recompute the fixture digest so the
document is entirely self-consistent, and `lazarus verify` refuses it while
`ariadne capture-state-fixture` accepts the same fixture and writes a statement
reporting six proof-backed records where two exist. Four recorded RPC responses
presented as proved state, in two documents that each pass their own author's
checks.

So a release holds a statement to what Lazarus's verification recomputed, never
to what the manifest claims. Run the demonstration to watch both halves happen:

```bash
python3 plugins/lazarus/examples/preservation-release-demo.py
```

## Writing one

```bash
python3 plugins/lazarus/scripts/lazarus.py release <fixture> \
  --statement <file> --out <directory>
```

The fixture is verified, the statement is bound to that verification, and the
output is written only if both pass. It holds three things:

- **`fixture/`.** A byte-for-byte copy of a directory that verifies.
- **`statement.json`.** The statement exactly as it arrived.
- **`release.json`.** What verification established, and which checks were
  made.

Four things about how it is written are worth knowing.

**The output appears whole or not at all.** Everything is built in a staging
directory beside the destination and moved in with one rename. A run that dies
halfway leaves a dot-prefixed directory that is not a release, rather than half
of one that reads as whole. The name is checked again after the copy, which is
the slow part; that narrows the window rather than closing it, and what a lost
race can cost is an empty directory somebody else created in the meantime.

**The statement is the bytes that arrived.** The release digests them, and a
re-encoded document is a different document even when it says the same thing.

**The fixture copy is verified again** after it is written, and its digest
compared to the original's, because copying is where bytes go missing. The copy
is driven by the verified manifest rather than by walking the directory, so
nothing the manifest does not list can ride along.

**The directory is read, not written.** A release leaves the fixture and the
statement byte for byte and mode for mode as it found them, and it refuses a
statement that lives inside the fixture it describes, because the fixture digest
would then cover the statement made about the fixture.

## What the binding checks

Eight checks, recorded in the release by name so a reader learns which questions
were asked rather than inferring them from the release existing.

- **`statement-type`.** Refuses a document that is not an in-toto Statement. A
  predicate type is read inside an envelope.
- **`predicate-type`.** Refuses a predicate in a vocabulary this binding has
  not read.
- **`chain-and-block`.** Refuses a statement naming another chain, height,
  block hash or state root. Pinning the hash alone would leave the other three
  free.
- **`evidence-counts`.** Refuses a count that disagrees with what the records
  verify to, in either direction. Understating describes a fixture nobody has.
- **`replay-claims`.** Refuses a statement saying verification reached a node,
  or that the header belongs to the canonical chain. Neither happened.
- **`components-declared`.** Refuses a component the statement names and the
  fixture does not hold.
- **`components-complete`.** Refuses a component the fixture holds and the
  statement does not name.
- **`subjects-cover-components`.** Refuses a component described in the
  predicate and absent from the in-toto `subject` list, which is what a policy
  engine matches on.

## Reading one back

```bash
python3 plugins/lazarus/scripts/lazarus.py verify-release <directory>
```

Everything the write did is done again from the bytes on disk. Nothing is taken
from the document except the two paths it names, because a document checked
against its own numbers is not checked. The release digest is checked here:
`validate` answers whether a document is well formed, the way `validate manifest`
does, and whether its digests hold is this question.

A release holds the document, the statement and the fixture, and nothing else.
That is the rule the fixture manifest already applies to its own directory. A
file nobody accounts for, inside something whose whole claim is that every part
of it was checked, is a file a reader has no reason to trust.

The paths in the document are the paths that are read. A release whose fixture
sits at `state/` and whose statement is called `attestation.json` verifies, so
long as the document says so.

## What a release does not say

- **That the block is canonical.** A self-consistent header is not proof that it
  belongs to Ethereum's chain. `canonical_chain_claim` is always false, and both
  the schema and the binding refuse anything else.
- **That the statement is signed.** Neither tool holds a key; `cosign` owns that
  boundary, and Ariadne reports signature state without checking signatures.
- **That every receipt or log field is proved.** A release-v2 may carry the two
  scoped relations checked against `receiptsRoot`: one consensus receipt
  payload and its filtered consensus-log projection. Transaction hashes and
  unrelated RPC fields remain recorded evidence. Release-v1 carries no receipt
  relation at all.
- **Anything about a second fixture.** A release describes one.

## Why the fixture does not mention the release

`README.md` inside the Aave v4 fixture is a manifest component: its bytes are
digested, and the release records that digest. Editing it to advertise the
release would change the digest the release records, which would invalidate the
release, which would need rewriting, which would change the README. The release
points at the fixture. The fixture does not point back.
