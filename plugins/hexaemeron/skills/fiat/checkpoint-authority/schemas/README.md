# Closed authority schemas

## Source

These 19 JSON Schema 2020-12 documents are generated from
[the schema source](../../scripts/checkpoint_authority/schema.py).

## Regeneration

Regenerate schemas and their fixture inventory from the repository root with
`python3 plugins/hexaemeron/tests/checkpoint_authority_corpus.py`; add `--check`
to inspect drift without writing.

## Release copies

`schema.family_document()` projects the same 19 shapes as one closed `oneOf`.
Ariadne's `plugins/ariadne/schemas/checkpoint-authority-v1.json` is a release
copy of that projection, held to this source by Ariadne's checkout parity
test and by the `authority-replay` manifest digest; regenerate it from the
projection rather than editing the copy.

## Boundaries

The mandatory independent JSON Schema
oracle checks every golden record, required field, tagged variant and hostile
field mutation. Record-local semantic joins are checked separately.
Native checkpoint v1 schemas remain unchanged.
