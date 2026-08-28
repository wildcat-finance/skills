---
name: phylax
description: >-
  Harden the off-chain surface: the Python that harvests, indexes, replays and
  releases, the commands it shells out to, the URLs it fetches, the secrets it
  holds, the dependencies it pulls, and the model output it acts on. Use when a
  step accepts data from outside the process, runs a subprocess, fetches a URL,
  reads a credential, adds a dependency, or feeds an agent. Do not use it to
  review Solidity, which belongs to solidity-auditor and x-ray, and do not use
  it to diagnose a failure that has already happened, which belongs to
  elenchus.
metadata:
  version: "1.3.0"
---

<p align="center">
  <img src="../../assets/characters/phylax.png" width="1200">
</p>

# Phylax

From *phylax*, the guard posted at a boundary. The guard's job is not to trust
the traveller more carefully. It is to check papers at the line, every time.

## Where this sits

Phylax owns the off-chain surface in all three shapes it takes here. Python
tooling: harvesters, indexers, release builders, replay servers, the controller
and the agent skills. A TypeScript application: Next.js routes, Prisma against
Postgres, rendered markdown, sessions and wallet connection. A long-running
service that holds a signer and submits transactions.

Fiat and Mason apply it during implementation. Warden reruns its mechanical
gate in non-Solidity audit rounds. The Pashov suite owns Solidity review;
Elenchus owns an observed failure; Ephoros owns retained telemetry. Phylax may
constrain those siblings' off-chain tooling but never claim their result.

Synkrisis is specified to compare already validated run observations. Its
current scaffold writes nothing, and neither it nor a future finding may cross
an off-chain boundary, expose protected data, or authorise a control change.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Current state.** Phylax mechanically checks its established Python boundaries and source-local TypeScript controls for raw HTML ordering, persisted session credentials and runtime-selected absolute fetch hosts. This frontier is mature.

## Name the boundaries before choosing controls

A control chosen before its boundary is named is a guess that happens to
compile. Spend five minutes as the attacker first.

Name the boundaries first: an RPC endpoint, a preserved capture, a venue
record, a third-party archive, a dependency, a subprocess, model output, an API
route, a session cookie, a rendered document and a signer. Then name what is
worth taking: key material, RPC and database credentials, a session, the
integrity of a release digest, and the ability to make something run a command
or sign a payload.

Then run STRIDE across each boundary as a lens, not a ceremony:

| Threat | Ask | Mitigation |
| --- | --- | --- |
| Spoofing | Can something pose as the source? | Pin the endpoint, verify the digest |
| Tampering | Can the bytes change on the way in? | Content addressing, proof checks |
| Repudiation | Can a step deny what it did? | Receipts, hash-chained ledger |
| Disclosure | Can a secret escape? | Keep it out of logs, argv and errors |
| Denial | Can input exhaust the run? | Size caps, timeouts, bounded loops |
| Elevation | Can input reach a command? | Argument lists, allowlists, no shell |

Write the abuse case next to the use case, then make it the first test. A
boundary you cannot name is a boundary you have not secured. Feed the result
into the study's risk register, which is where the audit loop reads it.

## Always, ask first, never

**Always.** Validate external data at the point it enters the process. Pass
subprocess arguments as a list. Pin every dependency to an exact version. Keep
credentials in the environment. Fail closed when a check cannot be completed.

**Ask first.** Adding a dependency. Widening a trust boundary. Fetching from a
host that was not fetched from before. Writing outside the state directory.
Granting an agent a new tool. Relaxing a proof check to make a run finish.

**Never.** Commit a key, a mnemonic or an RPC credential. Log one, or put one
in a command line where the process table can read it. Build a shell string
from external data. Pass model output to a shell, an eval, a query or a file
path. Weaken a verification step to get past a failure.

## Everything from outside is hostile

An RPC response, a preserved capture, a venue record, a downloaded archive and
a model reply are all data from outside the process. Each gets checked at the
boundary rather than trusted because of where it came from.

Check the shape before reading fields, and reject rather than coerce. Cap the
size of anything read into memory, and the time spent reading it. Parse JSON
with the standard library parser, never with `eval`. And never unpickle what
arrived from outside: unpickling is arbitrary execution by design.

Ariadne already carries `tests/test_untrusted_input.py` for exactly this. A new
ingestion path without an equivalent test is unfinished.

## Never fetch a URL you were handed

Anywhere the tooling fetches a host the operator supplied, an attacker can aim
it inward. The cloud metadata address is the usual target, and an RPC URL from
a config file is a supplied host.

```python
import ipaddress, socket
from urllib.parse import urlparse

ALLOWED = {"mainnet.example.org"}

def checked(raw: str) -> str:
    u = urlparse(raw)
    if u.scheme != "https" or u.hostname not in ALLOWED:
        raise ValueError("host not allowed")
    for *_, sa in socket.getaddrinfo(u.hostname, 443):
        if not ipaddress.ip_address(sa[0]).is_global:
            raise ValueError("resolves to a reserved address")
    return raw
```

The check has a gap worth stating: the name resolves again when the connection
opens, so a short record can move between the check and the connect. Where that
matters, resolve once and connect to the pinned address.

## Subprocesses and paths

This marketplace shells out in dozens of places, to `git`, `gh`, `forge` and
the fuzzers. Every one of those is a command boundary.

Pass arguments as a list and leave the shell out of it. A path or ref that came
from outside gets validated before it becomes an argument, because a ref
beginning with a dash is an option, not a name.

Paths derived from external data need the same care. A digest is safe to build
a path from once you have checked it is a digest; a filename from an archive is
not. Resolve the result and confirm it is still inside the directory you meant.

## Secrets

Credentials live in the environment, never in source, and the repository
already ignores the files that would carry them. Check before committing:

```bash
git diff --cached | grep -iE "private[_-]?key|mnemonic|secret|api[_-]?key|token"
```

A secret that reaches a remote is compromised from that moment. Rotate first,
then clean the history. Removing the line is not a remedy, and neither is a
force push, because the object survives in clones and caches.

Keep secrets out of logs, out of exception messages and out of argv. An error
that prints the request it failed on prints the credential in the header.

## Dependencies

Lazarus pins its four runtime dependencies to exact versions, and everything
else in this marketplace runs on the standard library. That is the house
default: reach for stdlib, and pin exactly when you cannot. The applications
carry a committed lockfile instead, and CI installs from it rather than
resolving afresh.

Installing a package executes its code. Review a new dependency for ownership,
release age, maintenance and the transitive graph it drags in, and read the
lockfile diff in the same review as the code that needed it. Names that differ
from a popular package by one character are the oldest trick still working.

Never let a tool apply forced remediation on its own. An audit reports known
advisories; it does not establish that a package is honest, nor that the
reported code is reachable. When you defer a finding, record why and set a date
to look again.

## Model output is untrusted input

This marketplace ships agent skills, so the model is inside the trust boundary
by construction. Treat what it returns exactly as you treat a web response.

Never pass model output into a shell, a query, an `eval` or a file path without
validating it first. Assume text arriving in a context window carries
instructions: a fetched page, an error message, a venue record, a comment in a
file. A system prompt is not a security control, so enforce permissions in code
where they can be tested.

Scope an agent's tools to the job and require confirmation before anything
irreversible. Bound what a crafted input can spend by capping tokens, requests
and recursion depth. Keep credentials and unrelated data out of the context in
the first place, because anything in there can come back out.

## The application and the service

**Rendered markdown is attacker input.** Borrower profiles, agreements and
notes arrive as markdown and render through `react-markdown`. `rehype-raw`
passes raw HTML through, so `rehype-sanitize` runs after it rather than instead
of it. Every `dangerouslySetInnerHTML` needs a sanitiser on its value and a
line saying which one.

**Session tokens belong in cookies.** A JWT goes in an httpOnly, secure,
sameSite cookie. `redux-persist` writes where scripts can read, so no token,
signature or credential belongs in a persisted slice.

**The policy already exists.** A CSP report route means a policy is enforced.
Widening it to `unsafe-inline` so a component renders trades the reporting away
and gets nothing back.

**Authorisation runs per route, on the server.** A connected wallet proves
control of an address and nothing more. Each route re-checks what that address
may do, because middleware ahead of a route is not a check inside it.

**Queries stay parameterised.** Prisma parameterises by default, `$queryRaw` is
the way out, and there are none today. Keep it that way, and let row-level
policy rather than a published anon key decide what Supabase returns.

**Signing is not a formality.** Show what is being signed, check the chain
before submitting, and simulate a transaction whose failure costs money. Never
put a payload in front of someone who cannot read it.

**A signer in a long-running process is a custody boundary.** Dry-run flags
exist because the wrong run moves money. Keep the key out of the process
manager's logs and saved environment, and make submission idempotent so a
restart does not send twice.

**Analytics see whatever the user sees.** Session recording ties behaviour to a
connected address, which is the linkage the next section refuses.

## Personal data

The application holds personal data whatever the chain does. Borrower names,
profiles, invitations and anything an analytics tool records are personal data,
and the cheapest record to protect is the one never collected.

Classify a field as you add it, because you cannot protect or erase what you
cannot find.

| Class | Examples | Handling |
| --- | --- | --- |
| Not personal | Aggregates, counts with no subject | Ordinary |
| Personal | Name, email, IP, device or account id | Minimise, restrict, include in export and deletion |
| Sensitive | Financial detail, location, government id | Stricter access, encryption at rest, access logged |

Collect a field against a stated purpose. "It may be useful later" is not a
purpose; it is breach scope acquired early. Give every store of personal data a
retention limit and a deletion path that actually runs, including backups,
caches, search indexes and analytics copies. Data with no expiry is an incident
scheduled for a later date.

Support export, correction and deletion where the jurisdiction requires them.
These are schema decisions rather than legal ones: design so that one subject's
data can be found and removed, instead of smeared across systems that each know
a little. Get consent before collection and before sharing, and keep it
auditable. Sending personal data to an analytics, advertising or model vendor is
sharing, the user's choice gates it, and the vendor needs an agreement covering
what it may do with it.

Do not hard-code one region's rules. Residency and obligations vary with where
the user is, so make the policy a boundary that can be configured rather than
an assumption baked into a query.

## Addresses are pseudonymous, not anonymous

This marketplace holds no user accounts, so the privacy question here is not
consent forms. It is linkage. Combining a declared address with timing, funding
paths and off-chain sources can identify a person, and Probitas forbids exactly
that.

Do not build the linkage accidentally. A cache that pairs addresses with
resolved names, a log that records who asked about which address, or a release
that joins declared holdings to an external profile each creates the thing the
marketplace refuses to produce. Keep only what the source supports, and say
what could not be established.

The one address rule that is telemetry shape rather than boundary control
belongs to ephoros, and
[ADR-010](../../../../docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md)
draws that line once, over the same TypeScript files both lints read.

## The mechanical subset

Eight of these rules are settled by a parser rather than by reading. Run the
lint over the paths a step touched, and require exit 0.

```bash
python3 "$PLUGIN_ROOT/skills/phylax/scripts/phylax.py" src tests
```

For Python and requirements files it reports a shell invocation, a subprocess
command passed as a string rather than an argument list, a requirement with no
exact pin, a credential in source, in command arguments or handed to something
that writes output, and import-resolved unsafe deserialization or dynamic
execution.

The last rule resolves module and direct-import aliases for `pickle.load`,
`pickle.loads`, `marshal.load`, `yaml.load`, and `builtins.eval` or
`builtins.exec`; bare `eval` and `exec` are also inside the grammar. A
`yaml.load` call stays clean only when its second positional argument or
`Loader=` value resolves directly to `SafeLoader` or `CSafeLoader`. An `eval`
or `exec` call stays clean only when its first argument is an inline string or
bytes constant. The parser does not follow assignments, prove input
provenance, inspect custom loader classes or include `marshal.loads`.

For tracked `.ts` and `.tsx` source it reports three source-local cases. A
`rehype-raw` binding in a rendered plugin array needs a later
`rehype-sanitize` binding, and a raw-named `dangerouslySetInnerHTML` value needs
a sanitiser imported from `sanitize-html`, `dompurify` or
`isomorphic-dompurify`. A `sessionToken`, `authToken`, `accessToken`, `jwt` or
`bearer` value cannot reach Web Storage or an unfiltered `persistReducer`. A
visibly absolute URL built from a runtime host cannot reach global `fetch`
until a same-scope named allowlist guard dominates it. Relative, same-origin,
fixed-host and source-opaque `fetch(url)` calls stay outside that claim.

The TypeScript recognisers use an attributed copy of Horos's lexer inside
Hexaemeron. They never import a separately installed Horos plugin, invoke Node,
load the target's dependencies or execute inspected source. A lexical construct
that cannot be terminated reports `P000`. The lint reads at most 1 MiB from
each TypeScript file and reports `P000` when that limit is exceeded, bounding
the lexer work before it accepts untrusted source.

Deliberate exceptions state a reason: `# phylax: allow <why>` in Python or
`// phylax: allow <why>` in TypeScript, on the line or the one above it. A bare
pragma with no reason does not suppress anything. Test material shaped like a
credential is the usual honest case, and a lint with no pragma to answer it is
a lint people learn to bypass.

Everything else in this skill stays judgement, and a clean exit says only that
these eight found nothing.

## Rationalisations

- "It is internal tooling." Internal tooling holds the RPC credential and
  writes the release everyone else trusts.
- "We will harden it later." The boundary is cheapest to place while the code
  that crosses it is still being written.
- "Nobody would attack this." Scanners are indiscriminate, and the metadata
  address is tried against everything.
- "It is a prototype." Prototypes acquire users and keep their defaults.
- "The library handles it." Libraries supply the control and leave its
  correct use to you.
- "It is only model output." That text can be a command, a path or a query.
- "The audit passed, so the dependency is fine." Audits match known
  advisories, and a new malicious package matches none of them.

## Red flags

- External data reaching a shell, a query or a file path unchecked.
- Shell strings built by formatting.
- A credential in source, in a log line, or in a command's arguments.
- Fetching a host the operator supplied, with no allowlist.
- A dependency added without a pin, or a lockfile diff nobody read.
- Model output used as a command, a path or a query.
- Relaxing a proof or digest check to make a run complete.
- Raw HTML rendered from user markdown with no sanitiser after it.
- A session token in local storage, or in a persisted store slice.
- A signing prompt whose payload the user cannot read.
- Personal data collected with no stated purpose, retention limit or deletion path.
- Personal data sent to an analytics or model vendor with no consent and no agreement.
- A deletion that flips a flag while the data stays in stores and backups.
- An ingestion path with no test that feeds it something malformed.

## Before the step is receipted

Report the count, then name every item that failed.

- [ ] Trust boundaries for this step are named, and each has a control.
- [ ] External data is validated where it enters, with size and time caps.
- [ ] Subprocess arguments are lists, and no shell string is built from data.
- [ ] Supplied hosts are allowlisted and checked against reserved ranges.
- [ ] Paths built from external data resolve inside their intended directory.
- [ ] No credential appears in source, logs, errors or argv.
- [ ] New dependencies are pinned, reviewed, and their lockfile diff read.
- [ ] Model output is validated before it reaches a command or a path.
- [ ] Rendered markdown is sanitised after any raw-HTML step.
- [ ] New personal-data fields are classified, purposed and given a retention limit.
- [ ] Deletion and export reach backups, caches, indexes and analytics copies.
- [ ] No session token or credential reaches persisted client storage.
- [ ] Each route checks what the authenticated address may do, not just that it connected.
- [ ] A signer in a long-running process is dry-run first and idempotent on retry.
- [ ] The malformed-input test for each new ingestion path exists and passes.

## Hand back

Lead with the state: hardened against the boundaries you named, or open on a
named gap. List the boundaries this step introduced and the control on each.

Say which controls you verified and which you only added. A control with a test
that feeds it hostile input is established; one that merely exists is asserted.
Name what you could not check and why.

End with one action: the boundary that still needs a control, the review a
dependency needs, or the approval a widened trust boundary is waiting on.

## Promise Machine contract

### phylax-mechanical-gate

- Promise: A zero-exit Phylax lint establishes that the bounded parser found none of its specified external-input, subprocess, fetch, secret, path and model-output patterns in the selected first-party paths.
- Evidence: The exact lint version, arguments, selected paths, structured findings and zero exit status.
- Evidence classes: checked
- Boundary: A clean lint covers only the rules and languages implemented by the parser; it is not a security review, a dependency audit, a privacy assessment or evidence that a control works against hostile input.
- Authorises: Passing the mechanical Phylax gate for the exact paths and checker version recorded.
- Consequence: 1
- Refuses: Unsafe paths, unreadable or oversized input, an unexplained suppression, a non-zero result or any claim about a rule the parser does not implement.
- Recovery: Correct the input or control, add a narrowly reasoned suppression only when the rule is inapplicable and rerun the same bounded lint.
- Exceptions: none

### phylax-boundary-review

- Promise: A completed boundary review establishes that every trust boundary introduced by the step is named, paired with a control and classified as verified or merely asserted, with unresolved exposure left visible.
- Evidence: The step diff, boundary inventory, hostile-input tests where available, dependency and lockfile review, sample output review, unresolved-gap list and reviewer conclusion.
- Evidence classes: checked, inferred, recorded
- Boundary: The review is scoped to the introduced boundaries and available evidence; it does not establish whole-system security or convert an asserted control into a verified one.
- Authorises: Proceeding with the reviewed step only to the consequence level supported by its verified controls and explicitly accepted open gaps.
- Consequence: 2
- Refuses: An unnamed boundary, unvalidated external data, data-built shell strings, unsafe host or path handling, exposed credentials, unreviewed dependency drift or model output used directly as authority.
- Recovery: Name the missing boundary, add and exercise its control, review the affected dependency or data path and repeat the boundary review.
- Exceptions: none
