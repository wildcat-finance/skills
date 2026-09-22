# Installed Promise Machine runtime

This directory is the dependency-closed installed form of Wildcat Labs Skills,
the Shoggoth. It carries the same collective, Promise Machine law, plugin
runtime contracts, and canonical first-party skills as a source checkout, with
the omissions listed below.

## Select the runtime

Use this path only when the router is installed as one Agent Skills package.
The full-source path is valid only when `../../../PROMISE_MACHINE.md` identifies
`promise-machine/v1` and the sibling `../../../plugins/` directory holds all
eighteen runtime contracts. A target repository's own `AGENTS.md` does not make
it a Wildcat Skills source checkout.

## Verify the copy

Before selecting a skill, run:

```bash
python3 "<promise-machine directory>/scripts/verify_runtime.py"
```

A failed verification blocks selection from this package. Repair or reinstall
it; do not fetch missing instructions ad hoc or continue from an unverified
partial copy. This check establishes internal agreement with the installed
manifest; it does not authenticate the publisher or source commit.

## Load one specialist

After a passing verification:

1. Treat `<promise-machine directory>/runtime/` as the distribution root.
2. Consult `runtime/.horos/boundary.json` before reading that tree broadly.
3. Read `runtime/SHOGGOTH.md` before interpreting a collective name.
4. Read `runtime/PROMISE_MACHINE.md`, then `runtime/AGENTS.md`.
5. For every source-layout route `../../../plugins/<name>/AGENTS.md` in
   `SKILL.md`, read `runtime/plugins/<name>/AGENTS.md` instead.
6. Resolve the selected canonical `SKILL.md` and every linked resource from the
   copied runtime tree. Keep the user's target repository separate and obey its
   own instructions before a write or external side effect.

## Honour the omissions

`runtime/MANIFEST.json` binds every copied file to its canonical source path,
byte count, and SHA-256 digest. It also binds the installed-tree Horos boundary
generated from those files. The package deliberately omits host discovery
manifests, plugin development suites, historical audit records, the checkpoint
authority conformance corpora under
`plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/` and
`native-fixture/`, and Alexandria's 16 MB Compound v3 Phase 0 trace inputs and
built release. The example's explanation and rebuild entrypoint remain present,
but they do not make the offline demonstration runnable, and the checkpoint
authority schemas, native profile and capability map remain present without
the corpora their conformance reporters read. If a selected operation needs one
of the omitted surfaces, stop and use a full checkout of
`wildcat-finance/skills`; absence does not authorise a substitute claim.

The complete Lazarus Aave v4 v1 fixture remains under
`runtime/plugins/lazarus/examples/aave-v4-spoke-v1-release/fixture/`, inside its
unchanged preservation release. The package omits six duplicate payload files
from `runtime/plugins/lazarus/examples/aave-v4-spoke-v1/`. Its manifest and
program remain for the historical demonstration record, but that directory is
not a complete installed fixture. Use the retained fixture for `verify` and
`replay`, and its parent release for `verify-release`. Run the source
reproduction demonstration from a full checkout. Before omitting any payload,
the generator requires both copies to be tracked regular files with identical
bytes and modes and no symlinked component. The decision is recorded in
`adr/keep-one-complete-lazarus-fixture-in-the-portable-runtime`.

Tabularium's superseding v1 payloads and reconstruction programs also require a
full checkout; their documents and the v0 evidence remain in this package.

Wildcat V1 and V2 interval demonstration payloads also remain in the full
source checkout: the direct JSON files and V1 pre-plan probes under
`plugins/alexandria/examples/wildcat-v1-interval-v0/` and
`wildcat-v2-interval-v0/`. Their documents and Python entrypoints remain.
Run their metadata checks, including the combined `verify-preserved` operation,
from a full checkout; rebuilding additionally requires the private staging
archives. Collector, verifier and schema runtime files are retained. See
`adr/keep-wildcat-interval-demonstration-payloads-in-full-checkouts`.

The Ariadne `plugins/ariadne/examples/wildcat-datasets-v0/` example retains
only its README in this package. Both metadata verification and its full
demonstration require the source checkout. All example evidence stays in that
checkout; core Ariadne capture, verifier and schema runtime files remain here.
The same distribution decision above records this extension.

Decorative PNG and WebP portraits in the root and plugin `assets/characters/`
directories also remain in the source checkout. Their inline Markdown images
and quoted HTML `img` references are removed only from packaged copies. The
manifest records the omitted files and each transformed file's original
digest, original byte length and removed byte ranges, beside its output digest
and length. Other Markdown content remains byte-identical to its source. Generation
requires at least 5,242,880 bytes of headroom below the 26,214,400-byte ceiling;
the complete package count includes the runtime manifest and outer files.
The installed verifier checks the resulting output manifest.

Portrait removal changes the whole-file identities used by the evaluation
record. The generator verifies the canonical record, emits all eleven source
and packaged prompts through the evaluation owner, and refuses if any prompt
differs. Only then does it replay the unchanged historical answers through
the owner's tally for the packaged record. Its manifest row binds the original
and derived bytes, unchanged prompt digests and answer identity. The original
model and date remain fixed; this derivation makes no new model observation.
