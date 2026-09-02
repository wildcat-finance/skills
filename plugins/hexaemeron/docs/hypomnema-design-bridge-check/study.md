# Study: Ship the Hypomnema design-bridge check

Assuming, unless corrected:

1. This run starts from main at 51fb586e41f67bff1cd53bed8414e3fc63ff48cb.
2. The checked study is supplied explicitly. Historical studies are not made retroactively invalid by an ordinary docs and plugins walk.
3. The selected design identity comes from one checked protasis-design-evidence/v1 record; free-form prose is not asked to identify the winner.
4. A bridge names one repository-relative standing record: an ADR below a decisions directory or an EVOLUTION.md beside the governed skill's SKILL.md.
5. Python remains the interpreter pinned by .python-version, the implementation stays in the existing stdlib checker, and no Solidity, dependency, CI, public ABI, or storage-layout change is in scope.

I will proceed on those assumptions unless corrected.

## 1. Problem statement

Hypomnema already requires a shipped study's chosen design and rejected alternatives to reach one standing record, but the pre-receipt review is still manual. Issue 461 and the held hypomnema-v4.6.0 frontier require a deterministic check for the missing bridge, a target that does not exist, and the same decision declared in both an ADR and a governed-skill ledger, while accepting either one valid ADR home or one valid skill-ledger home.

The working prototype adds an explicit study-check mode to the existing Hypomnema command. It reads the exact study, its checked Protasis design-evidence record, and the one declared standing record. It requires one closed design-bridge block whose decision equals the selected Protasis candidate and whose record is one existing established home. A missing block, malformed block, second home, selection mismatch, unsafe path, wrong home, or absent target refuses visibly. The default path walk and H000 through H007 keep their present behaviour.

Done is proved by fixtures for absent, dangling, duplicate, valid ADR, and valid governed-ledger cases; all existing checker cases staying green; the Hexaemeron suite passing; the root suite passing; the Promise Machine copies staying current; and the Hypomnema frontier advancing exactly once under the versioning contract.

## 2. Prior art

The current checker at plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py already owns bounded file reads, repository-relative Markdown targets, ADR discovery, record shape, stable H000 to H007 findings, JSON output, fixture exclusions, and one shared tree walk. plugins/hexaemeron/tests/test_hypomnema_checker.py shows the established recovery pattern: a bad specimen names one code, restoring its target clears it, and each earlier interface retains a direct guard.

The last two merged pull requests touching the in-scope Hypomnema surface were read before choosing a design:

- [skills#1013](https://github.com/wildcat-finance/skills/pull/1013) changed the walk so preserved specimens are not treated as repository records. Its body carries Anamnesis steps 2 and 3, not Hypomnema work. The relevant authoritative source is audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md, read directly after the whole-set synopsis check passed. In Step 1, S1-R1-01, S1-R1-02, S1-R1-03, S1-R2-01, S1-R2-02, and S1-R3-01 are all fixed. The Elenchus verdicts are guarded, guarded, passed, and null across rounds 1 to 4. S1-R3-01 is the in-scope warning: the portable runtime still held a stale hypomnema.py until the mirror and manifest were resynchronised. Covered fields concern Anamnesis admission; the non-Solidity suite, hosted publication, and later Anamnesis mechanisms were Not checked. The recorded tmp runner flake and Lazarus macOS path lead are outside this parser and remain neither reopened nor silently claimed fixed.
- [skills#1003](https://github.com/wildcat-finance/skills/pull/1003) changed Hypomnema's public prose but no checker behaviour. Its body reports the full check set green and carries no unfinished Hypomnema item.

The held work comes from [skills#314](https://github.com/wildcat-finance/skills/pull/314), with its scaffold in [skills#312](https://github.com/wildcat-finance/skills/pull/312). That run chose point-or-write, left the bridge mechanical check for a later frontier after the record parser existed, and carried environment-bound tests and host cache refresh outside the product change. The present run consumes the mechanical-check item; it does not reopen the completed ADR backfill or claim to refresh another host. [skills#684](https://github.com/wildcat-finance/skills/pull/684) is the latest Hypomnema-specific parser delivery: it preserved H000 to H007 and added no new broad-walk finding.

The authoritative root source audit/AUDIT.md was read directly for “Hypomnema design bridge”, “Hypomnema ADR shape check”, “Hypomnema source-comment references”, and “Hypomnema runbook shape check”. The design-bridge rounds recorded no findings and no leads; double-record, scope-creep, and ledger-arithmetic were reviewed. The ADR-shape rounds recorded the heading-pragma defect fixed in-step and no open finding. The source-comment rounds recorded no findings or leads. The runbook-shape rounds recorded no open finding, the generated-directory is_file guard fixed in-step, and the still-manual design bridge as the evidenced successor. There is no missing legacy field in those selected records.

The verified synopsis view was eligible because this exact command exited zero from the target root before any audit record was used:

    python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .

No other discovered audit source bears on the design-bridge parser. The current issue body, Hypomnema SKILL and EVOLUTION ledger, the shared VERSIONING contract, the current checker and its tests are the remaining authoritative inputs.

## 3. Constraints and non-goals

- The starting ref is main at 51fb586e41f67bff1cd53bed8414e3fc63ff48cb.
- H000 to H007 are stable. The bridge check takes H008 rather than changing an earlier code.
- The new mode is explicit, for one caller-named study and one caller-named design record. The ordinary docs and plugins walk remains unchanged, so old shipped studies do not become a migration queue.
- The closed block has exactly three rows: schema, decision, and record. The schema is hypomnema-design-bridge/v1; decision is the selected candidate id; record is one repository-relative path.
- A record path is lexically below the supplied repository root, has no empty, dot, dot-dot, backslash, or control segment, and reaches an ordinary non-symlink file. ADR homes are ADR-numbered Markdown below a decisions directory. Skill-ledger homes are EVOLUTION.md beside a SKILL.md whose governed name matches its directory.
- The checker proves the declared selected design points to exactly one valid home. It does not semantically prove that every sentence of the alternatives was copied correctly; ADR shape and the versioning contract remain the separate record-content gates.
- The completed frontier job increments only evolution: hypomnema-v4.6.0 becomes hypomnema-v5.6.0, with one new row, matching SKILL frontmatter, a recomputed frontier digest, and either one evidenced successor or a mature close.
- The frontier completion cold-reads and reconciles all mutable first-party marketplace prose. Historical studies, runbooks, audit records, fixtures, specimens, and vendored skills remain records, not rewrite targets.
- Non-goals: infer a decision from arbitrary prose, scan for semantic duplicates outside the closed declaration, change Protasis's schema, change Fiat controller state, add a dependency, or widen the existing broad walk.
- Always: run the focused Hypomnema guards, the Hexaemeron suite, the root suite, Promise Machine and portable-copy checks, the selected repository checks, and the prose/tree lints before the frontier row is accepted.
- Ask first: a dependency, CI change, public interface outside the checker CLI, new trust boundary, or a change to an existing H000 to H007 meaning.
- Never: edit vendored security skills, weaken a pre-existing finding, follow a record-path symlink, rewrite historical audit bytes, delete a failing guard, or claim an unrun command passed.

## 4. Design options

1. **closed-bridge-block.** Chosen. Add one exact fenced design-bridge block and check its decision against the selected candidate in the Protasis record. The record row names one established target, so zero rows catches absence, two rows or blocks catch duplicate homes, and target classification catches wrong or dangling homes. An explicit --study mode keeps the old tree walk compatible. The trade is three structured fields and one additional bounded input read compared with inference.
2. **section-link-inference.** Rejected. Infer a bridge from ADR- or EVOLUTION-looking links in item 12. It saves the three declaration fields and one design-evidence read, but free-form item 12 also cites ownership contracts and can name several governed decisions. A link has no selected-candidate identity, so the parser cannot prove which record belongs to the candidate Protasis selected. That fails the correctness gate even though absence, dangling targets, and duplicate record-looking links can each produce a diagnostic.

The checked matrix covers correctness, compatibility, recovery, time, and space. section-link-inference uses two bounded reads and zero new fields; closed-bridge-block uses three reads and three fields. Both preserve the legacy walk and can name recovery. Only closed-bridge-block binds the exact selected id, so the unique-frontier rule selects it.

## 5. Risk register seed

```risk-register
selection-binding | the join from the study block to the Protasis record | the decision id equals the checked selection candidate and a free-form mention cannot satisfy it
block-shape | the fenced design-bridge declaration | zero, repeated, reordered, duplicated, unknown, or empty rows refuse as H008
path-confinement | the caller-supplied root and record row | absolute, escaping, control-bearing, symlinked, special, missing, and unstable targets refuse without a follow
home-classification | the standing-record target | only an ADR below decisions or a governed EVOLUTION.md beside its matching SKILL.md passes
duplicate-home | one chosen design against the record rows and blocks | an ADR and ledger declaration for the same decision produce one duplicate-home refusal
legacy-scope | the explicit study mode beside the default walk | H000 to H007 and historical docs keep their existing results
mirror-drift | the canonical checker beside the portable Promise Machine copy | the portable sync and manifest checks bind identical bytes before delivery
ledger-arithmetic | the frontier row and sibling SKILL metadata | version tests prove one evolution increment, matching metadata, digest, and successor or mature close
prose-reconciliation | mutable first-party descriptions of Hypomnema | a cold-read inventory changes only surfaces made stale by H008
```

The audit loop should look hardest at selection-binding, path-confinement, and duplicate-home. A parser that accepts a plausible link without proving the candidate, follows a changed path, or treats two homes as two harmless links would reproduce the manual gap under a new code.

## 6. Glossary seeds

- Design bridge: the closed declaration joining one selected Protasis candidate to one standing record.
- Standing record: one valid ADR or one governed-skill EVOLUTION.md, never both for the same declared decision.
- Selected candidate: selection.candidate in the checked protasis-design-evidence/v1 record.
- H008: a missing, malformed, mismatched, unsafe, duplicate, wrong-home, or dangling design bridge.
- Legacy walk: the existing path-oriented Hypomnema scan whose H000 to H007 behaviour stays unchanged.

## 7. Sources

- Issue 461 and plugins/hexaemeron/skills/hypomnema/EVOLUTION.md at hypomnema-v4.6.0.
- plugins/hexaemeron/skills/hypomnema/SKILL.md and scripts/hypomnema.py.
- plugins/hexaemeron/tests/test_hypomnema_checker.py and its Hypomnema fixtures.
- plugins/hexaemeron/skills/VERSIONING.md.
- The active Protasis 5.10.0 and Fiat 5.47.1 contracts.
- skills#1013, skills#1003, skills#314, skills#312, and skills#684.
- audit/AUDIT.md and audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md, under the successful whole-set synopsis currency result.
- .hexaemeron/design-evidence.json and its ten digest-bound selection reports.

## 8. Signals, and the questions behind them

The check is a terminal command, not an unattended service, so no metric, trace, or alert is added. The operator still needs three answers from its existing surface: “why did this study refuse?” is answered by H008, path, line, and message; “which declaration was checked?” is answered by the study path and structured finding output; “did a portable install receive the same checker?” is answered by the portable-copy check. The implementation and verification steps emit those exit codes and exact diagnostics. Ephoros owns signal content; this change reuses the current CLI result rather than inventing telemetry.

## 9. Boundaries, per capability

The new capability reads three untrusted local inputs: the caller-named study, the caller-named strict JSON design record, and the record path declared inside the study. Each read is bounded, stable, ordinary-file-only, below the supplied repository root, and does not follow a symlink. JSON rejects duplicate keys, non-finite values, excessive depth, and an unsupported schema before selection is read. Markdown accepts only one closed block outside quoted examples. The checker starts no subprocess, opens no socket, reads no secret, and writes nothing. Phylax owns these input and filesystem controls; its lint runs in every audit round.

## 10. The budget, or its absence

There is no performance budget because the command checks one study, one small design record, and one record file and makes no speed claim. The selection record counts bounded input reads only to compare constructions; it is not a latency promise. Metron owns any future measurement if a real repository demonstrates a runtime problem.

## 11. The fail-closed posture

Unreadable or oversized input, malformed or duplicate JSON, an unsupported design schema, no selected candidate, an absent or repeated bridge, a candidate mismatch, unsafe path, wrong home, absent target, symlink, special file, or unstable reread stops with exit 1 and H008. Bad invocation remains exit 2. Each acceptance and refusal gets a committed fixture; a reported defect is reproduced on the parent, fixed at its cause, and guarded under Elenchus before a round closes. Restoring the missing target or correcting the one declaration is the recovery; a pragma does not manufacture a bridge.

## 12. Decisions and their homes

The closed block, H008 interface, opt-in mode, and one-home classification are decisions about the governed Hypomnema skill. Their standing record is the hypomnema-v5.6.0 evolution row this frontier run will cut, not a second ADR. This study preserves the rejected link-inference alternative and the selection reports preserve the checked trade.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | closed-bridge-block
record | plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
```
