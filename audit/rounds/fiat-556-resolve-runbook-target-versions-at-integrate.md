# Issue 556: resolve runbook target versions at integrate time

Rounds for the run on branch
`fiat/556-resolve-runbook-target-versions-at-integrate`, off `main` at
`8e6480230a5f43c57aef4f9a6c52f4c602d86790`. The run's audit record is this
file; `audit/AUDIT.md` is unchanged.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`. Two findings, both fixed on the
named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | The relation row and path checks rejected C0 controls and DEL but accepted C1 and Unicode format controls. An otherwise valid path containing U+0080 or U+202E returned no P006 finding, despite the closed contract refusing control characters. | fixed in this round: one printable-boundary check now covers the complete row and the path helper; both code points are regression cases in `test_unsafe_paths_refuse` |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | Five P006 messages interpolated a runbook-controlled target id, ledger path, or relation value. A row can occupy almost the 2 MiB document cap; a refusal then copies source content into output instead of naming only the failed field and check. | fixed in this round: P006 diagnostics are value-free, and `test_relation_findings_do_not_echo_runbook_controlled_values` covers the invalid-id, duplicate-path, unknown-relation, and concrete-token paths |

### Evidence

The Warden red report is
`.elenchus/fiat-556-step-1-warden-round1-red.json`, SHA-256
`4f5d633f93444d39e5f86c1036cfbbedf84ef4d9da8b5cb071c22915c7a4dd9f`.
It records `elenchus.unittest.v1`, 1,057 tests, six assertion failures, zero
errors, and zero skips while the worktree diff contained the guards and no
product fix. The fixed-tree report is
`tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
It records 1,057 tests, zero failures, zero errors, and zero skips.

Mason's earlier evidence remains intact. The first parser red is
`.elenchus/fiat-556-step-1-mason-red.json` with 1,055 tests and 22 assertion
failures. The link-placement red is
`.elenchus/fiat-556-step-1-link-conflict-red.json` with 1,056 tests and two
assertion failures. Both have zero errors and zero skips. Mason's signed commit
has parent `8e6480230a5f43c57aef4f9a6c52f4c602d86790`, a good local Shoggoth
signature, and exactly one co-author trailer and one origin trailer.

The fixed tree passes 89 focused Protasis tests, 350 root tests, all 71 Promise
Machine coverage rows, and the 1,057-test Hexaemeron report above. Phylax,
Ephoros, and Hypomnema exit 0 over the changed product paths. Both Promise
Machine commands are clean. Protasis accepts the receipted study and amended
runbook, and Horos reports that the boundary matches the tree.

The bounded Sapheneia record pass preserves every finding, qualification,
identifier, path, hash, count, verdict, and status. Imprimatur scores this file
100.0 with zero defects. Brevitas reports B011 only: the required findings
table has two data rows. It stays one row per actual finding; adding a third
would change the round's finding count.

The tracked study is byte-identical to the receipted study at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`.
Its five relative skill links resolve from `docs/fiat-version-relations-study.md`.
The tracked runbook is byte-identical to the amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. The changed product paths are
six paths, all authorised by the amended Step 1 Files field; no other product
file changed.

### Risk register

Four risk-register concerns are reachable in this step. `relation-block-shape`
surfaced S1-R1-01; every other malformed, duplicate, misplaced, oversized,
blank, decoy, and lexical path case is green. `literal-compatibility` is green
for a missing block, a partial target list, and every concrete-token position.
`diagnostic-leak` surfaced S1-R1-02. `promise-overclaim` is green: the Protasis
Promise names a lexical structure verdict and disclaims suitability, version
selection, and integration-base knowledge.

The other 19 concerns are not reachable in Step 1 and are not claimed as
reviewed here: `anchor-substitution`, `generation-arithmetic`, `frontier-drift`,
`ledger-history-rewrite`, `metadata-mismatch`, `multi-target-partial`,
`base-ref-race`, `run-ref-race`, `post-check-race`,
`remote-evidence-failure`, `git-object-shape`, `sync-carriage`,
`revalidation-coverage`, `resolution-staleness`, `state-history-growth`,
`self-hosted-collision`, `legacy-state`, `receipt-replay`, and
`interrupted-resolution` belong to later steps.

Leads not pursued: none.

## Step 1, round 2 -- 2026-08-25

Zero findings over signed audit-tip commit
`4278196365a8d288e1224be3e864cd505a4f7697`. Its parent is Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`; both local signatures verify.
Round 1 remains the unchanged 79-line prefix of this record.

### Evidence

Independent hostile probes refused all 33 C0 controls, 32 C1 controls, 12
bidi controls, 170 Unicode format controls, 19 other sampled nonprinting code
points, and 13 unsafe path forms. Five concrete-token positives refused; five
near tokens and the legacy no-block case stayed accepted. Six controlled-value
cases produced seven value-free P006 messages, at most 80 characters. A
maximum-size 2 MiB row produced one 75-character P006 message without echoing
its contents.

The fixed tree passes 89 focused Protasis tests, 350 root tests, and the full
1,057-test Hexaemeron report with zero failures, errors, or skips. The report
is `tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
The identical Round 1 green report remains preserved at
`.elenchus/fiat-556-step-1-warden-round1-green.json`; every earlier red report
also remains present.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
The Protasis Promise still limits P006 to lexical structure and disclaims
relation suitability, version selection, and integration-base knowledge.
Phylax, Ephoros, and Hypomnema exit 0 over their complete repository paths and
this record. Horos reports that the boundary matches the tree.

The tracked study remains byte-identical to its receipt at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
all five relative skill links resolve. The tracked runbook remains
byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. All six product paths remain
inside the amended Step 1 Files field, and `audit/AUDIT.md` remains unchanged.

The bounded Sapheneia pass preserves the full Round 1 prefix and every Round 2
hash, count, qualification, path, and status. Imprimatur scores this record
100.0 with zero defects. Brevitas reports B011 only, from the required two-row
Round 1 findings table; this zero-finding round adds no finding row.

### Risk register

The four Step 1 concerns are green. `relation-block-shape` covers malformed,
duplicate, decoy, nonprinting, and unsafe path inputs. `literal-compatibility`
covers near tokens, partial declarations, and no-block runbooks.
`diagnostic-leak` covers the maximum-size and controlled-value probes.
`promise-overclaim` remains bounded by the Promise text. The other 19 study
concerns belong to later steps and receive no claim in this round.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-25

Non-Solidity round over signed Mason commit
`c924b4766b6bc8011ba52b1caff0faace443aeae`, whose parent is the audited Step
1 tip `417c2a876df77ac2a3d04e6378d959bca6299fc1`. Three findings were fixed on
the named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Relation anchor reads honoured local Git replacement refs. Replacing the named commit, or replacing both selected blobs, let `done runbook` record `fiat-v9.9.9` while `anchor_commit` still named the native `fiat-v1.2.3` commit. Branch-point derivation also accepted grafted ancestry. | fixed in this round: relation ref, ancestry, tree, size, and blob reads bypass replacement refs; grafts refuse; branch refs are reread; commit, two-blob, and graft specimens guard the boundary |
| S2-R1-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The metadata regex searched all of `SKILL.md`. A body example containing `  version: "1.2.3"` stood in for absent frontmatter, and a file whose frontmatter named another skill still anchored as `fiat`. | fixed in this round: one bounded parser reads only the first closed YAML frontmatter, requires the exact target name, and takes one numeric version from the `metadata` mapping |
| S2-R1-03 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A 5,000-digit counter matched the label grammar, then escaped as Python's decimal-conversion exception instead of the controller's value-free malformed-label refusal. | fixed in this round: conversion-limit failure returns the existing malformed-label result; the 5,000-digit specimen guards it, while `7.99.13` projects to `7.100.13` without SemVer reset |

### Evidence

The Warden pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-1-red.json`, SHA-256
`a00dfe45c6c2eacfbfc8a09e0554c216c4aabf54c09f40c833ed6342f7db6762`.
It records `elenchus.unittest.v1`, 1,081 tests, four assertion failures, one
error, and zero skips while the diff from Mason's commit contained the five
new guards and no Warden product repair. The fixed-tree report is
`.elenchus/fiat-556-step-2-warden-round1-green.json`, SHA-256
`d27a91f360cb57639a240f6a865c07b792f6af52d9cc564e10744a0b63a0c1fb`.
It records 1,084 tests with zero failures, errors, or skips.

Mason's causal matrix remains at
`tmp/elenchus/fiat-556-step-2-red-matrix.json`, SHA-256
`38805d0e89fdceb632b7fa54860dec9a990770606a6bec08932f5e04f128adc9`:
1,073 tests, nine assertion failures, six errors, and zero skips. Its canonical
green report remains unchanged at `tmp/elenchus/fiat-556-step-2.json`, SHA-256
`3fe2ea15aea672bb4deaae16a85c18f80260a10c2ef697ee5fef8ffc08a2be72`:
1,076 tests with zero failures, errors, or skips.

The fixed tree passes 26 focused relation tests and all 350 root tests.
Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema exit 0 over the complete repository paths.
Horos reports that the boundary matches the tree. The tracked study remains
byte-identical to its receipt at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the tracked runbook remains byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five product paths remain inside Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The bounded Sapheneia pass preserves every finding, counterexample, path,
commit, hash, count, severity, qualification, and status in the required
round shape. It changes no existing audit byte. Imprimatur scores the complete
record 100.0 with zero defects. Brevitas accepts the new Step 2 append; the
complete append-only file retains only its inherited B011 at the two-row Step
1 findings table.

### Risk register

`anchor-substitution`, `metadata-mismatch`, and `generation-arithmetic`
surfaced S2-R1-01 through S2-R1-03. `multi-target-partial` is green for one,
two, partial, reordered, and one-bad-target capture. `git-object-shape` is
green for unsafe, missing, tree, symlink, submodule, non-UTF-8, oversized, and
native-object cases. `literal-compatibility`, `legacy-state`,
`receipt-replay`, `diagnostic-leak`, and `promise-overclaim` are green within
Step 2's anchor and packet boundary. Live base and run snapshots, frontier and
ledger drift, remote failures, sync carriage, revalidation coverage, stale or
capped resolution history, the terminal parent race, self-hosted collision,
and interrupted resolution belong to Steps 3 and 4 and receive no claim here.

Leads not pursued: none.

The first source-bound mechanical guard run against preliminary signed Warden
object `eeb9fe8f508fe1a316d3cdbcb52dc41b49267ec9` was inconclusive because the
5,000-digit counter specimen let the known parent `ValueError` register as a
unittest error. The guard now translates that exact old exception into an
assertion failure; no product repair changed in response.

## Step 2, round 2 -- 2026-08-25

Non-Solidity correctness round over signed Warden tip
`30a929065c65b3d41df6a1fb75087acdb7d08d5b`. Three residual findings were
fixed on the exact Step 2 audit branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Relation Git reads still inherited repository-substitution variables. `GIT_DIR` redirected the same branch names to an attacker repository and receipted `fiat-v9.9.9`; `GIT_ALTERNATE_OBJECT_DIRECTORIES` also changed command output, and a repository-local alternate remained admissible. | fixed in this round: relation reads discard inherited `GIT_*` state, disable global and system configuration and lazy fetching, retain fixed argv with `--end-of-options`, and refuse a populated repository alternate before either an exact-start or derived-start read |
| S2-R2-02 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A crafted shallow boundary changed the unique merge base from the real run start to an earlier commit, so the controller could anchor the wrong ledger and skill bytes. | fixed in this round: relation capture requires a non-shallow repository before accepting an exact or derived starting commit |
| S2-R2-03 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | With `PYTHONINTMAXSTRDIGITS=0`, a 5,000-digit label was accepted and persisted instead of receiving the value-free malformed-label refusal. A stored surrogate in `frontier_revision` escaped as a traceback during `status`, `next`, and `verify`. | fixed in this round: ASCII counters have an explicit 128-digit pre-conversion limit and matching stored-state maximum; invalid UTF-8 scalar values reach the stable field-specific refusal without encoding first |

### Evidence

The Warden pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-2-red.json`, SHA-256
`1d36cdea1bf33c25e274cfb6412663f5212e99e39d790f86e14432fdfc63b0b0`.
It records `elenchus.unittest.v1`, 1,089 tests, seven assertion failures, zero
errors, and zero skips. The fixed-tree report is
`.elenchus/fiat-556-step-2-warden-round2-final-green.json`, SHA-256
`29d2a7eed48962b1cae726b225f9441ab935d936200263200052763bce278ac1`.
It records 1,090 tests with zero failures, errors, or skips.

The fixed tree passes 32 focused relation tests, the 397-test controller and
Fiat contract gate, and all 350 root tests. Promise Machine reports 14 clean
plugin copies and 71 of 71 covered promises. Phylax, Ephoros, and Hypomnema
exit 0 over the complete repository paths. Horos reports that the boundary
matches the tree. The tracked study remains byte-identical to its receipt at
SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the tracked runbook remains byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All four changed product paths are admitted by Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The prior 12,780-byte audit record is the exact prefix of this append, SHA-256
`3d60fef2a407c3611d78a649220d1d4d479a7c2b6c677c36ce62eca03f0aa02c`.
The bounded Sapheneia comparison preserves all three findings, severities,
counterexamples, paths, hashes, counts, qualifications, statuses, and later
step boundaries. Imprimatur reports zero defects. Brevitas accepts the new
round; the complete file retains only its inherited B011 at the two-row Step
1 findings table.

### Risk register

`anchor-substitution`, `git-object-shape`, `generation-arithmetic`,
`diagnostic-leak`, and `legacy-state` surfaced S2-R2-01 through S2-R2-03.
`multi-target-partial` remains green for one, two, partial, reordered, and
one-bad-target capture. Exact starting-commit reads now cover ref and worktree
drift, replacement refs, grafts, inherited Git state, repository alternates,
and shallow history. Top-level `SKILL.md` identity, all anchor fields,
all-or-nothing state and ledger capture, explicit `resolution: null`, Promise
declarations, literal-only byte identity, no-block Git silence, and legacy v1
replay remain green.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, revalidation coverage, stale or capped resolution history, terminal
parent races, self-hosted collision, and interrupted resolution belong to
Steps 3 and 4 and receive no claim here.

Lead not pursued: recomputing every native Git object identity after direct
object-store corruption. This round refuses the observed substitution paths;
native object-store integrity remains Git's repository boundary.

## Step 2, round 3 -- 2026-08-25

Non-Solidity correctness audit over signed Warden tip
`f9d6cac2d33e25ce4ae1cea845b4c0aef493956c`. Three residual findings were
fixed on the exact Step 2 audit branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Receipt replay accepted a tree SHA in `anchor_commit`. `status` and `next` read target blobs from that tree and returned success even though the stored object did not establish the promised starting commit. | fixed in this round: replay resolves the stored SHA through `^{commit}`, requires the stored SHA to name that commit object directly, and refuses before reading either target blob |
| S2-R3-02 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | After a valid receipt, adding a populated repository-local alternate or a shallow boundary left `status` and `next` green. Initial capture checked full-history repository state, but replay did not re-establish it. | fixed in this round: every relation-bearing replay repeats the native graft, alternate, and shallow checks before exact commit and blob reads; inherited `GIT_*` scrubbing and `--no-replace-objects` remain in force |
| S2-R3-03 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A `SKILL.md` with canonical `name` or nested `metadata.version` plus the same protected key in quoted YAML spelling was receipted. The parser selected the canonical line while the real frontmatter identity remained duplicate and ambiguous. | fixed in this round: the accepted subset counts plain, single-quoted, and double-quoted spellings of `name`, `metadata`, and nested `version`, then requires one canonical occurrence with the matching skill and numeric version |

### Evidence

The causal pre-fix report is
`tmp/elenchus/fiat-556-step-2-warden-round-3-red.json`, SHA-256
`ee8e5032530b7ed3024545b305348a984cffcd3c5fac607b937b43ef9763dafc`.
It records `elenchus.unittest.v1`, 1,095 tests, eight assertion failures, zero
errors, and zero skips. The five new guard methods and no Warden product fix
were present. The failures are the two quoted-key receipts and the `status`
and `next` acceptance of a tree anchor, a post-receipt alternate, and a
post-receipt shallow boundary.

The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round3-precommit-green.json`, SHA-256
`47fd37514f781eaa6f57b97bc60618be7cd3508baef66a541a6d89d95eaff8c9`.
It records `elenchus.unittest.v1`, 1,095 tests with zero failures, errors, or
skips. The fixed tree passes 37 focused relation tests, the 434-test controller
and Fiat companion gate, and all 350 root tests. All 16 non-Solidity suite
commands in `AGENTS.md` are green; Lazarus contributes 364 tests under its
pinned Python 3.13 lockfile runtime.

Mason's causal matrix remains
`tmp/elenchus/fiat-556-step-2-red-matrix.json`, SHA-256
`38805d0e89fdceb632b7fa54860dec9a990770606a6bec08932f5e04f128adc9`:
1,073 tests, nine assertion failures, six errors, and zero skips. The canonical
green remains `tmp/elenchus/fiat-556-step-2.json`, SHA-256
`3fe2ea15aea672bb4deaae16a85c18f80260a10c2ef697ee5fef8ffc08a2be72`:
1,076 tests with zero failures, errors, or skips.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema each exit 0 on the complete repository paths.
Horos reports that the boundary matches the tree. Python compilation and
`git diff --check` are clean. The receipted study remains at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook bytes remain at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All three product paths are admitted by Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The prior 17,402-byte audit record is the exact prefix of this round, SHA-256
`872da975ff1fab131d52cafec58c57776f9951ca5ed1c79fdda94e2928ba522f`.
The bounded Sapheneia comparison preserves every finding, severity,
counterexample, path, hash, count, qualification, status, scope exclusion,
and unpursued lead. Imprimatur and Brevitas accept the new append; the
complete file retains only its inherited B011 at the two-row Step 1 table.

### Risk register

`anchor-substitution`, `git-object-shape`, `metadata-mismatch`,
`receipt-replay`, `diagnostic-leak`, `legacy-state`, and
`literal-compatibility` surfaced S2-R3-01 through S2-R3-03 or received new
adjacent guards. One, two, partial, reordered, and one-bad-target capture;
counter arithmetic and non-SemVer treatment; every anchored ledger, skill,
evolution, epoch, and frontier field; all-or-nothing multi-target refusal;
state and ledger receipt matching; malformed and tampered anchors; explicit
`resolution: null`; Promise declarations; and legacy v1 replay remain green.
The no-block specimen now runs `done runbook`, `status`, and `next` behind a
refusing Git wrapper without a call, while its directive stays byte-identical.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Leads not pursued: recomputing every native Git object identity after direct
object-store corruption. The guarded substitutions, stored object type, and
full-history state now refuse or reconstruct from native objects; physical
object-store integrity remains Git's repository boundary.

## Step 2, round 4 -- 2026-08-25

Non-Solidity correctness audit over signed Warden tip
`5d2e8c1bf60ade02466a5333876fbe142c2ae0d2`. Four residual findings were
fixed on the exact Step 2 audit branch.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The frontmatter reader accepted a canonical `name` or `metadata.version` beside a YAML-equivalent protected key written with an escape, tag, or explicit-key form. It also accepted an indented scalar continuation that changes the parsed `name`. A YAML consumer could therefore read a different governed identity from the one Fiat anchored. | fixed in this round: anchor capture accepts a closed plain block-mapping key subset, requires one canonical protected line at the correct level, and refuses unsupported or continuing identity syntax |
| S2-R4-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | A 128-digit maximum generation was accepted into the anchor, but its required successor has 129 digits and is outside the controller's own label bound. The stored anchor could not produce a valid projection. | fixed in this round: capture refuses the maximum generation before state or ledger mutation, and state replay refuses such a stored anchor with a value-free field fault |
| S2-R4-03 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Anchor-capture failures interpolated the runbook-controlled skill id into diagnostics. A valid id can occupy most of the admitted path budget, so the failure was neither content-free nor held to the intended short diagnostic shape. | fixed in this round: Git-object, ledger, identity, and metadata failures use fixed field labels and never echo the controlled target id |
| S2-R4-04 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Anchor derivation checked for a shallow repository only before reading refs and running `merge-base`. A shallow boundary created after that check was accepted with unchanged refs. Replay had the same one-sided history check around exact blob reads. | fixed in this round: starting-commit derivation, all-target capture, and receipt replay bracket their Git reads with full-history checks; a persistent graft, alternate, or shallow change during the read refuses before a receipt or packet is returned |

### Evidence

The first causal report is
`.elenchus/fiat-556-step-2-warden-round4-red.json`, SHA-256
`02233e098266cbe1e2ca4ef49fbc481b97ade7f25a6324ab2769d69467166ce7`.
It records `elenchus.unittest.v1`, 1,098 tests, seven assertion failures,
zero errors, and zero skips. Those failures cover five YAML-equivalent
protected-key specimens, the unrepresentable generation successor, and the
controlled-id diagnostic echo. No Warden product repair was present.

The second causal report is
`.elenchus/fiat-556-step-2-warden-round4-history-race-red.json`, SHA-256
`2c586194af3d1e6f79ae9e2fcf4621c07883ec70a5d237f20bcce7ed88c4ba02`.
It records `elenchus.unittest.v1`, 1,099 tests, one assertion failure, zero
errors, and zero skips. The new specimen inserted a shallow boundary after
the first history check; anchor derivation returned success instead of the
required refusal. An adjacent replay specimen covers the same mid-read change
while the exact blobs are reconstructed.

The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round4-precommit-green.json`, SHA-256
`55b77dfee9003ca96e22b4f608aee7880d9598c2ba3cae0d0a4d26f89392d3f6`.
It records `elenchus.unittest.v1`, 1,100 tests with zero failures, errors, or
skips. The fixed tree also passes 42 focused relation tests, the 397-test
controller and Fiat companion gate, and all 350 root tests. All 16
non-Solidity suite commands in `AGENTS.md` are green; Lazarus contributes 364
tests under the pinned Python 3.13 lockfile runtime. The inherited root HTTP
fixture cleanup warnings, controller fixture `ResourceWarning`, and Pandects
catalogue `ResourceWarning` remain non-failing and unchanged by this round.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema each exit 0 on the complete repository paths.
Horos reports that the boundary matches the tree. Python compilation and
`git diff --check` are clean. The receipted and tracked study bytes remain at
SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook bytes remain at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five relative study links resolve from both copies. The three product
paths and this audit record are admitted by Step 2's Files field, and
`audit/AUDIT.md` remains unchanged.

The prior 22,955-byte audit record is the exact prefix of this round,
SHA-256
`d05928665e8e4dc3aba9640ca30c7a751097b47edbabc0042c9abc4c6f75bbb4`.
The bounded Sapheneia comparison preserves every finding, severity,
counterexample, path, hash, count, qualification, status, scope exclusion,
and unpursued lead in the new candidate. Its audit heading, findings table,
evidence, risk register, scope boundary, and lead boundary are present.
Imprimatur accepts the append. Brevitas reports only the inherited B011 at the
two-row Step 1 table in the unchanged prefix.

### Risk register

`metadata-mismatch`, `generation-arithmetic`, `diagnostic-leak`,
`anchor-substitution`, and `receipt-replay` surfaced S2-R4-01 through
S2-R4-04. The new guards cover escaped, tagged, explicit, duplicated, and
continued protected identity syntax; the last representable generation;
content-free failure text; and history changes during derivation and replay.
One, two, partial, reordered, and one-bad-target capture; exact object type and
path checks; every anchored ledger, skill, evolution, epoch, and frontier
field; all-or-nothing mutation; state and ledger receipt matching; status and
worker reconstruction with explicit `resolution: null`; Promise declarations;
and legacy v1 replay remain green. The no-block fixture keeps `done runbook`,
`status`, and `next` byte-identical behind a Git wrapper that refuses any call.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Lead not pursued: an uncooperative process can change and restore Git's
internal shallow, graft, alternate, or object-store state between two local
observations. This round establishes matching before-and-after history checks;
it does not claim an operating-system lock over `.git`. Physical repository
integrity remains Git's boundary, as in the prior direct-corruption lead.

## Step 2, round 5 -- 2026-08-25

Non-Solidity correctness audit over signed repaired tip
`9406dafede6d351ea132a11a8f37ef8521b4df5b` found one residual defect. The
repair is in signed candidate `3bff8faef41db00d415a074b17ec47c7814336ae`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Without a stored commit-form base, anchor derivation trusted the current `merge-base` of the run and integration-base branches. Rewinding the base after `init` moved that result before the run's actual start. If the older commit carried valid but different ledgers or skill metadata, `done runbook` receipted the wrong governed versions. | fixed in this round: the native run-branch reflog supplies its creation commit; capture requires that exact commit to be the sole merge base, and repository identity, refs, branch-start history, and full-history state must remain stable across the read |

### Evidence

The causal report is
`.elenchus/fiat-556-step-2-warden-round5-red.json`, SHA-256
`94c31576f60c69b77bb4d879e6d8047ffffa49dd2e665a3bbbdbcdf1ab35906b`.
It records `elenchus.unittest.v1`, 1,101 tests, one assertion failure, zero
errors, and zero skips. The reduced specimen starts from a valid version
anchor, runs `init`, rewinds only the integration-base branch to its preceding
commit, and attempts `done runbook`. The unmodified controller returned success
and wrote a receipt instead of refusing the earlier merge base.

Elenchus reports `guarded` for signed repair candidate
`3bff8faef41db00d415a074b17ec47c7814336ae` against its exact parent
`9406dafede6d351ea132a11a8f37ef8521b4df5b`. Its complete parent replay ran
1,101 tests with the one new assertion failure, zero errors, and zero skips;
the report is `tmp/elenchus/fiat-556-step-2.json`, SHA-256
`3fe2ea15aea672bb4deaae16a85c18f80260a10c2ef697ee5fef8ffc08a2be72`.
The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round5-green.json`, SHA-256
`84373f0c146e3e090d41fb138ec93da93ba1bfff7f46c5a8794e1a2d2eaf5fc3`.
It records 1,101 tests with zero failures, errors, or skips. All 43 focused
relation tests and all 350 root tests are green. All 16 non-Solidity suite
commands in `AGENTS.md` are green; Lazarus contributes 364 tests under the
pinned Python 3.13 lockfile runtime. The inherited root HTTP fixture cleanup
warnings, controller fixture `ResourceWarning`, and Pandects catalogue
`ResourceWarning` remain non-failing and unchanged by this round.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
Phylax, Ephoros, and Hypomnema each exit 0 on the complete repository paths.
Protasis accepts the receipted study and runbook. Horos reports that the
boundary matches the tree. Python compilation, JSON parsing, and
`git diff --check` are clean. The receipted and tracked study copies remain
byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five relative study links resolve from both copies, the misplaced
plugin-local study path remains absent, and `audit/AUDIT.md` remains unchanged.

The prior 29,729-byte audit record is the exact prefix of this round, SHA-256
`85f2324a1a5705da043cba23c21db48f248b8a0cd1df169f5d3c5b93a51979f5`.
The bounded Sapheneia comparison preserves the finding, severity,
counterexample, paths, hashes, counts, warnings, status, scope exclusions, and
unpursued lead. Its audit heading, findings table, evidence, risk register,
scope boundary, and lead boundary are present. Imprimatur accepts the append.
Brevitas reports the inherited B011 at the two-row Step 1 table and the same
shape diagnostic at this required one-finding table. Removing the table or
inventing two finding rows would break the audit-loop schema.

### Risk register

`anchor-substitution`, `snapshot-race`, and `receipt-replay` surfaced
S2-R5-01. The new guard binds branch-form starts to the native run-branch
creation commit and brackets derivation, capture, and replay with exact
repository-identity and full-history observations. Stable base advances remain
valid; base rewinds, unrelated replacements, missing or malformed reflogs,
ref races, history substitutions, and repository swaps fail closed with
bounded value-free diagnostics.

Canonical top-level skill identity and metadata, projection and label bounds,
exact blob path, type, bytes, and text checks, one- and multi-target capture,
all-or-nothing state and ledger recovery, receipt replay, and `status`, `next`,
and worker-packet reconstruction remain green. The legacy v1 fixture and the
no-block fixture retain their exact bytes; `done runbook`, `status`, and `next`
make no Git call when no relation block exists.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Lead not pursued: a process with direct write access to Git's internal refs,
reflogs, or object store can change and restore them between local
observations. This repair fails closed when those observations disagree; it
does not claim an operating-system lock over `.git`. Physical repository
integrity remains Git's boundary.

## Step 2, round 6 -- 2026-08-25

Non-Solidity correctness audit over signed repaired tip
`696892c046c76b521f339828fadd9274366508c2` found one residual defect. The
repair is in signed candidate `1bea9566913c02484a361ba1afdfeb2fe866dd16`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R6-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Native `git update-ref` commands could delete and recreate the run branch after `init`, replacing the branch-creation reflog with a later commit. If the integration base moved to that commit and it carried valid but different ledgers and skill metadata, `done runbook` accepted the replacement as the run start and receipted the wrong governed versions. | fixed in this round: `init` records the exact worktree starting commit in its hash-chained initial event; relation capture and receipt replay require their anchor to match that evidence, while the existing two-argument replay helper remains compatible |

### Evidence

The causal report is
`.elenchus/fiat-556-step-2-warden-round6-red.json`, SHA-256
`8ac02b34d38dbaf7955c5a5831adeadba11cea91b4af1f919e6b81c12946dab8`.
It records `elenchus.unittest.v1`, 1,102 tests, one assertion failure, zero
errors, and zero skips. The reduced specimen starts from one valid governed
version, runs `init`, advances the base to a different valid version, deletes
and recreates the checked-out run ref at that commit with native Git commands,
then attempts `done runbook`. The unmodified controller returned success and
wrote the replacement anchor instead of refusing it.

Elenchus reports `guarded` for signed repair candidate
`1bea9566913c02484a361ba1afdfeb2fe866dd16` against its exact parent
`696892c046c76b521f339828fadd9274366508c2`. A reduced detached-parent replay
ran all 44 focused relation cases with the one new assertion failure and zero
errors. The complete runner produced the same guarded verdict. An earlier
guard attempt was inconclusive because a changed existing helper call raised a
parent-only `TypeError`; the final repair retains that two-argument interface,
and both the reduced replay and complete guard are assertion-only.

The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round6-green.json`, SHA-256
`f39894a89b695e6af54acf798c601351c4dd8ba49ad8efb6ff97edbd01b51dfa`.
It records 1,102 tests with zero failures, errors, or skips. All 44 focused
relation tests and all 350 root tests are green. All 16 non-Solidity suite
commands in `AGENTS.md` are green: Alexandria ran 255 tests; Ariadne 632 with
six skips; Berean 151 with one skip; Brevitas 21; Hermes 72; Hexaemeron 1,102;
Imprimatur 62; Horos 217; Lazarus 364; Pandects 116; Probitas 276; Sapheneia
11; and Tabularium 134. Both Lemma runners report zero failures; the Solidity
runner leaves its compiler cases skipped without `--solc`. Lazarus ran under
its pinned Python 3.13 lockfile runtime because the system Python lacks its
declared third-party packages.

The inherited root HTTP fixture cleanup warnings and Pandects catalogue
`ResourceWarning` remain non-failing. Promise Machine reports 14 clean plugin
copies and 71 of 71 covered promises. Phylax, Ephoros, and Hypomnema each exit
0 on the complete repository paths. Protasis accepts the receipted study and
runbook. Horos reports that the boundary matches the tree. Imprimatur and
Brevitas accept the changed Fiat contract prose. Python compilation, JSON
parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five relative study links resolve from both copies, the misplaced
plugin-local study path remains absent, and `audit/AUDIT.md` remains unchanged.

The prior 35,186-byte audit record is the exact prefix of this round, SHA-256
`3d043a1464cb2d7a599ba2121ce8f422ba66140b937d4b5aec3a8e3a92e3933d`.
The bounded Sapheneia comparison preserves the finding, severity,
counterexample, paths, hashes, counts, warnings, status, scope exclusions, and
unpursued lead. Its audit heading, findings table, evidence, risk register,
scope boundary, and lead boundary are present. Imprimatur accepts the append.
Brevitas reports the inherited B011 at the two-row Step 1 table and the same
shape diagnostic at each required one-finding table. Removing a table or
inventing finding rows would break the audit-loop schema.

### Risk register

`anchor-substitution`, `snapshot-race`, and `receipt-replay` surfaced
S2-R6-01. The hash-chained init event now fixes the exact worktree start before
a relation block is receipted. Capture and replay require the derived or stored
anchor to equal that commit, so deleting and recreating a run ref cannot move
the anchor even when its current reflog, merge base, ledger, and skill metadata
form a coherent replacement. Repository identity, full-history state, refs,
branch history, objects, and metadata retain their before-and-after checks and
bounded value-free diagnostics.

Canonical top-level skill identity and metadata, projection and counter
bounds, exact blob path, type, bytes, and text checks, one- and multi-target
capture, all-or-nothing state and ledger recovery, receipt replay, and
`status`, `next`, and worker-packet reconstruction remain green. The legacy v1
fixture still replays. A no-block runbook retains the exact legacy receipt and
directive shapes; `done runbook`, `status`, and `next` make no version Git read.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Lead not pursued: a process with direct write access to both controller storage
and Git internals can rewrite the init event, recompute the complete local hash
chain, and coordinate matching ref and object substitutions. Hash chaining
detects partial or accidental edits; without an external signed anchor it does
not prove the local evidence store survived a malicious complete rewrite. That
physical-storage trust boundary is unchanged and receives no stronger claim.

## Step 2, round 7 -- 2026-08-25

Non-Solidity correctness audit over signed audit tip
`9b1cc58885a8bff3f31d3f2c9f80d576fe66c2bb` found two defects in the native
init-anchor path. Their signed repair is
`f990e1119f01628c52354549e65390231c399732`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R7-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Init and relation capture unconditionally read native `HEAD` and run-branch reflogs. A repository with `core.logAllRefUpdates=false` therefore failed `init` with a malformed branch-creation-history diagnostic, including a runbook with no version relation block, even though the hash-chained init event already supplies the immutable start. | fixed in this round: init brackets direct `HEAD` and checked-out branch reads, while later relation capture derives the merge base from stable run and base refs and requires it to equal the hash-chained init starting commit; neither path requires a reflog |
| S2-R7-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The relation receipt validator, init-evidence reader, and merge-base reader each required exactly 40 hexadecimal characters. Git repositories using SHA-256 object IDs could initialize, but relation receipt capture stopped with a malformed init-starting-commit diagnostic instead of accepting the controller's otherwise supported 64-character commit identity. | fixed in this round: every relation commit boundary uses the controller's existing closed 40-or-64-character `COMMIT_RE`, with a real SHA-256 repository guard across capture, receipt replay, `status`, `next`, and `verify` |

### Evidence

The first causal report is
`.elenchus/fiat-556-step-2-warden-round7-red.json`, SHA-256
`252309be916b09c4024755805ba4519cba2abb92776caa33e2931d8c8b551539`.
It records `elenchus.unittest.v1`, 1,104 tests, two assertion failures, zero
errors, and zero skips against the signed audit tip. The two specimens disable
`core.logAllRefUpdates`: one carries a version relation block and one uses the
legacy no-block runbook. Both stop at `init` with `version relation run branch
creation history is malformed`; neither writes a state receipt.

A third reduced specimen creates a real repository with `git init
--object-format=sha256`, records a valid governed target, and follows the
ordinary study and runbook receipts. Before the complete repair, `done
runbook` stopped with `version relation init starting commit is missing or
malformed`. Its native starting commit is 64 hexadecimal characters. This
isolates the closed object-ID assumption from reflog availability.

Elenchus reports `guarded` for signed repair candidate
`f990e1119f01628c52354549e65390231c399732` against exact parent
`9b1cc58885a8bff3f31d3f2c9f80d576fe66c2bb`. Its detached-parent replay ran
1,105 tests with four assertion failures, zero errors, and zero skips: the
three new regression guards and the existing base-rewind guard whose expected
diagnostic changed from the removed branch-creation proof to the init-starting
commit proof. The repaired tree runs all 47 focused relation cases, the prior
44 plus those three guards, with zero failures.

The repaired-tree report is
`.elenchus/fiat-556-step-2-warden-round7-final-green.json`, SHA-256
`8474a72c8712c76676d5fb2bc82a76a548ab7e74fa7930f32f696c2203924b93`.
It records 1,105 tests with zero failures, errors, or skips. The controller and
Fiat contract selection runs 397 tests, and the root suite runs 350 tests,
all green. All 16 non-Solidity suite commands in `AGENTS.md` are green:
Alexandria ran 255 tests; Ariadne 632 with six skips; Berean 151 with one skip;
Brevitas 21; Hermes 72; Hexaemeron 1,105; Imprimatur 62; Horos 217; Lazarus
364; Pandects 116; Probitas 276; Sapheneia 11; and Tabularium 134. Both Lemma
runners report zero failures; the Solidity runner leaves its compiler cases
skipped without `--solc`. Lazarus ran under its pinned Python 3.13 lockfile
runtime because the system Python lacks its declared third-party packages.

The inherited root HTTP fixture cleanup `ResourceWarning`s, the controller
fixture's unclosed `EVOLUTION.md` `ResourceWarning` at `test_hexctl.py:5537`,
and the Pandects catalogue `ResourceWarning` at `test_search_record.py:46`
remain non-failing. Promise
Machine reports 14 clean plugin copies and 71 of 71 covered promises after the
six controller digest bindings were updated to
`bfcbac780719f26f2a10132721dd30c4bb6662d2d5b673189a852e40a16afe2f`.
Phylax, Ephoros, and Hypomnema each exit 0. Horos reports that the boundary
matches the 1,542-file tree with 100 entries and 29 candidates. Python
compilation, JSON parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
Protasis accepts both source and tracked copies. All five relative study links
resolve from the tracked study, the misplaced plugin-local study path remains
absent, and `audit/AUDIT.md` remains unchanged from the Step 1 tip.

The prior 41,539-byte audit record is the exact prefix of this round, SHA-256
`ab8fead61860a20643162e61a4f853f7893f73dc2d9cad562602a286177a58e2`.
The bounded Sapheneia comparison preserves both findings, severities,
counterexamples, paths, hashes, counts, warnings, statuses, scope exclusions,
and the unpursued lead. Its audit heading, findings table, evidence, risk
register, scope boundary, and lead boundary are present. Imprimatur scores the
complete record 100.0 out of 100 with zero defects. Brevitas reports four B011
table-shape diagnostics: the prior two-row Step 1 table, the prior one-row Step
2 round 5 and round 6 tables, and this required two-row findings table.
Removing a required findings table or inventing rows would break the audit-loop
schema.

### Risk register

`anchor-substitution`, `literal-compatibility`, `legacy-state`,
`git-object-shape`, and `receipt-replay` surfaced S2-R7-01 and S2-R7-02. Init
now records the exact directly read `HEAD` commit in the first hash-chained
event without requiring reflogs. Relation capture brackets repository identity,
history state, run ref, base ref, and merge base, then requires the sole derived
anchor to equal that init commit. A later ref or reflog mutation cannot select
a different anchor. Legitimate base advancement remains accepted; base rewind,
run-ref recreation, repository replacement, shallow or substituted history,
and ambiguous ancestry remain refused with bounded value-free diagnostics.

Repository identity, full-history state, commit object shape, exact target blob
path, type, bytes, text, and metadata remain coherent before and after capture.
The same closed 40-or-64-character commit grammar governs init evidence,
capture, stored receipt shape, recovery, and replay. One- and multi-target
projection, all-or-nothing state and ledger recovery, receipt replay, and
deterministic `status`, `next`, and worker packets remain green.

The legacy v1 fixture still replays. A no-block runbook retains its exact
legacy receipt and directive shapes. After init, `done runbook`, `status`, and
`next` make no version Git read when no relation block exists. Disabling native
reflogs changes neither relation-bearing nor no-block behavior, apart from
removing the former false refusal.

`diagnostic-leak` and `promise-overclaim` were rechecked. Refusals name only
the bounded evidence class and do not echo repository paths, refs, commit IDs,
or blob contents. Promise bindings name the hash-chained init evidence and
optional relation reconstruction without claiming that local storage is an
external trust anchor.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution receipt recovery, stale or capped resolution history,
terminal parent races, and the self-hosted collision remain Steps 3 and 4 and
receive no Step 2 claim.

Leads not pursued: a process with direct write access to both controller
storage and Git internals can rewrite the init event, recompute the complete
local hash chain, and coordinate matching ref and object substitutions. Hash
chaining detects partial or accidental edits; without an external signed
anchor it does not prove that local evidence survived a malicious complete
rewrite. No operating-system lock or external storage guarantee is claimed.

## Step 2, round 8 -- 2026-08-25

Zero findings over signed audit tip
`3521bd5c83aeb79d90574a99f1e2d607b2e84e04`. Its signed repair parent is
`f990e1119f01628c52354549e65390231c399732`; both local Shoggoth signatures
verify, and each commit carries exactly one co-author trailer and one origin
trailer.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

### Evidence

All 47 focused relation cases are green. They cover the hash-chained init
starting commit, stable native ref and branch-point reconstruction without a
reflog, real SHA-1 and SHA-256 repositories, receipt replay, `status`, `next`,
`verify`, and Mason, Warden, and Scribe packets. The adjacent controller and
Fiat contract selection runs 397 tests, and the root suite runs 350 tests, all
green.

The fresh complete report is
`.elenchus/fiat-556-step-2-warden-round8-green.json`, SHA-256
`8474a72c8712c76676d5fb2bc82a76a548ab7e74fa7930f32f696c2203924b93`.
It records `elenchus.unittest.v1`, 1,105 tests, zero failures, zero errors,
and zero skips.

All 16 non-Solidity suite commands in `AGENTS.md` are green: Alexandria ran
255 tests; Ariadne 632 with six skips; Berean 151 with one skip; Brevitas 21;
Hermes 72; Hexaemeron 1,105; Imprimatur 62; Horos 217; Lazarus 364; Pandects
116; Probitas 276; Sapheneia 11; and Tabularium 134. Both Lemma runners report
zero failures; the Solidity runner leaves its compiler cases skipped without
`--solc`. Lazarus ran under its pinned Python 3.13 lockfile runtime.

The inherited root HTTP fixture cleanup warnings, controller fixture
`ResourceWarning` at `test_hexctl.py:5537`, and Pandects catalogue
`ResourceWarning` at `test_search_record.py:46` remain non-failing. Promise
Machine reports 14 clean plugin copies and 71 of 71 covered promises. Phylax,
Ephoros, and Hypomnema each exit 0. Horos reports that the boundary matches
the tree. Protasis accepts both source and tracked study and runbook copies.
Python compilation, JSON parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
All five relative study links resolve, the misplaced plugin-local study path
remains absent, and `audit/AUDIT.md` remains byte-identical to the Step 1 tip.

The prior 50,053-byte audit record is the exact prefix of this append,
SHA-256
`2cc4653bc3211678581e39cfc586cd025e55c5f61250079c9c19ecef6571d7fc`.
The bounded Sapheneia comparison preserves the zero-finding status, commits,
paths, hashes, counts, skips, warnings, qualifications, scope exclusions, and
unpursued lead. The required heading, empty findings table, evidence, risk
register, scope boundary, and lead boundary are present.

Imprimatur scores the complete record 100.0 out of 100 with zero defects.
Brevitas reports five B011 table-shape diagnostics: the four required
finding tables already present in the unchanged prefix and this round's
required empty findings table. Removing a table or inventing finding rows
would break the audit-loop schema and the recorded finding counts.

### Risk register

`anchor-substitution`, `git-object-shape`, and `receipt-replay` are green. The
first hash-chained init event records the exact directly read worktree commit.
Relation capture reconstructs one native branch point from stable run and base
refs, requires it to equal that init evidence, and does not require a reflog.
The same closed 40-or-64-character object-id grammar governs init evidence,
capture, stored receipt validation, recovery, replay, `status`, `next`, and
`verify`; a real SHA-256 repository also completes packet reconstruction.

`literal-compatibility` and `legacy-state` are green. A runbook without the
optional block retains the prior receipt and worker directive shapes, works
with native reflogs disabled, and makes no version Git read during `done
runbook`, `status`, or `next`. One- and multi-target capture, source sorting,
all-or-nothing refusal, metadata identity, projection arithmetic, value-free
diagnostics, exact blob reconstruction, and explicit `resolution: null`
remain green.

Live integration snapshots, frontier and ledger drift, remote failures, sync
carriage, resolution recovery, stale or capped resolution history, terminal
parent races, and the self-hosted collision remain Steps 3 and 4 and receive
no Step 2 claim.

Leads not pursued: a process with direct write access to both controller
storage and Git internals can rewrite the init event, recompute the complete
local hash chain, and coordinate matching ref and object substitutions. Hash
chaining detects partial or accidental edits; without an external signed
anchor it does not prove that local evidence survived a malicious complete
rewrite. No operating-system lock or external storage guarantee is claimed.

## Step 3, round 1 -- 2026-08-25

Non-Solidity round over signed Mason commit
`eacc5cfa9bdb6fe73a22c7d7fce0fd9fe8e375d2`, whose direct parent is the
audited Step 2 tip `882776b8e1e5c33d6b93fefa997552b3fb75b1b4`. Both local
Shoggoth signatures verify, and the Mason commit carries exactly one
co-author trailer and one origin trailer. Four findings were fixed with
regression guards on the named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Initial and terminal remote relation reads used the generic Git subprocess environment while exact local-object reads used the native relation environment. An inherited `GIT_DIR` could redirect the base and run observations to another repository and let substituted remote evidence enter a resolution receipt or terminal base check. | fixed in this round: all base and run observations, both stability rereads, and the terminal post-merge base observation use the replacement-, config-, and repository-environment-free relation reader; a real attacker repository under inherited `GIT_DIR` guards the receipt path |
| S3-R1-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Resolution history parsing enforced ordering and generation rules but omitted two evolution-contract rules. It accepted an evolution row retaining the prior digest and an epoch row changing the digest without recording a reopen. Both invalid histories reached compatibility evaluation. | fixed in this round: the relation parser enforces both evolution-contract rules. Value-free refusals cover an unchanged evolution digest and an epoch digest change without reopen evidence |
| S3-R1-03 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The pending-resolution reader capped records at 131,072 bytes, but the closed accepted receipt shape permits a 228,690-byte marker at 32 targets. The writer could publish that valid marker and every later recovery attempt would refuse it. | fixed in this round: writer and reader share a 262,144-byte ceiling, the writer bounds the final encoded bytes before replacement, and a maximum admitted target envelope round-trips through the pending marker |
| S3-R1-04 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Snapshot parsing required every candidate generation to have a successor. A valid base at the maximum generation minus one therefore could not resolve a candidate at the maximum representable generation, although that candidate is representable and accepted by the receipt schema. | fixed in this round: successor availability is required only for the base; a final-generation candidate now resolves and is guarded at the exact counter ceiling |

### Evidence

The final all-four-guard causal report is
`.elenchus/fiat-556-step-3-warden-round1-red-final.json`, SHA-256
`0041afe9db4e15dbb64eafe25a5a15220f52a5b2e60917b523fbbdb4de92f741`.
It records `elenchus.unittest.v1`, 1,149 tests, two assertion failures, three
errors, and zero skips while all four regression guards were present and no
Warden product fix was present. The earlier full Warden red is
`.elenchus/fiat-556-step-3-warden-round1-red.json`, SHA-256
`c776f6c4de7847050585119f8e10e22177e85ec877c237352897d519225d257f`:
1,148 tests, two assertion failures, two errors, and zero skips. Both reports
are complete and remain preserved outside the tracked tree.

The repaired-tree report is
`.elenchus/fiat-556-step-3-warden-round1-green.json`, SHA-256
`11a60c69fca3535d9141af174e898765869693273997e651d5dbdba6550229b0`.
It records `elenchus.unittest.v1`, 1,149 tests with zero failures, errors,
or skips. The four reduced guards pass independently. All 89 focused relation
cases, 399 adjacent controller and Fiat contract-selection cases, nine
evolution-contract cases, and 350 root cases are green.

Mason's causal red remains at `tmp/elenchus/fiat-556-step-3-red.json`, SHA-256
`c9b6bba81dbcf83d5776b9cc029d5773fc0120ae8a61148c1da37d4e506c07e8`.
It records 1,106 tests and the one expected argument-parser error. Mason's
canonical green remains byte-for-byte intact at
`tmp/elenchus/fiat-556-step-3.json`, SHA-256
`02cae51edd345007bd777c23b4b20c07c9eb9881c6319e00741c3b8d3461415d`:
1,145 tests with zero failures, errors, or skips.

The full Mason range contains exactly eight product paths: Fiat's `SKILL.md`,
`references/push-discipline.md`, `scripts/hexctl.py`,
`tests/test_fiat_skill.py`, `tests/test_hexctl.py`,
`tests/test_version_relations.py`, `tests/promise_machine_coverage.json`, and
`tests/test_promise_machine_contract.py`. Warden's product repair changes only
the controller, its focused relation tests, and the controller digest bindings
inside that range. The audit record is the only additional tracked path.

All 16 complete non-Solidity suite commands in `AGENTS.md` are green:
Alexandria ran 255 tests; Ariadne 632 with six skips; Berean 151 with one skip;
Brevitas 21; Hermes 72; Hexaemeron 1,149; Imprimatur 62; Horos 217; Lazarus
364; Pandects 116; Probitas 276; Sapheneia 11; and Tabularium 134. Both Lemma
runners report zero failures; the Solidity runner leaves its compiler cases
skipped without `--solc`. Lazarus ran under its pinned Python 3.13 lockfile
runtime because the system Python lacks its declared third-party packages.

The inherited root HTTP fixture cleanup warnings, controller fixture
`ResourceWarning` at `test_hexctl.py:5538`, and Pandects catalogue
`ResourceWarning` at `test_search_record.py:46` remain non-failing. Promise
Machine reports 14 clean plugin copies and 72 of 72 covered promises. Phylax,
Ephoros, and Hypomnema each exit 0. Horos reports that the boundary matches the
tree. Python compilation, JSON parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
Protasis accepts both. All five relative study links resolve from the tracked
study, the misplaced plugin-local study path remains absent, and
`audit/AUDIT.md` remains byte-identical to the Step 2 tip at SHA-256
`582aa3cfe6b83344c0c6f52987d55ab5a180b429a2199fccd14f6ff769a267d1`.

The prior 55,023-byte, 844-line audit record is the exact prefix of this
append, SHA-256
`c1ecfcfc50de5cc8ee1eb117dc898b4d4123925633393e54f5ba9eabd741ab7d`.
The bounded Sapheneia comparison preserves all four findings, severities,
counterexamples, paths, hashes, counts, skips, warnings, statuses, scope
exclusions, and the unpursued leads. The required audit heading, findings
table, evidence, risk register, scope boundary, and lead boundary are present.

Imprimatur scores the complete record 100.0 out of 100 with zero defects.
Brevitas reports five B011 table-shape diagnostics, all inside the unchanged
prefix. This round's required four-row findings table satisfies its structural
threshold; no protected row was removed or invented.

### Risk register

`base-ref-race`, `run-ref-race`, `remote-evidence-failure`, and
`post-check-race` surfaced S3-R1-01. Stable base and run observations now use
the same native Git boundary as commit, ancestry, tree, path, type, size, and
blob inspection. Both refs are reread after object reconstruction. Signed sync
selection requires the exact product-first and base-second parents, verified
signature, pushed head, affected ledger and `SKILL.md` paths, and a green
covering integration check. Terminal replay verifies the actual
`[base,candidate]` merge parents, signature and head, then refuses if the base
moves after that check. Timeout, nonzero, oversized, malformed, missing, and
credential-bearing Git or GitHub responses retain bounded value-free
diagnostics.

`frontier-drift` and `ledger-history-rewrite` surfaced S3-R1-02. Compatible
generation-only base drift still proceeds. Every incompatible tuple field --
evolution, epoch, status, revision, digest, frontier text, and next job --
refuses. Deleted, reordered, edited, duplicated, generation-invalid,
evolution-invalid, and epoch-invalid history refuses before resolution.
`generation-arithmetic` surfaced S3-R1-04: ordinary successors, carries,
leading-zero and malformed labels, the exact axis rule, base exhaustion, and
the final representable candidate are now distinct and green.

`interrupted-resolution`, `multi-target-partial`, and `state-history-growth`
surfaced S3-R1-03. A receipt still resolves every declared target or none,
sorts them once, and joins state and ledger to one exact event. Every pending
window before the ledger append, between ledger and state replacement, and
after state replacement either completes that event once or returns a named
recoverable refusal. Malformed, tampered, stale, oversized, wrong-subject,
state-only, ledger-only, duplicate, and mismatched pending or durable records
refuse. Eight append-only receipts remain replayable; a ninth refuses without
eviction. The repaired ceiling covers the complete admitted 32-target shape
and is enforced before publication as well as during recovery.

`anchor-substitution`, `git-object-shape`, `metadata-mismatch`,
`resolution-staleness`, `receipt-replay`, and `legacy-state` are green. Base,
candidate, and optional signed-sync evidence is reconstructed from exact
native objects. Each candidate has exactly one matching history row and exact
`SKILL.md` name and version metadata. Altered runbook, active receipt, state,
ledger, target, object, order, base, head, or sync identity refuses. Legacy
states and literal or absent relation blocks retain their prior shapes and
explicit null status. Human status, worker packets, provisional receipts,
current receipts, stale receipts, and terminal integration receipts remain
distinct; stale or absent current resolution withholds integration rather
than presenting old evidence as current.

`sync-carriage`, `revalidation-coverage`, and `self-hosted-collision` are
green. The divergent issue 555 topology requires one signed two-parent sync;
one-parent, wrong-parent-order, unsigned, unpushed, wrong-head, incomplete-path,
or uncovered-check candidates refuse. Concurrent Fiat or Protasis generation
changes are treated as ordinary incompatible or compatible evidence under the
same controller rather than trusted from the model packet.

`diagnostic-leak`, `promise-overclaim`, and `literal-compatibility` are green.
Refusals name only the bounded evidence class and do not echo repository paths,
refs, commits, contents, credentials, signatures, or remote bodies. Promise
text authorises only an exact resolution receipt and later checked carriage;
it does not claim semantic compatibility, label reservation, or an atomic
GitHub base lock. The push discipline still requires integration authority and
verified evidence before any external mutation; this audit made none.

### Scope boundary

This round cold-read the complete Step 3 contract and the eight-file Mason
range, then changed only three product paths inside that range plus this
append-only audit record. No Solidity was present, so the non-Solidity waiver
and three mandatory lint exits apply. No controller command that mutates state,
push, pull request, merge, issue change, or other GitHub mutation was run.

Leads not pursued: a process with direct write access to both controller state
and its ledger can rewrite both durable copies consistently, and a process
with direct write access to the native Git object database can replace the
underlying local evidence. The closed controller shapes detect partial,
stale, and mismatched edits; they do not provide an external trust anchor or
an operating-system storage guarantee. The shared root history parser's
fenced-row convention was not changed here because Step 3 consumes the same
canonical ledger grammar already accepted by the evolution contract; changing
that suite-wide grammar belongs to a separately studied contract.

## Step 3, round 2 -- 2026-08-25

Non-Solidity round over signed repair-and-audit tip
`93921e4e3a550d165623b129826968cd689b3bb0`, whose direct parent is Mason's
signed Step 3 commit `eacc5cfa9bdb6fe73a22c7d7fce0fd9fe8e375d2`.
Both local Shoggoth signatures verify, and the repair tip carries exactly one
co-author trailer and one origin trailer. Three findings were fixed with
regression guards on the named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | The signed `[product, base]` sync check read parents without replacement objects, then ran signature, author, and message checks through ordinary Git replacement handling. An unsigned native sync object could therefore borrow a valid signature and provenance trailers from a signed replacement object while its native parent pair passed separately. | fixed in this round: exact local verification ignores replacement objects; the relation path also removes inherited Git repository and configuration variables for signature, author, and message reads. A real repository probe proves ordinary verification accepts the replacement while native verification refuses the unsigned object, and a controller guard checks the replacement-free command boundary |
| S3-R2-02 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `done resolve-versions` rebuilt live base and run evidence before examining a pending marker. If the ledger event, state replacement, and marker were all durable but only the final clear was interrupted, a later ref move stranded that completed transaction behind a stale-evidence refusal instead of clearing the marker exactly once. | fixed in this round: recovery first reconciles a matching durable state/event pair without consulting refs; incomplete write windows still rebuild and compare current evidence before any completion or rollback. The guard makes any live-evidence reread fail after the durable transition and proves recovery clears only the matching marker |
| S3-R2-03 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Active sync replay converted stored `affected_paths` and per-check `paths` directly to sets after checking only that the outer values were arrays. A nested array raised an unhandled `TypeError` during resolution and status replay instead of returning a bounded refusal. | fixed in this round: replay applies the existing capped, string-only, safe, sorted, unique path validator before set operations, caps the check array, and confines check paths to recorded affected paths. Both nested-array locations now refuse without a traceback |

### Evidence

The first causal report is
`.elenchus/fiat-556-step-3-warden-round2-red.json`, SHA-256
`54f09948dcc474d6f27e154764ccb94d30f1dda8c22699acb3ebb2f050011960`.
It records `elenchus.unittest.v1`, 1,150 tests, one assertion failure, zero
errors, and zero skips. In the isolated real-Git specimen, ordinary
`verify-commit` over the replaced SHA exited 0 while
`git --no-replace-objects verify-commit` over the same native unsigned object
exited 1.

The recovery causal report is
`.elenchus/fiat-556-step-3-warden-round2-red-recovery.json`, SHA-256
`00e0dfa4ac57071e692c2c517f7610ed20dcc80d22e76f43e45952de4f094c72`.
It records the same schema, 1,151 tests, one assertion failure, zero errors,
and zero skips. The sync-shape causal report is
`.elenchus/fiat-556-step-3-warden-round2-red-sync-shape.json`, SHA-256
`4b6169cdaa139622e122340232d07df1aeac196f4b1212fb4207e71d6d001cc8`.
It records 1,153 tests, zero failures, two errors, and zero skips: one raw
`TypeError` for nested affected paths and one for nested check paths. These
reports remain outside the tracked tree.

The final report is
`.elenchus/fiat-556-step-3-warden-round2-green-final.json`, SHA-256
`7ebdf22ad8fe3b9f78d96c3f58dc8b7f8666916752adbe592191f4ddc7e9773a`.
It records `elenchus.unittest.v1`, 1,153 tests with zero failures, errors, or
skips. All 92 focused relation cases, 400 adjacent controller and Fiat
contract-selection cases, 11 Hexaemeron evolution cases, and 350 root cases
are green.

All non-Solidity suite commands in `AGENTS.md` are green: Alexandria ran 255
tests; Ariadne 632 with six skips; Berean 151 with one skip; Brevitas 21;
Hermes 72; Hexaemeron 1,153; Imprimatur 62; Horos 217; Lazarus 364; Pandects
116; Probitas 276; Sapheneia 11; and Tabularium 134. Both Lemma runners report
zero failures; the Solidity runner leaves its compiler cases skipped without
`--solc`. Lazarus ran under its pinned Python 3.13 lockfile runtime.

The inherited root HTTP fixture cleanup warnings, controller fixture
`ResourceWarning` at `test_hexctl.py:5564`, and Pandects catalogue
`ResourceWarning` at `test_search_record.py:46` remain non-failing. Promise
Machine reports 14 clean plugin copies and 72 of 72 covered promises. Phylax,
Ephoros, and Hypomnema each exit 0. Horos reports that the boundary matches the
tree. Python compilation, JSON parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted and tracked runbook copies remain byte-identical at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
Protasis accepts both. All five relative study links resolve from the tracked
study, the misplaced plugin-local study path remains absent, and
`audit/AUDIT.md` remains byte-identical at SHA-256
`582aa3cfe6b83344c0c6f52987d55ab5a180b429a2199fccd14f6ff769a267d1`.

The prior 67,084-byte, 1,013-line audit record is the exact prefix of this
append, SHA-256
`8f21ca225215dc117f2adebf7b23e08370fde23e282cd9a3eae5ce9ab4a6062f`.
The bounded Sapheneia comparison preserves all three findings, severities,
counterexamples, paths, hashes, counts, skips, warnings, statuses, scope
exclusions, and unpursued leads. The required audit heading, findings table,
evidence, risk register, scope boundary, and lead boundary are present.

Imprimatur scores the complete record 100.0 out of 100 with zero defects.
Brevitas reports the five B011 table-shape diagnostics already present in the
unchanged prefix. This round's required three-row findings table satisfies its
structural threshold; no protected row was removed or invented.

### Risk register

`sync-carriage`, `anchor-substitution`, and `git-object-shape` surfaced
S3-R2-01. The active sync now has one native-object boundary for commit
identity, product-first and base-second parents, signature, author, provenance
trailers, and product-to-sync target-path delta. Replacement refs and inherited
repository substitution state cannot mix those facts across objects. Generic
local commit verification also ignores replacement refs, while existing local
key and GitHub-signing-key diagnostics remain value-bounded.

`interrupted-resolution`, `resolution-staleness`, and `receipt-replay`
surfaced S3-R2-02. A matching state-after fingerprint and final hash-chained
ledger event clear the leftover marker before mutable refs are read. State-only,
ledger-only, before-state, mismatched, corrupt-tail, unrelated-event, and
incomplete windows retain their prior exact-evidence checks. The admitted
32-target maximum marker round-trips through the same recovery path. Eight
append-only receipts remain replayable; the ninth still refuses without
eviction.

`revalidation-coverage`, `legacy-state`, and `diagnostic-leak` surfaced
S3-R2-03. Stored affected paths and covering check paths now share the same
closed path grammar used when the revalidation artefact enters the controller.
Empty or oversized check lists, nested values, duplicate or unsorted paths,
unsafe paths, and paths outside the affected set refuse before coverage is
computed. The refusal does not print the stored value or a traceback.

`base-ref-race`, `run-ref-race`, `remote-evidence-failure`,
`post-check-race`, `frontier-drift`, `ledger-history-rewrite`,
`generation-arithmetic`, `multi-target-partial`, `state-history-growth`,
`metadata-mismatch`, `self-hosted-collision`, `promise-overclaim`, and
`literal-compatibility` are green. Stable native base and run observations,
exact object and history snapshots, evolution and epoch rules, non-repeating
frontier digests, compatible generation-only drift, incompatible tuple drift,
the maximum representable candidate, complete signed sync coverage, stale
withholding, actual terminal parent replay, and post-check base movement all
retain direct focused guards. Status and worker packets distinguish absent,
provisional, active, stale, and terminal relation evidence without widening
what the receipt authorises.

### Scope boundary

This round cold-read the complete Step 3 contract, current controller, tests,
Promise bindings, push discipline, and round 1 record. It changed the
controller, two focused test files, controller digest bindings, and this
append-only audit record. No Solidity was present, so the non-Solidity waiver
and three mandatory lint exits apply. No controller command that mutates run
state, push, pull request, merge, issue change, remote write, or other GitHub
mutation was run.

Leads not pursued: a process with coordinated direct write access to controller
state, its hash-chained ledger, and native Git storage can rewrite all three
local evidence classes. The checks detect partial, stale, substituted, and
mismatched reads; no external signed state anchor or operating-system storage
guarantee is claimed. Repository-local Git configuration is read within the
native object store and is not independently pinned in the resolution schema.
The exact issue-or-document wording in issue #556's eventual generation rows
remains a Step 4 product obligation; this Step 3 audit did not invent a generic
history-citation grammar beyond the shared versioning contract.

## Step 3, round 3 -- 2026-08-25

Non-Solidity round over signed repair-and-audit tip
`b98bf7e8a9cf2a9f5d5b05101d038331c43d4599`, whose direct parent is the
signed round 1 repair tip `93921e4e3a550d165623b129826968cd689b3bb0`.
The local Shoggoth signature verifies, and the tip carries exactly one
co-author trailer and one origin trailer. One high finding was fixed with
causal guards on the named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Active sync replay admitted open or incomplete stored sync, revalidation, and check records. It did not bind `starting_base`, rederive the merge-base, product, upstream, overlap, composition, and affected path proof, or require successful checks to cover every affected path. A state record with no check identity or command, or with a non-target affected path left uncovered, could remain active and release the integration directive. | fixed in this round: replay requires exact field sets, the recorded starting base, a native unique merge-base, exact native path-set recomputation, bounded unique check identities and commands, non-boolean exit 0, and complete affected-path coverage. Eight malformed shape specimens and one uncovered-path specimen guard the refusal |

### Evidence

The first pre-fix report is
`.elenchus/fiat-556-step-3-warden-round3-red.json`, SHA-256
`eb35e206de498c7cdb2dd4d3eaf7f9ce15fc11d368d3319aa89837e30c32720c`.
It records `elenchus.unittest.v1`, 1,155 tests, one assertion failure, eight
errors, and zero skips. The errors came from a guard-context mistake, so this
report is preserved as inconclusive rather than cited as causal evidence.

The corrected causal report is
`.elenchus/fiat-556-step-3-warden-round3-red-final.json`, SHA-256
`d20614b6b6e4e53b02d5fde8254e87ecc91fc1893cd2a29499c1f2919037abb4`.
It records 1,155 tests, nine assertion failures, zero errors, and zero skips
while the worktree carried the guards and no product repair. The failures are
the eight admitted stored-shape variants and the uncovered affected path.

The fixed-tree report is
`.elenchus/fiat-556-step-3-warden-round3-green-final.json`, SHA-256
`eb00b4adcfe179dbc03e3c93893bd9859138021de6a131c03be6e1e8d8e65cdd`.
It records `elenchus.unittest.v1`, 1,155 tests with zero failures, errors, or
skips. All 94 focused relation cases, 400 adjacent controller and Fiat
contract-selection cases, nine evolution-contract cases, and 350 root cases
are green. The Elenchus verdict is guarded.

All non-Solidity suite commands in `AGENTS.md` are green: Alexandria ran 255
tests; Ariadne 632 with six skips; Berean 151 with one skip; Brevitas 21;
Hermes 72; Hexaemeron 1,155; Imprimatur 62; Horos 217; Lazarus 364; Pandects
116; Probitas 276; Sapheneia 11; and Tabularium 134. Both Lemma runners report
zero failures; the Solidity runner leaves its compiler cases skipped without
`--solc`. Lazarus ran under its pinned Python 3.13 lockfile runtime.

The inherited root HTTP fixture cleanup warnings, controller fixture
`ResourceWarning` at `test_hexctl.py:5564`, and Pandects catalogue
`ResourceWarning` at `test_search_record.py:46` remain non-failing. Promise
Machine reports 14 clean plugin copies and 72 of 72 covered promises. Phylax,
Ephoros, and Hypomnema each exit 0. Horos reports that the boundary matches the
tree. Python compilation, JSON parsing, and `git diff --check` are clean.

The receipted and tracked study copies remain byte-identical at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
the receipted, amended, and tracked runbook copies remain byte-identical at
SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
Protasis accepts both. All five relative study links resolve from the tracked
study, the misplaced plugin-local study path remains absent, and
`audit/AUDIT.md` remains byte-identical at SHA-256
`582aa3cfe6b83344c0c6f52987d55ab5a180b429a2199fccd14f6ff769a267d1`.

The prior 76,987-byte, 1,153-line audit record is the exact prefix of this
append, SHA-256
`67b7cd330d3cb1e06e404b905fcf6a46b1f3fb8b09bc0fe5136b61228fc71cf7`.
The bounded Sapheneia comparison preserves all earlier findings, severities,
counterexamples, paths, hashes, counts, skips, warnings, statuses, scope
exclusions, and unpursued leads. This round adds only its heading, one finding,
its evidence, risk register, scope boundary, and lead boundary.

Imprimatur scores the complete record 100.0 out of 100 with zero defects.
Brevitas reports six B011 finding-table shape diagnostics: five in the
unchanged prefix and this round's one-row table. The row count stays equal to
the actual finding count; no protected finding was removed or invented.

### Risk register

`revalidation-coverage`, `sync-carriage`, and `receipt-replay` surfaced
S3-R3-01. Active replay now accepts only the exact stored shape emitted by
`done sync-run`. It binds the starting and integration bases, requires one
native product/base merge-base, and recomputes product, upstream, overlap,
composition, and affected paths through the replacement-free relation reader.
Every stored set must equal that proof. Checks carry unique bounded ids and
commands, exact fields, exit 0, safe paths confined to the affected set, and
their union covers the full affected set. Unknown, missing, duplicate,
oversized, unsafe, failed, boolean-exit, stale, and partially covered records
refuse without printing stored values.

`anchor-substitution`, `git-object-shape`, `base-ref-race`, `run-ref-race`,
`remote-evidence-failure`, `post-check-race`, `resolution-staleness`,
`interrupted-resolution`, `frontier-drift`, `ledger-history-rewrite`,
`generation-arithmetic`, `multi-target-partial`, `state-history-growth`,
`metadata-mismatch`, `self-hosted-collision`, `legacy-state`,
`diagnostic-leak`, `promise-overclaim`, and `literal-compatibility` are green.
The native sync signature, author, provenance trailers, product-first and
base-second parents, stable remote observations, exact target objects and
histories, pending recovery before live rereads, eight-receipt cap, stale
withholding, terminal parent replay, post-check base observation, and bounded
status and worker packets retain focused guards. Runs without a relation block
retain their prior literal behaviour.

### Scope boundary

This round cold-read the complete Step 3 contract, current controller and
tests, Promise bindings, push discipline, and both earlier Step 3 audit
records. It changed the controller, one focused test file, controller digest
bindings, and this append-only audit record, all within the Step 3 file set.
No Solidity was present, so the non-Solidity waiver and three mandatory lint
exits apply. No controller command that mutates run state, push, pull request,
merge, issue change, remote write, or other GitHub mutation was run.

Leads not pursued: a process with coordinated direct write access to controller
state, its hash-chained ledger, and native Git storage can rewrite all three
local evidence classes. The controller detects partial, stale, substituted,
and mismatched reads; no external signed state anchor or operating-system
storage guarantee is claimed. Repository-local Git configuration remains
inside the native object-store trust boundary. The stored check command and
exit record what the operator ran; the Promise does not claim that a check was
semantically sufficient for every future composition. Step 4 still owns the
exact issue-or-document wording in issue #556's eventual generation rows.
