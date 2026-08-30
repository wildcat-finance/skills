# ADR-059: evaluate Noema as a sliced instruction IR in shadow mode

## Status

Accepted, 2026-08-29. The prototype outcome remains open until Step 5 records
its fixed semantic, token and model-family gates. A later ADR must supersede
this one before any authority reversal or repository migration.

## Context

The repository repeatedly loads large agent-facing Markdown files. Issue #909
is building `wildcat-agent-instruction/v1`: authored Markdown remains
authority, a closed reviewed model carries governed meaning, and compact bytes
are a derived full-model codec. Its active stack gives Noema a control design
and reusable boundary lessons, but changing that stack would erase the control
while four or more contributors are working nearby.

Issue #942 asks a different question. A native instruction IR could author
governed semantics as a typed graph, select only the constraints reachable for
one operation and state, and let a small runtime check consequential effects
outside model obedience. The supplied seed demonstrates a possible notation
and one useful sliced-token result. It does not implement typed modules,
source-span closure, a manifest-bound slicer or a policy runtime, and it has no
cross-family behavior evidence.

The choice affects an authorship format, trust boundary and runtime interface.
Reversing it after skills depend on the format would be expensive, so the
prototype must preserve the current authority direction while it is measured.

## Decision

Build Noema as bounded root tooling in shadow mode: existing Markdown remains
authoritative; canonical `.noe`, its graph and every projection are derived;
the runtime returns policy decisions but executes no external effect; and the
final step accepts, narrows or rejects the hypothesis against the fixed #942
gates.

Noema is not a plugin or selectable skill during this run. It changes no
marketplace, router, Promise Machine claim, CI workflow, #909 path or external
repository. Native Noema authorship, a skill conversion and Shoggoth migration
each require a later decision with separate evidence.

Use fixed-position canonical JSON arrays for authored records and prefix terms,
then derive a profile-bound `NT1` text projection by injective exact-string
substitution. Store graph and lock together as one atomic build artifact. This
keeps the governing layer structural and provider-neutral while retaining Git
review, byte recovery and ordinary standard-library parsing. The text carrier
is not the semantics; the recovered typed graph is.

## Alternatives

### Extend `wildcat-agent-instruction/v1`

Rejected for this run. #909 fixes a full derived codec and Markdown authority;
Noema tests task-state slicing and a possible later native-authoring endpoint.
Combining them would move the control design, couple two active stacks and make
either result harder to interpret.

### Keep Markdown and generate task-specific prose summaries

Rejected as the Noema endpoint. Summaries can reduce prompt size and remain an
evaluation baseline, but a deterministic checker cannot prove that an omitted
prohibition, authority edge or recovery path survived model-written prose.

### Compress prose into binary, base64 or private aliases

Rejected. Carrier bytes are not operational semantics, base encodings can cost
more model tokens than source, and an alias table can erase its local saving
once bootstrap cost is counted. Opaque carriers also discard ordinary Git
review and semantic diff.

### Make Noema authoritative immediately

Rejected. Source-to-graph review can establish span coverage and still encode a
reviewer's misunderstanding. Until the fixed mutations, critical vectors,
token measurements and two-family cases exist, an authority flip would promote
an untested interpretation.

## Consequences

The prototype can reuse #909's closed-model, canonicalization, bounds,
source-binding and stable-refusal lessons without modifying its files. GitHub
review keeps canonical text, semantic diff, generated views, vectors and
digests visible. Prompt-only consumers pay the complete kernel and reachable
dictionary cost; runtime consumers can keep policy enforcement outside model
context.

The parser, type checker, module registry, projector, slicer and policy
evaluator become a larger security-sensitive base. Every layer therefore has a
separate stacked step, fixed resource limits, hostile fixtures and no partial
result on refusal. Live tokenizer and model adapters remain ask-first and
outside instruction authority.

An accepted Step 5 result permits continued shadow evaluation only. It does
not permit native skill authorship, a plugin registration, a repository-wide
conversion or migration. A rejected result stays useful: it records which
semantic, compression or transfer gate failed without moving the gate after
observation.

This run stops after its final prototype checkpoint. Fiat integration, merging
the run branch, closing #942 or adopting Noema anywhere is outside this ADR and
requires separately scoped follow-up issues.
