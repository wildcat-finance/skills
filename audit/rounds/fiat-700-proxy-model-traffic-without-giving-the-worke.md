## Step 1, round 1 -- 2026-08-28T06:17:48Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=not-applicable; frame-exhaustion=not-applicable; schema-smuggling=not-applicable; credential-crossing=not-applicable; origin-confusion=reviewed; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=reviewed; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=reviewed; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 1 produces no Solidity; guest framing, live credentials, DNS and TLS, redirects, provider transport and responses, quota concurrency, cancellation, runtime expiry, durable receipts, and cleanup belong to Steps 2 through 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, native Windows, and a slow remote regular filesystem were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/canonical.py | The bounded reader opened an accepted-job candidate before checking its file kind without nonblocking mode, so a FIFO with no writer held activation indefinitely instead of refusing with `MP100`. | fixed in this commit; FIFO timeout guard parent-red and fixed-green |
| S1-R1-02 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy.py | Argument parsing ran outside the value-free diagnostic boundary, so an unknown option echoed its supplied value, including the synthetic credential canary, in free-form stderr. | fixed in this commit; no-echo and exact-option guard parent-red and fixed-green |
| S1-R1-03 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/canonical.py | The exported canonicalizer called `.encode()` on a non-string object name and leaked an `AttributeError` traceback instead of returning the bounded wrong-scalar refusal. | fixed in this commit; non-string-key guard parent-red and fixed-green |

Leads not pursued: POSIX nonblocking mode prevents special-file open hangs but does not impose a wall-clock deadline on reads from a slow regular filesystem; no remote-filesystem input profile exists in this component, so the trusted local supervisor boundary remains explicit rather than claiming a time bound it does not enforce. Repeated `--accepted-job` or `--expect` options still use argparse's last value; no untrusted argv merger or supervisor adapter exists in Step 1, and #702 owns construction of that fixed trusted invocation. Policy compilation validates the accepted expiry and duration but does not compare expiry with the current clock; Step 4 owns activation-time and per-admission wall and monotonic expiry enforcement. The synthetic accepted-job evidence is not a signed #698 acceptance receipt, the loopback profile makes no live provider call, and the provider non-exfiltration limitation remains explicit.

## Step 1, round 2 -- 2026-08-28T07:13:17Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=not-applicable; frame-exhaustion=not-applicable; schema-smuggling=not-applicable; credential-crossing=not-applicable; origin-confusion=reviewed; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=reviewed; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=reviewed; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 1 produces no Solidity; guest framing, live credentials, DNS and TLS, redirects, provider transport and responses, quota concurrency, cancellation, runtime expiry, durable receipts, and cleanup belong to Steps 2 through 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, native Windows, and a slow remote regular filesystem were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: POSIX nonblocking mode prevents special-file open hangs but does not impose a wall-clock deadline on reads from a slow regular filesystem; no remote-filesystem input profile exists in this component, so the trusted local supervisor boundary remains explicit rather than claiming a time bound it does not enforce. Repeated `--accepted-job` or `--expect` options still use argparse's last value; no untrusted argv merger or supervisor adapter exists in Step 1, and #702 owns construction of that fixed trusted invocation. Policy compilation validates the accepted expiry and duration but does not compare expiry with the current clock; Step 4 owns activation-time and per-admission wall and monotonic expiry enforcement. The synthetic accepted-job evidence is not a signed #698 acceptance receipt, the loopback profile makes no live provider call, and the provider non-exfiltration limitation remains explicit.

## Step 2, round 1 -- 2026-08-28T08:33:34Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=not-applicable; origin-confusion=not-applicable; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=not-applicable; provider-exfiltration=not-applicable; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 2 produces no Solidity; live credentials, DNS, TLS, HTTP, redirects, provider-native requests and responses, atomic quotas, concurrency, cancellation, runtime expiry, durable receipts, secret-echo checks, and terminal cleanup belong to Steps 3 and 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, arbitrary code inside the trusted proxy process, and concurrent calls into the ordered-stream parser were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | Frame activation trusted equality among caller-replaceable `CompiledPolicy` fields. Replacing both JobSpec digest fields and recomputing the public policy bytes and digest produced a self-consistent substituted policy that `FramingCore` accepted without replaying compiler input. | fixed in this commit; accepted-evidence replay guard parent-red and fixed-green |
| S2-R1-02 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | `TextRequest._owner` was returned inside a public dataclass and survived `dataclasses.replace()`. In the reproducer, a copied request selected an issued sequence and one issued object emitted repeated responses, so response authority was neither exact-object nor one-shot. | fixed in this commit; copied-request and repeated-response guard parent-red and fixed-green |
| S2-R1-03 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | The exported `check_framing_manifest(None)` path passed the wrong scalar type into `Path` and leaked a raw `TypeError` instead of returning the fixed content-free `MP218` refusal. | fixed in this commit; invalid-path guard parent-red and fixed-green |

Leads not pursued: replay establishes that the frame policy matches the captured accepted-job evidence, not that #698 signed it or that #702 supplied it through the trusted supervisor channel. The Python objects remain a trusted-process interface rather than a sandbox against arbitrary code already executing inside the proxy; #699 must keep the guest behind the serialised frame channel. `FramingCore.feed` assumes the abstract ordered stream serialises calls and makes no thread-safety claim. Aggregate quotas, output reservation, cancellation, expiry, receipt durability, and cleanup remain Step 4 work rather than framing claims.

## Step 2, round 2 -- 2026-08-28T09:09:03Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=not-applicable; origin-confusion=not-applicable; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=not-applicable; provider-exfiltration=not-applicable; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 2 produces no Solidity; live credentials, DNS, TLS, HTTP, redirects, provider-native requests and responses, atomic quotas, concurrent calls, cancellation, runtime expiry, durable receipts, secret-echo checks, and terminal cleanup belong to Steps 3 and 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, and arbitrary code inside the trusted proxy process were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | The core accepted any exact unconsumed issued request, so after one concatenated read a caller could encode sequence 2 before sequence 1. That reordered responses and supplied the multiplexing the Step 2 exit says is unavailable. | fixed in this commit; admission-order response guard parent-red and fixed-green |

Leads not pursued: the three round-1 policy-replay, one-shot request-object, and invalid-manifest-path failures remain guarded on this tree. Replay establishes that the frame policy matches the captured accepted-job evidence, not that #698 signed it or that #702 supplied it through the trusted supervisor channel. The Python objects remain a trusted-process interface rather than a sandbox against arbitrary code already executing inside the proxy; #699 must keep the guest behind the serialised frame channel. Thread-safe admission and response scheduling, aggregate quotas, output reservation, cancellation, expiry, receipt durability, and cleanup remain Step 4 work rather than framing claims.
