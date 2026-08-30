# Wildcat agent instruction language, version 1

## Status and authority

`wildcat-agent-instruction/v1` is the contract for a bounded prototype. Human
Markdown is authored and authoritative. Canonical JSON is a reviewed semantic
model of supported statements. The compact form is a deterministic derived
view. A compact document has no authority unless its source binding, canonical
model, schema, and decoder digests match.

The contract is licensed under the repository's existing
[Apache-2.0 licence](../LICENSE). Its implementation uses the interpreter in
[`.python-version`](../.python-version), constrained by
[`pyproject.toml`](../pyproject.toml). This document does not duplicate either
file or introduce a package dependency.

[ADR-051](decisions/ADR-051-encode-a-closed-agent-instruction-model.md) records
why the source remains authoritative and why a closed model was selected.

## What version 1 carries

One model carries one ordered document with:

- sources bound by repository-relative path and lowercase SHA-256;
- ordered sections and ordered directives with stable ids;
- directive kinds `require`, `forbid`, `permit`, `refuse`, `recover`, and
  `unknown`;
- nested `when`, `unless`, `scope`, and `exception` expressions;
- explicit `before`, `after`, and `overrides` relations;
- Promise Machine claims, evidence, evidence classes, boundary, authorised
  actions, consequence, refusals, recovery, and structured exceptions;
- exact literals typed as `identifier`, `path`, `sha256`, `command`, `number`,
  `date`, `link`, `quotation`, or `text`; and
- reviewed source bindings from model-node id to source id, half-open byte span,
  and reviewer.

Version 1 assigns no meaning to arbitrary prose. A statement outside this
closed set is unsupported and blocks encoding. Display prose and comments may
be preserved as exact literals only when a model field explicitly carries
them; their presence alone grants no instruction authority.

## Canonical model

The machine-readable shape is
[`schemas/agent-instruction-v1.schema.json`](../schemas/agent-instruction-v1.schema.json).
The root object has exactly these fields, in semantic rather than serialized
order:

| field | meaning |
| --- | --- |
| `schema` | exactly `wildcat-agent-instruction/v1` |
| `document` | stable document id and exact title literal |
| `sources` | closed source records in canonical id order |
| `sections` | authored section and directive order |
| `relations` | explicit precedence edges in canonical tuple order |
| `bindings` | reviewed source spans in canonical tuple order |

Every object rejects unknown fields. Every array is present, including an
empty `relations` array. A directive always carries `expressions`; its
`promise` value is either `null` or the complete promise object. An empty
Promise Machine field is not inferred from absence: the claim is an exact
literal, required promise lists are non-empty, and `exceptions: []` explicitly
means none.

Ids are lowercase ASCII and match `[a-z][a-z0-9.-]*`. References resolve to
one declared id of the expected kind. Section and directive arrays preserve
order. Source, relation, binding, and evidence-class arrays use the canonical
orders below; duplicate values are rejected rather than collapsed.

JSON input is UTF-8 without a BOM. Duplicate object keys, floating-point
numbers, JSON numeric values, non-scalar Unicode, and values outside the schema
are rejected. Numbers that carry instruction meaning are decimal strings.
Canonical bytes use UTF-8 JSON with sorted object keys, no insignificant
whitespace, lowercase `true`, `false`, and `null`, and one final LF. Strings
retain their Unicode scalar sequence; no normalisation is applied.

Canonical array order is:

1. `sources` by source id;
2. `relations` by `(kind, source, target)`;
3. `bindings` by `(source, start as an integer, end as an integer, node,
   reviewer)`;
4. `evidence_classes` in the fixed order `checked`, `recomputed`, `proved`,
   `measured`, `recorded`, `attested`, `inferred`, `unknown`; and
5. all other arrays in authored order.

The validator rejects a model that is structurally valid but not in these
orders. It also rejects a dangling reference, a duplicate id, a precedence
cycle, a self-relation, an `exception` target outside its directive's ancestor
scope, a source span whose end is not greater than its start, an uncovered
governed node, or two bindings that claim the same source bytes for different
nodes without an exact declared nesting relation.

## Compact document

The compact magic is `WAI1`. A document is UTF-8, begins with that line, uses
LF line endings, and ends with one LF. Each later physical line is one record.
Two ASCII spaces add one nesting level; tabs, blank lines, trailing whitespace,
and any other indentation refuse.

At a high level, the grammar is:

```abnf
compact      = magic LF document-line LF
               *source-line *section-block *relation-line *binding-line
magic        = "WAI1"
indent       = *("  ")
record       = indent opcode *(SP field) LF
opcode       = %x21-7E
field        = fixed-token / literal
literal      = literal-kind byte-count ":" escaped-data
byte-count   = "0" / (%x31-39 *DIGIT)
```

`escaped-data` is scanned until exactly `byte-count` decoded UTF-8 bytes have
been produced. The next byte must be LF or the one ASCII-space field separator.
This length rule is semantic and is not expressible by ABNF alone.

A literal begins with one kind tag:

| tag | model kind |
| --- | --- |
| `i` | `identifier` |
| `p` | `path` |
| `h` | `sha256` |
| `c` | `command` |
| `n` | `number` |
| `d` | `date` |
| `u` | `link` |
| `q` | `quotation` |
| `t` | `text` |

Literal length counts decoded UTF-8 bytes, not code points or encoded source
characters. The canonical escapes are `\\` for backslash, `\s` for ASCII
space, `\:` for colon, `\t`, `\n`, `\r`, and `\xHH` for the remaining C0
control bytes and DEL. Hex digits are uppercase. A byte that must be escaped
cannot appear raw; a printable scalar that need not be escaped cannot use an
escape. Non-ASCII scalar values appear as their original UTF-8 sequence. Empty
literals use length zero, for example `t0:`.

Records occur only in this order and at these depths:

| opcode | depth | canonical model value |
| --- | ---: | --- |
| `D` | 0 | document id, title |
| `S` | 1 | source id, path, SHA-256 |
| `H` | 1 | section id, title |
| `R` | 2 | `require` directive id and statement |
| `F` | 2 | `forbid` directive id and statement |
| `P` | 2 | `permit` directive id and statement |
| `X` | 2 | `refuse` directive id and statement |
| `Y` | 2 | `recover` directive id and statement |
| `U` | 2 | `unknown` directive id and statement |
| `W` | 3 or deeper | `when` predicate and child expressions |
| `N` | 3 or deeper | `unless` predicate and child expressions |
| `C` | 3 or deeper | `scope` id and child expressions |
| `E` | 3 or deeper | `exception` target, predicate, and child expressions |
| `M` | 3 | promise id and exact claim; remaining promise fields are its children |
| `V` | 4 | one evidence literal |
| `K` | 4 | one fixed evidence-class token |
| `G` | 4 | promise boundary literal |
| `A` | 4 | one authorised-action literal |
| `Q` | 4 | consequence token `0`, `1`, `2`, or `3` |
| `J` | 4 | one refusal literal |
| `Z` | 4 | one recovery literal |
| `I` | 4 | exception id, authority, gate, subject, scope, record, expiry, recovery |
| `<` | 1 | `before` source and target ids |
| `>` | 1 | `after` source and target ids |
| `^` | 1 | `overrides` source and target ids |
| `B` | 1 | source id, node id, start, end, reviewer |

Every id, reference, path, digest, decimal span, and free value is represented
by the literal kind the schema assigns. Fixed enums such as evidence classes
and consequences are bare tokens. Repeated `V`, `K`, `A`, `J`, `Z`, and `I`
records preserve their corresponding array order. Exactly one `G` and `Q` are
required in each `M`; its claim is required; and at least one `V`, `K`, `A`,
`J`, and `Z` is required.

The formatter emits sources, sections, directives, expressions, promises,
relations, and bindings in canonical-model order. The decoder accepts no
alternative spelling or record position. It returns the complete canonical
model bytes or one refusal; it never returns a partial model.

## Fixed bounds

The decoder and canonical-model loader apply these limits before allocating or
descending further:

| item | version-1 maximum |
| --- | ---: |
| input or output file | 1,048,576 bytes |
| physical lines | 16,384 |
| one physical line | 65,536 bytes before LF |
| nesting depth | 32 levels |
| object members | 32 |
| identifier | 128 UTF-8 bytes |
| repository-relative path | 512 UTF-8 bytes |
| one decoded literal | 65,536 UTF-8 bytes |
| all decoded literals | 786,432 UTF-8 bytes |
| sources | 64 |
| sections | 128 |
| directives | 4,096 |
| expressions | 8,192 |
| relations | 8,192 |
| bindings | 8,192 |
| promise exceptions | 1,024 |

Schema `maxLength` values count code points and are an early shape check. The
byte limits in this table still apply. A count at the limit is accepted when
all other rules pass; limit plus one refuses.

Paths are relative ASCII strings with no empty, `.`, or `..` component, no
leading slash, backslash, control, or bidirectional-control character. Every
opened component is checked with `lstat`. Inputs and existing parents must be
regular directories or files as appropriate; symlinks and special files
refuse. Output uses a confined sibling temporary regular file, flush and sync,
then atomic replace. The codec runs no shell and resolves no includes.

## Validation result and refusal codes

A command emits one bounded result containing schema id, input digest, outcome,
stable code, and node path. It does not echo an unbounded source fragment. A
successful decode or format also records the canonical-model and compact
digests.

Version 1 reserves these stable refusal families:

| code | subject |
| --- | --- |
| `WAI-E-VERSION` | schema id, magic, or unsupported version |
| `WAI-E-UTF8` | BOM, malformed UTF-8, or invalid scalar |
| `WAI-E-JSON` | JSON syntax, duplicate key, or forbidden numeric form |
| `WAI-E-SHAPE` | unknown, missing, or mistyped model field |
| `WAI-E-BOUNDS` | any fixed resource limit |
| `WAI-E-REFERENCE` | id, relation, binding, scope, or exception closure |
| `WAI-E-CYCLE` | cyclic precedence |
| `WAI-E-PATH` | unsafe, escaping, linked, or special path |
| `WAI-E-COMPACT` | indentation, line, opcode, field, literal, or escape syntax |
| `WAI-E-CANONICAL` | non-canonical order, bytes, or formatter mismatch |
| `WAI-E-IO` | bounded read, flush, sync, or atomic-write failure |

Implementations may append a stable dot-separated detail, such as
`WAI-E-COMPACT.OPCODE`, without changing the family. A new family or changed
meaning requires a contract revision.

## Consumer sequence

1. Read the manifest and all named regular files under the selected root.
2. Verify source, schema, decoder-bootstrap, model, and compact digests.
3. Load and validate the canonical model under the fixed bounds.
4. Decode the compact bytes and compare canonical model bytes.
5. Format the decoded model again and compare compact bytes.
6. Only then expose the model to an instruction consumer.

Failure at any stage blocks that document. A majority of valid nodes, a
matching model answer, or a byte-only saving cannot replace a failed check.

## Compatibility and recovery

Version 1 readers accept only `wildcat-agent-instruction/v1` and `WAI1`.
Unknown versions and opcodes refuse. Adding an optional field, opcode, enum,
escape, default, coercion, or inferred relation changes semantics and therefore
requires a new version. A version-1 writer always emits the one canonical form;
readers do not accept aliases from a later version.

The authored Markdown stays available through every recovery. On a stale
digest, invalid model, malformed compact form, or formatter mismatch, restore
the exact bound source, repair the reviewed model or codec, regenerate the
derived bytes, and rerun validation. Editing a digest to fit changed bytes,
dropping a hostile fixture, widening an answer set after observation,
normalising a literal, or interpreting an unknown record is not recovery.

The codec establishes model equality only. It does not establish that the
source-to-model review captured arbitrary English, that a model family follows
the instructions, that tokens were saved, or that another repository is ready
to migrate.
