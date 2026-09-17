# Decision: Omit checkpoint authority conformance corpora from the portable runtime

## Status

Proposed, 2026-09-18, for P-862 in issue #1676. This draft awaits the governed
implementation and integration. It changes no cap, reserve or numbered record.

## Context

The portable Promise Machine runtime packages every tracked file under
`plugins/` except the classes [ADR-040](../ADR-040-package-one-dependency-closed-portable-router.md)
and [ADR-090](../ADR-090-omit-portable-decorative-portraits.md) omit. The
skills CLI's archive ceiling is 26,214,400 bytes and ADR-090 reserves
5,242,880 bytes below it, so a generated runtime may hold at most 20,971,520
bytes. At the Step 3 tip of this run the runtime held 20,892,920 bytes, 78,600
below that maximum. The Step 4 candidate before this decision held 21,187,330
bytes, 215,810 over it, and the root suite refused the package.

The checkpoint authority protocol keeps its conformance corpora beside its
schemas under `plugins/hexaemeron/skills/fiat/checkpoint-authority/`:
`fixtures/` carries the Step 2 record and signature specimens (125,904 bytes)
and the four Step 4 replay files, `replay-history.json`,
`replay-manifest.json`, `replay-hostile.json` and `replay-budget.json`
(124,853 bytes); `native-fixture/` carries the Step 3 native boundary archive,
its public key and fixture record (65,353 bytes). Only the conformance
reporters read these files: `conformance.py`, `native_conformance.py` and
`replay_conformance.py`, driven from
`plugins/hexaemeron/tests/checkpoint_authority_conformance.py`, which the
runtime already omits with every `plugins/*/tests/**` path. `native.py` reads
`native-profile.json` at run time, and the router reads the schemas and READMEs.

## Decision

Omit `plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/**` and
`plugins/hexaemeron/skills/fiat/checkpoint-authority/native-fixture/**` from
the generated runtime. Everything else under `checkpoint-authority/` stays in
the payload: `schemas/**`, `native-profile.json`, `native-capabilities.json`
and the READMEs. The four Step 4 replay files move into `fixtures/`, so one
directory holds every record, signature and replay specimen; no Step 1 to 3
file moves. The cap, the reserve and every numbered decision record keep their
bytes.

## Alternatives

Lowering the ADR-090 reserve would spend the growth margin that record set
aside and would recur at Step 5, which adds release fixtures of its own.
Relocating release fixtures into `plugins/hexaemeron/tests/` would misfile
corpora that consumers pin by digest and that the runbook places beside the
schemas. Raising the byte cap leaves the CLI's own refusal unchanged, as
ADR-090 records. ADR-040 already omits data the router never reads, the
Anamnesis specimens and the Alexandria Compound v3 trace inputs, and has the
installed adapter name the omitted data and refuse an operation that needs it;
the conformance corpora fit that class exactly.

## Consequences

The installed router names the omitted data and refuses an operation that
needs it: `PORTABLE.md` lists the corpora among the omitted surfaces and
instructs the router to stop and use a full checkout. The three conformance
reporters run only from a full checkout, where their manifests bind the
corpora by digest; a runtime user who needs a conformance result checks out
the source. The runtime manifest records the two omission patterns and their
reasons beside the other omitted classes; per-file omitted rows remain the
ADR-090 portrait class only. With this decision the generated package measures
20,855,284 bytes across 1,510 files, 5,359,116 bytes below the ceiling.
`tests/test_skills_sh_package.py` holds the omission set and records those
figures beside the 1,600-file tripwire and the unchanged cap and reserve. The
protocol reference and the fixtures README point here from the corpus layout.
