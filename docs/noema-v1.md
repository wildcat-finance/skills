# Noema version 1 shadow-prototype contract

## Contract identity and authority

The contract identity is `noema/v1`. `NOE1` is the canonical-source magic,
`NT1` the baseline text-projection magic and `noema-result/v1` the CLI result
shape. A different identity is unsupported input rather than a compatible
minor version.

This version runs only in shadow mode. Existing repository Markdown is the
authored authority. Canonical `.noe`, NIR, text projections, slices, renders,
semantic diffs and evidence records are derived artifacts. A Noema decision is
data for a caller that already holds separately recorded authority; the runtime
does not execute an effect and cannot grant repository, publication,
deployment, security or financial authority.

## Closed semantic domain

Version 1 admits these nominal core types:

```text
actor artifact action claim command effect event evidence literal operation
path predicate promise repository rule scope state transition type value
```

Modules may define nominal subtypes, qualified predicate signatures and pure
graph macros. They cannot add a core operator, change an operator's arity or
meaning, shadow a qualified name, introduce ambient state or execute code.

The closed structural operators and their meanings are:

| opcode | arity | result | meaning |
| --- | ---: | --- | --- |
| `!` | 1 | directive | require the proposition |
| `-` | 1 | directive | prohibit the proposition or effect |
| `+` | 1 | directive | permit; permission never implies requirement |
| `?` | 2 | directive | apply the directive only when the guard is checked true |
| `/` | 2 | directive | apply the directive only when the guard is checked false |
| `@` | 2 | directive | limit the directive to the named scope |
| `^` | 2 | directive | name the actor with exclusive authority for the effect |
| `;` | N | directive | apply a finite ordered directive sequence |
| `&` | N | proposition | finite conjunction |
| `|` | N | proposition | finite disjunction |
| `~` | 1 | proposition | three-valued negation |
| `=` | 2 | proposition | typed equality without coercion |
| `=>` | 2 | proposition | implication |
| `<` | 2 | relation | require the left term before the right term |
| `all` | 3 | proposition | finite typed universal quantification |
| `any` | 3 | proposition | finite typed existential quantification |
| `one` | 3 | proposition | exactly one member of a finite typed set |
| `in` | 2 | proposition | typed membership |
| `subset` | 2 | proposition | typed finite-set containment |
| `lt`,`le`,`gt`,`ge` | 2 | proposition | canonical decimal-string comparison |
| `count` | 1 | value | finite collection cardinality |

Named record forms are rule, import, literal, definition, precedence,
override, transition, promise, handoff and exception. Their version-1 fields
are fixed:

```text
rule       id directive source-binding
import     module-id module-sha256
literal    id kind byte-count exact-utf8
definition qualified-name typed-parameters pure-body
precedence higher-rule lower-rule authority scope evidence
override   id authority high-rule low-rule scope evidence
transition id machine from event guard to ordered-effects
promise    id subject claim evidence classes boundary grants refuses recovery level
handoff    id producer consumer subject scope evidence classes time transform gaps
exception  id authority gate subject scope record expiry recovery
```

Unknown record forms, keys, types, operators and extra fields refuse. Numeric
values are canonical unsigned decimal strings: `0` or a non-zero digit followed
by digits. No float, exponent, sign, whitespace or numeric coercion is admitted.

## Three-valued facts and authority

Established facts are true or false; absent or insufficient evidence is
unknown. Negation maps true to false, false to true and unknown to unknown.
Conjunction returns false if any member is false, unknown if none is false and
one is unknown, and true otherwise. Disjunction is the dual. A guard containing
unknown blocks its dependent effect unless a rule explicitly handles an
unknown-valued predicate.

Capability, authority, execution, receipt and verification are separate typed
relations. None implies another. Consequence-2 and consequence-3 effects
default deny unless an applicable authority fact and every named gate are
checked. Permission does not cancel prohibition. Conflicting requirements
refuse unless one closed override record names the higher rule, authority,
scope and evidence. Precedence and override edges form one acyclic governing
relation; a cycle within or across the two record forms refuses.

An exception cannot assert absent evidence, strengthen an evidence class,
change a source binding or operate outside its subject and scope. Missing,
expired, unattributed, unrecorded or over-broad exceptions refuse.

## Canonical `.noe` and NIR

Canonical `.noe` is UTF-8, line-oriented and ends with one LF. Its first record
is `NOE1`. Structural opcodes, qualified predicates, stable ids and typed
literal references are governing syntax; prose is not. Every later line is one
canonical JSON array. The first item is the record form and the remaining items
occur in the field order above. Arrays avoid field-name bootstrap cost without
making arity contextual.

Terms are prefix arrays. `['$',id]` references an inert literal; `['%',id]`
references a bound variable; `[':',type,text]` is a typed atom; and
`['{}',type,...members]` is a finite typed set. An operator or qualified
predicate is the first item of every other term. Quantifiers use
`[operator,[variable,type],finite-set,proposition]`. These examples use single
quotes only for exposition; governing source uses canonical JSON double
quotes. Numeric fields and values are unsigned decimal strings, never JSON
numbers. Finite-set members are unique and sorted by their canonical term
bytes; duplicate or descending members refuse.

JSON is canonical with UTF-8 NFC scalar strings, no BOM, CR, blank line,
insignificant whitespace, alternate escape, duplicate object key or non-finite
number. Object keys in module, profile and derived records are lexicographically
sorted. Arrays retain semantic order except for finite sets. Records are sorted
by the form order
published above, then by id; precedence uses the `(higher,lower)` pair. These
rules make the source byte string singular.

The published JSON Schema closes object keys, record and module tuple shapes,
term tags and structural arities. It is an interchange envelope, not a second
type checker: canonical ordering, NFC and UTF-8 byte limits, digest relations,
name resolution, nominal types and cross-record invariants remain executable
validator obligations. Schema acceptance alone never creates a NIR.

Canonicalization is singular: no insignificant alternate whitespace, key
order, escape, Unicode normalization or integer spelling exists. Parsing must
complete validation before a graph is returned. Formatting that graph must
reproduce the exact canonical source bytes. NIR identity is SHA-256 over those
canonical bytes and the lock identity; an optional binary cache is derived,
non-authoritative and never base64 prompt input.

Every governed directive has a stable rule id and source binding. An id remains
stable across a wording-only source change whose reviewed semantics do not
change. A semantic change updates the affected graph node and appears in a
semantic diff.

## Modules and lock identity

A module is canonical data containing one module identity, a closed list of
typed predicate signatures and pure definitions over already admitted
operators and signatures. Imports bind complete module SHA-256 values. Import
cycles, definition cycles, absent modules, multiple bytes for one identity and
ambient lookup refuse.

`noema-module/v1` has exactly `schema`, `id`, `imports`, `types`, `signatures`
and `definitions`. Import entries are `[id,sha256]`; nominal subtype entries are
`[qualified-name,core-parent]`; signatures are
`[qualified-name,[parameter-types],result-type]`; definitions are
`[qualified-name,[[parameter,type],...],pure-term]`. Collections are unique and
source-sorted. The 64-import limit covers the complete transitive registry, not
each file independently. A source import resolves only `<module-id>.json` below
the named module directory. Unmentioned files have no meaning.

`noema-lock/v1` binds source, graph, compiler, kernel and projection-profile
SHA-256 values plus the ordered module id/digest list. Any changed or missing
component makes the lock stale. A consumer may use no module meaning that the
lock does not name.

## Typed inert literals

Literal kinds are `id`, `path`, `sha256`, `command`, `number`, `date`, `url`,
`quote`, `text` and `bytes`. Identity is the pair of kind and exact UTF-8 bytes;
different kinds with equal bytes remain distinct. Literal bytes cannot parse as
a record, predicate, alias, module, fact or authority edge. A command, path or
URL literal still needs a separately authorised typed effect before a caller
uses it.

Large opaque values may remain content-addressed sidecars. The projection
exposes a literal only when it is reachable from the selected slice. Base64 is
not a transport unless the base64 spelling itself is the exact governed value.

## Text projections

A projection is derived text for one exact tokenizer profile. `NT1` identifies
the version-1 projection grammar. A profile binds its text alphabet, reserved
opcodes, tokenizer or vocabulary identity, kernel bytes, alias dictionary and
their SHA-256 values. Raw token ids are forbidden because text APIs and
tokenizer revisions do not share their meaning.

`noema-profile/v1` fixes the printable-ASCII alias alphabet and stores sorted
`[source,target]` pairs. A projection contains exactly an ASCII header
`NT1 <profile-sha256> <graph-sha256>`, one canonical JSON graph line and a final
LF. The graph line substitutes exact strings using the profile. Its
`noema-projection-manifest/v1` binds graph, lock, profile, alias-list and
projection digests. The projection bundle carries the closed lock whose digest
the manifest names. Inverse substitution must recover the byte-identical graph,
and lock graph/profile identities must agree, before the bundle is returned.

Aliases are injective across reserved opcodes, qualified predicates, literal
ids and values visible in the same slice. Arity does not disambiguate an alias.
One alias source cannot occupy more than one of those semantic namespaces. A
collision or namespace overload refuses. Recovery validates the complete
profile shape before reading its aliases. The manifest plus projection must
recover the same NIR; shorter bytes or tokens never excuse a changed graph.

A profile may carry an alias whose source is absent from one graph or slice;
that entry is inert there and still counts in profile/bootstrap bytes. Its
target must remain disjoint from every visible string so inverse substitution
cannot capture unrelated data.

Prompt-only mode includes the complete kernel, every reachable definition,
the slice and its reachable literals. All of those bytes and tokens count.
Runtime mode may keep checked policy evaluation outside model context, but its
manifest and lock still bind the same graph.

## Source bindings and semantic diff

A source identity is one unique repository-relative path and exact blob
SHA-256. Each governed UTF-8 byte span maps to one graph node or one explicit
unsupported remainder. Spans for one physical source cannot overlap. Gaps in a
declared governed region, stale bytes, aliased source paths and a remainder that
grants authority refuse.

Source-span coverage is reviewed evidence. It establishes the recorded mapping
for exact bytes and does not establish that the reviewer captured unexpressed
intent. An unsupported remainder blocks authority migration and remains visible
in every evidence record. Bound files must decode as UTF-8, and span endpoints
must fall between complete scalar values.

A semantic diff has closed entries for added, removed or modified effects,
gates, authority, scope, evidence classes, literals, transitions, precedence
and source bindings. A changed semantic digest with no entry, or an entry with
unchanged before and after identities, refuses.

`noema-semantic-diff/v1` entries contain exactly `node`, `kind`, `change`,
`before` and `after`. The final two fields are canonical-value SHA-256 values or
null on addition/removal. Definition, module, promise, handoff and exception
kinds expose changes that do not collapse honestly into the nine rule facets.

## Conservative slicing

`select` receives graph and lock identity, operation, state, target, tools,
authority inputs and checked facts. Roots are the requested operation, its
possible effects and output type plus every applicable higher-precedence rule.
Closure retains referenced definitions, literals, promises, handoffs,
exceptions, prohibitions, authority constraints, ordering, refusal and
recovery.

A checked-true guard retains its dependent rule. A checked-false guard may omit
it only when the manifest carries the exact fact and evidence identity. An
unknown guard retains it. Any rule that can forbid, constrain, order or recover
a reachable effect remains reachable.

`noema-manifest/v1` commits to the complete graph and lock, compiler, profile,
kernel, selection inputs, checked facts, included ids, omitted ids with reasons,
reachable definitions and literals, projection and every digest. Included and
omitted ids form an exact partition of the full graph's selectable ids.

## Local codec interface

`scripts/noema.py parse` accepts named source, module-directory, profile,
kernel and output paths. It validates everything before atomically writing one
`noema-build/v1` object containing the graph and lock. `format` recovers the
canonical source; `project` writes one `noema-projection/v1` bundle;
`semantic-diff` compares two builds; and `verify` rereads every dependency and
lock identity. Those four commands take the same module, profile and kernel
paths. `self-test` performs the checked-in complete-fixture round trip without
writing a file.

All input leaves must be regular files; module resolution is confined to one
real directory and never scans it. Output uses a random `.noema-write-` leaf
independent of the target name, loops on partial writes, syncs file and parent,
then replaces the target. A refusal before replacement leaves the prior target
intact and removes the temporary. A post-replacement directory-sync failure is
reported as uncertain durable state, never success.

## Policy runtime

The runtime surface is exactly:

```text
select(operation,state,target,tools,authority,facts) -> manifest + projection
check(effect,facts,manifest)                         -> permit | refuse | unknown
next(machine,state,event,receipts,manifest)          -> transition | stop
literal(id,manifest)                                 -> kind + exact bytes
explain(node,manifest)                               -> non-authoritative render
```

`next` owns no external domain judgment; it evaluates declared state, event,
guard and ordered effects. `literal` refuses an unreachable id. `explain`
labels its output and no policy operation may consume that render as evidence.
The runtime has no operation for subprocess, network, Git, GitHub, file
mutation, publication or deployment.

## Resource limits

Version 1 applies every limit before returning a partial graph or result:

| resource | maximum |
| --- | ---: |
| input file | 1,048,576 bytes |
| physical line | 65,536 bytes |
| source records | 16,384 |
| graph nodes | 16,384 |
| imports | 64 |
| nesting depth | 64 |
| one literal | 65,000 decoded UTF-8 bytes |
| all decoded literal occurrences | 786,432 bytes |
| expanded macro graph | 65,536 nodes |
| one finite quantifier set | 4,096 members |
| one derived output | 1,048,576 bytes |

The graph-node count includes source records, term nodes, each embedded module
and every module import, subtype, signature and definition declaration.

The seed archive verifier separately accepts at most 1,048,576 archive bytes,
64 members, 1,048,576 uncompressed bytes in aggregate, 1,048,576 bytes for one
member and 512 UTF-8 bytes for one member path. It rejects encryption,
non-canonical or unsafe paths, links, special files, unsupported compression,
duplicate names and any inventory mismatch. Root and member spellings use the
exact alphabets published in the seed-inventory schema.

## Result and refusal contract

Each command writes at most one `noema-result/v1` JSON line to standard output.
It names command, deterministic correlation id, verdict, stable code, input and
output digests and bounded counts that exist for that command. It never carries
source text, literal payloads, prompts, model output or credentials.
Malformed argument vectors use the same line with `NOE-E-TYPE.ARGUMENTS` and
never echo argument bytes; `command` is the recognised operation or `invalid`.

Stable refusal families are:

| family | subject | recovery |
| --- | --- | --- |
| `NOE-E-SYNTAX` | malformed or non-canonical source/tape | repair exact bytes and rerun |
| `NOE-E-TYPE` | unknown type, operator, key, arity or typed value | use the closed version-1 form |
| `NOE-E-BOUNDS` | a fixed resource limit | reduce input without deleting governed meaning |
| `NOE-E-REFERENCE` | id, cycle, source span or closure | repair the named reference relation |
| `NOE-E-DIGEST` | source, graph, module, compiler, kernel or profile mismatch | restore matching bytes or regenerate derived data |
| `NOE-E-ALIAS` | projection collision or overload | choose one injective mapping and regenerate |
| `NOE-E-SLICE` | omitted reachable rule or invalid omission proof | restore conservative closure |
| `NOE-E-AUTHORITY` | missing, conflicting or over-broad authority | supply applicable checked authority or refuse the effect |
| `NOE-E-PATH` | unsafe, escaping, linked or special path | select a confined regular path |
| `NOE-E-IO` | read, write, sync or atomic replacement uncertainty | inspect complete old/new state and rerun safely |
| `NOE-E-EVALUATION` | packet, profile, family, case or answer mismatch | restore the exact isolated cohort and retally |
| `NOE-E-UNIMPLEMENTED` | operation reserved for a later prototype step | finish and verify its declared step |

A refusal returns no partial graph, tape, slice, decision or evidence file.
Failure blocks its dependent operation while leaving inspection, repair, rerun
and safe exit available when their own inputs validate.

## Measurement and family evaluation

Measurement records bytes and real tokenizer counts separately for Markdown
source, canonical `.noe`, full projection, operation slice, literals, kernel,
reachable definitions, first use, steady state and corpus amortisation. Source
and projections use the same exact profile. Missing exact OpenAI, Anthropic,
Google or open-weight profiles remain `unknown`; heuristic counts do not
replace them.

The fixed gates are first use at most 70% of relevant Markdown, steady state at
most 40%, complete canonical Noema at most 55% of the declared source corpus,
and 100% for critical permission/prohibition, authority, negation,
unknown-guard, ordering, exact-literal and consequence-3 vectors.

Evaluation emits one answer-free source prompt and one Noema prompt per case,
one isolated context each. The packet is complete only after its manifest is
written. Tally requires exact case-set equality, no duplicate id, exact tree,
source, graph, kernel, projection, profile and model identity, and two genuinely
different family identities for a cross-family result. A committed run records
that run; it does not predict a rerun or establish model quality.

External tokenizer or model programs are explicit digest-bound argv lists with
a minimal environment allowlist, timeout and output cap. New dependencies,
downloads, credentials, network calls, source disclosure and paid use require
separate operator authority. Model output is untrusted data and never becomes a
command, query, path, fact or authority edge.

## Versioning and recovery

Version 1 is closed. An added operator, type, record field or changed meaning
requires a new contract identity. A new projection profile may be added under
version 1 only when it recovers the same NIR and binds its own complete bytes.

Canonical source and lock are the recovery root for derived graph caches,
projections, slices, renders, semantic diffs and evidence. Regenerate derived
artifacts after verifying source and module identities; never edit a derived
view to make a stale check pass. During this issue, canonical source itself is
recoverable from authoritative Markdown and reviewed source bindings because
Noema remains in shadow mode.
