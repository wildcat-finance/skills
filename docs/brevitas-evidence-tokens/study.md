# Study: Protect bare evidence tokens in Brevitas

## Assuming, unless corrected

1. Issue `wildcat-finance/skills#372` authorises one Brevitas generation change from `main` at `646dbff7c12202e8b9417ac51546d72b27dde5e3`; it does not authorise work on the held frontier.
2. A bare SHA-256 digest is exactly 64 hexadecimal characters with hexadecimal-token boundaries. A 4-byte selector is exactly `0x` followed by 8 hexadecimal characters with hexadecimal-token boundaries.
3. A full Git object id is a boundary-delimited 40-hex token. An abbreviated Git object id is 7 to 39 hex characters only when Markdown code quoting, an explicit Git label, or an `owner/repository@oid` form supplies Git context. Unlabelled hex-like words are not Git evidence.
4. Literal survival is the promise. The checker need not establish that a digest, selector, or Git object exists or is semantically relevant.
5. The exact interpreter in `.python-version`, the standard library, the existing Brevitas test runner, and the repository's generated-file tools remain the toolchain. No dependency or CI change is needed.
6. The current `held-engineering-corpus` frontier revision, digest, status, and Next Fiat job remain byte-for-byte unchanged. This generation increments only after the integration base is known.

## 1. Problem statement

Brevitas's `--source` comparison currently protects `0x`-prefixed 64-hex transaction hashes, `0x`-prefixed 40-hex addresses, `file:line` references, and numeric tokens. It does not protect a bare SHA-256 digest, a Git object id, or a 4-byte selector. A compressed engineering record can therefore delete identifiers used by Alexandria, Ariadne, Tabularium, Lazarus, Hermes, and this repository's evolution ledgers while `B030` remains silent.

The working prototype extends `protected_tokens()` so those three families become literal evidence tokens without weakening the existing families or treating arbitrary hex-like prose as a Git object id. It ships focused positive, negative, boundary, overlap, casing, duplicate, and regression tests; updates the Brevitas evidence-preservation contract and usage prose; appends one generation row whose version is resolved against the integration base; preserves the held frontier; regenerates governed copies; and passes the affected repository checks.

The direct demonstration uses a source containing a bare 64-hex digest, a contextual abbreviated Git SHA, a full 40-hex Git object id, and `0xa9059cbb`, then removes each from the draft. The checker must emit `B030` for each missing literal; restoring every literal must return exit 0. The repository demonstration is:

```text
python3 plugins/brevitas/tests/run_tests.py .elenchus/brevitas-372.json
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
make -C plugins/brevitas/skills/brevitas test
python3 scripts/run_checks.py
```

## 2. Prior art and current evidence

The entry implementation is `plugins/brevitas/skills/brevitas/scripts/brevitas.py`. `protected_tokens()` uses separate regular expressions and set subtraction to keep an address from duplicating an already recognised transaction hash. `B030` reports the category and literal found in the source but absent from the draft. `plugins/brevitas/tests/test_brevitas.py` already proves survival, deletion, restoration, subject mismatch, and the boundary that token survival does not establish semantic equivalence.

The exact entry baseline ran 70 Brevitas tests successfully. A direct source/draft comparison then removed a bare 64-hex digest, `646dbff7c122`, and `0xa9059cbb`; the current checker exited 0. That is observed negative evidence for the three missing classes, not a claim about other token shapes.

The last two merged pull requests that changed `brevitas.py` were read:

- [PR #113](https://github.com/wildcat-finance/skills/pull/113), commit `da4f5c47ab21151aa5842ad1714eb382a833d47c`, removed the per-point fence rule and widened the code-fence cap. It advanced only the Brevitas generation and retained the frontier revision and digest. This run keeps that generation/frontier separation.
- [PR #91](https://github.com/wildcat-finance/skills/pull/91), commit `7da7dc95a88c413d87080d70afc8dd624204432a`, introduced the linter, `B030`, the protected token set, tests, evaluations, and marketplace surfaces. This run extends that existing category-specific construction instead of replacing the parser.

Issue [#374](https://github.com/wildcat-finance/skills/issues/374) is partially present on `main`: its held-corpus scaffold and ten-case corpus are committed, while its runbook still assigns current-diagnostic comparison and rule repair to Step 3 and frontier reconciliation to later steps. `docs/brevitas-held-corpus/runbook.md` and `plugins/brevitas/skills/brevitas/EVOLUTION.md` therefore remain prior art and a hard scope boundary. #372 may make the missing evidence rule available to that work; it must not claim #374's corpus result or advance its frontier.

Audit synopsis currency was checked from the entry tree with `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`; it exited 0 for the whole discovered set. The following verified views were read:

- `audit/AUDIT_SYNOPSIS.md`, mapped from `audit/AUDIT.md`, including the three legacy Repository-wide Brevitas rounds. Those records contain missing legacy fields and no finding that settles these token grammars; the missing fields remain unknown.
- `audit/rounds/fiat-374-forward-test-brevitas-across-a-held-engineer.synopsis.md`, mapped from its same-named `.md` source. It preserves #374's open boundary: current-diagnostic comparisons and any Brevitas rule repair remain assigned to its later step. Its reviewed `evidence-token-gap` lanes do not establish #372's implementation.

The #374 finding inventory was retained rather than silently narrowed. `S1-R1-01` and `S1-R1-02` are fixed and remain closed. `S2-R1-01`, `S2-R1-02`, and `S2-R1-03` were recorded open in their round and then repaired or truthfully reframed by `S2-R2-01`, `S2-R2-02`, and `S2-R2-03`; `S2-R1-04` was fixed in its own round. `S2-R2-01` through `S2-R7-02`, including every intermediate `S2-R3-*`, `S2-R4-*`, `S2-R5-*`, and `S2-R6-*` id, are fixed and regression-tested; the final Step 2 round keeps them closed and records no new finding. Step 1's Elenchus verdicts are `passed` then `null`; Step 2's finding-bearing rounds are `guarded` and its clean closing round is `null`. Their `Covered` lanes, `Not checked` fields, and leads keep live-provider identity, off-record human review, current-diagnostic comparison, marketplace reconciliation, frontier arithmetic, publication, and controller mutation outside the evidence. #372 reopens none of those findings. The one interaction it must respect is that adding a `B030` evidence category can change #374's later diagnostic comparison; that comparison remains #374 Step 3 work, not a corpus mutation here.

No `plugins/brevitas/audit/AUDIT.md` exists. The root legacy source and the #374 per-run source are the in-scope audit sources discovered for this skill change; verified synopses were used because the whole-set currency check succeeded. Their findings, `Covered`, `Not checked`, Elenchus verdicts, leads, negative evidence, and legacy unknowns remain authoritative within their recorded scopes.

## 3. Constraints and non-goals

- Start from the immutable entry commit above and integrate through the Fiat run branch into `main`. Do not rebase or rewrite signed product commits.
- Use the existing standard-library linter and test runner. Do not add dependencies, CI, network access, a semantic parser, or a repository lookup.
- Preserve the current transaction-hash, address, `file:line`, and numeric-token behaviour and diagnostic code `B030`.
- Do not alter held-corpus fixtures, classifications, capture provenance, current expectation mismatches, frontier revision, frontier digest, frontier status, or Next Fiat job.
- Do not claim a token is a valid digest, live Git object, callable selector, or semantically preserved statement. Only exact lexical survival is checked.

Always: run both the focused Brevitas runner and affected repository checks before a commit; run Imprimatur on shipped prose; preserve every existing protected token and the direct negative specimen. Ask first: add a dependency, change CI, widen the Git grammar beyond the stated contexts, change `B030`, edit held-corpus bytes, or change a public promise beyond lexical survival. Never: commit credentials, edit generated runtime copies by hand, delete a failing test, weaken evidence precedence, claim frontier completion, or change the held digest to make a check pass.

## 4. Design options

### Option A: one broad hexadecimal regular expression

Recognise every boundary-delimited 7-to-64-character hexadecimal token, then infer a category from length. This is small, but ordinary hex-like words and opaque values become protected Git SHAs, category overlap becomes implicit, and a later rule change can silently recategorise existing evidence. Rejected because false positives would make ordinary compression refuse without evidence that the token is Git-related.

### Option B: ordered category-specific recognisers with bounded Git context

Add separate recognisers for exact bare 64-hex digests, exact `0x` 8-hex selectors, full 40-hex Git object ids, and 7-to-39-hex abbreviated Git ids only in a closed context grammar. Extract literal Git ids from Markdown code spans, explicit labels (`git`, `commit`, `sha`, `sha-1`, `oid`, `ref`, `head`, `base`, `parent`, or `tree`), and `owner/repository@oid`. Keep category precedence explicit and exclude already claimed literals from broader categories. Chosen because it extends the existing construction, makes false-positive policy testable, and is cheapest to comprehend while covering the issue's evidence shapes.

The trade is deliberate: an unquoted, unlabelled abbreviated object id is not mechanically distinguishable from a hex-like word and stays outside the promise. A full 40-hex object id is protected without context because its collision with ordinary prose is low and losing it is costlier than preserving an opaque 40-hex identifier.

### Option C: validate tokens through Git or domain registries

Ask `git cat-file` about candidate object ids and interpret selectors or digests by repository context. This could reduce lexical ambiguity, but makes results checkout-dependent, adds subprocess and repository-state boundaries, rejects legitimate evidence from another repository, and turns an offline text linter into a semantic resolver. Rejected because it strengthens the claim in the wrong direction and violates the no-network/no-subprocess boundary.

## 5. Risk register seed

```risk-register
token-truncation | hexadecimal text adjacent to a longer hexadecimal token | exact boundaries refuse prefixes and suffixes of longer values
category-shadowing | overlap among transaction hashes addresses selectors digests and Git ids | longest and most specific categories claim a literal before broader categories
git-false-positive | ordinary hex-like prose that resembles an abbreviated object id | abbreviated ids require one closed Git context and negative specimens cover near misses
git-false-negative | an unlabelled abbreviated object id with no lexical context | the limitation is explicit and no broader preservation claim is made
case-drift | upper and lower case evidence literals | recognition accepts both and literal set comparison remains case-sensitive
duplicate-loss | one literal appearing several times in the source | the existing set promise remains literal presence not multiplicity and tests state that boundary
frontier-collision | generation work landing beside unfinished held-corpus work | version relation resolves at integration while held revision digest status and next job stay exact
generated-copy-drift | canonical Brevitas prose copied into portable runtime and manifests | repository generators run before Horos and the checked runner verifies byte parity
```

The audit loop should also confirm that the direct entry reproduction goes red only after guard tests are overlaid on the unfixed parent, that every newly protected literal survives unchanged, and that unrelated numeric or hexadecimal prose remains governed by its existing category or stays unprotected as designed.

## 6. Glossary seeds

- **Bare digest:** exactly 64 hexadecimal characters without an `0x` prefix, protected lexically as a SHA-256-shaped token.
- **4-byte selector:** `0x` plus exactly eight hexadecimal characters, protected lexically without asserting ABI meaning.
- **Full Git object id:** a boundary-delimited 40-hex token.
- **Abbreviated Git object id:** 7 to 39 hexadecimal characters admitted only by the closed Git context grammar.
- **Git context:** Markdown code quoting, a closed explicit label, or `owner/repository@oid`.
- **Category precedence:** the fixed order that prevents a more general recogniser from swallowing a more specific evidence class.
- **Literal survival:** the source token occurs unchanged in the draft at least once; multiplicity and semantic equivalence are outside the promise.

## 7. Sources

- Issue #372 body and current review: `https://github.com/wildcat-finance/skills/issues/372`, read 2026-08-30.
- Entry source: `plugins/brevitas/skills/brevitas/scripts/brevitas.py` at `646dbff7c12202e8b9417ac51546d72b27dde5e3`.
- Entry tests and reporter: `plugins/brevitas/tests/test_brevitas.py` and `plugins/brevitas/tests/run_tests.py`.
- Canonical contract and ledger: `plugins/brevitas/skills/brevitas/SKILL.md` and `plugins/brevitas/skills/brevitas/EVOLUTION.md`.
- Held frontier material: `docs/brevitas-held-corpus/study.md`, `docs/brevitas-held-corpus/runbook.md`, and `plugins/brevitas/skills/brevitas/evals/`.
- Prior merged work: PR #113 and PR #91, with commit identities recorded in item 2.
- Audit views: `audit/AUDIT_SYNOPSIS.md` and `audit/rounds/fiat-374-forward-test-brevitas-across-a-held-engineer.synopsis.md`, verified against their authoritative sources by the whole-set synopsis check.
- Phase contracts: `plugins/hexaemeron/skills/phylax/SKILL.md`, `plugins/hexaemeron/skills/ephoros/SKILL.md`, `plugins/hexaemeron/skills/metron/SKILL.md`, `plugins/hexaemeron/skills/elenchus/SKILL.md`, and `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

## 8. Signals, and the questions behind them

The applicable contract is `plugins/hexaemeron/skills/ephoros/SKILL.md`.

1. Which literal and category failed survival? Existing `B030` output answers with the source path, line, category, and literal; the implementation extends that bounded diagnostic.
2. Did the complete focused suite execute, and how many tests, failures, errors, and skips occurred? `plugins/brevitas/tests/run_tests.py` writes the existing `unittest-json-v1` report.
3. Did generation, portable parity, boundary currency, or another affected repository gate fail? `scripts/run_checks.py` reports the selected check id and exit.

No retained runtime telemetry, metric, trace, alert, or correlation id is needed. The checker is an interactive finite command, not an unattended service; its bounded diagnostics and source-owned test report are execution evidence rather than operational telemetry.

## 9. Boundaries, per capability

The applicable contract is `plugins/hexaemeron/skills/phylax/SKILL.md`.

- Source and draft text cross into the existing linter. Worth taking: bounded UTF-8 text and literal evidence tokens. Controls: retain the existing regular-file/read behaviour, use compiled regular expressions with bounded token lengths, add no shell, subprocess, network, credential, or path derivation.
- Regex classification crosses from text into a preservation obligation. Worth taking: only the exact literal and closed category. Controls: explicit boundaries, closed Git contexts, category precedence, hostile near-miss tests, and no semantic validity claim.
- Version generation crosses from the product diff into mutable `main`. Worth taking: one next generation after the actual integration base. Controls: the runbook declares `next-generation-after-integration-base`, controller resolution checks the ledger row, and the held frontier fields remain exact.
- Canonical prose crosses into generated portable copies and host manifests. Worth taking: installable behaviour and version parity. Controls: repository generators, no manual generated edits, `scripts/run_checks.py`, and Horos currency after generation.

No new dependency, host, credential, external data source, personal-data field, model-output authority, or persistent write path is introduced.

## 10. The budget, or its absence

The applicable contract is `plugins/hexaemeron/skills/metron/SKILL.md`. There is no performance budget and no speed, memory, throughput, or cost claim. The recognisers are bounded lexical checks over text the linter already reads, but that observation is not a measured improvement. Runtime printed by tests is diagnostic only. Any optimisation proposal requires a separate recorded baseline and same-command remeasurement; this run neither makes nor keeps one.

## 11. The fail-closed posture

The applicable contract is `plugins/hexaemeron/skills/elenchus/SKILL.md`. Stop on a malformed boundary rule, a token prefix or suffix accepted as a complete token, a category overlap that hides a literal, a previously protected token lost, an unrelated hex-like word newly protected outside policy, a non-zero focused or repository check, generated-copy drift, invalid version arithmetic, or any held-frontier change.

The known failure is already reproduced: all three requested families can disappear with exit 0. Before accepting the fix, add focused tests and run the source-owned Elenchus runner against the unfixed parent. The exact audit runner contract is command `python3 plugins/brevitas/tests/run_tests.py {report}`, report format `unittest-json-v1`, report file `.elenchus/brevitas-372.json`. A valid guard report must show assertion failure without infrastructure error on the parent, then the same tests and both relevant suites must pass on the fixed tree. Do not change expectations, delete cases, broaden the grammar, or suppress a failure to manufacture green.

## 12. Decisions and their homes

The applicable contract is `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- The closed token grammar, category precedence, semantic boundary, rejected broad regex, and rejected Git subprocess design belong in the governed Brevitas ledger row because this is one skill's behaviour decision. No repository ADR is warranted.
- The executable grammar and literal extraction belong beside `protected_tokens()` in `brevitas.py`; positive and negative examples belong in focused Brevitas tests.
- The public evidence-preservation promise and operator instructions belong in Brevitas `SKILL.md` and the existing marketplace context only where current wording becomes incomplete.
- The exact generation is declared symbolically in the runbook and resolved by Fiat against the integration base; one history row records the result while the held frontier fields stay unchanged.
- The study and runbook are committed as delivery evidence under a topic-specific docs directory in the one implementation step. They point to the ledger as the standing decision record and do not become a second decision scheme.

No alert runbook, interface ADR, dependency record, or new agent instruction is required. Any audit finding and red-before evidence belongs in the run's per-run audit record, not in an existing append-only record rewritten after the fact.
