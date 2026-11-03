"""The native remote tip read authenticates with the caller's helpers (#2093).

`remote_branch_tip(..., native_relation=True)` reads the caller's
`credential.*` entries with the caller's Git, replays them in command scope
after one empty helper reset, and adds `HOME`. Nothing else the native
relation environment excludes reaches the read, and every local relation read
keeps that environment unchanged.

Every case runs against a loopback fixture: bare repositories served over
dumb HTTP on 127.0.0.1, one of which demands HTTP Basic authentication with a
credential generated for the test. Each caller configuration starts with an
empty `credential.helper` and pins its global and system files, so no real
keychain or GitHub helper runs and no socket leaves the loopback address.
These tests live outside `test_hexctl.py`, which sits at the promise
machine's read ceiling.
"""

import base64
import collections
import contextlib
import http.server
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock

try:
    from plugins.hexaemeron.tests import test_version_relations as relations
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase, hexctl_module
except ModuleNotFoundError:  # direct discovery from this directory
    import test_version_relations as relations
    from test_hexctl import HexctlCase, hexctl_module


NATIVE_GIT = shutil.which("git", path=os.defpath)
RUN_BRANCH = "fiat/native-sync-evidence"
NATIVE_ENVIRONMENT = {
    "PATH": os.defpath,
    "LANG": "C",
    "LC_ALL": "C",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_TERMINAL_PROMPT": "0",
}
AUTHENTICATION = (
    "{label} could not be read: origin refused authentication, and the native "
    "read offers only the credential helpers your Git configuration names"
)
PROJECTION = "{label} could not be read: the caller's Git credential configuration {fault}"
# Child output that must never reach a refusal.
CHILD_MARKERS = (
    "could not read",
    "terminal prompts",
    "Authentication failed",
    "401",
    "fatal:",
    "127.0.0.1",
    "http://",
)


def _write(path, text, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)
    return path


def _closed_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class CredentialFixture:
    """Bare repositories on a loopback server, plus callers to vary.

    `remote` demands HTTP Basic `fixture:<secret>`; `hostile` and `open`
    answer anyone. Every request is counted per repository, so a rewrite that
    reached the hostile endpoint is visible even when the answer looks right.
    """

    def __init__(self):
        if NATIVE_GIT is None:
            raise unittest.SkipTest("no Git on the platform default path")
        self.root = Path(tempfile.mkdtemp(prefix="s2093-"))
        self.secret = "fixture-" + secrets.token_hex(12)
        self.hits = collections.Counter()
        self.protected = {"remote"}
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
        self._start_server()
        self.url_key = f"http://127.0.0.1:{self.port}"
        self._build_tools()

    def git(self, *args, cwd=None):
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

    def url(self, name):
        return f"{self.url_key}/fixture/{name}.git"

    def serve(self, name, source, refs):
        """Publish `refs` (branch to commit) from `source` as `name`."""
        bare = self.served / "fixture" / f"{name}.git"
        if not bare.exists():
            self.git("init", "-q", "--bare", str(bare))
        self.git(
            "push", "-q", "--force", str(bare),
            *[f"{commit}:refs/heads/{branch}" for branch, commit in refs.items()],
            cwd=source,
        )
        self.git("update-server-info", cwd=bare)
        return self.url(name)

    def _start_server(self):
        fixture = self
        expected = "Basic " + base64.b64encode(
            f"fixture:{self.secret}".encode("utf-8")
        ).decode("ascii")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(fixture.served), **kwargs)

            def log_message(self, *args):
                return

            def do_GET(self):  # noqa: N802 - stdlib handler name
                path = self.path.split("?", 1)[0]
                parts = path.split("/")
                if len(parts) < 4 or parts[1] != "fixture" or not parts[2].endswith(".git"):
                    self.send_error(404)
                    return
                name = parts[2][: -len(".git")]
                fixture.hits[name] += 1
                if (
                    name in fixture.protected
                    and self.headers.get("Authorization") != expected
                ):
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

    def build_run(self):
        """A run worktree whose origin is the protected remote.

        The served run branch is a signed-sync shape: `sync` merges the
        product into the base, all over one tree. The worktree's tracking ref
        is stale, so a reader that answered from local refs would be wrong.
        """
        self.seed = self.root / "seed"
        self.git("init", "-q", "-b", "main", str(self.seed))
        self.git("commit", "-q", "--allow-empty", "-m", "root", cwd=self.seed)
        self.root_commit = self.git("rev-parse", "HEAD", cwd=self.seed)
        tree = self.git("rev-parse", "HEAD^{tree}", cwd=self.seed)
        self.product = self.git(
            "commit-tree", tree, "-p", self.root_commit, "-m", "product", cwd=self.seed
        )
        self.base = self.git(
            "commit-tree", tree, "-p", self.root_commit, "-m", "base", cwd=self.seed
        )
        self.sync = self.git(
            "commit-tree", tree, "-p", self.product, "-p", self.base,
            "-m", "sync", cwd=self.seed,
        )
        self.git("update-ref", "refs/heads/main", self.base, cwd=self.seed)
        self.git("update-ref", f"refs/heads/{RUN_BRANCH}", self.sync, cwd=self.seed)
        refs = {"main": self.base, RUN_BRANCH: self.sync}
        self.serve("remote", self.seed, refs)
        self.serve("open", self.seed, refs)

        hostile_seed = self.root / "hostile-seed"
        self.git("init", "-q", "-b", "main", str(hostile_seed))
        self.git("commit", "-q", "--allow-empty", "-m", "hostile", cwd=hostile_seed)
        self.hostile_tip = self.git("rev-parse", "HEAD", cwd=hostile_seed)
        self.serve(
            "hostile", hostile_seed, {"main": self.hostile_tip, RUN_BRANCH: self.hostile_tip}
        )

        self.work = self.root / "work"
        self.git("clone", "-q", "--no-hardlinks", str(self.seed), str(self.work))
        self.git("remote", "set-url", "origin", self.url("remote"), cwd=self.work)
        self.git(
            "update-ref", f"refs/remotes/origin/{RUN_BRANCH}", self.product, cwd=self.work
        )
        self.attacker = self.root / "attacker"
        self.git("init", "-q", "-b", "main", str(self.attacker))
        self.git("remote", "add", "origin", self.url("hostile"), cwd=self.attacker)

    def advance(self):
        """Move the served run branch past the sync commit."""
        tree = self.git("rev-parse", f"{self.sync}^{{tree}}", cwd=self.seed)
        moved = self.git("commit-tree", tree, "-p", self.sync, "-m", "moved", cwd=self.seed)
        self.serve("remote", self.seed, {RUN_BRANCH: moved})
        self.git("fetch", "-q", str(self.seed), moved, cwd=self.work)
        return moved

    def _build_tools(self):
        self.bin = self.root / "caller-bin"
        good = f"username=fixture\npassword={self.secret}\n"
        script = "#!/bin/sh\n" 'test "$1" = get || exit 0\n' "cat <<'EOF'\n" + good + "EOF\n"
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
        self.good_credential = good
        self.wrong_helper = _write(
            self.bin / "fixture-wrong-cred",
            "#!/bin/sh\n"
            'test "$1" = get || exit 0\n'
            "printf 'username=fixture\\npassword=wrong\\n'\n",
            0o700,
        )
        self.order_log = self.root / "helper-order.log"
        self.recorder = _write(
            self.bin / "fixture-recorder",
            "#!/bin/sh\n"
            'test "$2" = get || exit 0\n'
            f'echo "$1" >> "{self.order_log}"\n'
            'test "$1" = local || exit 0\n'
            "cat <<'EOF'\n" + good + "EOF\n",
            0o700,
        )
        # A caller Git that answers the projection read with chosen bytes and
        # hands every other command to the real Git.
        self.fake_bin = self.root / "fake-caller-bin"
        _write(
            self.fake_bin / "git",
            f"#!{sys.executable} -I\n"
            "import os, sys, time\n"
            "args = sys.argv[1:]\n"
            "mode = os.environ.get('FIXTURE_PROJECTION_MODE', '')\n"
            "if '--get-regexp' in args and mode:\n"
            "    if mode == 'exit-128':\n"
            "        sys.stderr.write('fatal: bad config line 1 in file /fixture/secret\\n')\n"
            "        raise SystemExit(128)\n"
            "    if mode == 'sleep':\n"
            "        time.sleep(20)\n"
            "        raise SystemExit(0)\n"
            "    payloads = {\n"
            "        'valueless': b'global\\0credential.usehttppath\\0',\n"
            "        'scope': b'planet\\0credential.helper\\n!x\\0',\n"
            "        'foreign': b'global\\0url.http://h/.insteadof\\nhttp://o/\\0',\n"
            "        'bare-prefix': b'global\\0credential.\\nx\\0',\n"
            "        'unterminated': b'global\\0credential.helper\\n!x',\n"
            "        'odd': b'global\\0credential.helper\\n!x\\0global\\0',\n"
            "        'encoding': b'global\\0credential.helper\\n\\xff\\0',\n"
            "        'empty': b'',\n"
            "        'flood': b'global\\0credential.helper\\n' + b'x' * 70000 + b'\\0',\n"
            "    }\n"
            "    sys.stdout.buffer.write(payloads[mode])\n"
            "    raise SystemExit(0)\n"
            f"os.execv({NATIVE_GIT!r}, [{NATIVE_GIT!r}, *args])\n",
            0o700,
        )

    def helper_lines(self, shape):
        section = f'[credential "{self.url_key}"]'
        if shape is None:
            return []
        if shape == "abs-exec":
            return [section, f"\thelper = {self.helper}"]
        if shape == "bang-abs":
            return [section, f'\thelper = "!{self.helper}"']
        if shape == "bang-path":
            return [section, '\thelper = "!fixture-cred"']
        if shape == "named-path":
            return [section, "\thelper = fixturecred"]
        if shape == "home-store":
            return [section, f'\thelper = "!{self.home_helper}"']
        if shape == "wrong":
            return [section, f'\thelper = "!{self.wrong_helper}"']
        raise AssertionError(f"unknown helper shape {shape}")

    def caller(
        self, *, shape="bang-abs", extra="", system="", global_file=True,
        home=True, reset=True,
    ):
        """A whole caller environment whose credential lives in config only.

        `reset=False` is for a caller whose system file carries the reset.
        """
        self.callers += 1
        base = self.root / f"caller-{self.callers}"
        home_dir = base / "home"
        home_dir.mkdir(parents=True)
        if shape == "home-store":
            _write(home_dir / ".fixture-credential", self.good_credential)
        # The empty reset first: Apple Git's own configuration names
        # osxkeychain, and no test may reach a real keychain.
        lines = [*(["[credential]", "\thelper ="] if reset else []), *self.helper_lines(shape)]
        global_text = "\n".join(lines) + "\n" + extra
        tmp = base / "tmp"
        tmp.mkdir()
        environment = {
            "PATH": f"{self.bin}{os.pathsep}{os.defpath}",
            "LANG": "C",
            "LC_ALL": "C",
            "TMPDIR": str(tmp),
            "GIT_CONFIG_SYSTEM": str(_write(base / "system.gitconfig", system)),
            "GIT_TERMINAL_PROMPT": "0",
        }
        if home:
            environment["HOME"] = str(home_dir)
        if global_file:
            environment["GIT_CONFIG_GLOBAL"] = str(
                _write(base / "global.gitconfig", global_text)
            )
        else:
            _write(home_dir / ".gitconfig", global_text)
        self.caller_home = home_dir
        self.caller_base = base
        return environment

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.root, ignore_errors=True)


def call(module, caller, function, *args, **kwargs):
    """Run one controller function with `caller` as its whole environment."""
    stderr = io.StringIO()
    with mock.patch.dict(os.environ, caller, clear=True), contextlib.redirect_stderr(stderr):
        try:
            return function(*args, **kwargs), None
        except SystemExit:
            return None, stderr.getvalue()


@contextlib.contextmanager
def recorded_children(module):
    """Every child the controller starts, with its argv and environment."""
    children = []
    real = subprocess.Popen

    def record(argv, *args, **kwargs):
        env = kwargs.get("env")
        children.append(
            {"argv": list(argv), "env": None if env is None else dict(env)}
        )
        return real(argv, *args, **kwargs)

    with mock.patch.object(module.subprocess, "Popen", side_effect=record):
        yield children


def refusal(text):
    return f"hexctl: error: {text}\n"


class NativeRemoteCase(unittest.TestCase):
    """Each case is a subtest on its own fresh loopback fixture.

    `plugins/hexaemeron/tests/run_tests.py` caps its manifest of test ids at
    409,600 bytes, and the suite had 963 bytes left when this module landed,
    so the cases are subtests of a few short-named methods rather than one
    method each.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = hexctl_module()

    @contextlib.contextmanager
    def case(self, name, **params):
        with self.subTest(name, **params):
            fx = CredentialFixture()
            try:
                fx.build_run()
                self.fx = fx
                self.work = str(fx.work)
                yield fx
            finally:
                fx.close()

    def read(self, caller, label="remote run branch tip", **kwargs):
        return call(
            self.module,
            caller,
            self.module.remote_branch_tip,
            self.work,
            RUN_BRANCH,
            label,
            native_relation=kwargs.pop("native_relation", True),
            **kwargs,
        )

    def assert_fixed(self, message):
        self.assertIsNotNone(message)
        for marker in (*CHILD_MARKERS, str(self.fx.port), self.fx.secret):
            self.assertNotIn(marker, message)

    def assert_authentication(self, tip, message, label="remote run branch tip"):
        self.assertIsNone(tip)
        self.assertEqual(message, refusal(AUTHENTICATION.format(label=label)))
        self.assert_fixed(message)

    def projection(self, fault):
        return PROJECTION.format(label="remote run branch tip", fault=fault)


class NativeReads(NativeRemoteCase):
    def test_reads(self):
        for shape in ("abs-exec", "bang-abs", "home-store"):
            with self.case("global helper authenticates", shape=shape) as fx:
                tip, message = self.read(fx.caller(shape=shape))
                self.assertIsNone(message)
                self.assertEqual(tip, fx.sync)
                self.assertGreater(fx.hits["remote"], 0)

        with self.case("two children, neither carries the credential") as fx:
            with recorded_children(self.module) as children:
                tip, message = self.read(fx.caller())
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(len(children), 2)
            reader, read = children
            self.assertEqual(
                reader["argv"],
                ["git", "config", "--includes", "--show-scope", "-z",
                 "--get-regexp", r"^credential\."],
            )
            self.assertEqual(
                read["argv"],
                [NATIVE_GIT, "--no-replace-objects", "ls-remote", "--refs",
                 "origin", f"refs/heads/{RUN_BRANCH}"],
            )
            for child in children:
                exposed = [*child["argv"], *child["env"].values()]
                self.assertFalse(any(fx.secret in item for item in exposed))

        with self.case("a moved remote tip is read again") as fx:
            caller = fx.caller()
            first, _ = self.read(caller)
            moved = fx.advance()
            second, message = self.read(caller)
            self.assertIsNone(message)
            self.assertEqual(first, fx.sync)
            self.assertEqual(second, moved)

        with self.case("helpers run in the caller's order after the reset") as fx:
            # System, global, then local, as the caller's Git offers them.
            # Without the leading reset the native read would try its own
            # local helper first and stop there.
            system = (
                "[credential]\n\thelper =\n"
                f'[credential "{fx.url_key}"]\n\thelper = "!{fx.recorder} system"\n'
            )
            extra = f'[credential "{fx.url_key}"]\n\thelper = "!{fx.recorder} global"\n'
            fx.git(
                "config", f"credential.{fx.url_key}.helper", f"!{fx.recorder} local",
                cwd=fx.work,
            )
            tip, message = self.read(
                fx.caller(shape=None, system=system, extra=extra, reset=False)
            )
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(
                fx.order_log.read_text(encoding="utf-8").split(),
                ["system", "global", "local"],
            )

        with self.case("a helper's standard error is not the answer") as fx:
            # Git hands every helper its own error stream. A PATH-only helper
            # that fails, then a working helper that writes a note, still
            # authenticate as the caller's Git does.
            noisy = _write(
                fx.bin / "fixture-noisy-cred",
                "#!/bin/sh\n"
                'echo "fixture helper note" >&2\n'
                f'exec "{fx.helper}" "$@"\n',
                0o700,
            )
            extra = (
                f'[credential "{fx.url_key}"]\n'
                '\thelper = "!fixture-cred"\n'
                f'\thelper = "!{noisy}"\n'
            )
            tip, message = self.read(fx.caller(shape=None, extra=extra))
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)

        with self.case("a caller Git that traces to standard error still projects") as fx:
            # trace2 output from the caller's own configuration lands on the
            # projection reader's standard error, never in the parsed entries.
            extra = "[trace2]\n\tnormalTarget = true\n"
            tip, message = self.read(fx.caller(extra=extra))
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)

        with self.case("a helper's lingering child does not hold the read") as fx:
            # The child keeps Git's error stream open for 30 seconds. The read
            # ends when Git exits, well inside its patched 5-second timeout,
            # which would otherwise refuse with a message.
            pid_file = fx.root / "linger.pid"
            linger = _write(
                fx.bin / "fixture-linger-cred",
                "#!/bin/sh\n"
                'test "$1" = get || exit 0\n'
                f'sleep 30 >/dev/null </dev/null & echo $! > "{pid_file}"\n'
                f'exec "{fx.helper}" "$@"\n',
                0o700,
            )
            extra = f'[credential "{fx.url_key}"]\n\thelper = "!{linger}"\n'
            started = time.monotonic()
            with mock.patch.object(self.module, "GIT_TIMEOUT", 5):
                tip, message = self.read(fx.caller(shape=None, extra=extra))
            elapsed = time.monotonic() - started
            with contextlib.suppress(OSError, ValueError):
                os.kill(int(pid_file.read_text(encoding="utf-8")), signal.SIGTERM)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertLess(elapsed, 15)

        with self.case("no credential configuration keeps the native environment") as fx:
            fx.git("remote", "set-url", "origin", fx.url("open"), cwd=fx.work)
            empty = _write(fx.root / "empty.gitconfig", "")
            caller = {
                **fx.caller(shape=None),
                "GIT_CONFIG_GLOBAL": str(empty),
                "GIT_CONFIG_NOSYSTEM": "1",
            }
            with recorded_children(self.module) as children:
                tip, message = self.read(caller)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(
                children[-1]["env"], {**NATIVE_ENVIRONMENT, "HOME": caller["HOME"]}
            )

        with self.case("a caller without HOME reads without it") as fx:
            with recorded_children(self.module) as children:
                tip, message = self.read(fx.caller(home=False))
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertNotIn("HOME", children[-1]["env"])

        with self.case("an inline helper secret travels only in the child") as fx:
            # The written limit: a helper string that embeds a secret reaches
            # the native read's environment as Git would read it, and no argv.
            inline = (
                f'[credential "{fx.url_key}"]\n'
                "\thelper = \"!f() { test \\\"$1\\\" = get && "
                f"printf 'username=fixture\\\\npassword={fx.secret}\\\\n'; }}; f\"\n"
            )
            with recorded_children(self.module) as children:
                tip, message = self.read(fx.caller(shape=None, extra=inline))
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            reader, read = children
            self.assertFalse(any(fx.secret in item for item in read["argv"]))
            self.assertTrue(any(fx.secret in value for value in read["env"].values()))
            self.assertFalse(any(fx.secret in value for value in reader["env"].values()))

    def test_inert(self):
        def rewrite(fx):
            return f'[url "{fx.url("hostile")}"]\n\tinsteadOf = {fx.url("remote")}\n'

        def home_file(caller, relative, text):
            _write(Path(caller["HOME"]) / relative, text)
            return caller

        channels = {
            "global-file": lambda fx: fx.caller(extra=rewrite(fx)),
            "home-gitconfig": lambda fx: fx.caller(extra=rewrite(fx), global_file=False),
            "xdg-config": lambda fx: home_file(
                fx.caller(global_file=False), ".config/git/config", rewrite(fx)
            ),
            "config-count": lambda fx: {
                **fx.caller(),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.{fx.url('hostile')}.insteadOf",
                "GIT_CONFIG_VALUE_0": fx.url("remote"),
            },
            "config-parameters": lambda fx: {
                **fx.caller(),
                "GIT_CONFIG_PARAMETERS":
                    f"'url.{fx.url('hostile')}.insteadof'='{fx.url('remote')}'",
            },
        }
        for name, build in channels.items():
            with self.case("hostile insteadOf is inert", channel=name) as fx:
                tip, message = self.read(build(fx))
                self.assertIsNone(message)
                self.assertEqual(tip, fx.sync)
                self.assertEqual(fx.hits["hostile"], 0)

        with self.case("a helper's standard error cannot name a tip") as fx:
            # Origin has no such branch; the only ref line is the helper's.
            forger = _write(
                fx.bin / "fixture-forging-cred",
                "#!/bin/sh\n"
                'test "$1" = get || exit 0\n'
                f"printf '%s\\trefs/heads/fiat/absent\\n' '{fx.hostile_tip}' >&2\n"
                f'exec "{fx.helper}" "$@"\n',
                0o700,
            )
            caller = fx.caller(
                shape=None,
                extra=f'[credential "{fx.url_key}"]\n\thelper = "!{forger}"\n',
            )
            tip, message = call(
                self.module, caller, self.module.remote_branch_tip, self.work,
                "fiat/absent", "remote run branch tip", native_relation=True,
            )
            self.assertIsNone(tip)
            self.assertEqual(message, refusal(
                "remote run branch tip names no ref: origin has no "
                "refs/heads/fiat/absent. A deleted branch reads this way; "
                "restore it at its recorded commit and retry"
            ))

        with self.case("only credential entries cross") as fx:
            included = _write(
                fx.root / "included.gitconfig",
                "\n".join(fx.helper_lines("bang-abs"))
                + f'\n[url "{fx.url("hostile")}"]\n'
                f"\tinsteadOf = {fx.url('remote')}\n",
            )
            extra = (
                f"[include]\n\tpath = {included}\n"
                f"[http]\n\tproxy = http://127.0.0.1:{_closed_port()}\n"
                "[core]\n\tsshCommand = /nonexistent/hostile-ssh\n"
                "\taskPass = /nonexistent/hostile-askpass\n"
            )
            with recorded_children(self.module) as children:
                tip, message = self.read(fx.caller(shape=None, extra=extra))
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(fx.hits["hostile"], 0)
            env = children[-1]["env"]
            count = int(env["GIT_CONFIG_COUNT"])
            keys = [env[f"GIT_CONFIG_KEY_{index}"] for index in range(count)]
            values = [env[f"GIT_CONFIG_VALUE_{index}"] for index in range(count)]
            self.assertTrue(all(key.startswith("credential.") for key in keys))
            self.assertEqual((keys[0], values[0]), ("credential.helper", ""))
            # The included file's helper crossed; its rewrite did not.
            self.assertIn(f"!{fx.helper}", values)

        with self.case("replace objects and alternates leave the answer") as fx:
            hostile = fx.git(
                "commit-tree", f"{fx.sync}^{{tree}}", "-m", "replacement", cwd=fx.work
            )
            fx.git("replace", fx.sync, hostile, cwd=fx.work)
            caller = {
                **fx.caller(extra="[core]\n\tuseReplaceRefs = true\n"),
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(fx.attacker / ".git" / "objects"),
                "GIT_REPLACE_REF_BASE": "refs/replace/",
            }
            with recorded_children(self.module) as children:
                tip, message = self.read(caller)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            for name in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE"):
                self.assertNotIn(name, children[0]["env"])
                self.assertNotIn(name, children[1]["env"])
            parents, message = call(
                self.module, caller, self.module._native_relation_parents,
                self.work, fx.sync, "replaced sync",
            )
            self.assertIsNone(message)
            self.assertEqual(parents, [fx.product, fx.base])

        with self.case("inherited repository and loader variables stay out") as fx:
            # A local reset and a wrong helper in the attacker's repository: if
            # GIT_DIR reached the reader, they would clear the right helper.
            fx.git("config", "credential.helper", "", cwd=fx.attacker)
            fx.git(
                "config", "--add", "credential.helper", f"!{fx.wrong_helper}",
                cwd=fx.attacker,
            )
            loader = fx.root / "loader"
            loader.mkdir()
            caller = {
                **fx.caller(),
                "GIT_DIR": str(fx.attacker / ".git"),
                "GIT_WORK_TREE": str(fx.attacker),
                "GIT_CONFIG_PARAMETERS": f"'credential.helper'='!{fx.wrong_helper}'",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.{fx.url('hostile')}.insteadOf",
                "GIT_CONFIG_VALUE_0": fx.url("remote"),
                "DYLD_LIBRARY_PATH": str(loader),
                "LD_LIBRARY_PATH": str(loader),
            }
            with recorded_children(self.module) as children:
                tip, message = self.read(caller)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(fx.hits["hostile"], 0)
            reader, read = (child["env"] for child in children)
            for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_PARAMETERS"):
                self.assertNotIn(name, reader)
                self.assertNotIn(name, read)
            for name in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
                self.assertNotIn(name, reader)
            # The read's own GIT_CONFIG_* pairs are the projection alone.
            self.assertFalse(any(
                fx.url("hostile") in value or str(fx.wrong_helper) in value
                for value in read.values()
            ))
            # The accepted reach: the caller's own Git keeps the caller's
            # loader variables; the native read never sees them.
            self.assertEqual(reader["DYLD_LIBRARY_PATH"], str(loader))
            self.assertEqual(reader["GIT_CONFIG_GLOBAL"], caller["GIT_CONFIG_GLOBAL"])
            self.assertNotIn("DYLD_LIBRARY_PATH", read)
            self.assertNotIn("LD_LIBRARY_PATH", read)
            allowed = {*NATIVE_ENVIRONMENT, "HOME", "GIT_CONFIG_COUNT"}
            for name in read:
                self.assertTrue(
                    name in allowed
                    or name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")),
                    name,
                )
            self.assertEqual(read["PATH"], os.defpath)
            self.assertEqual(read["GIT_CONFIG_GLOBAL"], os.devnull)

    def test_refusals(self):
        # The selected design keeps PATH at the platform default, so these two
        # shapes are the recorded trade, refused with the fixed text.
        for shape in ("bang-path", "named-path", None, "wrong"):
            with self.case("refused as authentication", shape=shape) as fx:
                self.assert_authentication(*self.read(fx.caller(shape=shape)))

        with self.case("an unreachable origin keeps the plain refusal") as fx:
            fx.git(
                "remote", "set-url", "origin",
                f"http://127.0.0.1:{_closed_port()}/fixture/closed.git",
                cwd=fx.work,
            )
            tip, message = self.read(fx.caller())
            self.assertIsNone(tip)
            self.assertEqual(message, refusal("remote run branch tip could not be read"))

        with self.case("the projection's entry bound is inclusive") as fx:
            # The reset and the helper are two entries; 62 more reach the cap.
            entries = "".join(
                f'[credential "https://cap-{index}.example.invalid"]\n\tusername = cap\n'
                for index in range(62)
            )
            at_cap = {**fx.caller(extra=entries), "GIT_CONFIG_NOSYSTEM": "1"}
            tip, message = self.read(at_cap)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            over = {
                **fx.caller(extra=entries + entries[: entries.index("[", 1)]),
                "GIT_CONFIG_NOSYSTEM": "1",
            }
            tip, message = self.read(over)
            self.assertIsNone(tip)
            self.assertEqual(message, refusal(self.projection("exceeds its bound")))

    def test_unchanged(self):
        with self.case("local relation reads keep the native environment") as fx:
            caller = {
                **fx.caller(),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": str(fx.root),
            }
            built, _ = call(self.module, caller, self.module._native_relation_environment)
            self.assertEqual(built, NATIVE_ENVIRONMENT)
            with recorded_children(self.module) as children:
                head, message = call(
                    self.module, caller, self.module._native_relation_commit,
                    self.work, "HEAD", "local head",
                )
                parents, _ = call(
                    self.module, caller, self.module._native_relation_parents,
                    self.work, fx.sync, "local sync",
                )
            self.assertIsNone(message)
            self.assertEqual(head, fx.base)
            self.assertEqual(parents, [fx.product, fx.base])
            self.assertEqual(len(children), 2)
            for child in children:
                self.assertEqual(child["env"], NATIVE_ENVIRONMENT)

        with self.case("caller-environment remote reads are unchanged") as fx:
            with recorded_children(self.module) as children:
                tip, message = self.read(fx.caller(), native_relation=False)
            self.assertIsNone(message)
            self.assertEqual(tip, fx.sync)
            self.assertEqual(
                children,
                [{"argv": ["git", "ls-remote", "--refs", "origin",
                           f"refs/heads/{RUN_BRANCH}"],
                  "env": None}],
            )


class SyncRun(NativeRemoteCase):
    """`done sync-run` in a disposable run, with only external effects patched."""

    def seed(self):
        fx = self.fx
        state = {
            "phase": "integrate",
            "halted": None,
            "base": fx.root_commit,
            "run_branch": RUN_BRANCH,
            "config": {"git": {"base": "main"}},
            "receipts": {},
            "steps": [{"n": 1, "receipts": {}, "audit": {}}],
            "integrate": {
                "merged": [1],
                "merges": {"1": {"merge_commit": fx.product}},
            },
        }
        os.makedirs(os.path.join(self.work, ".hexaemeron"))
        self.module.commit(self.work, state, "fixture:seed", {})

    def run_bytes(self):
        paths = (self.module.state_path(self.work), self.module.ledger_path(self.work))
        return tuple(Path(path).read_bytes() for path in paths)

    def sync_run(self, caller):
        args = SimpleNamespace(
            dir=self.work,
            commit=self.fx.sync,
            base_commit=self.fx.base,
            revalidation="ignored.json",
            supersede_sync=None,
            reason=None,
        )
        state = json.loads(
            Path(self.module.state_path(self.work)).read_text(encoding="utf-8")
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(self.module, "verify_run"),
            mock.patch.object(
                self.module, "_integrate_directive", return_value={"do": "integrate"}
            ),
            mock.patch.object(
                self.module, "integration_revalidation_record", return_value={"checks": []}
            ),
            mock.patch.object(self.module, "verify_local_commit", return_value=self.fx.sync),
            mock.patch.object(
                self.module, "verify_github_commits", return_value=[self.fx.sync]
            ),
            contextlib.redirect_stdout(stdout),
        ):
            _, message = call(self.module, caller, self.module.done_sync_run, args, state)
        return message, stdout.getvalue()

    def refused_before_contact(self, caller, expected):
        before = self.run_bytes()
        message, _ = self.sync_run(caller)
        self.assertEqual(message, refusal(expected))
        self.assert_fixed(message)
        self.assertEqual(self.fx.hits["remote"], 0)
        self.assertEqual(self.run_bytes(), before)

    def fake_caller(self, mode):
        caller = self.fx.caller()
        caller["PATH"] = f"{self.fx.fake_bin}{os.pathsep}{caller['PATH']}"
        caller["FIXTURE_PROJECTION_MODE"] = mode
        return caller

    def test_sync_run_receipts(self):
        with self.case("receipts against a helper-only remote") as fx:
            self.seed()
            message, stdout = self.sync_run(fx.caller())
            self.assertIsNone(message)
            self.assertIn("integration may continue", stdout)
            state_bytes, ledger_bytes = self.run_bytes()
            state = json.loads(state_bytes)
            last = json.loads(ledger_bytes.splitlines()[-1])
            self.assertEqual(last["event"], "done:sync-run")
            self.assertEqual(last["data"]["commit"], fx.sync)
            self.assertEqual(state["integrate"]["sync"]["commit"], fx.sync)
            self.assertEqual(state["integrate"]["sync"]["parents"], [fx.product, fx.base])
            self.assertGreater(fx.hits["remote"], 0)
            for recorded in (state_bytes, ledger_bytes):
                self.assertNotIn(fx.secret.encode(), recorded)
                self.assertNotIn(str(fx.helper).encode(), recorded)

        with self.case("refuses a sync commit the remote tip moved past") as fx:
            self.seed()
            fx.advance()
            before = self.run_bytes()
            message, _ = self.sync_run(fx.caller())
            self.assertEqual(
                message, refusal("run sync commit does not match the remote run branch tip")
            )
            self.assertEqual(self.run_bytes(), before)

    def test_sync_run_refusals(self):
        unreadable = self.projection("could not be read")
        malformed = self.projection("is malformed")
        bound = self.projection("exceeds its bound")
        entries = "".join(
            f'[credential "https://cap-{index}.example.invalid"]\n\tusername = cap\n'
            for index in range(64)
        )
        big = '[credential "https://big.example.invalid"]\n\tusername = ' + "a" * 16384 + "\n"
        cases = [
            ("no caller git", unreadable,
             lambda fx: {**fx.caller(), "PATH": str(fx.root / "no-git-here")}),
            ("caller git refuses", unreadable, lambda fx: self.fake_caller("exit-128")),
            *[(f"malformed {mode}", malformed, lambda fx, mode=mode: self.fake_caller(mode))
              for mode in ("valueless", "scope", "foreign", "bare-prefix",
                           "unterminated", "odd", "encoding", "empty")],
            ("real valueless key", malformed,
             lambda fx: fx.caller(extra="[credential]\n\tuseHttpPath\n")),
            ("over the entry bound", bound, lambda fx: fx.caller(extra=entries)),
            ("over the byte bound", bound, lambda fx: fx.caller(extra=big)),
            ("over the output cap", bound, lambda fx: self.fake_caller("flood")),
        ]
        for name, expected, build in cases:
            with self.case(name) as fx:
                self.seed()
                self.refused_before_contact(build(fx), expected)
        with self.case("caller git stalls") as fx, mock.patch.object(
            self.module, "GIT_TIMEOUT", 1
        ):
            self.seed()
            self.refused_before_contact(self.fake_caller("sleep"), unreadable)


class Resolution(HexctlCase):
    """`build_version_resolution` makes its four reads through the same seam."""

    _fixture = relations.VersionRelationTests.__dict__
    ledger_path = _fixture["ledger_path"]
    skill_path = _fixture["skill_path"]
    skill = _fixture["skill"]
    chain_ledger = _fixture["chain_ledger"]
    install_chain = _fixture["install_chain"]
    integrate_state = _fixture["integrate_state"]
    commit_seed = _fixture["commit_seed"]
    relation_block = _fixture["relation_block"]
    receipt_runbook = _fixture["receipt_runbook"]

    def setUp(self):
        super().setUp()
        # The relation run needs the real object database, not the delivery
        # shim's `git show`.
        self.env["PATH"] = os.pathsep.join(self.env["PATH"].split(os.pathsep)[1:])

    def test_resolution_reads(self):
        self.install_chain("fiat", (2,))
        anchor = self.commit_seed()
        _, state = self.receipt_runbook("fiat")
        self.install_chain("fiat", (2, 3))
        self.git("add", "-A")
        self.git("commit", "-m", "candidate relation generation")
        head = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.integrate_state(state, head)
        fx = CredentialFixture()
        self.addCleanup(fx.close)
        url = fx.serve("remote", self.target, {"main": anchor, state["run_branch"]: head})
        self.git("remote", "add", "origin", url)
        module = hexctl_module()

        receipt, message = call(
            module, fx.caller(), module.build_version_resolution, self.target, state
        )
        self.assertIsNone(message)
        self.assertEqual(receipt["base_commit"], anchor)
        self.assertEqual(receipt["head_commit"], head)
        self.assertGreater(fx.hits["remote"], 0)

        receipt, message = call(
            module, fx.caller(shape=None), module.build_version_resolution, self.target, state
        )
        self.assertIsNone(receipt)
        self.assertEqual(
            message,
            refusal(AUTHENTICATION.format(label="version resolution base ref")),
        )


if __name__ == "__main__":
    unittest.main()
