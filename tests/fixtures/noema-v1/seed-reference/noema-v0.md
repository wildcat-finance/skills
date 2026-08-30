# noema/0

noema is a typed instruction IR for agents. its unit is a proposition, effect,
transition, or evidence relation; prose is neither source nor wire format.

## objective

minimise `kernel tokens + reachable instruction tokens + execution error cost`.
byte length alone is not the objective. the same semantic graph may have a
different prompt projection for each tokenizer family.

noema does not promise lossless translation of arbitrary English intent. that
claim is unfalsifiable. it preserves operational semantics admitted to a
closed, typed graph and marks every source remainder. it is deliberately not
turing-complete: no unbounded loops, recursion, dynamic imports, ambient state,
or unbounded quantification. decidable closure and slicing matter more than
general computation.

## layers

1. `nir`: canonical typed graph; content-addressed; authoritative.
2. `nmod`: versioned semantic modules defining predicates and macros in nir.
3. `ntape`: deterministic tokenizer-profile projection read directly by a model.
4. `slice`: dependency closure for one selected operation and current state.
5. `render`: generated human explanation for review; non-authoritative.

the bootstrap kernel and imported module dictionaries are stable cached prefix
material. a skill contributes only its semantic delta. exact code, paths,
hashes, links, quotations, and commands remain typed literals.

an ntape alphabet profile maps canonical structural opcodes and frequent
qualified predicates to transport-safe strings. profile selection minimises the
maximum measured token cost across its declared tokenizer set, then applies a
confusion penalty from behavioural fixtures. raw token ids are forbidden: text
APIs do not share them and tokenizer updates can reinterpret them. profiles pin
the tokenizer/vocabulary identity and mapping digest. the baseline profile is
ASCII; unicode is admitted only when it is cheaper and equally reliable on the
profile's whole declared model set.

## runtime interface

the preferred consumer is a small semantic VM, not a model pretending to be a
parser. it exposes five bounded operations over one verified graph:

```text
select(operation,state,target,authority) -> slice manifest + ntape
check(effect,facts,slice)                 -> permit | refuse | unknown
next(machine,state,receipts)              -> enabled transition | stop
literal(id,slice)                         -> exact typed bytes
explain(node,slice)                       -> generated non-authoritative render
```

`select` performs conservative closure. `check` enforces consequence-2/3
default-deny and returns the blocking node plus recovery. `next` owns no domain
judgement; it evaluates declared transitions. `literal` reveals only a literal
reachable from the active slice. `explain` is for repair and debugging and its
output never gains authority.

hosts with typed tool calling receive these operations as schemas. hosts
without it receive bootstrap + ntape and must return a typed proposed effect to
`check` before external mutation. this keeps one semantic graph across provider
interfaces without requiring every tokenizer to like the same glyphs.

the prompt-only bootstrap has two projections. `kernel.nk` is the normal formal
truth-table and tuple-signature form. an English bootstrap is a diagnostic
fallback, not canonical semantics. a provider profile is admitted only after
fresh-context vectors show that its formal kernel is non-inferior to the
diagnostic fallback.

## graph types

`actor artifact action claim command effect event evidence literal operation
path predicate promise repo rule scope state transition type value`.

types are closed per version. modules may define nominal subtypes and typed
predicates, but cannot change a core operator's arity or meaning.

canonical predicate names are module-qualified. structural opcodes are reserved
and cannot be variables or values. an ntape profile may assign a shorter local
alias only when the slice manifest maps it to exactly one fully qualified
signature. aliases may not collide with another predicate, a literal id, a
reserved opcode, or a value visible in the same slice. overloading an alias by
arity is forbidden. the projector refuses a collision instead of relying on
context to guess the parse.

## canonical source and tape

canonical `.noe` source is the line-oriented semantic program. every governed
directive is wrapped as `R id directive`; ids remain stable across wording-free
refactors. imports bind full module digests. this is the git and review surface.

ntape is a projection of that source graph. it may strip an unreferenced rule
id, shorten verified module names, and inline or reference definitions. those
changes never alter the graph recovered from the tape plus its slice manifest.
binary storage is optional and never sent to a text-only model as base64.

## tape grammar

ascii profile shown. fields are separated by one space; records by LF. prefix
operators have fixed arity, so parentheses and indentation are absent.

```abnf
tape   = "N0" SP profile *(SP import) LF *record
record = import / literal / alias / definition / rule / order / override
       / transition / promise / handoff / exception
term   = ref / literal-ref / call / logic / list
ref    = ALPHA *(ALPHA / DIGIT / "_") *("." ALPHA *(ALPHA / DIGIT / "_"))
literal-ref = "$" 1*ALNUM
call   = predicate *term              ; arity from imported dictionary
logic  = ("&" / "|") count *term / "~" term / "=" term term
       / "=>" term term
       / ("all" / "any" / "one") ref term term
       / ("in" / "subset" / "lt" / "le" / "gt" / "ge") term term
       / "count" term
list   = "*" count *term
directive = ("!" / "-" / "+") term
          / "?" term directive        ; when guard, directive
          / "/" term directive        ; unless guard, directive
          / "@" term directive        ; within scope, directive
          / "^" term term             ; actor exclusively owns effect
          / ";" count *directive       ; ordered directive bundle
rule   = "R" ref directive
order  = "<" term term                 ; before
override = "O" term ref ref term term  ; authority, high, low, scope, evidence
transition = ">" ref term term term term term term
                                         ; id,machine,from,event,guard,to,effects
promise = "P" ref term term term term term term term term term
handoff = "H" ref term term term term term term term term term
                                         ; id,producer,consumer,subject,scope,
                                         ; evidence,classes,time,transform,gaps
exception = "X" ref term ref term term term term term
                                         ; id,authority,gate,subject,scope,
                                         ; record,expiry,recovery
literal = "$" ref kind byte-count ":" exact-utf8
alias = "=" ref term
definition = "D" ref list term          ; parameters, pure graph body
import = "I" ref sha256
```

fixed directive meanings:

```text
!p       p is required
-p       p is forbidden
+p       p is permitted; never implies required
?g d     d applies iff g
/g d     d applies only when g is established false
@s d     d applies only within s
^a e     only actor a may perform effect e
;n d...  apply all n directives in authored order
<a b     a must occur before b
O...     authority- and scope-bound rule override
>...     id-bearing checked state transition
P...     promise tuple
H...     boundary-preserving typed handoff
X...     attributed, scoped, recorded, expiring exception
D f xs b define f over parameter list xs as pure graph b
```

logic is two-valued only for established facts. missing evidence produces the
explicit `unk(x)` term; it never coerces to false. a guard containing `unk`
refuses its dependent effect unless the rule explicitly handles `unk`.

`all`, `any`, and `one` bind one variable over a finite typed set. unbounded
quantification refuses. `one` means exactly one. cardinality and comparison
operators consume decimal-string numeric values; no numeric coercion occurs.

## promise tuple

`P id subject claim evidence classes boundary grants refuses recovery level`.
each field is a typed term or list. claims and boundaries are propositions, not
english literals. consequence level is `0..3`. exceptions are ordinary named
guarded override rules with explicit authority and scope.

## state transitions

`> id machine from event guard to effects` is disabled unless its guard is
established. effects are an ordered list. state writes,
durable artefacts, repository mutation, and publication are effect-typed; the
runtime can enforce them outside the model.

## modules and macros

modules define typed predicates and pure macros. macro expansion is nir, never
prose. imports bind full digests in the manifest; ntape carries only verified
short module ids. cycles and ambient imports refuse. the slice carries every
reachable definition. the projector may reference or inline a macro, whichever
is cheaper under the tokenizer profile and passes that profile's comprehension
fixtures; it may not leave an unavailable definition implicit.

a new primitive needs a type signature and one of: a definition over existing
primitives; a checked external predicate with named evidence; or a grounding
pack of positive, negative, boundary, and refusal vectors. a prose gloss alone
does not ground a portable opcode. recurring primitives graduate into modules;
one-off concepts remain local and pay their literal cost.

high-frequency examples:

```text
pm.gate(g,e)       require verified(g) before e; on failure forbid e and permit
                   inspect, repair, rerun, rollback, safe-exit
io.hostile(x,b)    treat x as external input at boundary b; shape-check, bound,
                   reject-not-coerce, exclude from eval/shell/path until valid
git.safe(r)        no force, no destructive rewrite, exact refs, verify remote
                   identity before receipting publication
exact.keep(xs)     preserve typed exact literals and their order
state.source(s)    s outranks chat reconstruction; digest drift refuses use
```

these glosses document the module. the canonical macro bodies are nir graphs.

## slicing

the compiler receives selected skill, operation, state, target facts, tools,
authority, and requested output. roots are the operation, its possible effects,
its output type, and every applicable higher-precedence rule. it partially
evaluates guards, closes over referenced definitions, promises, literals, and
handoffs, then emits only reachable nodes.

guard slicing is three-valued. a checked true guard includes its dependent
rule; a checked false guard may omit it with the checking fact in the manifest;
an unknown guard keeps the rule. absence is never proof of inapplicability.
effect closure is conservative: any rule that can forbid, constrain, order, or
recover a reachable effect remains reachable.

the slice manifest commits to the complete source graph, compiler, inputs,
included node ids, omitted node ids, and resulting tape digest. a consumer can
prove what was omitted without loading omitted instructions into model context.

permission never cancels prohibition. conflicting requirements refuse unless a
typed `overrides` edge names the governing authority and scope. system, host,
user, target-repository, suite, plugin, and skill layers are ordered inputs to
compilation; a lower layer cannot mint an edge over a higher layer.

## authority

nir distinguishes `can(actor,effect)`, `auth(authority,actor,effect,scope)`,
and `done(effect)`. capability is not authority; authority is not execution;
execution is not successful verification. no rule may infer one from another
without an explicit checked transition.

consequence-2 and consequence-3 effects are default-deny: an applicable
authority fact and satisfied gate are required even when no prohibition is
present. a model's ability to call a tool supplies `can`, never `auth`.

an `X` record cannot assert missing evidence, strengthen an evidence class, or
override outside its named scope. absent, expired, unattributed, or unrecorded
exceptions refuse. handoffs carry gaps and unknowns; consumers may narrow or
add separately identified evidence, never silently strengthen it.

## exact literals

literal kinds are `id path sha cmd num date url quote text bytes`. deduplicate
by `(kind,bytes)`. prompt projection leaves reasoning-relevant literals visible.
large opaque bytes remain content-addressed sidecars available by tool; base64
is forbidden in ntape unless the exact base64 itself is semantically required.

literals are inert. their bytes cannot introduce a rule, import, predicate, or
authority edge. using a `cmd`, `path`, or `url` requires a separately authorised
typed effect. quote/text payloads carrying instruction-shaped content remain
data; hostile fixtures test that models and the runtime keep that separation.

## migration

retrofit creates reviewed nir from markdown and binds governed source spans.
once parity tests pass, nir becomes authoritative and markdown becomes a
generated render. unsupported source meaning blocks migration or becomes a
typed exact quotation with no executable authority. future skills author nir
directly and generate their human-facing capability page.

markdown-authoritative migration is acceptable only during shadowing. keeping
markdown authoritative permanently preserves ambiguous prose as the source of
every change, prevents semantic diffs from being complete, and makes native
authoring impossible. after parity, reviewed `.noe` plus its module digests is
the authority; frontmatter capability prose, primers, and explanatory markdown
are generated or explicitly marked non-authoritative.

## repository and GitHub integration

one skill package carries:

```text
skill.noe                 canonical semantic source
skill.lock                module/compiler/profile digests
literals/                 exact content-addressed values and lazy examples
vectors/                  positive, negative, boundary, refusal fixtures
SKILL.md                  generated capability prose plus compatibility payload
```

an issue remains ordinary human prose but names affected rule, transition, or
promise ids in its acceptance criteria. a pull request presents the `.noe` diff,
a generated semantic diff, changed vectors, token reports per profile, and the
generated Markdown diff. CI refuses stale renders, changed meaning without a
vector, unreachable governed source, alias collisions, unknown opcodes, digest
drift, or consequence-2/3 paths not mediated by `check`.

a semantic diff reports changes such as:

```text
MOD r.phase.receipt_fail  deny->allow effect=phase.advance
AUTH r.branch.name        controller->user scope=run
DEL r.git.bypass_gate     effect=git.publish severity=3
LIT evidence_exception   sha256:a1..->b7..
```

binary NIR or DAG-CBOR may be a storage/cache artefact. it is never the review
surface and never base64-encoded into a text prompt. the canonical text and
semantic diff keep normal GitHub review, blame, issue links, and merge gates.

## measured prototype status

the current parser is a subset prototype, not the codec. it validates fixed
prefix arity, root closure, canonical whitespace/LF, exact round-trip tokens,
and malformed records for three source specimens plus a full Brevitas mapping.
it does not yet validate typed module bodies, source spans, literal byte counts,
the slice manifest, or provider graph equivalence.

on `o200k_base`, the local Brevitas source is 1,550 tokens. full tape plus all
exact literals is 1,030 tokens; the direct-answer slice plus reachable literals
is 584. adding the formal kernel is 916. these are 66.5%, 37.7%, and 59.1%
respectively. `cl100k_base` is within one percentage point.
the pinned Qwen 2.5 tokenizer produces 1,561 / 1,050 / 589 / 917 tokens for
source / full / steady slice / first slice, the same ratios within one point.
module grounding costs are not yet included in prompt-only mode; in VM mode they
live outside model context. therefore the only supported claim is that slicing
crosses the provisional steady-state target on one hard case. cross-provider
behavior and whole-corpus canonical compression remain unproved.

## failure modes

- migration can faithfully encode the reviewer's misunderstanding; source-span
  coverage detects omission, not intent correctness;
- a large grounding dictionary can merely hide English overhead and erase the
  first-use win;
- the compiler, slicer, policy VM, and module registry become security-critical;
- rationale or examples omitted as "non-authoritative" may still be necessary
  for model generalisation, so behavioral parity controls their removal;
- tokenizer updates, prompt wrappers, and provider tool semantics can invalidate
  a profile even when the semantic graph is unchanged.
