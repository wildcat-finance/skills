# Issue 386: record a structured multi-provider chain anchor

## Step 1, round 1 -- 2026-08-25

Non-Solidity round over commit
`d917f41034743cb9d27db5e2da6eb27319f59ffb` on
`fiat/386-record-a-structured-multi-provider-chain-anc-step-1-define-the-anchor-formats`
against parent branch `fiat/386-record-a-structured-multi-provider-chain-anc`
at `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. Security receipt:
`waived: issue 386 changes Lazarus Python, JSON schemas, tests, and documentation; no Solidity or Pashov security-suite target applies`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

Zero findings. The review covered all 16 changed paths against Step 1 at
effective SHA-256
`d861773977ffd121ac84e8b1da8b0e160396d1951869e3888293c0ab92f643a6`
and the risk register in `.hexaemeron/study.md` at SHA-256
`f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd`.
Plan v2 retains the complete plan-v1 shape and adds only 1 to 32 sorted, unique
source identifiers. Anchor records are closed, bounded, schema-digest-pinned,
UTC-checked, source-sorted, and source-unique; neither plan nor record admits a
provider URL, header, raw error, independence claim, or canonical-chain claim.
The temporary capture guard refuses plan v2 before client construction or
staging. The tracked study and runbook match the receipted bytes, and existing
manifest and release schemas are unchanged.

The focused schema, record, scaffold, and runner set reports 61/61. The source-
owned runner reports 386/386 Lazarus tests, and the root suite reports 350/350.
Phylax exits 0 over `plugins tests`; Ephoros exits 0 over `plugins tests`;
Hypomnema exits 0 over `README.md AGENTS.md .agents plugins docs`.

Leads not pursued: live provider disagreement, runtime secret scanning, shared
network budgets, atomic multi-provider finalisation, digest-bound one-read
verification, exact plan-to-record coverage, and anchored release compatibility
are not reachable in this format-only step. Step 1 refuses plan-v2 capture;
Steps 2 and 3 own those transitions. These remain required risk-register
checks, not accepted risks.

## Step 2, round 1 -- 2026-08-25

Non-Solidity round over implementation range
`5529225625e407d93563c67729206d2e0f260518..1a49a3c6cf865641e2a0abdad3a05d7de0623fb8`
on `fiat/386-record-a-structured-multi-provider-chain-anc-step-2-verify-anchor-records-offline`.
Security receipt: `waived: issue 386 changes Lazarus Python, JSON schemas, tests, and documentation; no Solidity or Pashov security-suite target applies`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

### Review

Zero findings. The review covered all 10 changed paths against Step 2 at
effective SHA-256
`6c3ee49bbf158ff32148cc6c4be5c188605f400bc1f1b45a9593feda2b39531c`
and the risk register in `.hexaemeron/study.md` at SHA-256
`f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd`.
After manifest verification, `anchors.jsonl` receives one digest-bound semantic
reread through `_read_bound`; `read_confined_bytes` supplies no-follow, size,
and stable-file controls. Schema and record checks refuse malformed, duplicate,
or reordered records. Plan and record source sets must match exactly, and chain,
height, or verified-header disagreements fail closed. The report adds only
`chain_anchors: {records: N, canonical_chain_claim: false, provider_independence_claim: false}`;
`proof_backed`, `header_bound`, and `recorded_rpc` stay unchanged. Release-v1
and the Ariadne-facing binding keep their structure while their component
inventory binds `anchors.jsonl`.

### Verification

The focused set reports 217/217. The Lazarus suite and source-owned structured
runner each report 399/399. The root suite reports 350/350, and its 1,258-case
inoculation reports 0 crashes and 0 unexpected clean results. Goldfinch verifies
at fixture digest
`d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49`;
the preservation-release demonstration exits 0 with both refusals held.
Phylax, Ephoros, Hypomnema, and `git diff --check` each exit 0.

Leads not pursued: runtime provider-secret handling, live provider identity,
shared network and resource budgets, and atomic multi-provider finalisation are
not reachable in this offline verification step. Step 3 owns those controls;
they remain required risk-register checks, not accepted risks.

## Step 3, round 1 -- 2026-08-25

Non-Solidity round over implementation range
`accc7a668d96cfd1c0888e371540880609031c7f..1a09fff1025be8c08cc0452394fd444884b1e966`
on `fiat/386-record-a-structured-multi-provider-chain-anc-step-3-capture-and-demonstrate-anchors`.
Security receipt: `waived: issue 386 changes Lazarus Python, JSON schemas, tests, and documentation; no Solidity or Pashov security-suite target applies`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |

### Review

Zero findings. The review covered all 21 changed paths under packet state
SHA-256 `e9dededc968db34a6f08b4d00ec6e9a822d1bbb5b4ff4475d6b2040ce4a056e8`,
study SHA-256
`f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd`,
and runbook SHA-256
`d5c13e5d5181a2699c39709218eebdcc4635f71092afeb713f64eed19afb8e52`.
It checked provider secrets and sanitised failures; provider-identity and
canonicality non-claims; exact mapping and record coverage; chain, height and
hash disagreement; shared request, response-byte, component-byte, total-byte
and elapsed-time limits; staged cleanup and atomic finalisation; schema and
Promise Machine digest currency; digest-bound one-read verification; release
compatibility; source ordering; UTC timestamps; and the unchanged single
`lazarus-v1.2.0` ledger row.

### Verification

The focused set reports 59/59, Lazarus 414/414, and root 350/350. Root
inoculation reports 1,258 cases, 0 crashes and 0 unexpected-clean results. A
fresh structured runner report records 414/414, 0 failures, 0 errors and 0 skips
at SHA-256
`0627faff75343a2329c7ef2c78b8a33229b89ddd8eff04a15b3fe4ed92a7b143`.
The anchored fixture verifies at
`188eb293ac1de8036ff4be861e339fe5757b51995c88e8ea1afcfa498134a72e`,
Goldfinch remains
`d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49`,
and the release remains
`1a86ed8f3d7df99aa696c01ce9ba4219bb6d9472b23ff4d0094a4b5e8ad11aa8`.
Promise Machine checks are clean over 14 plugins and 14 copies. Phylax,
Ephoros, Hypomnema and `git diff --check` each exit 0. No fixes commit exists;
the Elenchus audit-fix verdict is null.

Leads not pursued: none.
