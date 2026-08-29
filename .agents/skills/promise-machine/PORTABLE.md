# Installed Promise Machine runtime

## Select the runtime

Use this path only when the router is installed as one Agent Skills package.
The full-source path is valid only when `../../../PROMISE_MACHINE.md` identifies
`promise-machine/v1` and the sibling `../../../plugins/` directory holds all
fifteen runtime contracts. A target repository's own `AGENTS.md` does not make
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
manifests, plugin development suites, historical audit records, and
Alexandria's 16 MB Compound v3 Phase 0 trace inputs and built release. The
example's explanation and rebuild entrypoint remain present, but they do not
make the offline demonstration runnable. If a selected operation needs one of
the omitted surfaces, stop and use a full checkout of
`wildcat-finance/skills`; absence does not authorise a substitute claim.
