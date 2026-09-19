# Closed authority schemas

## Source

These 19 JSON Schema 2020-12 documents are generated from
[the schema source](../../scripts/checkpoint_authority/schema.py).

## Regeneration

Regenerate schemas and their fixture inventory from the repository root with
`python3 plugins/hexaemeron/tests/checkpoint_authority_corpus.py`; add `--check`
to inspect drift without writing.

## Boundaries

The mandatory independent JSON Schema
oracle checks every golden record, required field, tagged variant and hostile
field mutation. Record-local semantic joins are checked separately.
Native checkpoint v1 schemas remain unchanged.
