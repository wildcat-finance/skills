# Horos runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Horos.** Horos records evidence-backed reading exclusions and deterministic skeleton maps for ordinary repository work. It does not chunk source, measure runtime cost, or narrow any security review. **Current frontier:** The v9.2.3 reopening's third and last job is done: map reads Markdown through a per-language extractor, held against markdown-it-py over all 900 tracked Markdown files of this repository with 9,527 of 9,527 headings and 1,130 of 1,130 fenced code blocks matched, zero misses, zero extras and zero crashes. Every filetype above 1% of this tree's readable bytes is now mapped or is a data format with no declarations to outline, so the frontier closes mature.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Horos contains one Agent Skill. Read `skills/horos/SKILL.md` in full before
scanning, checking or mapping a repository.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/horos/` directory.
- Run `skills/horos/scripts/horos.py` from that fixed plugin path.
- Treat the repository named by the user as the target. Do not substitute this
  distribution checkout unless the user named it.
- `scan --write` writes `.horos/boundary.json` and optional census/candidate
  records inside the target. `check` and `map` are read-only.
- Names such as `$horos`, `/horos:horos` and `horos:horos` are invocation
  aliases, not shell commands.

## Network and side effects

Horos reaches no network, imports none of the source it inspects and executes no
target file. Writes are atomic and confined to the target's `.horos/`
directory. A non-zero command exit means the requested scan, check or map did
not succeed.

## What this skill must refuse

- No reading boundary during a security review, audit or incident.
- No hard exclusion without the evidence carried by the boundary entry.
- No claim that omitted paths are safe or cheap; classification is fail-open.
- No whole-repository claim from a scoped check.
- No generated, vendored or binary source executed in order to classify it.
- No stale boundary treated as current after `check` reports drift.

If a scan, check, map or test did not run, say so plainly and do not describe
its result as successful.
