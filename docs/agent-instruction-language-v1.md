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

| field | shape | meaning |
| --- | --- | --- |
| `schema` | string | exactly `wildcat-agent-instruction/v1` |
| `document` | object | stable document id and exact title literal |
| `sources` | array | closed source records in canonical id order |
| `sections` | array | authored section and directive order |
| `relations` | array | explicit precedence edges in canonical tuple order |
| `bindings` | array | reviewed source spans in canonical tuple order |

Every object rejects unknown fields. Every array is present, including an
empty `relations` array. A directive always carries `expressions`; its
`promise` value is either `null` or the complete promise object. An empty
Promise Machine field is not inferred from absence: the claim is an exact
literal, required promise lists are non-empty, and `exceptions: []` explicitly
means none.

Ids are lowercase ASCII and match `[a-z][a-z0-9.-]*`. References resolve to
one declared id of the expected kind. Section and directive arrays preserve
order. Each source path occurs once in a model, so two source ids cannot alias
the same bytes and bypass span-overlap checks. Source, relation, binding, and
evidence-class arrays use the canonical orders below; duplicate values are
rejected rather than collapsed.

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

A `scope` expression declares its id beneath its containing directive or named
scope. An `exception` expression may target only that containing directive or
one named scope on its ancestor chain. Governed nodes are the document,
sections, directives, named scopes, promises, and structured promise
exceptions. Each needs at least one binding. A binding reviewer is an
`identifier` literal; this makes its canonical tuple order exact rather than
dependent on a display rendering.

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

| tag | model kind | field form |
| --- | --- | --- |
| `i` | `identifier` | length-prefixed literal |
| `p` | `path` | length-prefixed literal |
| `h` | `sha256` | length-prefixed literal |
| `c` | `command` | length-prefixed literal |
| `n` | `number` | length-prefixed literal |
| `d` | `date` | length-prefixed literal |
| `u` | `link` | length-prefixed literal |
| `q` | `quotation` | length-prefixed literal |
| `t` | `text` | length-prefixed literal |

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

| item | version-1 maximum | measured as |
| --- | ---: | --- |
| input or output file | 1,048,576 | bytes |
| physical lines | 16,384 | lines |
| one physical line | 65,536 | bytes before LF |
| nesting depth | 32 | levels |
| object members | 32 | members |
| identifier | 128 | UTF-8 bytes |
| repository-relative path | 512 | UTF-8 bytes |
| one decoded literal | 65,000 | UTF-8 bytes |
| all decoded literals | 786,432 | UTF-8 bytes |
| sources | 64 | records |
| sections | 128 | records |
| directives | 4,096 | records |
| expressions | 8,192 | records |
| relations | 8,192 | records |
| bindings | 8,192 | records |
| promise exceptions | 1,024 | records |
| adapter argv entries | 32 | entries |
| adapter environment names | 16 | names |
| adapter stdin | 262,144 | bytes |
| adapter stdout or stderr | 65,536 | bytes each |
| recorded parity response | 512 | UTF-8 bytes |
| adapter executable | 268,435,456 | bytes |

Schema `maxLength` values count code points and are an early shape check. The
byte limits in this table still apply. The literal limit leaves room for record
framing when its bytes need no escape expansion; escapes and additional fields
remain subject to the fixed 65,536-byte physical-line bound. A count at the
limit is accepted when all other rules pass; limit plus one refuses.

Paths are relative ASCII strings with no empty, `.`, or `..` component, no
leading slash, backslash, control, or bidirectional-control character. Every
opened component is checked with `lstat`. Inputs and existing parents must be
regular directories or files as appropriate; symlinks and special files
refuse. Output uses a confined sibling temporary regular file, flush and sync,
then atomic replace. The codec runs no shell and resolves no includes.

## Validation result and refusal codes

A command emits one JSON line with result schema
`wildcat-agent-instruction-result/v1`, event `validation` or `roundtrip`, input
digest, outcome, stable code, and node path. It does not echo an unbounded
source fragment. A successful decode or format also records the
canonical-model and compact digests. The reference CLI exposes `validate`,
`format`, `decode`, `roundtrip`, and the in-memory `self-test`; its file commands
take a selected root plus relative input and output paths.

Version 1 reserves these stable refusal families:

| code | subject | effect |
| --- | --- | --- |
| `WAI-E-VERSION` | schema id, magic, or unsupported version | refuse |
| `WAI-E-UTF8` | BOM, malformed UTF-8, or invalid scalar | refuse |
| `WAI-E-JSON` | JSON syntax, duplicate key, or forbidden numeric form | refuse |
| `WAI-E-SHAPE` | unknown, missing, or mistyped model field | refuse |
| `WAI-E-BOUNDS` | any fixed resource limit | refuse |
| `WAI-E-REFERENCE` | id, relation, binding, scope, or exception closure | refuse |
| `WAI-E-CYCLE` | cyclic precedence | refuse |
| `WAI-E-PATH` | unsafe, escaping, linked, or special path | refuse |
| `WAI-E-COMPACT` | indentation, line, opcode, field, literal, or escape syntax | refuse |
| `WAI-E-CANONICAL` | non-canonical order, bytes, or formatter mismatch | refuse |
| `WAI-E-IO` | bounded read, flush, sync, or atomic-write failure | refuse |
| `WAI-E-MANIFEST` | fixture or evidence closure | refuse |
| `WAI-E-DIGEST` | stale profile, prompt, bootstrap, or report binding | refuse |
| `WAI-E-ADAPTER` | executable, identity, argv, environment, runtime, timeout, cap, or response | refuse |
| `WAI-E-TOKENIZER` | vocabulary identity or real-model token count | refuse |
| `WAI-E-MEASURE` | bootstrap accounting, cohort comparison, or compression gate | refuse |
| `WAI-E-PARITY` | family identity, fresh context, answer, or required equality | refuse |

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

## Fixture manifest and source review

The version-1 demonstration manifest is
[`tests/fixtures/agent-instruction-v1/manifest.json`](../tests/fixtures/agent-instruction-v1/manifest.json).
Its closed machine-readable shape is declared by the digest-bound
[`manifest.schema.json`](../tests/fixtures/agent-instruction-v1/manifest.schema.json).
The manifest names exactly `fiat-study-runbook-phase`, `horos-boundary-check`,
and `promise-machine-router-selection`, in that canonical order. It fixes the
source identity and path for each row, `15` reviewed bindings, `9` closed
questions, and `14` hostile mutations; each row carries its own fixed counts.
A fixture
directory contains exactly `model.json`, `compact.wai`, `questions.json`,
`mutations.json`, and `source-spans.json`; an absent, additional, linked, or
special entry refuses.

Each fixture binds the full authored source blob by repository-relative path
and SHA-256, then binds one half-open source envelope and every reviewed model
node span within it. Bytes in the envelope that have no node span remain
authored source context rather than model authority. `source-spans.json`
repeats each canonical model binding with
the reviewer id and SHA-256 of the exact source slice. The checker verifies the
whole source first, so changing source bytes outside a reviewed span still
refuses. It then verifies every artifact digest, validates the model, decodes
and re-formats the compact bytes, compares the source-span inventory with the
model bindings, and checks the question and mutation records. These fixture
records are evidence about the named source bytes; they do not replace those
bytes or establish a general English-to-model translation.

A question has one stable id, an exact prompt, a non-empty closed accepted
answer set, a non-empty disjoint refusal set, one required accepted answer,
and a fresh-context inventory. Version 1 requires empty prior-message and
example inventories. Repository-instruction paths and tool-definition ids are
always present, even when none are available. An answer outside both declared
sets is not coerced into a nearby value.

A mutation applies one `remove` or `replace` operation through a bounded JSON
pointer to a copy of the canonical model. The manifest freezes the seven risk
classes `negation`, `precedence`, `scope`, `evidence-class`, `authorisation`,
`recovery`, and `exact-literal`. A mutation must produce its declared exact
structural refusal, a different valid canonical-model digest, or a declared
answer change linked to one closed question. The changed answer must already
belong to that question's accepted or refusal set and must differ from its
required answer. Risk labels are checked against their targets: precedence
changes a relation; scope changes a scope or exception expression; evidence
class, authorisation, and recovery change their matching Promise fields;
negation changes directive content and declares an answer change; and an
exact-literal target must match its declared literal class. Each fixture has
exactly one negation mutation with an answer-change expectation. The complete
corpus has one checked exact-literal mutation for every literal class it uses:
`identifier`, `path`, `sha256`, `command`, `number`, and `text`. A no-op,
missing pointer, unexpected refusal, unknown class, incomplete literal-class
inventory, or stale mutation record refuses as silent acceptance rather than
weakening the expected result after observation.

`check --manifest` reads every path through the same confined regular-file
boundary as the codec and executes no fixture content. A successful run emits
one bounded `binding.result` and `roundtrip.result` per fixture, one
`mutation.result` per mutation, and one `run.summary`. Once manifest bytes are
readable, every record carries their digest; fixture records also carry a
digest of the exact fixture row.
They contain ids, digests, counts, verdicts, and stable refusal codes, not
source fragments, prompts, model responses, credentials, or hidden reasoning.

## Measurement and parity evidence

The manifest also binds exactly six regular files in
[`evidence/`](../tests/fixtures/agent-instruction-v1/evidence/): the complete
decoder bootstrap, tokenizer profile, two-family profile record, parity prompt,
measurement report, and parity report. Missing, additional, linked, stale, or
internally inconsistent evidence refuses before a runtime is launched. The two
commands are:

```bash
python3 scripts/agent_instruction.py measure --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tmp/agent-instruction-v1-measurement.json
python3 scripts/agent_instruction.py parity --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tmp/agent-instruction-v1-parity.json
```

Both commands re-run the fixture and mutation checks, verify every selected
profile, write one canonical report by atomic replacement, and emit its bounded
`run.summary`. A refusal still writes the complete bounded report when the
failure occurs after report construction. Counts and answers are observations;
they do not change source, canonical-model, or compact instruction authority.

### Token measurement

The checked tokenizer profile is `gptoss-120b-ollama-0.32.15`, model
`gpt-oss:120b`, vocabulary and model-blob SHA-256
`6be6d66a3f546d8c19b130dc41dc24b2fc159f84ffbc76a0ee0676205083cf5a`.
It binds Ollama `0.32.15`, the Ollama executable digest
`eee609f0a6da58b978d453e0385fd0e3496e6cf319c639875669b51cb4277d2d`,
the `/usr/bin/curl` digest
`5ab042572ea0e068644e3b8f9e8dd1ad197bfcf33d199316615b46ddc4390a41`,
the exact model-manifest output digest, argv, raw-prompt context, limits, seed,
and acquisition date. The adapter posts only to the declared loopback Ollama
generate endpoint. It clears the environment, admits `HOME`, fixes
`OLLAMA_HOST=http://127.0.0.1:11434` and `OLLAMA_NOHISTORY=1`, and starts
curl with `--disable` so user configuration is not loaded. It passes no shell
text and treats Ollama's
integer `prompt_eval_count` as the count. A different executable, runtime version,
model manifest, blob, vocabulary, model name, non-integer count, or negative
count refuses.

The baseline is the three source spans under that profile. The comparison then
counts the canonical models, compact documents, and the complete 893-byte
decoder bootstrap under the same profile. The checked report records:

| material | bytes | tokens |
| --- | ---: | ---: |
| source corpus | 11,025 | 2,499 |
| canonical-model corpus | 8,563 | 2,068 |
| compact corpus | 6,150 | 2,228 |
| decoder bootstrap | 893 | 270 |
| compact corpus plus bootstrap | 7,043 | 2,498 |
| compact-plus-bootstrap minus source | -3,982 | -1 |

The strict three-document gate passes because `2,498 < 2,499`. The report also
keeps each document and the bootstrap-amortised prefixes. A one-document run is
not assumed to save tokens: the Fiat fixture reports `-44`, Horos reports
`+740`, and Promise Machine reports `-157` after adding the entire bootstrap.
The two-document prefix reports `+426`; only the declared three-document cohort
is the acceptance cohort.

### Isolated family parity

The family record names two distinct local identities:

- `qwen35-aeon-27b-q4-k-m`: family `qwen35`, model
  `qwen3.8-27b-aeon:q4_k_m`, model blobs
  `5caf67d19e598ac71ba02c3df7785f86247ec77ca4d54cba2e2d342453c87f27`
  and
  `d466586099626aa3572522d8b6138a3c5b7793e699959da200a69169428d7b5a`.
- `gptoss-120b-mxfp4`: family `gptoss`, model `gpt-oss:120b`, model blob
  `6be6d66a3f546d8c19b130dc41dc24b2fc159f84ffbc76a0ee0676205083cf5a`.

Each profile binds its family name, model name, model-manifest acquisition
digest, vocabulary, executable digests, loopback chat argv, context window,
thinking mode, seed, time limit, and byte limits. Two profile rows with the
same family, model-blob tuple, or acquisition digest are aliases and refuse.

For each of the nine declared questions and each family, the runner launches a
new curl process and sends one user message containing either the source span
or the compact document with its bootstrap. The request carries no prior
message, example, repository instruction, tool definition, stored context,
credential, or remote URL. The bound prompt presents one neutral candidate list
without identifying the required id or separating document conclusions from
evidence refusals. The transport schema admits any bounded answer-id string so
the local parser can preserve and refuse malformed or unlisted values instead
of letting the runtime coerce them. The report retains the bounded final JSON
answer or refusal, input and prompt digests, prompt token count, job id, verdict,
unknowns, and refusal codes. It does not retain model reasoning.

The checked run contains 18 source-versus-compact pairs and 36 isolated model
calls. All 18 pairs returned the declared required answer from both forms; the
summary reports 18 passed, zero failed, zero refused, and zero unknown. This is
evidence for these fixture bytes, profiles, and local runtime only. It does not
show parity for another model build, another prompt, arbitrary English, tools,
conversation history, or a deployed agent.

### Adapter trust boundary and recovery

Ollama, curl, their outputs, and model responses are untrusted external
adapters. The checked profiles make their identity and launch contract
reproducible, but neither adapter interprets instruction authority. The Python
validator alone decides whether a bound profile, count, response, and report
fit this evidence contract. It never executes a source command or acts on a
model answer.

Every adapter process receives an explicit argv list, a cleared allowlisted
environment, bounded stdin, separate stdout and stderr caps, and a timeout;
`shell=False` is fixed. Only the public synthetic corpus is sent to the local
loopback runtime. Credentials and provider SDKs are absent. A timeout,
unavailable runtime, cap breach, changed identity, reused context, model
refusal, required-answer mismatch, or unknown answer remains visible and
refuses the run.

Recovery is to restore the recorded local identity or create a newly reviewed
profile and rerun the complete cohort. Do not edit a digest, hide a bounded
response, collapse two model aliases into two families, substitute bytes or a
heuristic for tokenizer output, or widen an answer set after seeing a result.
Adding a dependency, downloading a model, contacting a credentialed or paid
endpoint, sending non-public source, or choosing a new licence remains an
operator decision.

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
