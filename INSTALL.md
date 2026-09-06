# INSTALL AND PUBLISH WILDCAT LABS SKILLS

Use this page after choosing what you want to run. The
[main README](./README.md) explains how Wildcat Labs Skills, the Shoggoth,
fits together and gives working examples;
this page covers installation, invocation, update checks, and publication.

| Situation | Install | Begin with |
| --- | --- | --- |
| Codex or the ChatGPT desktop app | The Wildcat Labs marketplace | Restart the app, then install the plugin you need. |
| Claude Code | The Wildcat Labs marketplace | Install one or more named plugins. |
| A local agent using the Agent Skills convention | The dependency-closed Promise Machine router | Invoke the router with your task. |
| A file-reading agent with no skill discovery | This source checkout | Open `AGENTS.md`. |

Installing one specialist does not install a general autonomous agent. The
selected skill still follows the target repository's instructions and performs
only its declared operations.

## INSTALL

### CODEX

Add the Wildcat Labs marketplace from the Codex CLI. The next two commands let
you inspect the configured sources and fetch later marketplace updates:

```bash
codex plugin marketplace add wildcat-finance/skills
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

After adding it, restart the ChatGPT desktop app, open **Plugins Directory**,
select **Wildcat Labs**, and install the plugin that owns your task.

See OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
for the marketplace workflow.

### CLAUDE CODE

Add the same marketplace and install a plugin from inside Claude Code:

```text
/plugin marketplace add wildcat-finance/skills
/plugin install alexandria@wildcat-labs
/plugin install ariadne@wildcat-labs
/plugin install berean@wildcat-labs
/plugin install brevitas@wildcat-labs
/plugin install dokimasia@wildcat-labs
/plugin install hermes@wildcat-labs
/plugin install hexaemeron@wildcat-labs
/plugin install homologia@wildcat-labs
/plugin install horos@wildcat-labs
/plugin install janus@wildcat-labs
/plugin install lemma@wildcat-labs
/plugin install lazarus@wildcat-labs
/plugin install pandects@wildcat-labs
/plugin install probitas@wildcat-labs
/plugin install sapheneia@wildcat-labs
/plugin install synkrisis@wildcat-labs
/plugin install tabularium@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`.

#### INVOKE

Claude namespaces plugin skills, so each entry skill answers as:

```text
/alexandria:alexandria
/ariadne:ariadne
/berean:berean
/brevitas:brevitas
/dokimasia:dokimasia
/hermes:hermes
/hexaemeron:fiat "<topic>"
/hexaemeron:kronos
/homologia:homologia
/horos:horos
/janus:janus
/lemma:lemma
/lazarus:lazarus
/pandects:pandects
/probitas:probitas
/sapheneia:sapheneia
/synkrisis:synkrisis
/tabularium:tabularium
```

Hexaemeron's first-party phase skills can also be called directly:

```text
/hexaemeron:protasis
/hexaemeron:elenchus
/hexaemeron:phylax
/hexaemeron:ephoros
/hexaemeron:metron
/hexaemeron:hypomnema
/hexaemeron:imprimatur
/hexaemeron:vulgate
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and
[plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
documentation for the underlying format.

#### ATTRIBUTION

The repository carries `.claude/settings.json` with one object:

```json
{"attribution": {"commit": "", "pr": "", "sessionUrl": false}}
```

Claude Code reads this shared project setting from the checkout. The three
values disable the attribution defaults described in its settings reference.
`commit` set to an empty string hides the
`Co-Authored-By: <model name> <noreply@anthropic.com>` trailer added to every
commit. `pr` set to an empty string hides the
`Generated with [Claude Code](https://claude.com/claude-code)` line added to
every pull-request description. `sessionUrl` set to `false` omits the claude.ai
session link a cloud or Remote Control session adds as a `Claude-Session`
trailer on commits and as a link in pull-request descriptions.

There are two important limits. The effect of `sessionUrl: false` is documented
but has not been observed here in a live cloud session. No documented switch
was found for Codex, GitHub Copilot, Cursor, Gemini CLI, or Windsurf; remove
runtime-host bylines before the receipt on those harnesses. In every case Fiat
reads the commit range and pull-request body back and refuses a runtime-host
co-author, generated-by line, or session-link byline. A setting is not evidence
that the line is absent. The rule is
[ADR-016](./docs/decisions/ADR-016-attribute-governed-agent-work-to-shoggoth.md);
the keys are documented in Anthropic's
[settings reference](https://code.claude.com/docs/en/settings-reference).

### LOCAL AGENTS

Install the collective through the Agent Skills convention by selecting the
single [Promise Machine router](./.agents/skills/promise-machine/SKILL.md),
published from
[wildcat-finance/skills-runtime](https://github.com/wildcat-finance/skills-runtime):

```bash
npx skills add wildcat-finance/skills-runtime --skill promise-machine
```

For a non-interactive project-local Codex install:

```bash
npx skills add wildcat-finance/skills-runtime \
  --skill promise-machine --agent codex --copy -y
python3 .agents/skills/promise-machine/scripts/verify_runtime.py
```

The installer copies only the selected directory. The router therefore carries
a generated runtime with the suite law, plugin contracts, canonical skills,
and their operational files. It verifies those bytes before routing and has no
separate behavioural version. A specialist entry copied on its own may lack
the scripts or parent contract it requires; use the collective router for the
supported portable install.

That runtime is generated from this repository rather than committed to it. A
scheduled job in the distribution repository rebuilds the package hourly and
publishes it only when it verifies, so an install can be up to an hour behind
this repository's `main`. ADR-066 records that trade, and
[the publication guide](./docs/skills-runtime-publication.md) records how to
check which source commit the published package was built from.

The portable package omits host manifests, development suites, historical
audit records, and Alexandria's 16 MB Compound v3 Phase 0 offline trace
inputs and built release. Use a full source checkout when an operation needs
one of those surfaces. To use a checkout directly, point the agent at this
repository; the router detects a source checkout and reads the real tree rather
than a bundled runtime.

A file-reading agent without automatic skill discovery should begin with
[AGENTS.md](./AGENTS.md). That file identifies the entrypoints, path rules, and
plugin-specific runtime contracts.

## PUBLISH

Work lands in the public repository, but an installed plugin can remain behind
that revision. The two distribution routes below fetch and cache different
things. In either case, verify the bytes a machine is actually serving instead
of treating a successful update command as proof of currency.

### GIT-BACKED INSTALLATION

A marketplace added with `/plugin marketplace add wildcat-finance/skills`, or
the Codex equivalent, is a clone fetched with the operator's own Git
credentials. For this route, merging to `main` is the publication step. A
machine then runs two updates with different jobs:

```bash
claude plugin marketplace update wildcat-labs
claude plugin update hexaemeron@wildcat-labs
```

Inside a session that is `/plugin marketplace update` and
`/plugin update <plugin>@wildcat-labs`. In a provisioning script, pass `--yes`.

`marketplace update` advances the checkout to the repository head. `plugin
update` compares the version declared in the plugin's
`.claude-plugin/plugin.json` against the version the install already records,
and the cache is laid out to match:
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>` is keyed on that
declared version and on nothing else. So a commit that changes a skill without
bumping its plugin's version arrives in the checkout, maps to the cache slot
already filled, and is reported as `already at the latest version`. The command
exits zero and the machine keeps the old files.

This gap was measured on 2026-08-22 over the 122 commits between an install at
`793b112` and a head at `cd48583`. `plugin update` moved Hexaemeron from 1.5.1
to 1.5.4 and left the
other <!-- front-door:historical captured="2026-08-22" figure="thirteen" -->thirteen
plugins pinned at `793b112`, and all thirteen had real changes under
`skills/*/SKILL.md`. Hermes was the worst of them: its plugin version stayed
at 0.1.1 while the skill's own frontmatter went from 0.1.0 to 0.1.1, so the
cached copy was short a 73-line `SKILL.md` diff carrying the pinned 120-rule
gas corpus, the reference to that corpus JSON, and the rule refusing work
outside the target's scope.

Do not trust the exit code alone. Each install records its pinned commit;
compare those commits with the marketplace checkout's current head:

```bash
git -C ~/.claude/plugins/marketplaces/wildcat-labs rev-parse HEAD
jq -r '.plugins | to_entries[]
  | select(.key | endswith("@wildcat-labs"))
  | "\(.key) \(.value[0].version) \(.value[0].gitCommitSha[0:7])"' \
  ~/.claude/plugins/installed_plugins.json
```

A plugin whose `gitCommitSha` is behind that head is serving stale files
whatever its version says. Reinstalling it is what re-pins the commit, because
the install is taken fresh from the checkout rather than diffed against it:

```bash
claude plugin uninstall <plugin>@wildcat-labs --keep-data
claude plugin install <plugin>@wildcat-labs --yes
```

`--keep-data` preserves `~/.claude/plugins/data/{id}/`, and enabled status
survived the round trip for
all <!-- front-door:historical captured="2026-08-22" figure="fourteen" -->fourteen
plugins present in that dated measurement. Apply the same check to every plugin
now behind the head, not only the one being worked on.

### ORGANISATION DISTRIBUTION THROUGH THE PRIVATE MIRROR

A marketplace distributed through
[Organization settings > Plugins](https://claude.ai/admin-settings/plugins) is
read server-side by the Claude GitHub App, and that repository has to be private
or internal. The two repositories therefore have different jobs:

- `wildcat-finance/skills` is public and holds the work.
- `wildcat-finance/skills-marketplace` is private. A scheduled job in that
  repository force-pushes every branch and tag from the public one into it. Its
  cron asks for every five minutes; GitHub's scheduler has been delivering
  closer to every twenty, so treat the interval as observed rather than
  declared.

The mirror is the publishing pipeline; there is nothing to package or upload
by hand.
Organisation sync packages each plugin during distribution, so an installer
does not need access to another source repository. To release, merge to `main`,
let the mirror run, and let organisation sync read it. Compare the two heads
instead of waiting a fixed interval:

```bash
gh api repos/wildcat-finance/skills/commits/main --jq '.sha'
gh api repos/wildcat-finance/skills-marketplace/commits/main --jq '.sha'
```

The job also takes a manual trigger, which is the way to release without waiting
for the schedule:

```bash
gh workflow run sync-skills-marketplace.yml --repo wildcat-finance/skills-marketplace
```

Plugin sources stay relative paths in `.claude-plugin/marketplace.json`, using
the form `./plugins/<name>`, so sync packages each plugin out of the mirror
instead of fetching it from somewhere it may not be able to authenticate to. A version
bump is released once it has crossed all three links: merged here, mirrored
there, and distributed by sync. Each link can look healthy while sitting behind
the one before it, which is how this route produces the gap named above.

### IDENTIFY THE ROUTE A MACHINE USES

The update commands above apply only to the Git-backed route. A Git-backed
install holds a Git checkout; an
organisation-distributed one holds an extracted package under an opaque
identifier, with a marketplace id and no remote, ref, or commit recorded.
Hexaemeron's
[plugin currency reference](./plugins/hexaemeron/skills/fiat/references/plugin-currency.md)
states the same distinction and explains what to do about a controller behind
its own repository.

Anthropic's [marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces)
covers source rules, and the
[organisation plugin workflow](https://support.claude.com/en/articles/13837433)
covers the administrator side.

## LICENCE BOUNDARY

Wildcat Labs first-party files are licensed under
[Apache-2.0](./LICENSE). The bundled Pashov security skills are vendored
upstream work and keep their own MIT licence and notices; they are not
relicensed by installation or publication of this marketplace.
