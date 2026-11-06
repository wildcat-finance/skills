"""Require a newer package version for every changed plugin Git tree."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


MARKETPLACES = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")
HOSTS = (".claude-plugin", ".codex-plugin")
NAME = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")
VERSION = re.compile(r"(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\Z")
OID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
MAX_BYTES = 4 * 1024 * 1024


class Refusal(ValueError):
    """The requested release comparison could not be established."""


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            result = subprocess.run(
                ["git", "--no-replace-objects", "-c", "core.fsmonitor=false", *args],
                cwd=root, env=env, stdout=out, stderr=err, timeout=30, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Refusal("Git could not complete the release comparison") from exc
        if result.returncode:
            raise Refusal(f"Git {args[0]} failed; fetch the named base and head objects")
        out.seek(0)
        data = out.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise Refusal("Git output exceeds the 4 MiB release-check limit")
        return data


def tree(root, ref):
    if not ref or ref.startswith("-") or len(ref) > 256 or any(ord(c) < 33 for c in ref):
        raise Refusal("invalid base or head reference")
    value = git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{tree}")
    oid = value.decode("ascii").strip()
    if not OID.fullmatch(oid):
        raise Refusal("Git did not return one tree object")
    return oid


def entries(root, tree_oid, path=None):
    target = tree_oid if path is None else f"{tree_oid}:{path}"
    result = {}
    for raw in git(root, "ls-tree", "-z", target).split(b"\0"):
        if not raw:
            continue
        metadata, name = raw.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        result[name.decode("utf-8")] = (mode, kind, oid)
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate JSON key")
        result[key] = value
    return result


def document(root, tree_oid, path):
    parent, filename = path.rsplit("/", 1)
    row = entries(root, tree_oid, parent).get(filename)
    if row is None or row[0] not in {"100644", "100755"} or row[1] != "blob":
        raise Refusal(f"{path}: expected a regular JSON file")
    data = git(root, "cat-file", "blob", row[2])
    try:
        value = json.loads(data, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refusal(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise Refusal(f"{path}: expected a JSON object")
    return value


def version(value, location):
    match = VERSION.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise Refusal(f"{location}: expected a stable MAJOR.MINOR.PATCH version")
    return tuple(int(part) for part in match.groups())


def packages(root, tree_oid):
    directories = entries(root, tree_oid, "plugins")
    plugins = {}
    for name, row in directories.items():
        if row[1] != "tree" or not NAME.fullmatch(name):
            raise Refusal("plugins must contain named plugin directories only")
        plugins[name] = row[2]
    if not plugins:
        raise Refusal("no plugin packages found")
    listings = {}
    for path in MARKETPLACES:
        listing = document(root, tree_oid, path).get("plugins")
        if not isinstance(listing, list):
            raise Refusal(f"{path}: expected a plugin list")
        found = {}
        for item in listing:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise Refusal(f"{path}: invalid plugin entry")
            name = item["name"]
            if name not in plugins or name in found:
                raise Refusal(f"{path}: duplicate or unknown plugin name")
            if "version" in item or path == MARKETPLACES[0]:
                version(item.get("version"), f"{path}: {name}")
            found[name] = item.get("version")
        if set(found) != set(plugins):
            raise Refusal(f"{path}: marketplace and plugin directories disagree")
        listings[path] = found
    result = {}
    for name, plugin_tree in plugins.items():
        versions = [listing[name] for listing in listings.values() if listing[name] is not None]
        for host in HOSTS:
            path = f"plugins/{name}/{host}/plugin.json"
            manifest = document(root, tree_oid, path)
            if manifest.get("name") != name:
                raise Refusal(f"{path}: manifest name disagrees with directory")
            versions.append(manifest.get("version"))
        parsed = [version(v, name) for v in versions]
        if any(v != parsed[0] for v in parsed):
            raise Refusal(f"{name}: both manifests and both marketplaces must agree")
        result[name] = (plugin_tree, parsed[0], versions[0])
    return result


def check(root, base, head):
    before = packages(root, tree(root, base))
    after = packages(root, tree(root, head))
    findings = []
    changed = []
    for name, (new_tree, new_version, new_text) in sorted(after.items()):
        if name not in before:
            changed.append(f"{name}: new package {new_text}")
            continue
        old_tree, old_version, old_text = before[name]
        if new_tree != old_tree:
            if new_version <= old_version:
                findings.append(f"{name}: changed package requires a version above {old_text}; got {new_text}")
            else:
                changed.append(f"{name}: {old_text} -> {new_text}")
    changed.extend(f"{name}: package removed" for name in sorted(before.keys() - after.keys()))
    return findings, changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True, help="release base commit or tree")
    parser.add_argument("--head", default="HEAD", help="candidate commit or staged tree object")
    args = parser.parse_args(argv)
    try:
        findings, changed = check(args.repository, args.base, args.head)
    except (Refusal, UnicodeError, ValueError) as exc:
        print(f"plugin-release: refused: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(f"plugin-release: {finding}", file=sys.stderr)
        return 1
    for change in changed:
        print(f"plugin-release: {change}")
    print(f"plugin-release: checked; {len(changed)} changed packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
