# Earned proof-backed state

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

This example shows how Alexandria earns `proof-backed-state` at verification
time. Its capture component is an unchanged Lazarus manifest. The other release
components supply every fixture file the manifest names, matched by digest and
byte count. Alexandria reconstructs that fixture outside the read-only release,
reruns Lazarus's offline verifier, and binds the capture to the proved block and
targets.

The embedded six-file fixture is synthetic. It proves nothing about any real
chain. Its capture uses finality `unknown` because Lazarus proves block binding
but reports no finality class. Its scope is subject-scoped and stays within the
fixture's proof targets because a finite proof set is not a full dataset. If
Lazarus or its pinned packages are unavailable, verification refuses because a
proof-backed claim is not earned until Lazarus has rechecked it.

Install the sibling verifier's pinned packages, then verify the checked-in
release from the repository root:

```bash
python3 -m pip install --requirement plugins/lazarus/requirements.lock
python3 plugins/alexandria/scripts/alexandria.py verify \
  plugins/alexandria/examples/proof-backed-state-v0/release
```

The command prints
`sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f`.
A refusal names the `state-proof` capture and the failed mapping or binding.
