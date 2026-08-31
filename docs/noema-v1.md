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
Typed atoms name only nominal core types or module subtypes. `proposition`,
`directive` and `relation` are structural results, never atom labels. A module
signature cannot return `directive`; directives originate only in the closed
operators below.

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
unknown-valued predicate. Finite sets use their expanded scalar members, so
definition aliases neither duplicate a member nor impose an order. `one` is
false as soon as two members are established true; an unknown member matters
only while it could still change the exactly-one result. Quantifier binders
shadow same-named outer variables during capture-avoiding substitution.
Recursive truth evaluation preserves both authored and expanded proposition
identities, so a checked subfact cannot disappear when its parent expands.

Capability, authority, execution, receipt and verification are separate typed
relations. None implies another. Consequence-2 and consequence-3 effects
default deny unless an applicable authority fact and every named gate are
checked. Permission does not cancel prohibition. Conflicting requirements
refuse unless one closed override record names an active, applicable higher
rule, the lower rule, authority, scope and evidence. Precedence and override
edges form one acyclic governing relation; a cycle within or across the two
record forms refuses.

Literal references remain distinct scalar identities inside finite sets even
when their payload bytes match. A reachable `number` literal supplies its exact
canonical decimal bytes to `lt`, `le`, `gt` and `ge`; no other literal kind is
coerced for numeric comparison.

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
ambient lookup refuse. A module may use only core forms and symbols/types owned
by itself or its transitive declared imports; source co-imports and
source-local definitions or literals do not widen that closure. Module ids
`local` and `local.*` refuse because the complete `local.*` namespace belongs
only to source definitions.

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

The prompt kernel begins `NK1` and is a complete interpretation prelude, not a
format label. It defines canonical-JSON prefix terms, inverse alias decoding,
typed atoms, literals, variables and sets, every directive used by the
evaluation corpus, three-valued truth, fact identity, consequence metadata,
record shapes, `NT1` binding, query application and the non-execution rule. It
also fixes the policy priority used by the critical cases: active prohibition
or failed requirement refuses; an unknown guard stays unknown; consequence 2
or 3 needs the selected exclusive authority; only then may an active
permission permit. A profile, lock or packet carrying other kernel bytes has a
different identity. A shorter glossary that leaves any evaluated construct to
model convention is not a valid kernel for family evidence.

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

The fixed corpus identities are `brevitas` at
`plugins/brevitas/skills/brevitas/SKILL.md`, `fiat` at
`plugins/hexaemeron/skills/fiat/SKILL.md`, `phylax` at
`plugins/hexaemeron/skills/phylax/SKILL.md` and `sapheneia` at
`plugins/sapheneia/skills/sapheneia/SKILL.md`. A source digest may advance with
reviewed repository bytes; an identity may not move to another path or alias.

Source-span coverage is reviewed evidence. It establishes the recorded mapping
for exact bytes and does not establish that the reviewer captured unexpressed
intent. An unsupported remainder blocks authority migration and remains visible
in every evidence record. Every v1 prototype specimen must retain at least one
such remainder and remain shadow-only; widening node spans cannot promote a
specimen. Bound files must decode as UTF-8, and span endpoints must fall between
complete scalar values.

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
authority inputs and checked facts. An operation or effect match and a
transition from the selected state are primary roots. Target or tool matches
are secondary roots when no primary root exists. If neither class resolves,
the safe fallback is the full selectable graph rather than an empty slice.
Closure expands locked pure definitions before following shared typed effect,
operation, state, event, artifact, action, claim and command identities, then
retains each connected promise, handoff, exception, prohibition, authority
constraint, order edge, refusal and recovery. An order or override edge pulls
both named rules into the slice even when the edge itself is a secondary root;
an edge with an inactive endpoint cannot survive alone, and a macro cannot hide
one of those links.

A checked-true guard retains its dependent rule. A checked-false guard may omit
it only when the manifest carries one checked fact for that exact full guard
and its evidence identity. Facts for proper subexpressions do not establish an
omission. An unknown guard retains its rule. Any rule that can forbid,
constrain, order or recover a reachable effect remains reachable.

Facts are addressed as `fact.` followed by SHA-256 over the canonical
proposition bytes. A fact has exactly that id, `true`, `false` or `unknown`, and
the SHA-256 identity of its evidence. A caller cannot attach truth to a free
name, and an explanation object does not fit the fact shape.

`noema-manifest/v1` commits to the complete graph and lock, compiler, profile,
kernel, selection inputs, checked facts, included ids, omitted ids with reasons,
reachable definitions and literals, the complete runtime tape, the slice
projection and every digest. The tape contains the included selectable records
plus normalized reachable definition and literal records. Included and omitted
ids form an exact partition of the full graph's selectable ids. A
checked-inactive omission repeats the exact fact and evidence digest; an
ordinary unreachable omission carries null fact fields.

The manifest's `artifacts` object names six plain sibling leaves: build,
module directory, profile, kernel, selection and projection. `verify
--manifest` rereads those bytes, recompiles the build, recomputes the selection
and recovers the projection before accepting the manifest. The leaf-only rule
is intentional: a portable fixture cannot smuggle path traversal or a linked
dependency into verification.

## Source-bound specimen corpus

`noema-specimen-corpus/v1` binds exactly four sorted shadow specimens:
Brevitas, Fiat, Phylax and Sapheneia. Each specimen owns canonical source,
modules, profile, kernel, selection, questions and hostile mutation inputs.
Deterministic regeneration produces its build and lock, full projection,
operation slice and manifest, literal evidence, policy answers, source-span map
and mutation results. The top manifest records a separate digest for every one
of those objects; source, canonical graph, full projection, slice, literals,
kernel and reachable definitions cannot alias one identity.
It also binds the digest of a sorted path, byte-count and SHA-256 inventory for
every specimen input and generated output. The specimen root and its `modules`
and `mutations` directories are closed to that derived inventory: a changed
mutation artifact, missing member, extra member, nested directory or link
refuses even when the observed mutation result would otherwise be unchanged.
Verification enumerates each closed directory through one retained descriptor,
stops at the first unexpected member, reads every admitted leaf relative to
that descriptor and enforces the aggregate byte cap while reading. It retains
the seed and four specimen directory descriptors plus every observed file
identity until the corpus verdict. The corpus manifest, exact seed-inventory
bytes and all four canonical Markdown sources are also identity-rechecked at
that boundary. Replacement, in-place mutation or mode drift during the
aggregate verification therefore refuses instead of certifying mixed states.

`noema-source-identity/v1` names one repository-relative Markdown path, exact
byte count and SHA-256, and governs its complete byte range. Every rule source
binding must name that same path and digest. `noema-source-spans/v1` forms one
ordered, gapless and non-overlapping partition over the whole file. A mapped
span names exactly one rule node. Every other byte is
`unsupported-by-noema-v1`, names no node or authority, and forces `shadow:
true`. Complete byte coverage is evidence about provenance, not evidence that
the reviewed mapping understood the prose correctly.

Each closed question records an effect and the complete expected
`noema-check/v1` output. Regeneration executes the checked slice and refuses if
decision, consequence, controlling node or reason differs. The committed
answer retains the full result and digests. Every specimen must demonstrate
permit, refuse and unknown.

The mutation plan admits exactly the thirteen fixed hostile categories. Each
category fixes its input kind, runtime query and one canonical structural
change derived from the specimen baseline. Exact artifact comparison happens
before execution, so a different change that happens to produce the same
facet, decision or refusal code cannot satisfy the category. A changed mutation records
the exact semantic diff, changed graph, baseline answer and changed answer;
all four digests are rederived. A refusing mutation records its exact stable
code plus the checked baseline. Category contracts additionally require the
declared semantic facets and behavior transition: negation, authority,
permission/prohibition, scope, unknown guard and consequence-3 mutations must
change their named policy outcome; an exact literal preserves id and kind but
changes bytes; ordering performs one exact two-effect swap; stale module,
missing dependency, unknown opcode and alias collision refuse under their
specific code. An unchanged graph or unchanged declared observation refuses.
Mutation ids, categories and specimen ownership are one fixed sorted corpus
assignment in both the runtime and public schema; categories cannot migrate
between specimens while retaining a familiar id.

The top manifest also binds the verified 17-file seed copy as
`non-executable-reference-evidence`. Its exact inventory bytes, full inventory
shape, archive digest, per-file size and digest, aggregate reference digest,
flat closed member set and non-executable regular-file mode are checked. Seed
Python is evidence bytes; the verifier never imports or executes it. Seven
complete, sorted critical vectors cover permission/prohibition, authority,
negation, unknown guard, ordering, exact literal and consequence-3. A vector
passes only when its mutation ids exactly equal the complete fixed set and
every member satisfies its category's outcome contract. A permitted subset is
not 100% coverage.

## Local codec interface

`scripts/noema.py parse` accepts named source, module-directory, profile,
kernel and output paths. It validates everything before atomically writing one
`noema-build/v1` object containing the graph and lock. `format` recovers the
canonical source; `project` writes one `noema-projection/v1` bundle;
`semantic-diff` compares two builds; and `verify --build` rereads every
dependency and lock identity. Those four commands take the same module,
profile and kernel paths. `verify --manifest` checks either one self-described
runtime manifest or the source-bound specimen corpus by its schema identity.
`mutations --manifest` accepts only the specimen corpus and rechecks all fixed
hostile and critical-vector outcomes. `self-test` performs the checked-in
complete-fixture round trip without writing a file.

`measure --manifest --profiles --output` records the fixed corpus under four
unlike external profiles before evidence is anchored. A live record also needs
an explicit `--budget-usd` and either `--credential-file` or the
`NOEMA_OPENROUTER_KEY_FILE` path variable. Once the corpus carries checked
evidence, the same command verifies the complete anchor and replays its exact
measurement bytes without an external call or spend. `emit-evaluation
--manifest --profiles --output` publishes the deterministic 16-prompt packet.
`run-evaluation --packet --manifest --profiles --output` is the separately
authorised live 32-call boundary; it likewise requires an explicit budget.
`tally-evaluation --packet --answers --output` performs no external call and
rederives the fixed 16 source/Noema family pairs.

All input leaves must be regular files. Repository-bound reads open and recheck
every ancestor relative to retained directory descriptors. Module resolution
opens one real module directory, reads only digest-requested leaves relative to
that descriptor, and never scans it; unmentioned files have no semantic role.
File digest, byte count and mode evidence come from the same opened identity.
Platforms without the required no-follow, descriptor-relative directory
operations refuse. Runtime-manifest verification retains and rechecks the real
manifest parent and anchored manifest leaf across every sibling-artifact check.
An output leaf must be Unicode-scalar UTF-8 and at most 255 bytes. Output opens
and retains the real parent directory, creates a random
`.noema-write-` leaf independent of the target name within that descriptor,
loops on partial writes, syncs file and parent, replaces the descriptor-relative
target, rereads the exact payload and rechecks the requested parent path. A
refusal before replacement leaves the prior target intact and removes the
temporary. A post-replacement sync or parent-binding failure is reported as
uncertain durable state, never success; a concurrently substituted path is
never followed outside the retained parent.

## Policy runtime

The runtime surface is exactly:

```text
select(operation,state,target,tools,authority,facts) -> manifest + projection
check(effect,facts,manifest)                         -> permit | refuse | unknown
next(machine,state,event,receipts,manifest)          -> transition | stop
literal(id,manifest)                                 -> kind + exact bytes
explain(policy-node,manifest)                        -> non-authoritative render
```

`next` owns no external domain judgment; it evaluates declared state, event,
guard and ordered effects. `literal` refuses an unreachable id. `explain`
accepts only a reachable policy record, never a literal or definition, labels
its output and no policy operation may consume that render as evidence.
The runtime has no operation for subprocess, network, Git, GitHub, file
mutation, publication or deployment.

All five operations consume data and return data. Their CLI forms accept only
input paths and identifiers; none exposes an output path. `select` reports the
manifest and projection identities and exact partitions. The in-process
operation returns those two derived objects so a caller can preserve them at a
separately authorised boundary. A prior manifest is optional comparison input;
when supplied, the result states whether the exact manifest identity changed.
In-process policy operations accept only a freshly selected manifest or the
fully rederived result of artifact verification. Deserialized manifest data
must cross that verifier; structural validity alone does not establish its
provenance, so an unsealed in-process value refuses before deep validation and
mutation after verification invalidates the manifest. Artifact verification
validates omission membership and fact evidence through precomputed indexes.
Slice selection likewise accepts only a locally compiled or fully
artifact-verified build, and hashes the complete validated profile value
against its locked digest before deriving a manifest.

Policy evaluation first expands only locked pure definitions. A checked fact
can settle any exact proposition whose closed evaluation is unknown; a fact
that contradicts a closed result or an equivalent expanded proposition
refuses. Otherwise the runtime evaluates the closed three-valued Boolean
operators, finite quantifiers, typed equality, membership, containment and
unsigned comparisons; an opaque predicate remains unknown. A self-identical
closed term is true without external evidence. Unknown guards retain their
dependent directive and yield unknown rather than permission.

`check` evaluates applicable `+`, `-` and `!` intents in authored `;` order
under their `?`, `/`, `@` and `^` wrappers. Nested authority and scope wrappers
accumulate; an inner wrapper cannot discard an outer constraint. A prohibition
or failed requirement refuses before any permission is considered; a satisfied
`!` is a gate, never a permission. Opposed requirements refuse unless one
included `override` names the higher and lower rules and its typed authority,
scope and
`core.checked(evidence)` fact all hold. Precedence alone does not resolve that
conflict, and an inactive or inapplicable higher rule cannot resolve it. A rule
carries at most one `core.consequence` atom with value `0` through `3`; each
relevant rule without a marker defaults independently to consequence 3, and
any invalid value or resulting disagreement refuses. Consequence 0 and 1 can
default permit only when at least one directive is active and applicable;
otherwise no policy applies. Consequence 2 and 3 default deny without an
applicable `^` authority and satisfied gates. An exception is
retained as policy and recovery context but cannot by itself cancel a
prohibition or mint authority in this shadow runtime. Any relevant exception
without applicable authority and scope, established gate and record evidence,
and an active expiry refuses before permission can be granted.
Relevance is determined by the exception's declared effect subject. Its
recovery directive remains slice context and does not make the exception a
policy constraint on that recovery effect.
For a permitted consequence-2 or consequence-3 effect, the reported
controlling node is one applicable permission that supplied that authority,
not an earlier unwrapped permission.

Pure definitions are expanded before runtime code reads typed fields as well
as directive bodies. Defined actors and scopes therefore govern overrides and
exceptions exactly like direct atoms, and defined machine, state and event
values govern transition matching and returned next state.

`next` matches one machine, from-state and event. A manifest is complete only
for its selected from-state, so a different state refuses and the caller must
reselect after a transition. Zero established matches stop, an unknown guard
stops unknown even beside one established competitor, and more than one
established match refuses. A successful result returns the next state and the
exact ordered directive terms without applying them.
`literal` returns the kind, byte count, digest and exact reachable value; even
`command`, `path` and `url` values stay inert. `explain` returns canonical
record JSON under
`noema-explanation/v1` with `authoritative:false`. Literal records use only the
separate `literal` result channel.

## Resource limits

Version 1 applies every limit before returning a partial graph or result:

| resource | maximum |
| --- | ---: |
| input file | 1,048,576 bytes |
| physical line | 65,536 bytes |
| source records | 16,384 |
| graph nodes | 16,384 |
| imports | 64 |
| source-record or module-document nesting depth | 64 |
| one literal | 65,000 decoded UTF-8 bytes |
| all decoded literal occurrences | 786,432 bytes |
| expanded macro graph | 65,536 nodes |
| slice fixed-point scans | 65,536 records |
| one policy directive pass | 65,536 expanded nodes |
| one selection, policy or transition truth pass | 65,536 expanded nodes |
| policy requirement pairs | 65,536 |
| one finite quantifier set | 4,096 members |
| one specimen artifact inventory | 16,384 files |
| one specimen artifact inventory | 1,048,576 bytes |
| one derived output | 1,048,576 bytes |
| external profiles | 8 |
| one adapter input / stdout / stderr | 1,048,576 / 65,536 / 8,192 bytes |
| one adapter timeout | 600 seconds |
| adapter completion | 16 measurement tokens / 2,048 evaluation tokens |
| evaluation packet | 4,194,304 bytes, 8 cases and 16 prompts |

The graph-node count includes source records, term nodes, each embedded module
and every module import, subtype, signature and definition declaration.
Derived graph and build envelopes add at most three and four fixed container
levels respectively; every embedded source record and module document remains
subject to the 64-level limit.
Expanded-macro accounting substitutes an argument at every occurrence of its
formal parameter; the macro-call node itself is absent from the expanded graph.
Slice closure refuses before repeated fixed-point passes inspect more than
65,536 record entries in aggregate.
One shared directive counter covers every rule and every nested guard,
authority, scope or sequence child visited by one `check` operation. One shared
truth counter covers every proposition and recursively evaluated Boolean or
quantified child visited by one `select`, `check` or `next` operation, so
record boundaries and quantifier substitution cannot reset the work budget.
Policy evaluation expands each requirement once, indexes override edges and
refuses before comparing more than 65,536 requirement pairs.

The seed archive verifier separately accepts at most 1,048,576 archive bytes,
64 members, 1,048,576 uncompressed bytes in aggregate, 1,048,576 bytes for one
member and 512 UTF-8 bytes for one member path. It rejects encryption,
non-canonical or unsafe paths, links, special files, unsupported compression,
duplicate names and any inventory mismatch. Root and member spellings use the
exact alphabets published in the seed-inventory schema.

## Result and refusal contract

Each command writes at most one `noema-result/v1` canonical JSON line to
standard output. The final emission boundary applies the 1,048,576-byte output
limit; an oversized result becomes one bounded refusal instead of a partial or
over-limit success.
It names command, deterministic correlation id, verdict, stable code, input and
output digests and bounded counts that exist for that command. It never carries
source text, prompts, model output or credentials. The sole payload exception
is a successful `literal` result, whose purpose is to return one exact reachable
inert value with its kind, byte count and digest.
Every runtime correlation binds the exact manifest identity. Runtime digest
maps name that manifest and the exact output; `check` also names selected facts,
while `next` names selected facts and additional receipts separately. A
`select` comparison binds its prior and current manifest identities as `before`
and `after`; an invocation without a prior manifest has no comparison digests.
Manifest verification correlates to the exact verified manifest. The runtime
self-test additionally reports one `cases` digest over all seven exact case
results, including receipt and alternate-selection evidence.
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
| `NOE-E-POLICY` | contradictory facts, consequence declarations or transition state | repair the inconsistent policy input or graph and reselect |
| `NOE-E-MUTATION` | a declared hostile input leaves its graph or checked observation unchanged | repair the counterexample so it exercises the named semantic boundary |
| `NOE-E-SELF_TEST` | checked-in demonstration no longer satisfies its fixed outcome | repair or regenerate the fixture before relying on the prototype |
| `NOE-E-EVALUATION` | packet, profile, family, case or answer mismatch | restore the exact isolated cohort and retally |
| `NOE-E-ADAPTER` | executable, environment, endpoint, response, timeout or identity boundary | restore the digest-bound closed invocation or record the profile unknown |
| `NOE-E-BUDGET` | absent spend authority, exhausted ceiling or uncertain accounting | inspect the append-only reservation ledger before authorising a fresh run |
| `NOE-E-MEASURE` | baseline, component, cohort, gate or observation mismatch | restore the same-profile source-first measurement and revalidate it |
| `NOE-E-TOKENIZER` | unavailable identity or impossible provider token count | retain the profile as unknown or repeat its exact acquired endpoint |
| `NOE-E-UNIMPLEMENTED` | operation reserved for a later prototype step | finish and verify its declared step |

A refusal returns no partial graph, tape, slice, decision or evidence file.
Failure blocks its dependent operation while leaving inspection, repair, rerun
and safe exit available when their own inputs validate.

## Measurement and family evaluation

Measurement records bytes and endpoint-reported token deltas separately for
Markdown source, canonical `.noe`, full projection, operation slice, literals,
kernel, reachable definitions, alias dictionary, first use, steady state and
corpus amortisation. Every payload is wrapped in the same fixed inert-data
instruction. Sequence zero measures that valid wrapper with an empty payload;
all four Markdown observations follow before any derived representation. Each
content count subtracts that exact endpoint's wrapper value. Source and
projections therefore use one request shape and one exact profile, while the
private vocabulary digest remains an explicit unknown. These are real provider
accounting values, not heuristic local estimates or a claim that a private
token vocabulary was recovered. Corpus amortisation exists only when every
specimen carries byte-identical kernel and alias-dictionary components; drift
refuses before an adapter call or evidence replay rather than hiding another
component behind the first specimen.

The fixed gates are first use at most 70% of relevant Markdown, steady state at
most 40%, complete canonical Noema at most 55% of the declared source corpus,
and 100% for critical permission/prohibition, authority, negation,
unknown-guard, ordering, exact-literal and consequence-3 vectors. The three
token thresholds apply to each profile's complete declared corpus. Per-document
and one-through-four-document amortised ratios remain evidence, but a single
document ratio is not a substitute acceptance gate.

Evaluation emits one answer-free complete-source prompt and one Noema
kernel/dictionary/slice prompt per case, one fresh process and nonce each, and
the fixed evaluation seed `0`. The seed is part of the profile and exact
adapter request; it reduces sampling variance but is not a provider-determinism
claim. Measurement requests carry no seed. The Noema prompt contains no
Markdown source excerpt. Both representations receive
the same closed runtime context: selected authority, tools, operation, state,
target and facts. `authority` lists established authorising actors. Facts bind
exact propositions to `true`, `false` or `unknown`; an absent condition is
unknown. Each fact exposes its truth value, evidence digest and exact
prefix proposition; its id must recompute from that proposition, and the
proposition must resolve to a typed authored or macro-expanded proposition in
the verified graph. A free fact name, non-proposition graph list or unresolved
digest refuses before packet publication. The source prompt additionally
receives its exact bound excerpt; the Noema prompt receives only the bound node
id because the slice is its semantic evidence.

Candidate ids are opaque and their order carries no oracle. The packet is
complete only after its manifest is written, its closed directory inventory is
checked, and every prompt is reread against the deterministic corpus
immediately before use. Tally requires exact case-set equality, no duplicate
id, exact tree, source, graph, kernel, projection, profile and model identity,
and two genuinely different family identities for a cross-family result. Only
the selected candidate id and bounded request, generation, token and cost
provenance are retained; raw model transcripts are not evidence. A committed
run records that run; it does not predict a rerun or establish model quality.

`noema-external-profiles/v1` binds the catalogue URL and observation date,
requested and endpoint model ids, provider name and exact route tag, context
and completion caps, quantisation, supported request parameters, uncached
prompt/completion prices, the explicit per-request price and threshold
overrides. Evaluation profiles also bind seed `0` and refuse an endpoint whose
acquisition does not advertise `seed`; measurement-only profiles bind `null`.
Its acquisition digest is separate from the complete profile digest. A
provider-private vocabulary is `null`, never an invented checksum.

External tokenizer or model programs are explicit digest-bound argv lists with
a cleared environment, minimal allowlist, timeout and output cap. The bundled
OpenRouter adapter is fixed to `/usr/bin/python3 -I`, the current
`scripts/noema.py` digest and one HTTPS origin with redirects disabled. Isolated
mode prevents repository and user-site modules from shadowing its transport.
Requests bind one provider route, disable fallbacks, require declared
parameters, deny data collection,
require zero-data-retention routing and cap prompt, completion and per-request
price at the acquired base rate. Evaluation calls send the profile-bound seed
`0`; measurement calls omit it. A route reporting no per-request fee records
and sends an exact zero rather than leaving that spend class unbounded. The
credential crosses only as a private regular-file path and is never an
argument, prompt, result or fixture value.

A live call rehashes both executable and repository invocation bytes before
and after use. Portable evidence verification rehashes the repository adapter
but treats the recorded host executable digest as historical provenance; it
does not require another machine to install or execute that binary.

Every paid request reserves a conservative upper bound in one locked canonical
ledger before the child starts. A recorded provider cost settles that exact
request; an unavailable or unaccounted response retains its reservation. The
ledger uses exact bounded decimal addition and multiplication throughout; host
decimal-context rounding cannot admit an over-ceiling reservation or hide
settled spend. The ceiling cannot change in place, so uncertain spend consumes
authority rather than being silently retried. New dependencies, downloads,
credentials, network calls, source disclosure and paid use require separate
operator authority. Model output is untrusted data and never becomes a command,
query, path, fact or authority edge.

When published by the corpus manifest, the checked-in
`tests/fixtures/noema-v1/evidence/` record binds one accepted measurement, 32
answer-provenance records and 16/16 tally to one ancestor commit, tree, corpus,
profile set, packet and case set. Corpus verification reconstructs the packet
and tally before accepting those bytes. The audit-repair checkpoint omits that
anchor until its changed compiler and profiles receive a fresh run. The exact
counts, rejected predecessor runs and shadow-only decision live in ADR-059;
raw provider transcripts are deliberately absent.

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
