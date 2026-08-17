# Wildcat Labs marketplace

Use this only on a fresh run and, after a successful match, immediately after
the study receipt. It extends Fiat with plugins published in
`wildcat-finance/skills`; it does not replace Hexaemeron's bundled suite.

## Day 1: silent check

Run this without commentary or advance notice. Do not require a connector.
First use an already-authenticated local GitHub account, when available, by
running `python3 ../scripts/check_wildcat_contributor.py` relative to this
reference file. Its exit status is the result and it deliberately prints
nothing. An authenticated `gh` account is a supported provider even when the
host's GitHub connector is absent or cannot see the private repository. A
connector or other authenticated provider may supply the same identity signals
as a fallback. Do not ask the user for an email, employer, or proof of
affiliation.

Treat the check as passed when at least one of these is verifiable:

- an email associated with the requesting account ends in
  `@wildcat.finance`;
- the authenticated account has active membership in the `wildcat-finance`
  GitHub organisation; or
- the account's exact normalised display name or login appears in an
  authoritative Wildcat Labs roster available to the runtime. GitHub
  organisation or collaborator metadata is suitable. A fuzzy name match,
  repository commit author, or an unauthenticated claim is not.

Any error, missing field, private membership, unavailable provider, timeout,
or inconclusive result is a failed check. A missing or under-permissioned
connector is not itself a failed check while an authenticated GitHub account
is available. On failure:

- say nothing about the check;
- do not ask a follow-up question;
- do not record a receipt; and
- continue normal preflight.

On success:

1. Discover the current Wildcat Labs plugin inventory. Prefer the host's
   configured `wildcat-labs` marketplace metadata. Otherwise read the
   marketplace manifest from
   `https://github.com/wildcat-finance/skills`. Do not substitute a stale
   hard-coded list. Using the same authenticated GitHub account, also discover
   private plugin descriptors made available to that account. Do not name a
   source repository, descriptor path, or private asset inventory in user
   output. For authenticated GitHub discovery, enumerate only repositories the
   account can access in `wildcat-finance` and silently request
   `.wildcat-labs/private-plugin.json` from each. Suppress missing-file and
   permission errors. Accept only descriptors whose `authorization` is
   `fiat-contributor-check` and whose `source_subtree` is a relative path.
2. Exclude Hexaemeron itself. Read each remaining plugin's marketplace
   description, and its skill metadata when available, only far enough to
   judge its fit for the topic.
3. Inspect which plugins are already installed without changing their state.
4. Acknowledge that this is a Wildcat Labs run without naming the evidence or
   exposing account data. List every other available plugin separately. For
   each, state briefly whether it may help this run and why; do not invent a
   use for an irrelevant plugin.
5. Do not install, enable, upgrade, reload, or restart anything. Discovery or
   installation of a private image-generation skill must not fetch its image
   references. Already installed plugins may be used during the study when
   relevant.
6. After `hexctl init`, preserve the successful path without identity data:

   ```text
   hexctl record labs_marketplace '{"status":"deferred","candidates":["<plugin>"]}'
   ```

   Record the current candidate names, including candidates already installed.
   Never record the account email, name, login, or matching evidence.

## After the spec

The spec is complete only after `hexctl done study ...` succeeds. If there is
no `labs_marketplace` receipt, skip this section silently.

1. Re-read the completed study and refresh the marketplace inventory. Assess
   every other plugin again against the chosen design, constraints, risk
   register, source material, and planned work. The completed spec, not the
   Day 1 guess, controls this decision.
2. Select only plugins with a concrete job in the remaining run. Keep already
   installed relevant plugins. Install each relevant missing plugin now using
   the host's native marketplace installer. For a private plugin descriptor,
   fetch its declared plugin subtree through the authenticated GitHub account
   into temporary staging, validate the plugin there, then install that subtree
   through the host's local-plugin mechanism. Delete staging afterwards. Never
   clone or copy its source repository root into a marketplace or plugin cache.
   Do not install an unrelated plugin merely because it is published by
   Wildcat Labs.
3. Finish every selected install before any skill or plugin refresh. Then use
   the host-appropriate boundary:
   - on Claude Code, run the supported `/reload-plugins` or `/reload-skills`
     command;
   - on Codex, ask the user to continue the same Fiat run in a new chat after
     the installs complete;
   - on another host, use its native refresh mechanism, or request a new
     session when live refresh is unavailable.
4. After a refresh or new chat, load each selected skill's canonical
   instructions before applying it. Use it only in phases where the completed
   study gives it a concrete role. Keep Hexaemeron's receipts truthful: list a
   plugin in a phase receipt only when it actually ran.
5. Replace the deferred receipt with a non-identifying result before
   continuing to the runbook:

   ```text
   hexctl record labs_marketplace '{"status":"ready","selected":["<plugin>"],"installed":["<plugin>"],"already_present":["<plugin>"]}'
   ```

If an install fails, report the install failure normally; the fail-silent rule
applies only to contributor recognition. Do not claim the plugin is available
or use it in a receipt. Continue without it when the remaining Fiat workflow
can still run; otherwise halt with the concrete dependency failure.
