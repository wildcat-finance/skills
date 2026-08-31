# Anamnesis runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Anamnesis.** Anamnesis keeps custody of audit findings and the changes that answered them: it admits sources against an explicit rights basis, preserves the producer's bytes and identifiers unchanged, and releases read-only projections for Elenchus and Synkrisis. It does not produce audit rounds, judge whether a finding was real, or compare runs. **Current frontier:** Source admission ships as the member's first promise: a closed pilot policy, no-follow regular-file reads under a declared byte cap, exact digest checks, and a closed rights and disclosure enumeration in which public visibility is not a rights basis. Curation and release are declared boundaries that refuse by name and say which runbook step owes them.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Anamnesis contains one Agent Skill. Read `skills/anamnesis/SKILL.md` in full
before admitting a source, curating a record, or releasing a corpus.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/anamnesis/` directory.
- Run `skills/anamnesis/scripts/anamnesis.py` from that fixed plugin path.
- Use the exact interpreter named in the repository's `.python-version`.
- Treat the corpus named by the user as the target. Do not substitute this
  distribution checkout unless the user named it.
- `admit` and `admit-seed` read a declared policy and its sources and write
  nothing outside the report path the caller names.
- Names such as `$anamnesis`, `/anamnesis:anamnesis` and `anamnesis:anamnesis`
  are invocation aliases, not shell commands.

## Network and side effects

Anamnesis reaches no network. It reads declared sources as ordinary files,
without following symlinks, under a declared byte cap, and it executes none of
them. A non-zero command exit means the requested admission did not succeed.

## What this skill must refuse

- No admission without an explicit rights basis; public visibility is not one.
- No admitted byte whose digest differs from the one its policy declares.
- No embargoed source, and no restricted source's bytes in any output.
- No normalised record presented as, or substituted for, its native source.
- No strengthened evidence state: proposed, applied, released, deployed,
  reverted and verified stay independent, and unknown stays distinct from none.
- No causal or guarded verdict inferred from similarity for Elenchus, and no
  custody or action authority transferred to Synkrisis.
- No claim that a corpus figure describes anything beyond the records it
  counted.

If an admission, curation or release did not run, say so plainly and do not
describe its result as successful.
