# Study: App publisher recovery r3

Assuming, unless corrected:

1. This is the ordinary Fiat run for
   [skills#925](https://github.com/wildcat-finance/skills/issues/925), not a
   held-frontier advance. The exact worktree resolved from
   `issue/16777233-521053050` is on
   `fiat/925-app-publisher-recovery-r3` at
   `b9f8e36b8b6210bcd023a68059ecb46da3e35769`; `main` and `origin/main`
   matched that commit during Study.
2. The verified controller is `fiat-v5.54.1`. It requires
   `protasis-design-evidence/v1`. The host package is Hexaemeron `1.6.32` and
   the checked-in package is `1.6.33`; their Fiat skill and controller bytes
   are identical, and R3 uses the checked-in `in-repo-source` route. Active
   Protasis is `5.10.0`. The R3 run anchor is
   `fiat-b60d07cc4253a2d353c03d01d2ceff569037bb0f1c228e51296dc8ce7f778152`;
   the current Study directive reported state SHA-256
   `1834971e9a5facfe3087edfc288d6a27c2b2edd86d84512e98f9e3e9d4474c35`.
3. The fresh controller receipt binds issue #925, exact `Fiat-Required: 1`,
   one `carryover` row with disposition `none`, and issue-contract SHA-256
   `b8f27e1823a882af6be152c4e04f9df6e7ecc705f9e7ac971097610fb50164e0`.
   The R2 source records labels `origin:ai`, `observation`, and
   `fiat-run-needed` from its anonymous read. Surveyor made no additional
   GitHub request beyond the controller's issue read at initialization.
4. Phylax owns the credential, untrusted-input, subprocess, socket, and fixed
   network boundaries. Sapheneia and Vulgate supply bounded judgement records;
   Imprimatur supplies the executable prose checks. Those skills do not receive
   the App key or installation token.
5. The repository prototype uses the supported Python, its standard library,
   and existing `openssl`. No GitHub SDK, daemon framework, or live network test
   dependency is added.
6. This run does not authorise reading or moving the live PEM, minting a live
   token, creating an issue, changing App permissions, installing a service,
   changing an OS account or group, or retiring a live helper.
7. Shoggoth is the author. Dr Laurence E. Day is the only authorised
   repository-delivery committer, signer, and publisher, using
   `B83B60AE16F5DD1A` and `laurenceday`. Codex is none of those. The App remains
   the remote issue-creation principal, not a runtime host.
8. The halted R2 archive and preserved Step 1 patch are source evidence only.
   R2 stopped before any Step 1 implementation receipt. Its receipts, base,
   versions, numeric ADR, signatures, and delivery status do not transfer.
   The R2 source also cites the older halted archive and three
   `fiat/925-gate-*` refs under the same restriction. No Solidity is in scope.

## 1. Problem statement

The repository requires this order before an agent-authored issue is created:
freeze required structure and evidence; apply Sapheneia; run Imprimatur; apply
Vulgate and compare content; then run Imprimatur on the exact publishable
bytes. GitHub does not enforce that order.

The existing helper lets any process that can read the App PEM mint a JWT and
installation token and call GitHub directly. Checks inside one helper function
do not close its token variables, token-only route, or direct PEM access.
Watching `fw51.md` protects one path, not issue-creation authority.

Issue #855 is the red specimen. Its recorded path reached the issue POST with
none of the four pass records, and the body lacked the required observation
opening. The current issue records an Imprimatur score of 76.2, including one
finding on this quoted phrase:

<!-- imprimatur:off -->
`load-bearing`
<!-- imprimatur:on -->

The selected prototype is a distinct-identity local service. It accepts one
bounded request over a fixed Unix socket, checks the queue and ordered digest
chain, reruns Imprimatur twice, and opens signer and GitHub transports only
after admission. It retains one in-memory title and body pair through one POST.

Success is testable: the exact #855 fixture and every missing, failed,
reordered, substituted, or mismatched record refuse with zero signer and POST
attempts; one clean injected fixture posts the exact checked bytes once;
authenticated and anonymous readback match; receipts and diagnostics contain
no prose or credential; the client exposes no signer, PEM, token, raw HTTP, or
arbitrary endpoint; and delivery commits verify the named author, committer,
and signer. The offline component proof publishes nothing and does not prove a
live installation.

## 2. Prior art

Current `AGENTS.md` fixes the four issue queues and prose-pass order. ADR-009
defines the queues; ADR-052 separates authorship from delivery identity;
ADR-058 requires independent review; ADR-061 requires progressive design
evidence; ADR-074 governs written records; and ADR-077 assigns new ADR numbers
only at integration.

Current Phylax is `phylax-v1.5.0` with a mature
`off-chain-boundary-controls` frontier. Its job-scoped model proxy supplies the
nearest reusable pattern: a closed protocol, credential access after admission,
fixed destinations, content-free receipts, and separate component and live
deployment claims.

The last two merged Phylax behaviour changes were verified without credentials:
[PR #953](https://github.com/wildcat-finance/skills/pull/953), merged 30 August
2026, added bounded single-assignment resolution and recorded five audit rounds
`2 -> 1 -> 4 -> 2 -> 0`; [PR #754](https://github.com/wildcat-finance/skills/pull/754),
merged 29 August 2026, published the 14-row model-proxy conformance proof while
retaining live-credential, same-UID, supervisor, provider, and integration gaps.

Applicable audit evidence:

| Source and synopsis | Status | Result used here |
| --- | --- | --- |
| Root audit: `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d` / `82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee` | Current; whole-tree synopsis check passed | Keep parsing bounded and diagnostic output content-free; earlier Phylax checks retain narrow dataflow limits. |
| Hexaemeron plugin audit: `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` / `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd` | Current; same check passed | A local hook is not host enforcement; explicit gates remain authoritative. |
| #700 model-proxy audit: `cc56fc7620834b7a6ac192565ce6dee6796a6122f71e4001eb24a9db92707182` / `1df49ab4fb8cb8b3b5c26dd3bb45e9ea676a8b2c6f537f9a9d3cf98dbf391444` | Current, 28 headings; same check passed | Check authority where the credential is used; test one-shot transport, uncertainty, receipts, cleanup, and same-UID limits separately. |
| #1538 base-recovery audit: `672fa7c23d7d74fca3113dd3983cca12cc165f0de0556b28352985de523ce4f2` / `62f12f565dc789a0e03cc6336b2feedc2d8783d108e98f21afa00a8b6e9c7cec` | Current; same check passed | The R2 root-suite blocker was repaired before R3. Its two Phylax-named changes concern audit binding and portable portrait transformation, not issue publication. |
| #953 audit on ref `17d35df30e35da6a0687177ed4c83b8bcfd9373e` | Historical source `4b37793e88dfbfbd3a2127ff8de56358fe42422adb4440dedf6434a425a0500b`; synopsis `9299168c1b820b38d3c9166b39be75fc7e542e343f4ed27f67738756eb104fa3` | Four finding rounds fixed bounded-work, scope, order, ambiguity, and diagnostic defects; round five was clean. The source is not on current `main`. |
| #925 donor audit on product/audit refs | Historical source `f08113a90290c3c0ccdf075648261abf5e2415d33a3570e15a559e4e9230e042`; synopsis `2864cdf070c1dee578aa492b1a59aa208cbd8f3755d301bf0bee1151ac36ffec` | Six admission findings were fixed before a clean fifth round. Socket, signer, token, POST, readback, and deployment were not built or audited. |

R3 starts eight commits after the R2 base. Those commits merge the #1538 root
suite recovery; they do not add publisher product paths. The preserved R2
Step 1 patch is 181,412 bytes with SHA-256
`cef0b4ad9f9f3a123b590f5c59da984e77cc749a68b33018882fd2cde5bafe1e`.
It adds 39 paths and 3,460 lines, and `git apply --check` accepts it against
this base without applying it. That establishes patch shape only, not current
tests, audit, authorship, signature, or delivery. Product source must be
reconciled and retested, generated paths regenerated, the ADR kept as a
numberless draft, and new Dr Laurence E. Day delivery signatures obtained.

## 3. Constraints and non-goals

The request is bounded canonical JSON with duplicate-key rejection, fixed
UTF-8 and NFC rules, closed fields, fixed depth and counts, and no paths. Code,
not the request, owns repository, installation, host, API version, operation,
queue grammar, reserved labels, permission, socket, signer, and PEM path.

The ordered subjects are frozen source; Sapheneia candidate; in-service
Imprimatur result; Vulgate candidate and parity record; in-service final
Imprimatur result; and explicit authority bound to the final digest. Judgement
records are checked for shape and digest continuity, not presented as proof of
semantic truth.

The service mints only after admission, requests only issue-write authority,
posts once, performs authenticated and anonymous readback, and closes response
and credential references on every terminal path. It never returns a token,
places credentials in argv or environment, fetches a caller URL, reopens a
caller path, or retries an uncertain create.

Version 1 creates issues only in `wildcat-finance/skills`. It does not fix
#855's pull-request workflow defect; publish comments or pull requests; edit or
close issues; install the live service; revoke an issued token; protect against
root; or make the App a runtime host.

## 4. Design options

Selection reports classify each declared topology against issue #925. They do
not establish implementation conformance.

| Candidate | Credential unavailable to agent | Every agent route gated | No retry after uncertain create | Privileged action classes | Extra trusted processes | Disposition |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `inline-helper-gates` | false | false | true | 0 | 0 | Reject: direct key and token routes remain. |
| `watched-file-gate` | false | false | false | 0 | 1 | Reject: other paths and direct API calls bypass it; events may repeat. |
| `same-uid-broker` | false | false | true | 0 | 1 | Reject: the caller UID can still read the key or replace the broker. |
| `isolated-publisher` | true | true | true | 4 | 1 | Select: only the checked socket operation crosses to the key-owning identity. |

The four privileged action classes are service identity and socket group, key
custody, service installation, and retirement of direct helper access. They
remain separately authorised deployment work. The hard gates leave only
`isolated-publisher`, so it is the unique frontier even though its deployment
cost is higher.

`.hexaemeron/design-evidence.json` contains the complete 4 by 10 matrix. Its 20
selection cells are resolved by reports over the digest-bound
`.hexaemeron/design-topology.json`. Its 20 conformance cells remain pending:
`ordered-admission-chain`, `request-work-bound`, and `request-byte-bound` block
Step 2; `signer-and-post-boundary` blocks Step 3; and
`public-route-and-deployment-check` blocks integration.

## 5. Risk register seed

```risk-register
same-uid-bypass | agent identity to PEM and mint authority | require a distinct service identity and no agent-readable key path
socket-spoofing | client connection to service | check fixed path file type owner group mode and peer policy before admission
frame-smuggling | untrusted frame into parser | cap length first and reject duplicate unknown unsafe deep or trailing input
queue-substitution | queue into title opening and labels | recompute code-owned queue rules from final bytes
inventory-loss | protected evidence across prose stages | require ordered items and recompute every digest join
judgement-forgery | Sapheneia or Vulgate record into admission | check closed subjects and digests while retaining their semantic limit
imprimatur-substitution | supplied lint verdict into credential use | rerun the pinned checker twice inside the service
stage-reordering | pass sequence into authority | fixed ids order subjects and digests reject missing duplicate or reordered stages
byte-mutation | final check into POST | retain one in-memory byte pair and never reopen a caller path
signer-early-access | admission into PEM use | every refusal proves zero signer calls
token-crossing | service credential into caller surfaces | content-free schemas and canary scans cover output argv environment files and receipts
destination-widening | request into GitHub route and permission | code owns host repository installation route API version and scope
duplicate-create | uncertain POST into retry | one attempt returns an indeterminate digest for operator reconciliation
readback-substitution | GitHub response into success | authenticated and anonymous reads match the exact returned issue and bytes
cleanup-gap | terminal path into credential lifetime | close handles and clear references without claiming memory erasure
service-misdeployment | deployment kit into live host | privileged verifier checks identity socket key service and helper state
public-helper-regression | client into hidden mint or HTTP route | scan commands imports packaging and outputs for forbidden capability
donor-drift | historical patch into current Phylax | reapply canonical source only then regenerate and rerun current checks
stale-receipt | halted state into new controller | treat old receipts only as source evidence and issue fresh receipts
signer-confusion | Shoggoth authorship into repository delivery | verify author Shoggoth and Dr Laurence E. Day committer signer before push
adr-collision | decision into numeric ADR path | use a numberless draft and assign only against integration base
root-bypass | administrator into service identity | state root and administrators outside the promise
```

Look hardest at same-UID access, stage or byte substitution, early signer use,
uncertain create, live misdeployment, donor drift, and signer confusion.

## 6. Glossary seeds

**Admission.** All checks completed before signer or network access.
**Candidate digest.** SHA-256 over a canonical length-delimited title and body.
**Credential-owning service.** The distinct identity that alone reads the PEM.
**Final bytes.** The title and body retained after final Imprimatur and posted unchanged.
**Indeterminate create.** One POST whose remote result cannot safely be established.
**Live isolation.** Deployed denial of PEM access to the agent UID; tests alone do not prove it.
**Publication receipt.** A bounded content-free record of digests, outcomes, counts, URL, and cleanup.
**Repository-delivery identity.** Dr Laurence E. Day for commit, signature, and publication; never Codex.

## 7. Sources

- The fresh R3 issue-contract receipt, the R2 anonymous issue capture, and the
  issue #855 specimen it preserves.
- Current `AGENTS.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`, and Promise Machine router.
- ADR-009, ADR-052, ADR-058, ADR-061, ADR-074, and ADR-077.
- Active Protasis, Phylax, Ephoros, Metron, Elenchus, Hypomnema, Sapheneia,
  Imprimatur, and Vulgate contracts; current Phylax `EVOLUTION.md`; and
  `plugins/hexaemeron/skills/VERSIONING.md`.
- The six source-and-synopsis audit pairs and two merged PRs named in item 2.
- Halted R2 archive
  `/Users/c0rtexzer0/Documents/GitHub/skills-925/.hexaemeron/archive/20260912T223435Z-halted-app-publisher-recovery-r2`,
  whose Study SHA-256 is
  `bdb9d60f9d3b14914cedb72014b13ac53e10f2abb8c3a578cf82b33d1a951529`
  and design-evidence SHA-256 is
  `ea5ab14cf3544fb3fbe28766f89b74f7fdb3d7dc89fbeea50f9df23a453ad8c8`.
- Preserved donor patch
  `/tmp/fiat-925-r2-preserve.JcViKz/step1-product.patch` at the digest and
  patch-shape result named in item 2.
- The older halted archive, product tip
  `09e70a6c7201c2a72fd5634d3780b63b4187aee7`, and audit tip
  `44a8107127634776170b42749c8a7dd667b9844c` cited by R2, as historical
  evidence only.

No live credential, key, installation token, authenticated GitHub call,
service installation, or publication was used in Study.

## 8. Signals, and the questions behind them

One content-free correlation record answers: which request and final digests
arrived; which gate and version accepted or refused; how many key, token, POST,
and readback attempts occurred; whether exact-byte readback matched; and whether
cleanup finished or an indeterminate create needs reconciliation.

Events carry fixed stage and outcome enums, short digests, counts, elapsed time,
versions, and cleanup state. They omit prose, inventory values, credentials,
headers, raw bodies, and raw errors. Expected policy refusals are not alerts.
Repeated internal error, an indeterminate create, permission drift, a canary
hit, or missing readback after confirmed create wakes the named operator.

## 9. Boundaries, per capability

| Boundary | Capability | Control |
| --- | --- | --- |
| Agent to socket | one issue request | fixed socket and peer policy; one bounded canonical frame; no paths |
| Request to policy | queue, prose, labels, inventory | code-owned rules over exact final bytes |
| Records to admission | judgement and lint outcomes | closed subjects, fixed order, digest chain, executable reruns |
| Service to signer | JWT signing input | post-admission call; fixed key, executable, argv, stdin, output, timeout |
| Service to GitHub | token and final bytes | fixed host, repository, routes, permission, one POST, bounded readback |
| Service to caller | terminal result | closed content-free schema and byte cap |
| Repository to live Mac | identity, key, socket, service, helper | privileged verifier and separate deployment receipt |
| Worktree to PR | authored code | Shoggoth author; Dr Laurence E. Day committer, signer, publisher; independent review |

The client receives no general key, signer, token, file, network, subprocess,
or GitHub mutation capability. Root and direct PEM access remain outside scope.

## 10. The budget, or its absence

No speed improvement is claimed. Design metrics count trusted processes and
privileged action classes. Initial safety caps are one active request, 1 MiB
per frame, 256 KiB per body stage, 256 title bytes, 64 protected items, 16
labels, 256 JSON members, depth 8, 4,096 response bytes, 8,192 remote response
bytes, 5 seconds for signing, 15 for token exchange, 20 for create, 10 per
readback, and 60 total. Raising a cap or adding concurrency or retry requires a
study amendment or new decision.

## 11. The fail-closed posture

Any socket, peer, frame, text, schema, cap, repository, operation, queue, label,
opening, inventory, stage, version, digest, order, outcome, or authority fault
refuses before key access. Imprimatur load, timeout, output, parse, binding, or
finding failure also refuses before key access.

Signer, token, destination, redirect, permission, expiry, or response failure
refuses before POST. A create is attempted once. Unknown outcome returns
`create-indeterminate` for operator reconciliation. Failed readback returns
created-but-unverified without editing or deleting the issue. Cleanup runs on
every terminal path and makes no process-memory-erasure claim.

Each confirmed defect gets a parent-red and fixed-green guard. Elenchus owns
implementation failures. The source-bound runner is
`python3 plugins/hexaemeron/tests/run_tests.py {report}`; the runbook must read
its current schema rather than copy the donor's old report-version claim.

## 12. Decisions and their homes

The selected `isolated-publisher` design is locked by
`.hexaemeron/design-evidence.json`. Its reason belongs in the numberless draft
`docs/decisions/drafts/use-a-credential-owning-github-issue-publisher.md`, with
stable identity `adr/use-a-credential-owning-github-issue-publisher`. Step 1
creates that complete draft before running the Hypomnema bridge check. ADR-077
assigns its number only against the final integration base.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | isolated-publisher
record | docs/decisions/drafts/use-a-credential-owning-github-issue-publisher.md
```

The Phylax reference owns the request, receipt, refusal, queue, signer,
transport, readback, cleanup, and deployment contracts. Its code owns policy;
fixtures own counterexamples; the deployment reference owns install, rollback,
and live verification. Phylax receives one generation after the integration
base is known while its mature frontier stays fixed.

Root `AGENTS.md` routes App issue creation through the checked service and
states that prose rules and hooks are diagnostic until deployment. Direct token
variables and token-only mode are forbidden. Their removal from a live host is
a privileged deployment transition. Final proof must distinguish offline
component, deployment-kit, and live-isolation evidence.
