# Runbook: Synkrisis, bounded diagnosis across agent runs

Derived from [the committed study](study.md) and the runbook attached to
[issue #449](https://github.com/wildcat-finance/skills/issues/449). Five
steps, dependency order, each landing only with its exit gates green. Steps 1
and 2 are delivered; Steps 3 through 5 are held, and the evolution ledger's
Next Fiat job names the next one.

## Step 1: Scaffold Synkrisis and commit its specification (delivered)

**Goal.** The standalone plugin with its contracts, packaging, study,
runbook, first decision record and a refusing command stub.
**Exit, held at delivery.** Both host manifests and the marketplace entries
agree at `0.1.0`; the Promise Machine router reaches
`plugins/synkrisis/AGENTS.md`; the canonical `skills/synkrisis/SKILL.md`,
`EVOLUTION.md`, byte-identical `LICENSE` and generated `PROMISE_MACHINE.md`
copy are present; ADR-001 records the standalone boundary; this study and
runbook are committed; `synkrisis.py --help` prints the four specified
operations and every operation refuses with `SK000`, naming the runbook step
that implements it and writing nothing; the scaffold suite under
`plugins/synkrisis/tests/`, the root suite, `scripts/promise_machine.py
check` and `coverage --check` exit 0, with the plugin discovered from disk
and the scaffold's single refusal promise bound to evidence.

## Step 2: Validate observations and construct one declared cohort (delivered)

**Goal.** One deterministic cohort from a complete declared manifest and one
comparison policy, without interpreting events.
**Exit, held at delivery.** `synkrisis.py cohort` checks producer identity, declared
validation, redaction and binding results, recomputed digests and bound
prefixes, run and event identity, path form, caps and equality dimensions;
classifies every declared run as included, excluded or unknown with the
responsible policy field; writes atomically only after the whole universe is
classified; the example manifest produces one cohort digest twice; positive
fixtures cover a refused transition retained in the cohort, a valid
unavailable observer recorded as unknown, and recorded token accounting;
hostile fixtures cover replaced and truncated records, prefix digest and
count mismatches, duplicate keys and run ids, unsafe paths, cap breaches,
unlike token accounting, empty eligibility and partial-output discipline.
The cohort and policy schemas land under `references/` with the
schema-compatibility record, and the comparability decision record lands
beside ADR-001.

## Step 3: Add the bounded diagnostic rule catalogue (held)

**Goal.** Evidence-linked candidate findings recomputed from one checked
cohort, with no cause, quality judgement or action.
**Exit.** `synkrisis.py diagnose` validates the digest-bound
`references/rules-v1.json`, applies only rules whose required dimensions and
minimum sample counts hold, records every refused rule with its reason, and
emits deterministic findings carrying cohort and rule digests, exact event
references, counterevidence, unknown runs, the nearest forbidden claim and
one handoff naming `ephoros`, `metron`, `elenchus`, `protasis`, `phylax`,
`horos` or `human-review`. The example produces
`late-boundary-consultation/v1` and `unchanged-retry-before-handoff/v1`, and
fingerprints survive harmless manifest reordering. Negative fixtures cover
unknown kinds and fields, evidence strengthening, causal and model-quality
language, template escapes, handoffs outside the named owner set, improper
fractions, duplicate rule ids, tampered cohorts and drifted records. The
checked-rule and issue-437 decision records land, and all Step 2 gates stay
green.

## Step 4: Render and verify the exact report (held)

**Goal.** A readable report whose every claim reconstructs from the
findings, then whole-path verification.
**Exit.** `synkrisis.py render` uses fixed templates and refuses findings
carrying causal language, a strengthened evidence class or unknown fields;
`synkrisis.py verify` independently recomputes the cohort, findings and
report bytes from the original manifest, policy, records and catalogue, and
refuses replacement, truncation, reordering, wrong-run association, a stale
rule digest, an unsupported producer identity and an edited narrative, each
with a stable code and recovery. The committed example report is
byte-recomputed in the suite, and all earlier gates stay green.

## Step 5: Measure, publish and demonstrate the refusal boundary (held)

**Goal.** The completed plugin held to its work budget, its three specified
promises bound to evidence, and the demonstration path proved from clean
inputs.
**Exit.** The benchmark materialises the 100-run, 100,000-event universe
from the committed fixture specification and holds cohort, diagnose and
verify to 5.0 seconds and 256 MiB on the recorded runner, printing
interpreter, platform, specification digest, repetitions and observed
maxima; the canonical `SKILL.md` replaces the scaffold promise with
`synkrisis-cohort-construction`, `synkrisis-bounded-diagnosis` and
`synkrisis-report-verification`, each bound in
`tests/promise_machine_coverage.json` to positive, missing-evidence, stale,
overclaim and recovery selectors; the complete demonstration path exits 0
twice with byte-identical outputs and the two negative demonstrations exit
non-zero; the root suite, the plugin suite, Promise Machine check and
coverage, the prose and tree lints and a fresh Horos boundary all exit 0.
