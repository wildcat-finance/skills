# macOS issue publisher deployment kit

This kit is not installed. A privileged operator must separately authorise
identity creation, key custody, service installation and retirement of direct
helper access. Do not run those actions as part of component conformance.
The verifier only reads and always reports `live_isolation: not-established`.

## Fixed layout

| Subject | Value |
| --- | --- |
| Service account | `_wildcatpublisher`, UID 499, shell `/usr/bin/false` |
| Socket group | `_wildcatpublishers`, GID 499 |
| Service home and key directory | `/var/db/wildcat-github-issue-publisher`, service owner and group, mode `0700` |
| Key | `shoggoth-wildcat-labs.pem` in that directory, service owner and group, mode `0600` |
| Socket | `/var/run/wildcat-github-issue-publisher.sock`, service owner and group, mode `0660` |
| Working directory | `/Library/WildcatIssuePublisher`, root:wheel, mode `0755` |
| Interpreter | `python3` in the working directory, root:wheel, mode `0755` |
| Program and client | `publisher-service.py` and `publisher-client.py` in the working directory, root:wheel, mode `0644` |
| Daemon | `/Library/LaunchDaemons/finance.wildcat.issue-publisher.plist`, root:wheel, mode `0644` |

The template uses Darwin's `inetdCompatibility` with `Wait: false`: launchd
accepts one connection and passes it on descriptor 0. The process serves one
request and exits. Both launchd resource-limit dictionaries fix 60 CPU seconds and no core dump.
The service sets its own soft and hard limits to 64 files and 8 processes
before constructing the runtime. The launchd `NumberOfFiles` and
`NumberOfProcesses` keys also change host sysctls for a system daemon, so the
kit omits them. The server adds a 60-second socket timeout;
the runtime has its own 60-second lifecycle ceiling. UID or GID 499 already
assigned to another identity is a deployment refusal, not permission to reuse
that identity.

## Operator installation record

1. Review the release, interpreter pinned by [`.python-version`](../../../../../../.python-version) and its dependencies. Reserve
   the exact service identity and group; add only authorised, non-admin callers.
2. Place the reviewed program, client and interpreter at the fixed paths. Copy
   the Phylax `github_issue_publisher_lib`, Imprimatur scripts, lexicons and
   `SKILL.md` below the same
   `plugins/hexaemeron/skills/` paths. All source files are root:wheel `0644`
   under root:wheel `0755` directories, with no ACL or symlink. The release
   inventory includes every file in those three flat directories, Imprimatur
   `SKILL.md` and the three top-level files. Caches, symlinks and nested packages
   refuse. Preserve its canonical JSON SHA-256 as the reviewed release
   digest. Inventory collection is `release_inventory(root)` in the verifier
   module; collect it from the reviewed staging directory before installation.
3. Put the key under service custody and retire the caller's direct helper and
   key paths. The verifier checks the named `file_as_app.sh`, `mint_token.sh`
   and PEM locations under the caller's `.config/gh-app`; the operator must
   investigate other copies and inherited tokens separately.
4. Install the exact daemon template, load it under separately recorded
   authority, and run the read-only check below with the reviewed release
   digest. Record the active service identity and a separately authorised
   lifecycle check; the metadata snapshot alone cannot establish live state.

```bash
python3 plugins/hexaemeron/skills/phylax/scripts/github_issue_publisher.py check-deployment --caller CALLER --release-sha256 REVIEWED_SHA256
```

The check requires effective UID 0 and never opens the key. It emits fixed predicate names, booleans and the SHA-256 binding of the caller
and reviewed release digest. Missing paths, failed predicates or missing
installation evidence block App issue creation. The operator retains the
checked snapshot with its release digest, caller and time in the separate
deployment record; the public output deliberately omits account and path text.

## Refusal and rollback

On a failed predicate, leave publication stopped, repair the named deployment
under separate authority and rerun the same check. For an uncertain create,
reconcile its request digest before any new publication request. Do not retry
from the client or delete a remote issue to hide uncertainty. The caller must
retain its request and received terminal output: this kit has no persistent
server receipt. A disconnect before the response arrives leaves publication
unknown and requires GitHub reconciliation before another request.

Rollback is an operator action: unload the service, revoke outstanding access
as appropriate, restore a reviewed release and repeat deployment verification.
Never restore direct agent access to the helper or key as a fallback. Root,
administrators, unknown copies, interpreter dependencies and host compromise
remain outside this component's promise.
