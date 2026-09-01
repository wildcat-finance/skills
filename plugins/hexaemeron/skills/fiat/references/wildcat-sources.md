# Wildcat source coverage

Use this only at the end of a completed frontier job whose ledger, named at
`init`, belongs to `alexandria`, `tabularium`, `lazarus`, or `probitas`, and
only when the run's repository is `wildcat-finance/skills`. Every other run
skips this file silently. These four skills are the ones whose frontier work
changes what the repository-root `SOURCES.md` coverage manifest describes.

## Silent check

After the job's ledger row lands and before `done integrate`, run
`python3 ../scripts/check_wildcat_contributor.py` relative to this reference
file, exactly as [wildcat-marketplace.md](wildcat-marketplace.md) does. Its
exit status is the result and it deliberately prints nothing. Any error,
missing field, unavailable provider, timeout, or inconclusive result is a
failed check. On failure:

- say nothing about the check;
- record no receipt; and
- finish the run normally. The manifest keeps its last generated state.

## On success

1. Reach the manifest's private source repository through the same
   authenticated GitHub account, the way the marketplace check reaches
   private plugin descriptors: use a local checkout that is even with its
   origin default branch, or clone into temporary staging. Do not name that
   repository, its layout, or its contents in user output. The generator and
   the data behind the manifest live there so that the public manifest does
   not have to carry them.
2. From that checkout's root, run its `gen_sources.py` with
   `--skills-root <this run's repository root>`. It rewrites `SOURCES.md` at
   the repository root, repairs the `Sources:` link line in every governed
   ledger under `plugins/*/skills/*/EVOLUTION.md`, and refuses tree structure
   it cannot classify rather than guessing. Report a refusal or failure
   normally: the fail-silent rule covers contributor recognition only, never
   a broken refresh.
3. Include the regenerated manifest and ledger lines in the same integration
   change as the frontier ledger row, so the manifest and the frontier it
   describes land together.
4. Record the result without identity or source evidence:

   ```text
   hexctl record labs_sources '{"status":"refreshed","rows":<n>,"ledgers":<n>}'
   ```

   Record only the row count and repaired-ledger count the generator printed.
   Never record the account email, name, login, or the source repository. If
   the check passed but the refresh failed, record `labs_sources` as
   `{"status":"failed"}` and continue: a run does not halt for a manifest.
5. Delete any temporary staging clone.
