<!-- Source: .hexaemeron/runbook.md; SHA-256: 559dacda83f40dac092180945ede035244dac6a2642beb1fc88439c829ee288d. Relative discipline links were adjusted for this durable location. -->

# Runbook: Homologia checked inputs

Derived from `.hexaemeron/study.md`. One step delivers the accepted Homologia Step 2 boundary without opening the mirror-execution or comparison boundaries. The held frontier advances from manifest validation to mirror execution only after the command, schemas, examples, records and public contracts pass together.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 08d19d3b379b0fde0939315afcd34063ff775ac24c650f216abdb1a52633caa5
candidate | strict-stdlib-validator
```

## Step 1: admit cap-bounded Homologia inputs

**Goal.** Implement `homologia.py check` as the selected one-pass standard-library validator. Admit one closed manifest and its declared vector sets, bind every source digest and identity into one canonical checked-inputs record, and leave mirror execution and any verdict refusing.

**Entry.** The worktree starts at `0987aa37f5110501b2c7a440f42370f81d58afe5`; issue [#458](https://github.com/wildcat-finance/skills/issues/458) is open with its owner approval; Homologia Step 1's scaffold suite passes; `.hexaemeron/study.md` and the design lock above are receipted; `plugins/homologia/skills/homologia/EVOLUTION.md` still names this exact held job at `homologia-v0.1.0`.

**Exit.** `python3 -m unittest plugins.homologia.tests.test_check -v` passes at least 20 focused cases. `check` validates closed pair identity, unique vector-set ids and paths, exact scale equality, closed per-answer provenance, declared tolerance use, safe path form and all four caps before any output is installed. A `proved` answer without its repository-relative Lazarus artefact reference refuses; missing or unequal scale refuses; per-file, aggregate, set-count and vector-count breaches refuse without creating or changing the target. The committed example is checked twice and `cmp` proves byte equality. `run-mirror`, `compare`, `render` and `verify` still refuse. The focused plugin suite, Promise Machine checks, selected checked runner, Phylax, Ephoros, Hypomnema, Imprimatur, Brevitas where applicable, Horos and `git diff --check` exit zero. Homologia's mutable first-party marketplace prose is cold-read and reconciled. Its canonical skill and ledger advance together to `homologia-v1.1.0`, with mirror execution as the next held job and a new checked-input Promise Machine coverage row.

```bash
python3 -m unittest plugins.homologia.tests.test_check -v
python3 plugins/homologia/scripts/homologia.py check --manifest plugins/homologia/examples/wad-interest-v0/manifest.json --out build/homologia/checked-inputs.json
python3 plugins/homologia/scripts/homologia.py check --manifest plugins/homologia/examples/wad-interest-v0/manifest.json --out build/homologia/checked-inputs-second.json
cmp build/homologia/checked-inputs.json build/homologia/checked-inputs-second.json
python3 scripts/run_checks.py
```

**Files.** Change `plugins/homologia/scripts/homologia.py`; add `plugins/homologia/references/manifest-v1.schema.json`, `plugins/homologia/references/vectors-v1.schema.json`, `plugins/homologia/tests/test_check.py`, bounded fixtures under `plugins/homologia/tests/fixtures/check/`, the committed `plugins/homologia/examples/wad-interest-v0/` inputs and checked record, `plugins/homologia/docs/schema-compatibility.md`, `plugins/homologia/docs/decisions/ADR-002-chain-answers-are-evidence.md`, and source-bound study/runbook copies under `plugins/homologia/docs/checked-inputs/`. Reconcile `plugins/homologia/README.md`, `plugins/homologia/AGENTS.md`, `plugins/homologia/skills/homologia/SKILL.md`, `plugins/homologia/skills/homologia/EVOLUTION.md`, host manifests, marketplace descriptions, Promise Machine coverage and generated portable copies. Add this run's audit record under `audit/rounds/`. Regenerate `.horos/boundary.json` only if the finished tracked tree changes the classified boundary. Update `tests/check-map-v1.json` only if the checked runner identifies an unowned path.

**Tests.** Start with red focused guards for: proved without artefact; missing scale; unequal scale id; unequal scale decimals; unknown provenance; missing recorded chain or block identity; missing asserted author; duplicate vector-set id; duplicate vector path; absolute path; parent path; symlink path; malformed manifest and JSONL; duplicate JSON key; non-canonical integer; undeclared or unequal tolerance; file, aggregate, set-count and vector-count caps; duplicate vector id; and refusal preserving an existing output. Positive cases cover proved, recorded, asserted, declared tolerance, mixed sets, canonical output, source digests and the committed example's repeated digest. Minimum: 20 focused cases plus the existing scaffold and repository-selected suites.

**Disciplines.** [Phylax](../../../hexaemeron/skills/phylax/SKILL.md) reviews the manifest, vector, filesystem and output boundaries against risk ids in the study. [Ephoros](../../../hexaemeron/skills/ephoros/SKILL.md) checks stable refusal codes, bounded subjects and the success summary. [Metron](../../../hexaemeron/skills/metron/SKILL.md) records no performance claim because Step 5 owns measurement. [Elenchus](../../../hexaemeron/skills/elenchus/SKILL.md) requires each discovered failure to be red before its cause is repaired and its guard retained. [Hypomnema](../../../hexaemeron/skills/hypomnema/SKILL.md) checks ADR-002 and keeps operational details in the compatibility document rather than inventing more decisions.
