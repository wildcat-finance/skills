# Study: retire mandatory Shoggoth co-signature and runtime-host authorship ban

Assuming, unless corrected:

1. Issue #1135 and the Creator's 2026-09-06 clarification are the product
   decision: runtime hosts may author, commit, co-author, open, and describe
   work, and neither canonical Shoggoth trailer is mandatory.
2. The clarification that connectors are substitutes is authoritative for
   GitHub access. A connected GitHub interface is acceptable when it can make
   or return the same exact authenticated mutation or readback; it is not an
   inferior source merely because it is not local `gh`.
3. The run starts from `main` at
   `3cc0ad7f521985e46cf29f364a20e19fa99b64dd`, recorded by the Fiat run
   anchor. The local `main` ref in the source checkout is stale and is not the
   run's base evidence.
4. “Signature-only” means a commit still needs the signature evidence its
   transition already names: local Fiat-created commits pass `git
   verify-commit`; pushed and host-created commits pass the platform's exact
   `verified: true`, `reason: valid` readback. It does not constrain the
   signer, author, committer, co-author, pull-request opener, or byline.
5. Runtime hosts may remain excluded from `CONTRIBUTORS.md` because that file
   ranks humans. That classification is not permission to reject their Git
   authorship and must no longer be parity-bound to Fiat's publication gate.
6. Historical studies, runbooks, audit rounds, ADR-016, ADR-019, ADR-058,
   proof records, and labelled-prose fixtures keep their bytes. New records
   supersede their live policy; they do not rewrite what those records meant.
7. This run changes no Solidity. The controller's security-suite waiver is
   therefore valid for the subject studied here.

These readings follow the filed decision and the Creator's correction. The
study proceeds on them.

## 1. Problem statement

The repository currently treats two attribution conventions as identity
requirements. Fiat requires every locally receipted commit to carry exactly
one `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and exactly
one `Wildcat-Origin: shoggoth` trailer. Fiat and the base-owned `identity` job
also reject a known runtime host in author, committer, co-author,
pull-request-opener, and byline positions. Those requirements contradict the
Creator's decision that a valid signature is sufficient and that Claude,
Fable, Codex, or another runtime host may appear in those positions.

The user is any human or agent contributing through local Git, a GitHub App,
or a connected GitHub interface. A working prototype removes both attribution
requirements from current enforcement and guidance while leaving signature
failure fail-closed, preserving bounded parsing and exact evidence readbacks,
and keeping the human-contributor ranking honest about non-human accounts.

The proving demo path is:

```text
python3 -m unittest tests.test_commit_identity tests.test_contributors tests.test_shoggoth_identity tests.test_host_settings plugins.hexaemeron.tests.test_hexctl -v
python3 scripts/run_checks.py --base 3cc0ad7f521985e46cf29f364a20e19fa99b64dd
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
git diff --check
```

The focused tests must show that a validly signed commit and platform-verified
commit pass with a runtime-host author, committer, co-author, opener, or byline;
that either, both, or neither Shoggoth trailer may appear; that an invalid or
missing required signature still refuses; and that the contributor generator
may exclude a non-human account without exporting that exclusion into Fiat.
The checked runner must then report green for every changed owner.

## 2. Prior art

In this repository, `SHOGGOTH.md` and ADR-016 say authorship follows the
contributing actor and ban runtime hosts from governed authorship. ADR-052
separates Shoggoth authorship from a human publisher. Fiat implements that
model in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, its worker briefs,
and `references/push-discipline.md`. `scripts/contributors.py` copied the three
`HOST_*` sets for its different task of ranking humans. ADR-058 and
`scripts/check_commit_identity.py` moved the same attribution model into a
base-owned `pull_request_target` workflow. `tests/test_commit_identity.py`,
`tests/test_contributors.py`, `plugins/hexaemeron/tests/host_identity_cases.py`,
and `tests/test_shoggoth_identity.py` bind those choices.

The last two merged pull requests that changed the subject were read in full:

- [PR #967](https://github.com/wildcat-finance/skills/pull/967), merged as
  `3b9a67f765be7256fa79a28fdfd4d4c33aeb7bad` on 2026-08-30, added the
  base-owned `identity` job, exact-range parser, host refusals, special
  Shoggoth identity and trailer checks, ADR-058, and its tests. It carried no
  `## Carried forward` section. Its “Bootstrap hold” is no longer open as
  written: live ruleset `21830871` now lists `identity` and `invariants` under
  `Required CI`, presently in `evaluate` enforcement. Retiring the job must
  remove its live required-context entry before deleting the workflow.
- [PR #646](https://github.com/wildcat-finance/skills/pull/646), merged as
  `4698ef7761dba6c4449da35c233a41c4471abf28` on 2026-08-26, widened and
  explained Fiat's host refusals, added `.claude/settings.json`, and required
  body readback. Its nine carried items resolve as follows: the
  `Claude-Session` classification, `claude` login classification, host-regex
  gaps, unadorned session links, and the prohibition on quoting host bylines
  are made moot by retiring the host ban; the unobserved attribution setting
  is no longer needed and the settings file may be removed; the Interceptor's
  copied regex remains an organisation-level follow-up outside this target;
  the old Horos synopsis observation is closed by the current boundary and
  synopsis checks; and the old study/runbook Elenchus-report path mismatch is
  a preserved historical record, not a current implementation defect.

Audit source selection was checked before design. `python3
plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero
for the whole repository: all committed synopsis bytes matched their
authoritative sources, including root source digest
`d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`
and the #617 source digest
`ff72ec85769e816ec1e49536253dab554bc171e0b3bc2011ef395024589af7a1`.
The following in-scope records were read:

- `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.synopsis.md`,
  the verified view of the directly relevant four-round source. Its Covered,
  Not checked, Elenchus verdict, findings, and Leads not pursued were retained.
  The two findings were low and fixed; final round found none. Its live GitHub,
  host-settings behaviour, Interceptor state, Pashov waiver, regex false
  positives and gaps, and historical report-path mismatch remain no stronger
  than recorded. This study resolves only the host-policy leads made moot by
  issue #1135 and keeps the Interceptor item outside target scope.
- `audit/AUDIT_SYNOPSIS.md` rows 316-321, the verified view of the Shoggoth
  contributor-guide rounds. Their explicit legacy fields remain unknown as
  `[missing legacy field: ...]`; their findings are fixed and their final
  `Leads not pursued` value is none. The published history remains unchanged.
- `audit/AUDIT_SYNOPSIS.md` rows 373 and 389-403, the verified view of the Fiat
  merged-attribution and contributor-generator rounds. Their recorded findings
  and fixes remain authoritative. In particular, the contributor job's
  Shoggoth-trailer absence was deliberate when authorship did not happen,
  GitHub signing was inferred rather than live-proved for that workflow, and
  the human-ranking classification was separate from commit permission. The
  missing legacy fields remain unknown. This run preserves those historical
  facts while removing their use as a current authorship ban.

PR #967 has no corresponding Warden audit record under `audit/` or
`plugins/hexaemeron/audit/`; its PR evidence is not relabelled as an audit.

Inside the organisation, `laurenceday/shoggoth-interceptor` was previously
recorded as carrying a copied host-byline expression. This run does not mutate
that separate repository. It records the need to remove the same policy there
as a named follow-up rather than pretending the Skills change reaches it.

Outside the organisation, Git's `git-verify-commit` contract validates the
signature embedded by `git commit -S`; it does not impose an author-name
policy. GitHub supports GPG, SSH, and S/MIME commit signatures, stores a
persistent repository-network verification record, signs web-interface
commits with its web-flow key, and exposes `verified`, `reason`, and
`verified_at` through its REST commit object. Those are compatible with a
signature-only rule and with commits made through connected interfaces.

No prior-art item requires retaining the Shoggoth trailers or host ban after
the governing decision changed.

## 3. Constraints and non-goals

- Exact start: run-anchor `main` at
  `3cc0ad7f521985e46cf29f364a20e19fa99b64dd`, Python `3.14.6` from
  `.python-version`, project support `==3.14.*` from `pyproject.toml`, stdlib
  `unittest`, Git, and the repository's checked runner.
- The two attribution rules are withdrawn, not made optional and not moved to
  another allowlist. A runtime host or GitHub App is accepted as an identity
  when the surrounding syntax and signature evidence are valid.
- Signature checks, exact object identity, range topology, bounded reads,
  malformed-record refusals, platform verification readbacks, and explicit
  publication authority remain. Authorship permission does not itself grant
  push or merge authority.
- Connected GitHub access and local `gh` are equivalent routes when they
  return the exact fields a gate needs. Missing, partial, or unbound connector
  output is not evidence. Designing a universal connector SDK is a non-goal.
- `CONTRIBUTORS.md` remains a ranked human list. The host-account exclusion may
  survive under contributor-owned names and tests, but the `HOST_*` parity
  contract with Fiat is removed.
- Historical records and labelled examples are immutable. Current public
  guidance, generated runtime mirrors, promises, tests, and package/version
  surfaces move together.
- The base-owned `identity` workflow has no justified identity rule after this
  decision. Preserving its hostile-object parser as a required CI job is a
  non-goal; reusable parsing may remain only where another live promise needs
  it.
- The separate one-approving-review decision in ADR-058 is not reversed by
  this issue. Live ruleset edits preserve unrelated rules and actors.
- The Interceptor's copied rule is not changed in this repository.
- No dependency, public ABI, storage layout, released digest rewrite, or
  Solidity change is authorised.

Always: run both the focused policy tests and every check selected by
`scripts/run_checks.py`; run Imprimatur on changed prose; verify every required
signature and exact platform verification record; preserve unrelated live
ruleset fields on read-modify-readback. Ask first: add a dependency, change
controller receipt shape, broaden a GitHub token permission, add a bypass
actor, alter review count, or define a new connector evidence schema. Never:
commit key material or credentials, treat an unavailable connector read as an
empty response, weaken signature verification to make a host-authored fixture
pass, rewrite historical records, edit vendored code, delete a failing test,
or claim an unrun command passed.

## 4. Design options

The closed candidate-by-criterion record is
`.hexaemeron/design-evidence.json`; its twenty reports are under
`.hexaemeron/design-reports/`. The matrix covers all five Protasis concerns.

**`signature-only-retirement` (selected).** Remove the Shoggoth trailer counts,
special Shoggoth lookalike refusals, runtime-host identity and byline refusals,
and their worker instructions. Retain syntax bounds and signature evidence.
Delete the base-owned identity workflow/checker after removing its live
required-context entry. Decouple contributor ranking from Fiat. Trade: the
repository deliberately stops distinguishing runtime-host attribution from any
other valid identity, which is the requested policy.

**`structural-identity-job`.** Remove both attribution rules but retain
`identity.yml` and `check_commit_identity.py` as a bounded grammar/range check.
Trade: it preserves hardened hostile-object code, but keeps a required hosted
job, status context, and maintenance surface with no remaining identity claim.

**`delete-all-identity-controls`.** Delete attribution and signature checks
together. Trade: the smallest apparent policy surface also admits unsigned or
invalidly signed commits and destroys the one requirement issue #1135 keeps.

**`compatibility-toggle`.** Put the former rules behind a configuration flag.
Trade: migration can be gradual, but the withdrawn rules remain available,
adds persistent policy state, and turns a direct decision into a mode matrix.

All selection commands exited zero and produced closed
`protasis-design-report/v1` objects. Both latter candidates fail hard gates.
Between the two survivors, `signature-only-retirement` has zero continuing
hosted policy jobs against one and adds the same zero persistent fields, so it
is the sole non-dominated survivor under `unique-frontier`.

## 5. Risk register seed

```risk-register
signature-loss | Fiat and platform commit admission after attribution checks are removed | unsigned invalid or unbound verification evidence still refuses at every commit-bearing transition
residual-host-ban | controller CI prose or tests retain one runtime-host refusal | the complete named enforcement inventory is deleted or rewritten and host-role fixtures pass
residual-trailer-mandate | a worker controller test or portable copy still requires either Shoggoth trailer | zero mandatory counts remain outside preserved historical records and either both or neither trailer passes
identity-job-wedge | live Required CI still names identity after its workflow is retired | ruleset 21830871 is read fresh changed without touching unrelated rules and read back without identity
ruleset-overwrite | external read-modify-write drops invariants review or unrelated actors | exact preimage and postimage diff changes only the identity context and preserves every other field
connector-evidence-gap | a connected interface returns a summary without exact object or verification fields | the transition refuses until exact immutable SHA verification and authority fields are available
contributor-policy-leak | human-ranking exclusions continue to control Git authorship | contributor classifications are locally owned and no parity or import reaches Fiat or the branch gate
shoggoth-lookalike-residue | special ambiguous-Shoggoth checks survive as an identity allowlist | exact and near-match Shoggoth identities are treated like other syntactically valid identities
historical-record-rewrite | current-policy cleanup edits records of the old policy | immutable paths from issue 1135 remain byte-identical to the base
generated-copy-drift | SHOGGOTH or Promise Machine changes leave portable copies or digest pins stale | portable sync and contract checks pass on the complete changed tree
signature-fixture-masking | tests disable signing globally to admit new host fixtures | disposable fixture configuration changes only the test repository and explicit invalid-signature guards remain red on the unfixed path
authority-confusion | allowing a host identity is treated as permission to publish or merge | authority and repository access stay separately checked and recorded
```

Warden should look hardest at `signature-loss`, `residual-host-ban`,
`identity-job-wedge`, `connector-evidence-gap`, and
`contributor-policy-leak`, where a wording deletion could silently weaken a
different gate or leave the reversed rule active elsewhere.

## 6. Glossary seeds

- Signature-only: admission based on valid cryptographic verification, not an
  allowlist or denylist of author names.
- Attribution rule: a requirement about author, committer, co-author, opener,
  byline, or provenance trailer, distinct from signature validity.
- Runtime host: Claude, Fable, Codex, ChatGPT, Copilot, or another execution
  environment; after this change the term carries no Git-authorship refusal.
- Platform verification: GitHub's exact commit `verification` record, including
  `verified: true` and `reason: valid`.
- Connector-equivalent readback: exact authenticated platform evidence returned
  through a connected interface rather than local `gh`.
- Human-contributor ranking: the generated list of humans thanked by the
  repository, which may exclude non-human accounts without banning commits.
- Historical record: a study, runbook, audit, ADR, proof, or fixture whose old
  policy statements remain evidence of what was then required.
- Identity job: the current base-owned `pull_request_target` status named
  `identity`, not the signed-commit repository rule.

## 7. Sources

- Issue #1135, `framework-79`,
  <https://github.com/wildcat-finance/skills/issues/1135>, body digest recorded
  by Fiat as
  `565f201ed41fc7a2dc9acded7ec3bf159801afa5c3495fdea1404a5005603c8c`.
- Fiat run state `.hexaemeron/state.json`, run id
  `fiat-70ac54c439197feb56e12230a60284428b7153fe5baaa716efdc13e0a93321ac`,
  base `3cc0ad7f521985e46cf29f364a20e19fa99b64dd`.
- `SHOGGOTH.md`; `PROMISE_MACHINE.md`; `AGENTS.md`; `README.md`; `INSTALL.md`;
  `.claude/settings.json`.
- `plugins/hexaemeron/AGENTS.md`, `agents/surveyor.md`, `agents/mason.md`,
  `agents/warden.md`, `skills/fiat/SKILL.md`,
  `skills/fiat/references/push-discipline.md`, and
  `skills/fiat/scripts/hexctl.py`.
- `scripts/check_commit_identity.py`, `scripts/contributors.py`,
  `.github/workflows/identity.yml`, `tests/test_commit_identity.py`,
  `tests/test_contributors.py`, `tests/test_shoggoth_identity.py`,
  `tests/test_host_settings.py`, and
  `plugins/hexaemeron/tests/host_identity_cases.py`.
- ADR-016, ADR-019, ADR-052, ADR-058, and ADR-077 under `docs/decisions/`;
  `docs/pr-identity-gate/study.md`; and
  `docs/fiat-host-byline-readback/study.md`.
- PR #967, <https://github.com/wildcat-finance/skills/pull/967>, and PR #646,
  <https://github.com/wildcat-finance/skills/pull/646>, read through GitHub's
  API with bodies, merge identities, and file lists.
- Live repository ruleset `21830871`, read 2026-09-06 through GitHub's API;
  name `Required CI`, enforcement `evaluate`, contexts `identity` and
  `invariants`, no bypass actor.
- Verified audit views and sources named in section 2, after the whole-set
  `audit_synopsis.py --check .` exit zero.
- Git `verify-commit` documentation,
  <https://git-scm.com/docs/git-verify-commit>.
- GitHub commit signature verification,
  <https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification>,
  and REST commit verification fields,
  <https://docs.github.com/en/rest/commits/commits>.
- `plugins/hexaemeron/skills/ephoros/SKILL.md`,
  `phylax/SKILL.md`, `metron/SKILL.md`, `elenchus/SKILL.md`, and
  `hypomnema/SKILL.md`, read at the run base and cited rather than copied.

## 8. Signals, and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` governs these signals. No new
unattended service is introduced, but three operator questions remain:

1. “Which exact commit failed signature admission?” The existing local
   verification failure names the immutable SHA and transition; the platform
   readback names SHA, `verified`, `reason`, and `verified_at` without storing
   raw signature material.
2. “Did the retirement leave a stale required context?” The live ruleset
   readback before and after the mutation prints the complete ordered context
   list and enforcement mode; deletion of the workflow waits for a readback
   without `identity`.
3. “Was a connector result exact enough to receipt?” The worker records the
   connector capability used and the exact immutable fields returned, or a
   fixed refusal that says which field is missing. Route name alone is not a
   success signal.

Existing controller ledger events answer which transition accepted each
signature. No new metric, trace backend, or alert is warranted because this is
a bounded repository policy and one external ruleset mutation, not a service.

## 9. Boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` governs the boundaries. Commit
objects, pull-request metadata, platform verification objects, and connector
results are untrusted inputs. Worth taking at those boundaries are object
substitution, false verification summaries, hostile text copied into a
diagnostic, and a ruleset write aimed at the wrong repository. Controls remain
full object identifiers, fixed repository identity, bounded regular reads,
no replacement objects, closed verification fields, value-free refusals, exact
pre/post ruleset documents, and no raw signature persistence.

Local Git and GitHub or connector execution are separate capabilities. Local
verification uses fixed argv and the repository's keyring. Platform access may
use local `gh` or a connected interface, but it must bind the same repository,
SHA, verification result, and mutation readback. No credential is copied from
one route to another, and no connector name itself establishes authority.

The contributor generator keeps its own GitHub-input controls and human-only
classification. Removing parity with Fiat closes, rather than widens, the
boundary between recognition and commit admission.

## 10. The budget, or its absence

`plugins/hexaemeron/skills/metron/SKILL.md` has no performance gate here.
Issue #1135 claims no latency, throughput, memory, or cost improvement. The
selected design removes one hosted policy job and adds no persistent policy
field; those are comparative design counts, not performance measurements.
There is therefore no Metron command. The exact focused and checked-runner
commands in section 1 are correctness gates and must not be reported as
benchmarks.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` governs the repair loop. Invalid,
unsigned, unbound, unreadable, or mismatched signature evidence stops the
specific commit-bearing transition. An unavailable platform or connector
readback is unknown and stops; it never becomes “no identity problem.” A live
ruleset preimage mismatch or post-write document that differs beyond removal
of `identity` stops deletion of the workflow and leaves the prior rule visible
for repair.

Every behavioural reversal gets a red-before-green guard. Host-author,
host-committer, host-co-author, host-opener, and host-byline specimens must fail
against the base for the old reason and pass on the candidate when their
signature evidence is valid. Missing and duplicate Shoggoth trailers must fail
against the base and pass on the candidate. Invalid signatures must fail on
both. Contributor exclusions must still work while a mutation that reconnects
them to Fiat fails. A fix discovered by Warden adds the smallest guard that
reproduces that exact failure and runs through the step's declared
`--elenchus-report {report}` runner; an error or skip is not a guarded verdict.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` governs placement. The
cross-cutting signature-only decision and supersession of ADR-016 and ADR-058
are expensive to reverse and live first at
`docs/decisions/drafts/accept-any-validly-signed-authorship.md`, stable identity
`adr/accept-any-validly-signed-authorship`. ADR-077 assigns its number only at
integration. The draft states that attribution creates neither signature
validity nor publication authority and records why the hosted identity job is
retired.

Fiat's behavioural generation belongs in
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`; it records removal of the
trailer counts, host refusals, special Shoggoth cases, connector inferiority,
and their tests without moving the held frontier. The contributor generator's
separate recognition rule stays explained in ADR-019 and its module comments;
new prose records that it no longer defines commit permission.

The live ruleset mutation is recorded in the run's integration evidence with
its exact preimage, postimage, repository, actor or connector route, and API
readback. Current contributor guidance lives in `README.md`, `INSTALL.md`,
`SHOGGOTH.md`, the Fiat worker briefs, and `push-discipline.md`. Portable
copies are generated from their canonical owners. Historical audits, studies,
runbooks, proofs, and ADRs are cited as superseded evidence and remain
byte-identical.

The outside-repository Interceptor rule is carried forward by name for its own
owner. This run does not claim that changing Skills changes the Interceptor.
