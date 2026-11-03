#!/usr/bin/env python3
"""Design probe for Fiat run #2093: native remote reads that authenticate.

Two modes. Each writes one closed ``protasis-design-report/v1`` object to an
``--out`` path that must not already exist, and prints the same bytes.

``select``  runs one candidate model of the native remote tip read against a
            fresh loopback fixture and measures one selection criterion.
``conform`` imports the built controller under ``--root`` and checks one
            conformance criterion for the selected candidate only.

The fixture binds 127.0.0.1 alone, generates a throwaway test credential per
run, keeps every Git child away from the operator's real configuration (the
caller configuration it builds starts with an empty ``credential.helper``
reset, so no real keychain or GitHub helper is consulted or written), and
removes its temporary tree before it exits. Nothing here reads a real
credential or reaches a host other than the loopback address.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import http.server
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from unittest import mock


REPORT_SCHEMA = "protasis-design-report/v1"
SELECTED = "credential-scope-projection"
CANDIDATES = (
    "credential-scope-projection",
    "github-rest-tip",
    "credential-fill-relay",
    "native-unchanged",
)
SELECTION_UNITS = {
    "global-credential-read": "boolean",
    "moved-tip-detected": "boolean",
    "global-insteadof-inert": "boolean",
    "ambient-substitution-inert": "boolean",
    "controller-holds-no-credential": "boolean",
    "authentication-refusal-named": "boolean",
    "child-processes-per-read": "count",
    "buffered-bytes-per-read": "bytes",
    "helper-shapes-authenticated": "count",
}
CONFORMANCE_UNITS = {
    "seam-reads-credentialed-remote": "boolean",
    "sync-run-module-passes": "boolean",
    "local-reads-stay-native": "boolean",
    "projection-cap-refuses": "boolean",
    "authentication-refusal-fixed": "boolean",
    "remote-read-children": "count",
}
HELPER_SHAPES = (
    "abs-exec",
    "bang-abs",
    "bang-path",
    "named-path",
    "home-store",
    "reset-order",
)
NATIVE_GIT = shutil.which("git", path=os.defpath)
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
PROJECTION_MAX_ENTRIES = 64
PROJECTION_MAX_BYTES = 16 * 1024
PROJECTION_SCOPES = frozenset({"system", "unknown", "global", "local", "worktree"})
CONFIG_LOCATORS = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM")
AUTH_MARKERS = (
    b"could not read Username",
    b"could not read Password",
    b"Authentication failed",
    b"Permission denied (publickey",
    b"returned error: 401",
    b"returned error: 403",
    b"HTTP 401",
    b"Bad credentials",
)
CHILD_MARKERS = (
    "could not read Username",
    "terminal prompts",
    "Authentication failed",
    "HTTP 401",
    "Bad credentials",
    "fatal:",
    "127.0.0.1",
)
AUTH_REFUSAL = (
    "{label} could not be read: origin refused authentication, and the "
    "native read offers only the credential helpers your Git configuration names"
)


class Refusal(Exception):
    """A candidate's fixed refusal text; never carries child output."""


# --------------------------------------------------------------------------
# Fixture
# --------------------------------------------------------------------------


def _write(path: Path, text: str, mode: int = 0o600) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)
    return path


class Fixture:
    """Two served bare repositories, one run worktree and a caller to vary."""

    def __init__(self) -> None:
        if NATIVE_GIT is None:
            raise SystemExit("probe: no Git on the platform default path")
        self.root = Path(tempfile.mkdtemp(prefix="s2093-probe-"))
        self.secret = "fixture-" + secrets.token_hex(12)
        self.hits = {"remote": 0, "hostile": 0}
        self.served = self.root / "served"
        self.callers = 0
        build_home = self.root / "build-home"
        build_home.mkdir()
        self.build_env = {
            "PATH": os.defpath,
            "HOME": str(build_home),
            "LANG": "C",
            "LC_ALL": "C",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
        self._build_repositories()
        self._start_server()
        self.remote_url = f"http://127.0.0.1:{self.port}/fixture/remote.git"
        self.hostile_url = f"http://127.0.0.1:{self.port}/fixture/hostile.git"
        self.url_key = f"http://127.0.0.1:{self.port}"
        self._build_work()
        self._build_tools()

    # Git used to build the fixture: hermetic, never the caller's.
    def git(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(
            [
                NATIVE_GIT,
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false",
                "-c", "init.defaultBranch=main",
                *args,
            ],
            cwd=str(cwd or self.root),
            env=self.build_env,
            capture_output=True,
            check=True,
        )
        return result.stdout.decode("utf-8").strip()

    def _commit(self, repo: Path, message: str) -> str:
        self.git("commit", "-q", "--allow-empty", "-m", message, cwd=repo)
        return self.git("rev-parse", "HEAD", cwd=repo)

    def _build_repositories(self) -> None:
        self.seed = self.root / "seed"
        self.git("init", "-q", "-b", "main", str(self.seed))
        self.main_tip = self._commit(self.seed, "main one")
        self.git("checkout", "-q", "-b", "run", cwd=self.seed)
        self.stale_tip = self._commit(self.seed, "run zero")
        self.run_tip = self._commit(self.seed, "run one")
        self.remote_dir = self.served / "fixture" / "remote.git"
        self.git("init", "-q", "--bare", str(self.remote_dir))
        self.git("push", "-q", str(self.remote_dir), "main", "run", cwd=self.seed)
        self.git("update-server-info", cwd=self.remote_dir)

        hostile_seed = self.root / "hostile-seed"
        self.git("init", "-q", "-b", "main", str(hostile_seed))
        self.hostile_main = self._commit(hostile_seed, "hostile main")
        self.git("checkout", "-q", "-b", "run", cwd=hostile_seed)
        self.hostile_run = self._commit(hostile_seed, "hostile run")
        self.hostile_dir = self.served / "fixture" / "hostile.git"
        self.git("init", "-q", "--bare", str(self.hostile_dir))
        self.git("push", "-q", str(self.hostile_dir), "main", "run", cwd=hostile_seed)
        self.git("update-server-info", cwd=self.hostile_dir)
        self.hostile_tips = {self.hostile_main, self.hostile_run}

    def advance(self) -> str:
        """Move the served run branch to a new commit the worktree never saw."""
        self.advanced_tip = self._commit(self.seed, "run two")
        self.git("push", "-q", str(self.remote_dir), "run", cwd=self.seed)
        self.git("update-server-info", cwd=self.remote_dir)
        return self.advanced_tip

    def _start_server(self) -> None:
        fixture = self
        expected = "Basic " + base64.b64encode(
            f"fixture:{self.secret}".encode("utf-8")
        ).decode("ascii")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(fixture.served), **kwargs)

            def log_message(self, *args):  # keep the probe's output clean
                return

            def do_GET(self):  # noqa: N802 - stdlib handler name
                path = self.path.split("?", 1)[0]
                if path.startswith("/fixture/remote.git/"):
                    name = "remote"
                elif path.startswith("/fixture/hostile.git/"):
                    name = "hostile"
                else:
                    self.send_error(404)
                    return
                fixture.hits[name] += 1
                if name == "remote" and self.headers.get("Authorization") != expected:
                    self.send_response(401)
                    self.send_header("WWW-Authenticate", 'Basic realm="fixture"')
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.path = path
                super().do_GET()

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _build_work(self) -> None:
        self.work = self.root / "work"
        self.git("clone", "-q", "--no-hardlinks", str(self.seed), str(self.work))
        self.git("remote", "set-url", "origin", self.remote_url, cwd=self.work)
        # A stale tracking ref: a reader that answered from local refs would
        # return this instead of the served tip.
        self.git("update-ref", "refs/remotes/origin/run", self.stale_tip, cwd=self.work)
        self.attacker = self.root / "attacker"
        self.git("init", "-q", "-b", "main", str(self.attacker))
        self.git("remote", "add", "origin", self.hostile_url, cwd=self.attacker)

    def _build_tools(self) -> None:
        self.bin = self.root / "caller-bin"
        self.hostile_bin = self.root / "hostile-bin"
        good = f"username=fixture\npassword={self.secret}\n"
        script = (
            "#!/bin/sh\n"
            'test "$1" = get || exit 0\n'
            "cat <<'EOF'\n" + good + "EOF\n"
        )
        self.helper = _write(self.bin / "fixture-cred", script, 0o700)
        _write(self.bin / "git-credential-fixturecred", script, 0o700)
        self.home_helper = _write(
            self.bin / "fixture-home-cred",
            "#!/bin/sh\n"
            'test "$1" = get || exit 0\n'
            'test -r "$HOME/.fixture-credential" || exit 0\n'
            'cat "$HOME/.fixture-credential"\n',
            0o700,
        )
        self.home_credential = good
        self.wrong_helper = _write(
            self.bin / "fixture-wrong-cred",
            "#!/bin/sh\n"
            'test "$1" = get || exit 0\n'
            "printf 'username=fixture\\npassword=wrong\\n'\n",
            0o700,
        )
        # The honest gh models GitHub REST: it answers from the served
        # repository, and only when its own login exists.
        _write(
            self.bin / "gh",
            "#!/bin/sh\n"
            'test -r "$HOME/.config/gh/fixture-login" || '
            "{ echo 'gh: Bad credentials (HTTP 401)' >&2; exit 1; }\n"
            'branch="${4##*/git/ref/heads/}"\n'
            f'sha=$({NATIVE_GIT} --git-dir "{self.remote_dir}" rev-parse '
            '--verify "refs/heads/$branch") || exit 1\n'
            "printf '{\"ref\":\"refs/heads/%s\",\"object\":{\"sha\":\"%s\","
            "\"type\":\"commit\"}}\\n' \"$branch\" \"$sha\"\n",
            0o700,
        )
        _write(
            self.hostile_bin / "gh",
            "#!/bin/sh\n"
            "printf '{\"ref\":\"refs/heads/run\",\"object\":{\"sha\":\"%s\","
            f"\"type\":\"commit\"}}}}\\n' '{self.hostile_run}'\n",
            0o700,
        )
        _write(
            self.hostile_bin / "git",
            f"#!{sys.executable} -I\n"
            "import os, sys\n"
            "args = sys.argv[1:]\n"
            "if 'config' in args and '--get-regexp' in args:\n"
            "    sys.stdout.buffer.write(b'global\\0credential.helper\\n"
            f"{self.wrong_helper}\\0')\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['credential', 'fill']:\n"
            "    sys.stdout.write('username=hostile\\npassword=hostile\\n')\n"
            "    raise SystemExit(0)\n"
            f"os.execv({NATIVE_GIT!r}, [{NATIVE_GIT!r}, *args])\n",
            0o700,
        )

    def caller(
        self,
        *,
        shape: str | None = "bang-abs",
        hostile_insteadof: bool = False,
        ambient: bool = False,
        gh_login: bool = False,
        extra_global: str = "",
        origin_url: str | None = None,
    ) -> dict[str, str]:
        """A caller environment whose only credential is in global config."""
        self.callers += 1
        base = self.root / f"caller-{self.callers}"
        home = base / "home"
        home.mkdir(parents=True)
        # The empty generic reset first: Apple Git's CommandLineTools config
        # names osxkeychain, and the probe must never reach a real keychain.
        global_lines = ["[credential]", "\thelper ="]
        system_lines: list[str] = []
        section = f'[credential "{self.url_key}"]'
        if shape == "abs-exec":
            global_lines += [section, f"\thelper = {self.helper}"]
        elif shape == "bang-abs":
            global_lines += [section, f'\thelper = "!{self.helper}"']
        elif shape == "bang-path":
            global_lines += [section, '\thelper = "!fixture-cred"']
        elif shape == "named-path":
            global_lines += [section, "\thelper = fixturecred"]
        elif shape == "home-store":
            global_lines += [section, f'\thelper = "!{self.home_helper}"']
            _write(home / ".fixture-credential", self.home_credential)
        elif shape == "reset-order":
            # A wrong system helper precedes the global reset; only Git's
            # exact scope order clears it before the right global helper.
            system_lines = ["[credential]", f'\thelper = "!{self.wrong_helper}"']
            global_lines = [
                "[credential]", "\thelper =",
                section, f'\thelper = "!{self.helper}"',
            ]
        elif shape is not None:
            raise SystemExit(f"probe: unknown helper shape {shape}")
        if hostile_insteadof:
            rewrite = f'[url "{self.hostile_url}"]\n\tinsteadOf = {self.remote_url}\n'
            global_lines.append(rewrite.rstrip("\n"))
            _write(home / ".gitconfig", rewrite)
            _write(home / ".config" / "git" / "config", rewrite)
        if gh_login:
            _write(home / ".config" / "gh" / "fixture-login", "logged in\n")
        global_config = _write(
            base / "global.gitconfig", "\n".join(global_lines) + "\n" + extra_global
        )
        system_config = _write(base / "system.gitconfig", "\n".join(system_lines) + "\n")
        tmp = base / "tmp"
        tmp.mkdir()
        environment = {
            "PATH": f"{self.bin}{os.pathsep}{os.defpath}",
            "HOME": str(home),
            "LANG": "C",
            "LC_ALL": "C",
            "TMPDIR": str(tmp),
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_CONFIG_SYSTEM": str(system_config),
            "GIT_TERMINAL_PROMPT": "0",
        }
        if ambient:
            environment["PATH"] = f"{self.hostile_bin}{os.pathsep}{environment['PATH']}"
            environment["GIT_DIR"] = str(self.attacker / ".git")
            environment["GIT_WORK_TREE"] = str(self.attacker)
            environment["GIT_CONFIG_COUNT"] = "1"
            environment["GIT_CONFIG_KEY_0"] = f"url.{self.hostile_url}.insteadOf"
            environment["GIT_CONFIG_VALUE_0"] = origin_url or self.remote_url
        return environment

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> "Fixture":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# --------------------------------------------------------------------------
# Candidate models
# --------------------------------------------------------------------------


class Launcher:
    """Every child a candidate starts: count, bytes held, credential exposure."""

    def __init__(self, secret: str) -> None:
        self.secret = secret.encode("utf-8")
        self.children = 0
        self.buffered = 0
        self.secret_seen = False

    def run(
        self,
        argv: list[str],
        env: dict[str, str],
        cwd: Path,
        stdin: bytes | None = None,
    ) -> tuple[int, bytes]:
        self.children += 1
        exposed = [item.encode("utf-8") for item in argv]
        exposed += [value.encode("utf-8") for value in env.values()]
        if stdin:
            exposed.append(stdin)
        if any(self.secret in item for item in exposed):
            self.secret_seen = True
        result = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        self.buffered += len(result.stdout)
        if self.secret in result.stdout:
            self.secret_seen = True
        return result.returncode, result.stdout


def native_environment(caller: dict[str, str]) -> dict[str, str]:
    """The base controller's relation environment, built from ``caller``."""
    environment = {
        "PATH": os.defpath,
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    if caller.get("SSH_AUTH_SOCK"):
        environment["SSH_AUTH_SOCK"] = caller["SSH_AUTH_SOCK"]
    return environment


def config_reader_environment(caller: dict[str, str]) -> dict[str, str]:
    """The caller's environment without any variable that selects a repository."""
    return {
        name: value
        for name, value in caller.items()
        if not name.startswith("GIT_") or name in CONFIG_LOCATORS
    }


def parse_tip(output: bytes, branch: str, label: str) -> str:
    expected = f"refs/heads/{branch}"
    lines = [line for line in output.decode("utf-8", "replace").splitlines() if line]
    if len(lines) != 1:
        raise Refusal(f"{label} must contain exactly one ref")
    fields = lines[0].split("\t")
    if len(fields) != 2 or not COMMIT_RE.fullmatch(fields[0]) or fields[1] != expected:
        raise Refusal(f"{label} is malformed")
    return fields[0]


def classified(output: bytes, label: str) -> Refusal:
    if any(marker in output for marker in AUTH_MARKERS):
        return Refusal(AUTH_REFUSAL.format(label=label))
    return Refusal(f"{label} could not be read")


def native_ls_remote(
    launcher: Launcher, work: Path, branch: str, env: dict[str, str], label: str,
    *, classify: bool,
) -> str:
    status, output = launcher.run(
        [NATIVE_GIT, "--no-replace-objects", "ls-remote", "--refs", "origin",
         f"refs/heads/{branch}"],
        env,
        work,
    )
    if status != 0:
        if classify:
            raise classified(output, label)
        raise Refusal(f"{label} could not be read")
    return parse_tip(output, branch, label)


def credential_projection(
    launcher: Launcher, caller: dict[str, str], work: Path, label: str
) -> list[tuple[str, str]]:
    git = shutil.which("git", path=caller.get("PATH", os.defpath))
    if git is None:
        raise Refusal(f"{label} could not be read: the caller's Git credential configuration could not be read")
    status, output = launcher.run(
        [git, "config", "--includes", "--show-scope", "-z", "--get-regexp", r"^credential\."],
        config_reader_environment(caller),
        work,
    )
    if status == 1 and not output:
        return []
    if status != 0 or not output.endswith(b"\0"):
        raise Refusal(f"{label} could not be read: the caller's Git credential configuration could not be read")
    fields = output[:-1].split(b"\0")
    if len(fields) % 2:
        raise Refusal(f"{label} could not be read: the caller's Git credential configuration is malformed")
    entries: list[tuple[str, str]] = []
    total = 0
    for index in range(0, len(fields), 2):
        try:
            scope = fields[index].decode("ascii")
            key, separator, value = fields[index + 1].decode("utf-8").partition("\n")
        except UnicodeDecodeError:
            raise Refusal(f"{label} could not be read: the caller's Git credential configuration is malformed") from None
        if not separator or not key.lower().startswith("credential."):
            raise Refusal(f"{label} could not be read: the caller's Git credential configuration is malformed")
        if scope == "command":
            continue
        if scope not in PROJECTION_SCOPES:
            raise Refusal(f"{label} could not be read: the caller's Git credential configuration is malformed")
        entries.append((key, value))
        total += len(key.encode("utf-8")) + len(value.encode("utf-8"))
    if len(entries) > PROJECTION_MAX_ENTRIES or total > PROJECTION_MAX_BYTES:
        raise Refusal(f"{label} could not be read: the caller's Git credential configuration exceeds its bound")
    return entries


def read_projection(fx: Fixture, launcher: Launcher, caller: dict[str, str], branch: str, label: str) -> str:
    entries = credential_projection(launcher, caller, fx.work, label)
    env = native_environment(caller)
    if caller.get("HOME"):
        env["HOME"] = caller["HOME"]
    if entries:
        # A leading empty helper clears what the native read collected from
        # local config, so the replay below reproduces the caller's exact
        # helper order: system, global, then local.
        pairs = [("credential.helper", ""), *entries]
        env["GIT_CONFIG_COUNT"] = str(len(pairs))
        for index, (key, value) in enumerate(pairs):
            env[f"GIT_CONFIG_KEY_{index}"] = key
            env[f"GIT_CONFIG_VALUE_{index}"] = value
    return native_ls_remote(launcher, fx.work, branch, env, label, classify=True)


def native_origin_url(fx: Fixture, launcher: Launcher, caller: dict[str, str], label: str) -> str:
    status, output = launcher.run(
        [NATIVE_GIT, "--no-replace-objects", "remote", "get-url", "origin"],
        native_environment(caller),
        fx.work,
    )
    lines = output.decode("utf-8", "replace").splitlines()
    if status != 0 or len(lines) != 1:
        raise Refusal(f"{label} could not be read")
    return lines[0]


def read_rest(fx: Fixture, launcher: Launcher, caller: dict[str, str], branch: str, label: str) -> str:
    url = native_origin_url(fx, launcher, caller, label)
    # The model treats the fixture host as the GitHub host; any other origin
    # keeps the unchanged native read, as the REST route would have to.
    prefix = f"{fx.url_key}/"
    if not url.startswith(prefix):
        return native_ls_remote(launcher, fx.work, branch, native_environment(caller), label, classify=True)
    owner_repo = url[len(prefix):].removesuffix(".git")
    gh = shutil.which("gh", path=caller.get("PATH", os.defpath))
    if gh is None:
        raise Refusal(f"{label} could not be read")
    status, output = launcher.run(
        [gh, "api", "--method", "GET", f"repos/{owner_repo}/git/ref/heads/{branch}"],
        dict(caller),
        fx.work,
    )
    if status != 0:
        raise classified(output, label)
    try:
        payload = json.loads(output.decode("utf-8"))
        sha = payload["object"]["sha"]
    except (ValueError, KeyError, TypeError):
        raise Refusal(f"{label} is malformed") from None
    if payload.get("ref") != f"refs/heads/{branch}" or not COMMIT_RE.fullmatch(str(sha)):
        raise Refusal(f"{label} is malformed")
    return sha


RELAY_HELPER = (
    '!f() { test "$1" = get || return 0; '
    "printf 'username=%s\\npassword=%s\\n' "
    '"$FIAT_RELAY_USERNAME" "$FIAT_RELAY_PASSWORD"; }; f'
)


def read_relay(fx: Fixture, launcher: Launcher, caller: dict[str, str], branch: str, label: str) -> str:
    url = native_origin_url(fx, launcher, caller, label)
    match = re.fullmatch(r"(?P<protocol>https?)://(?P<host>[^/]+)(?:/.*)?", url)
    if match is None:
        return native_ls_remote(launcher, fx.work, branch, native_environment(caller), label, classify=True)
    git = shutil.which("git", path=caller.get("PATH", os.defpath))
    if git is None:
        raise Refusal(f"{label} could not be read")
    request = f"protocol={match['protocol']}\nhost={match['host']}\n\n".encode("utf-8")
    fill_env = config_reader_environment(caller)
    fill_env["GIT_TERMINAL_PROMPT"] = "0"
    status, output = launcher.run([git, "credential", "fill"], fill_env, fx.work, stdin=request)
    if status != 0:
        raise classified(output, label)
    fields = dict(
        line.split("=", 1)
        for line in output.decode("utf-8", "replace").splitlines()
        if "=" in line
    )
    if "username" not in fields or "password" not in fields:
        raise Refusal(AUTH_REFUSAL.format(label=label))
    env = native_environment(caller)
    env.update({
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": RELAY_HELPER,
        "FIAT_RELAY_USERNAME": fields["username"],
        "FIAT_RELAY_PASSWORD": fields["password"],
    })
    return native_ls_remote(launcher, fx.work, branch, env, label, classify=True)


def read_unchanged(fx: Fixture, launcher: Launcher, caller: dict[str, str], branch: str, label: str) -> str:
    return native_ls_remote(launcher, fx.work, branch, native_environment(caller), label, classify=False)


MODELS = {
    "credential-scope-projection": read_projection,
    "github-rest-tip": read_rest,
    "credential-fill-relay": read_relay,
    "native-unchanged": read_unchanged,
}


def attempt(candidate: str, fx: Fixture, caller: dict[str, str], branch: str = "run") -> dict:
    launcher = Launcher(fx.secret)
    label = "remote run branch tip"
    try:
        tip = MODELS[candidate](fx, launcher, caller, branch, label)
        refusal = None
    except Refusal as error:
        tip = None
        refusal = str(error)
    return {"tip": tip, "refusal": refusal, "launcher": launcher}


def refusal_is_fixed(refusal: str | None, fx: Fixture) -> bool:
    return bool(refusal) and not any(marker in refusal for marker in CHILD_MARKERS) and str(fx.port) not in refusal


def measure_selection(candidate: str, criterion: str) -> object:
    with Fixture() as fx:
        if criterion == "global-credential-read":
            return attempt(candidate, fx, fx.caller())["tip"] == fx.run_tip
        if criterion == "moved-tip-detected":
            first = attempt(candidate, fx, fx.caller())["tip"]
            moved = fx.advance()
            second = attempt(candidate, fx, fx.caller())["tip"]
            # A sync commit equal to the first tip now differs from the
            # remote tip, so the tip comparison must refuse it.
            return first == fx.run_tip and second == moved and moved != first
        if criterion == "global-insteadof-inert":
            tip = attempt(candidate, fx, fx.caller(hostile_insteadof=True))["tip"]
            return tip == fx.run_tip and fx.hits["hostile"] == 0
        if criterion == "ambient-substitution-inert":
            tip = attempt(candidate, fx, fx.caller(ambient=True))["tip"]
            return tip not in fx.hostile_tips and fx.hits["hostile"] == 0
        if criterion == "controller-holds-no-credential":
            return not attempt(candidate, fx, fx.caller())["launcher"].secret_seen
        if criterion == "authentication-refusal-named":
            result = attempt(candidate, fx, fx.caller(shape=None))
            refusal = result["refusal"]
            return (
                result["tip"] is None
                and refusal_is_fixed(refusal, fx)
                and "authentication" in refusal
            )
        if criterion == "child-processes-per-read":
            return attempt(candidate, fx, fx.caller())["launcher"].children
        if criterion == "buffered-bytes-per-read":
            return attempt(candidate, fx, fx.caller())["launcher"].buffered
        if criterion == "helper-shapes-authenticated":
            return sum(
                attempt(candidate, fx, fx.caller(shape=shape))["tip"] == fx.run_tip
                for shape in HELPER_SHAPES
            )
    raise SystemExit(f"probe: unknown selection criterion {criterion}")


# --------------------------------------------------------------------------
# Conformance against the built controller
# --------------------------------------------------------------------------


def load_controller(root: Path):
    path = root / "plugins" / "hexaemeron" / "skills" / "fiat" / "scripts" / "hexctl.py"
    spec = importlib.util.spec_from_file_location("hexctl_2093_conformance", path)
    if spec is None or spec.loader is None:
        raise SystemExit("probe: the built controller cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def controller_call(module, caller: dict[str, str], function, *args, **kwargs):
    """Run one controller function under ``caller`` as the whole environment."""
    stderr = io.StringIO()
    with mock.patch.dict(os.environ, caller, clear=True), contextlib.redirect_stderr(stderr):
        try:
            return function(*args, **kwargs), None
        except SystemExit:
            return None, stderr.getvalue()


BASE_NATIVE_KEYS = frozenset({
    "PATH", "LANG", "LC_ALL", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_SYSTEM", "GIT_NO_LAZY_FETCH", "GIT_TERMINAL_PROMPT",
})


def measure_conformance(criterion: str, root: Path) -> object:
    module = load_controller(root)
    tip_reader = module.remote_branch_tip
    with Fixture() as fx:
        work = str(fx.work)
        if criterion == "seam-reads-credentialed-remote":
            caller = fx.caller(hostile_insteadof=True)
            caller.update({
                "GIT_DIR": str(fx.attacker / ".git"),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.{fx.hostile_url}.insteadOf",
                "GIT_CONFIG_VALUE_0": fx.remote_url,
            })
            first, _ = controller_call(module, caller, tip_reader, work, "run", native_relation=True)
            moved = fx.advance()
            second, _ = controller_call(module, caller, tip_reader, work, "run", native_relation=True)
            return first == fx.run_tip and second == moved and fx.hits["hostile"] == 0
        if criterion == "local-reads-stay-native":
            caller = fx.caller()
            caller["GIT_CONFIG_COUNT"] = "1"
            caller["GIT_CONFIG_KEY_0"] = "core.hooksPath"
            caller["GIT_CONFIG_VALUE_0"] = str(fx.root)
            environments: list[dict] = []
            real = subprocess.Popen

            def record(*args, **kwargs):
                environments.append(dict(kwargs.get("env") or {}))
                return real(*args, **kwargs)

            with mock.patch.object(module.subprocess, "Popen", side_effect=record):
                built, _ = controller_call(module, caller, module._native_relation_environment)
                commit, _ = controller_call(
                    module, caller, module._native_relation_commit, work, "HEAD", "probe head"
                )
            if built is None or commit is None or not environments:
                return False
            return all(
                set(environment) <= BASE_NATIVE_KEYS | {"SSH_AUTH_SOCK"}
                and environment.get("PATH") == os.defpath
                and environment.get("GIT_CONFIG_GLOBAL") == os.devnull
                and "HOME" not in environment
                for environment in [built, *environments]
            )
        if criterion == "projection-cap-refuses":
            extra = "".join(
                f'[credential "https://cap-{index}.example.invalid"]\n\tusername = cap\n'
                for index in range(PROJECTION_MAX_ENTRIES + 1)
            )
            caller = fx.caller(extra_global=extra)
            tip, message = controller_call(module, caller, tip_reader, work, "run", native_relation=True)
            return (
                tip is None
                and message is not None
                and "credential configuration" in message.lower()
                and fx.hits["remote"] == 0
            )
        if criterion == "authentication-refusal-fixed":
            caller = fx.caller(shape=None)
            tip, message = controller_call(module, caller, tip_reader, work, "run", native_relation=True)
            named = tip is None and message is not None and "authentication" in message.lower()
            named = named and refusal_is_fixed(message, fx)
            fx.git("remote", "set-url", "origin", "http://127.0.0.1:9/fixture/closed.git", cwd=fx.work)
            other, unreachable = controller_call(module, fx.caller(), tip_reader, work, "run", native_relation=True)
            plain = (
                other is None
                and unreachable is not None
                and "could not be read" in unreachable
                and "authentication" not in unreachable.lower()
            )
            return named and plain
        if criterion == "remote-read-children":
            count = 0
            real = subprocess.Popen

            def counted(*args, **kwargs):
                nonlocal count
                count += 1
                return real(*args, **kwargs)

            with mock.patch.object(module.subprocess, "Popen", side_effect=counted):
                tip, _ = controller_call(module, fx.caller(), tip_reader, work, "run", native_relation=True)
            if tip != fx.run_tip:
                # A read that did not succeed cannot evidence its child bound.
                raise SystemExit("probe: the built remote read did not return the served tip")
            return count
        if criterion == "sync-run-module-passes":
            module_path = root / "plugins" / "hexaemeron" / "tests" / "test_native_remote_credentials.py"
            if not module_path.is_file():
                return False
            environment = {
                name: value for name, value in os.environ.items()
                if name not in ("FORCE_COLOR", "CLICOLOR_FORCE")
            }
            environment["NO_COLOR"] = "1"
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-v",
                 "-s", str(module_path.parent), "-p", module_path.name],
                cwd=str(root),
                env=environment,
                capture_output=True,
                timeout=1800,
                check=False,
            )
            text = result.stderr.decode("utf-8", "replace")
            return (
                result.returncode == 0
                and re.search(r"^OK", text, re.MULTILINE) is not None
                and re.search(r"^test\w*sync_run\w* ", text, re.MULTILINE) is not None
            )
    raise SystemExit(f"probe: unknown conformance criterion {criterion}")


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def write_report(out: Path, report: dict) -> None:
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Create-only: a receipted report is never overwritten by a rerun.
    with open(out, "xb") as handle:
        handle.write(data)
    sys.stdout.write(data.decode("utf-8"))
    sys.stdout.write(f"sha256 {hashlib.sha256(data).hexdigest()}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    select = sub.add_parser("select")
    select.add_argument("--candidate", required=True, choices=CANDIDATES)
    select.add_argument("--criterion", required=True, choices=sorted(SELECTION_UNITS))
    select.add_argument("--out", required=True)
    conform = sub.add_parser("conform")
    conform.add_argument("--candidate", required=True, choices=CANDIDATES)
    conform.add_argument("--criterion", required=True, choices=sorted(CONFORMANCE_UNITS))
    conform.add_argument("--root", required=True)
    conform.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if os.path.lexists(out):
        parser.error("--out must not already exist")
    if args.mode == "select":
        value = measure_selection(args.candidate, args.criterion)
        unit = SELECTION_UNITS[args.criterion]
        command = (
            f"python3 .hexaemeron/design/probe.py select --candidate {args.candidate} "
            f"--criterion {args.criterion} --out {args.out}"
        )
    else:
        if args.candidate != SELECTED:
            parser.error(f"only {SELECTED} is built; {args.candidate} has no conformance surface")
        value = measure_conformance(args.criterion, Path(args.root).resolve())
        unit = CONFORMANCE_UNITS[args.criterion]
        command = (
            f"python3 .hexaemeron/design/probe.py conform --candidate {args.candidate} "
            f"--criterion {args.criterion} --root {args.root} --out {args.out}"
        )
    write_report(out, {
        "schema": REPORT_SCHEMA,
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": unit,
        "command": command,
        "exit": 0,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
