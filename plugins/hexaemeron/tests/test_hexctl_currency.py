"""The controller-currency gate suite, in its own module.

`test_hexctl.py` is cited as authored law by the promise machine, whose
bounded read refuses a contract over 262144 bytes; the gate suite did not
fit in the file's remaining headroom. The class drives the same CLI surface
through the same fixtures -- `HexctlCase` and its fake delivery tools -- so
only the file boundary moved, not the arrangement under test.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import (
        HEXCTL,
        HexctlCase,
        hexctl_module,
        run_target,
    )
except ModuleNotFoundError:
    from test_hexctl import (
        HEXCTL,
        HexctlCase,
        hexctl_module,
        run_target,
    )


PROVENANCE_FIELDS = {
    "ledger_version",
    "route",
    "pin",
    "observed_head",
    "verdict",
    "warning",
    "waiver",
}
"""Every key the controller-currency receipt and init transition carry."""


class TestControllerCurrency(HexctlCase):
    """The init gate on the running controller's pin-versus-upstream verdict.

    The pre-fix red these guards captured: the entry controller recorded only
    topic, base and run branch at init, so a fabricated behind pin started a
    run silently. Each test here fails when the `observe_controller_currency`
    call is removed from `cmd_init`.
    """

    PIN = "b" * 40
    HEAD = "a" * 40

    def install_layout(self, pin=PIN, head="ref: refs/heads/main\n",
                       registry=None, clone=True, ledger=True):
        """A fabricated host install around a cache copy of the controller.

        Builds `<root>/cache/<marketplace>/<plugin>/<version>/skills/fiat/
        scripts/hexctl.py` with the registry and marketplace clone beside it,
        so the copy observes the git-backed route with no real install and no
        network: the fake `git` on PATH answers the one `ls-remote`.
        """
        root = os.path.join(self.dir, "plugins-root")
        install = os.path.join(root, "cache", "wildcat-labs", "hexaemeron",
                               "1.5.9")
        scripts = os.path.join(install, "skills", "fiat", "scripts")
        os.makedirs(scripts)
        controller = os.path.join(scripts, "hexctl.py")
        shutil.copyfile(HEXCTL, controller)
        if ledger:
            with open(os.path.join(install, "skills", "fiat", "EVOLUTION.md"),
                      "w", encoding="utf-8") as handle:
                handle.write("- Current version: `fiat-vTEST`\n")
        if registry is None:
            registry = json.dumps({
                "version": 2,
                "plugins": {
                    "hexaemeron@wildcat-labs": [{
                        "scope": "user",
                        "installPath": install + os.sep,
                        "version": "1.5.9",
                        "installedAt": "2026-08-24T00:00:00Z",
                        "gitCommitSha": pin,
                    }],
                },
            })
        if registry is not False:
            with open(os.path.join(root, "installed_plugins.json"), "w",
                      encoding="utf-8") as handle:
                handle.write(registry)
        if clone:
            clone_git = os.path.join(root, "marketplaces", "wildcat-labs",
                                     ".git")
            os.makedirs(clone_git)
            if head is not None:
                with open(os.path.join(clone_git, "HEAD"), "w",
                          encoding="utf-8") as handle:
                    handle.write(head)
        return controller

    def run_installed_ctl(self, controller, *args, expect=0, extra_env=None):
        """Drive one cache copy of the controller against this checkout."""
        env = dict(self.env)
        env["FAKE_GIT_REFS"] = json.dumps({"main": self.HEAD})
        env["FAKE_GIT_PARENTS"] = "{}"
        env["FAKE_GH_PRS"] = "{}"
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            [sys.executable, controller, *args],
            cwd=self.dir,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"installed hexctl {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\n"
                f"stderr: {proc.stderr}"
            )
        return proc

    def provenance(self):
        """The controller-currency receipt and init transition, read back."""
        target = run_target(self.dir)
        with open(os.path.join(target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as handle:
            state = json.load(handle)
        with open(os.path.join(target, ".hexaemeron", "ledger.jsonl"),
                  encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        receipt = state["receipts"]["controller_currency"]
        transition = entries[0]["data"]["controller_currency"]
        self.assertEqual(entries[0]["event"], "init")
        self.assertEqual(receipt, transition)
        self.assertEqual(set(receipt), PROVENANCE_FIELDS)
        return receipt

    def porcelain(self):
        """The target tree's untracked and modified paths, lock aside.

        The lock file under `.hexaemeron/` is excluded: every refused init
        leaves it, with or without this gate, because the lock is taken
        before the command runs.
        """
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.dir, capture_output=True, text=True, check=True,
        )
        return sorted(line for line in status.stdout.splitlines()
                      if line.strip() and ".hexaemeron" not in line)

    def assert_tree_untouched(self, before):
        """No worktree, state, ledger or breadcrumb after a refusal."""
        state_root = os.path.join(self.dir, ".hexaemeron")
        for name in ("state.json", "ledger.jsonl", "worktree"):
            self.assertFalse(os.path.exists(os.path.join(state_root, name)),
                             f"a refused init recorded {name}")
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tmp")))
        self.assertEqual(self.porcelain(), before,
                         "a refused init changed the target tree")
        trees = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.dir, capture_output=True, text=True, check=True,
        )
        self.assertEqual(len(trees.stdout.strip().splitlines()), 1,
                         "a refused init left a worktree behind")

    # ------------------------------------------------- git-backed route

    def test_init_refuses_a_proven_behind_pin_before_any_mutation(self):
        controller = self.install_layout()
        before = self.porcelain()
        proc = self.run_installed_ctl(controller, "init", "--topic", "t",
                                      expect=1)
        self.assertIn("controller currency", proc.stderr)
        self.assertIn(self.PIN, proc.stderr)
        self.assertIn(self.HEAD, proc.stderr)
        self.assertIn("installer", proc.stderr)
        self.assertIn("--controller-currency-waiver", proc.stderr)
        self.assertNotIn("https://", proc.stderr)
        self.assert_tree_untouched(before)

    def test_init_waiver_proceeds_on_behind_and_records_the_reason(self):
        controller = self.install_layout()
        self.run_installed_ctl(
            controller, "init", "--topic", "t",
            "--controller-currency-waiver", "pin refresh needs the operator",
        )
        receipt = self.provenance()
        self.assertEqual(receipt["ledger_version"], "fiat-vTEST")
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["pin"], self.PIN)
        self.assertEqual(receipt["observed_head"], self.HEAD)
        self.assertEqual(receipt["verdict"], "behind")
        self.assertIsNone(receipt["warning"])
        self.assertEqual(receipt["waiver"], "pin refresh needs the operator")

    def test_init_refuses_an_empty_waiver_reason(self):
        controller = self.install_layout()
        before = self.porcelain()
        proc = self.run_installed_ctl(
            controller, "init", "--topic", "t",
            "--controller-currency-waiver", "   ", expect=2,
        )
        self.assertIn("reason", proc.stderr)
        self.assert_tree_untouched(before)

    def test_init_current_pin_proceeds_with_provenance(self):
        controller = self.install_layout(pin=self.HEAD)
        proc = self.run_installed_ctl(controller, "init", "--topic", "t")
        # Scoped to currency. A run naming no task issue also warns that it read
        # no filed decision, which is that gate's own report rather than drift
        # in this one.
        self.assertNotIn("controller currency", proc.stderr)
        self.assertNotIn("older than a Fiat", proc.stderr)
        self.assertNotIn("currency is unknown", proc.stderr)
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["verdict"], "current")
        self.assertEqual(receipt["pin"], self.HEAD)
        self.assertEqual(receipt["observed_head"], self.HEAD)
        self.assertIsNone(receipt["waiver"])

    def test_init_remote_url_confined_to_the_marketplace_clone(self):
        """A hostile target repository cannot steer where the read goes.

        The target's own config carries a URL rewrite; the observation must
        run inside the marketplace clone and name the remote `origin`, so the
        rewrite never applies and no URL string passes through the
        controller at all.
        """
        subprocess.run(
            ["git", "config", "url.https://evil.example/.insteadOf",
             "https://github.com/"],
            cwd=self.dir, check=True, capture_output=True,
        )
        controller = self.install_layout(pin=self.HEAD)
        log = os.path.join(self.dir, "ls-remote.log")
        self.run_installed_ctl(controller, "init", "--topic", "t",
                               extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        with open(log, encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(calls), 1, "exactly one upstream read at init")
        clone = os.path.realpath(
            os.path.join(self.dir, "plugins-root", "marketplaces",
                         "wildcat-labs"))
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), clone)
        self.assertEqual(
            calls[0]["args"],
            ["ls-remote", "--refs", "origin", "refs/heads/main"],
        )
        self.assertNotIn("evil.example", json.dumps(self.provenance()))

    # ------------------------------------------- managed and in-repo routes

    def test_init_managed_route_proceeds_without_a_network_read(self):
        """Managed means the registry records no pin; nothing is read remote.

        The marketplace clone is present in this fixture on purpose: the
        managed route is decided by the absent pin, and even an available
        clone is not read.
        """
        controller = self.install_layout(pin=None)
        log = os.path.join(self.dir, "ls-remote.log")
        self.run_installed_ctl(controller, "init", "--topic", "t",
                               extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        self.assertFalse(os.path.exists(log),
                         "the managed route made a network read")
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "managed")
        self.assertEqual(receipt["verdict"], "managed")
        self.assertIsNone(receipt["pin"])
        self.assertIsNone(receipt["observed_head"])

    def test_init_pinned_install_with_missing_clone_reads_unknown(self):
        """Deleting the marketplace clone must not read as `managed` (S2-R1-02).

        A registry pin makes the install git-backed; with the clone gone the
        head is unobservable, so the verdict is `unknown` with a named warning
        and the pin still recorded -- never a warning-free `managed` that
        silences the gate.
        """
        controller = self.install_layout(clone=False)
        log = os.path.join(self.dir, "ls-remote.log")
        receipt = self.assert_unknown_proceeds(
            controller, "clone-missing",
            extra_env={"FAKE_GIT_LS_REMOTE_LOG": log})
        self.assertFalse(os.path.exists(log),
                         "a missing clone still made a network read")
        self.assertEqual(receipt["route"], "git-backed")
        self.assertEqual(receipt["pin"], self.PIN)

    def test_init_in_repo_route_records_nulls_and_no_pin(self):
        log = os.path.join(self.dir, "ls-remote.log")
        self.env["FAKE_GIT_LS_REMOTE_LOG"] = log
        try:
            self.init()
        finally:
            self.env.pop("FAKE_GIT_LS_REMOTE_LOG", None)
        self.assertFalse(os.path.exists(log),
                         "the in-repo route made a network read")
        receipt = self.provenance()
        self.assertEqual(receipt["route"], "in-repo-source")
        self.assertEqual(receipt["verdict"], "no-pin")
        self.assertIsNone(receipt["pin"])
        self.assertIsNone(receipt["observed_head"])
        self.assertTrue(receipt["ledger_version"].startswith("fiat-v"))

    # ------------------------------------------------- hostile registry

    def assert_unknown_proceeds(self, controller, warning, extra_env=None):
        proc = self.run_installed_ctl(controller, "init", "--topic", "t",
                                      extra_env=extra_env)
        self.assertIn("controller currency", proc.stderr)
        self.assertIn(warning, proc.stderr)
        receipt = self.provenance()
        self.assertEqual(receipt["verdict"], "unknown")
        self.assertEqual(receipt["warning"], warning)
        self.assertIsNone(receipt["observed_head"])
        return receipt

    def test_init_missing_registry_is_unknown_and_warns(self):
        controller = self.install_layout(registry=False)
        receipt = self.assert_unknown_proceeds(controller, "registry-missing")
        self.assertEqual(receipt["route"], "unknown")
        self.assertIsNone(receipt["pin"])

    def test_init_malformed_registry_json_is_unknown(self):
        controller = self.install_layout(registry="{not json")
        self.assert_unknown_proceeds(controller, "registry-malformed")

    def test_init_wrong_kind_registry_is_unknown(self):
        controller = self.install_layout(
            registry=json.dumps({"version": 2, "plugins": [1, 2]}))
        self.assert_unknown_proceeds(controller, "registry-wrong-kind")

    def test_init_oversized_registry_is_unknown(self):
        controller = self.install_layout(
            registry="x" * (1024 * 1024 + 1))
        self.assert_unknown_proceeds(controller, "registry-oversized")

    def test_init_unmatched_install_path_is_unknown(self):
        controller = self.install_layout(registry=json.dumps({
            "version": 2,
            "plugins": {
                "hexaemeron@wildcat-labs": [{
                    "installPath": os.path.join(self.dir, "elsewhere") + os.sep,
                    "gitCommitSha": self.PIN,
                }],
            },
        }))
        self.assert_unknown_proceeds(controller, "registry-unmatched")

    def test_init_malformed_remote_line_is_unknown(self):
        controller = self.install_layout(pin=self.HEAD)
        self.assert_unknown_proceeds(
            controller, "remote-malformed",
            extra_env={"FAKE_GIT_MODE": "remote-malformed"},
        )

    # ----------------------------------------------------- old-state compat

    def test_old_state_without_the_receipt_stays_loadable(self):
        """A run recorded before this change loads, reports and verifies."""
        self.init()
        module = hexctl_module()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        self.assertIn("controller_currency", state["receipts"])
        del state["receipts"]["controller_currency"]
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        del entries[0]["data"]["controller_currency"]
        entries[0]["state"] = module.state_fingerprint(state)
        entries[0]["hash"] = hashlib.sha256(
            module.canonical(
                {
                    "ts": entries[0]["ts"],
                    "event": entries[0]["event"],
                    "data": entries[0]["data"],
                    "prev": entries[0]["prev"],
                    "state": entries[0]["state"],
                }
            ).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        self.run_ctl("status")
        self.run_ctl("verify")
        self.run_ctl("next")

    # --------------------------------------------------- receipt integrity

    def test_record_refuses_to_rewrite_the_currency_receipt(self):
        """`hexctl record` cannot replace init's observation (S2-R1-01).

        The receipt is init's own evidence, protected like `task_issue`: a
        later `record controller_currency` would replace the recorded verdict
        and waiver with a value nothing observed, while the honest copy
        survived only in the init transition.
        """
        self.init()
        receipt = self.provenance()
        proc = self.run_ctl(
            "record", "controller_currency",
            json.dumps({"verdict": "current", "route": "git-backed"}),
            expect=2,
        )
        self.assertIn("only `hexctl init` writes it", proc.stderr)
        self.assertEqual(self.provenance(), receipt,
                         "a refused record changed the currency receipt")

    # ------------------------------------------------- observation units

    def test_observation_seam_confines_remote_reader_inputs(self):
        """The reader receives only the clone path and branch derived from
        the controller's own file; a verdict follows from its answer."""
        module = hexctl_module()
        controller = self.install_layout()
        calls = []

        def reader(clone_dir, branch):
            calls.append((clone_dir, branch))
            return self.HEAD, None

        observation = module.observe_controller_currency(
            controller_file=controller, remote_reader=reader)
        clone = os.path.join(self.dir, "plugins-root", "marketplaces",
                             "wildcat-labs")
        self.assertEqual(
            [(os.path.realpath(path), branch) for path, branch in calls],
            [(os.path.realpath(clone), "main")],
        )
        self.assertEqual(observation["verdict"], "behind")
        self.assertEqual(observation["pin"], self.PIN)
        self.assertEqual(observation["observed_head"], self.HEAD)

    def test_remote_head_parsing_refuses_hostile_output(self):
        """Anything but exactly one well-formed ref line reads as a warning."""
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "parse-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        cases = {
            "absent": "",
            "duplicate": f"{self.HEAD}\\trefs/heads/main\\n" * 2,
            "not-a-sha": "not-a-sha\\trefs/heads/main\\n",
            "wrong-ref": f"{self.HEAD}\\trefs/heads/other\\n",
        }
        clone = os.path.join(self.dir, "clone")
        os.makedirs(clone)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        for name, output in cases.items():
            with open(script, "w", encoding="utf-8") as handle:
                handle.write(
                    "#!/usr/bin/env python3\n"
                    f"import sys; sys.stdout.write('{output}')\n"
                )
            os.chmod(script, 0o755)
            with mock.patch.dict(os.environ, {"PATH": path}):
                head, warning = module.currency_remote_head(clone, "main")
            self.assertIsNone(head, name)
            self.assertEqual(warning, "remote-malformed", name)
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                f"import sys; sys.stdout.write('{self.HEAD}\\trefs/heads/main\\n')\n"
            )
        os.chmod(script, 0o755)
        with mock.patch.dict(os.environ, {"PATH": path}):
            head, warning = module.currency_remote_head(clone, "main")
        self.assertEqual(head, self.HEAD)
        self.assertIsNone(warning)

    def test_observe_currency_timeout_reads_unknown(self):
        """A stalled upstream read is a named warning, never a verdict."""
        module = hexctl_module()
        controller = self.install_layout()
        fake_bin = os.path.join(self.dir, "slow-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write("#!/usr/bin/env python3\nimport time\ntime.sleep(5)\n")
        os.chmod(script, 0o755)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        with mock.patch.object(module, "GIT_TIMEOUT", 0.2), \
                mock.patch.dict(os.environ, {"PATH": path}):
            observation = module.observe_controller_currency(
                controller_file=controller)
        self.assertEqual(observation["route"], "git-backed")
        self.assertEqual(observation["pin"], self.PIN)
        self.assertIsNone(observation["observed_head"])
        self.assertEqual(observation["verdict"], "unknown")
        self.assertEqual(observation["warning"], "remote-timeout")

    def test_prompts_are_disabled_on_the_upstream_read(self):
        """The one network call runs with credential prompts turned off."""
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "env-bin")
        os.makedirs(fake_bin)
        script = os.path.join(fake_bin, "git")
        witness = os.path.join(self.dir, "prompt-env.json")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                f"with open({witness!r}, 'w') as out:\n"
                "    json.dump(os.environ.get('GIT_TERMINAL_PROMPT'), out)\n"
                f"sys.stdout.write('{self.HEAD}\\trefs/heads/main\\n')\n"
            )
        os.chmod(script, 0o755)
        clone = os.path.join(self.dir, "clone")
        os.makedirs(clone)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        with mock.patch.dict(os.environ, {"PATH": path}):
            head, warning = module.currency_remote_head(clone, "main")
        self.assertEqual(head, self.HEAD)
        self.assertIsNone(warning)
        with open(witness, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), "0")

    # ------------------------------------------------ the currency report

    FLEET = (
        "alexandria", "ariadne", "berean", "brevitas", "hermes",
        "hexaemeron", "horos", "janus", "lazarus", "lemma",
        "pandects", "probitas", "sapheneia", "tabularium",
    )
    """The fourteen-plugin shape the host registry held on 2026-08-24."""

    ROW_FIELDS = {"plugin", "version"} | (
        PROVENANCE_FIELDS - {"ledger_version", "waiver"}
    )
    """A report row: identity plus the init observation's own field names."""

    def fleet_layout(self, pins, marketplaces=None):
        """A fourteen-plugin install registry around one controller copy.

        `pins` maps plugin name to a commit SHA, None for a pinless managed
        record, or a non-SHA string for a hostile pin. Every plugin shares
        the wildcat-labs marketplace clone unless `marketplaces` names
        another for it; each named marketplace gets its own clone.
        """
        root = os.path.join(self.dir, "plugins-root")
        marketplaces = marketplaces or {}
        plugins = {}
        controller = None
        for plugin in self.FLEET:
            marketplace = marketplaces.get(plugin, "wildcat-labs")
            install = os.path.join(root, "cache", marketplace, plugin, "1.0.0")
            os.makedirs(install)
            if plugin == "hexaemeron":
                scripts = os.path.join(install, "skills", "fiat", "scripts")
                os.makedirs(scripts)
                controller = os.path.join(scripts, "hexctl.py")
                shutil.copyfile(HEXCTL, controller)
                with open(os.path.join(install, "skills", "fiat",
                                       "EVOLUTION.md"), "w",
                          encoding="utf-8") as handle:
                    handle.write("- Current version: `fiat-vTEST`\n")
            plugins[f"{plugin}@{marketplace}"] = [{
                "scope": "user",
                "installPath": install + os.sep,
                "version": "1.0.0",
                "installedAt": "2026-08-24T00:00:00Z",
                "gitCommitSha": pins[plugin],
            }]
        with open(os.path.join(root, "installed_plugins.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"version": 2, "plugins": plugins}, handle)
        for marketplace in {"wildcat-labs", *marketplaces.values()}:
            clone_git = os.path.join(root, "marketplaces", marketplace, ".git")
            os.makedirs(clone_git)
            with open(os.path.join(clone_git, "HEAD"), "w",
                      encoding="utf-8") as handle:
                handle.write("ref: refs/heads/main\n")
        return controller

    def mixed_pins(self):
        """Ten current, two behind, one managed, one hostile pin."""
        pins = {plugin: self.HEAD for plugin in self.FLEET}
        pins["ariadne"] = self.PIN
        pins["lemma"] = self.PIN
        pins["horos"] = None
        pins["janus"] = "not-a-sha"
        return pins

    def test_currency_reports_every_installed_plugin_with_mixed_verdicts(self):
        controller = self.fleet_layout(self.mixed_pins())
        proc = self.run_installed_ctl(controller, "currency", "--json",
                                      expect=3)
        rows = json.loads(proc.stdout)
        self.assertEqual([row["plugin"] for row in rows],
                         sorted(self.FLEET))
        verdicts = {row["plugin"]: row["verdict"] for row in rows}
        self.assertEqual(verdicts["ariadne"], "behind")
        self.assertEqual(verdicts["lemma"], "behind")
        self.assertEqual(verdicts["horos"], "managed")
        self.assertEqual(verdicts["janus"], "unknown")
        self.assertEqual(
            sum(1 for row in rows if row["verdict"] == "current"), 10)
        behind = next(row for row in rows if row["plugin"] == "ariadne")
        self.assertEqual(behind["pin"], self.PIN)
        self.assertEqual(behind["observed_head"], self.HEAD)
        self.assertEqual(behind["route"], "git-backed")
        hostile = next(row for row in rows if row["plugin"] == "janus")
        self.assertEqual(hostile["warning"], "registry-pin-malformed")
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, ".hexaemeron")),
            "a read-only report created run state")

    def test_currency_exits_zero_when_nothing_is_behind(self):
        controller = self.fleet_layout(
            {plugin: self.HEAD for plugin in self.FLEET})
        proc = self.run_installed_ctl(controller, "currency", "--json")
        rows = json.loads(proc.stdout)
        self.assertEqual(len(rows), len(self.FLEET))
        self.assertEqual({row["verdict"] for row in rows}, {"current"})

    def test_currency_text_rows_match_the_json_rows(self):
        controller = self.fleet_layout(self.mixed_pins())
        text = self.run_installed_ctl(controller, "currency", expect=3)
        rows = json.loads(self.run_installed_ctl(
            controller, "currency", "--json", expect=3).stdout)
        lines = [line for line in text.stdout.splitlines() if line]
        self.assertEqual(len(lines), len(rows))
        for line, row in zip(lines, rows):
            fields = line.split()
            self.assertEqual(fields[0], row["plugin"])
            self.assertEqual(fields[5], row["verdict"])
            self.assertEqual(fields[3], row["pin"] or "null")
            self.assertEqual(fields[4], row["observed_head"] or "null")
        hostile = next(line for line in lines if line.startswith("janus "))
        self.assertIn("(registry-pin-malformed)", hostile)

    def test_currency_reads_upstream_once_per_distinct_origin(self):
        """Fourteen plugins over two marketplaces cost exactly two reads."""
        module = hexctl_module()
        pins = {plugin: self.HEAD for plugin in self.FLEET}
        controller = self.fleet_layout(
            pins, marketplaces={"tabularium": "mirror-labs"})
        calls = []

        def reader(clone_dir, branch):
            calls.append((os.path.realpath(clone_dir), branch))
            return self.HEAD, None

        rows, refusal = module.currency_report(
            controller_file=controller, remote_reader=reader)
        self.assertIsNone(refusal)
        self.assertEqual(len(rows), len(self.FLEET))
        self.assertEqual({row["verdict"] for row in rows}, {"current"})
        marketplaces = os.path.join(self.dir, "plugins-root", "marketplaces")
        self.assertEqual(sorted(calls), [
            (os.path.realpath(os.path.join(marketplaces, "mirror-labs")),
             "main"),
            (os.path.realpath(os.path.join(marketplaces, "wildcat-labs")),
             "main"),
        ], "one remote read per distinct marketplace origin, no more")

    def test_currency_refuses_an_unreadable_registry(self):
        """A registry that cannot answer is exit 1, not an empty success.

        A read-only reporter that printed nothing and exited 0 would read as
        a fleet with nothing behind, which is the silent hole again.
        """
        controller = self.install_layout(registry=False)
        proc = self.run_installed_ctl(controller, "currency", expect=1)
        self.assertIn("registry-missing", proc.stderr)
        self.assertEqual(proc.stdout, "")
        registry = os.path.join(self.dir, "plugins-root",
                                "installed_plugins.json")
        with open(registry, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        proc = self.run_installed_ctl(controller, "currency", expect=1)
        self.assertIn("registry-malformed", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_currency_refuses_outside_an_install_cache(self):
        """The in-repo dev controller cannot say whose installs to report."""
        proc = self.run_ctl("currency", expect=1)
        self.assertIn("install cache", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_currency_row_fields_match_the_init_observation(self):
        """Rows and the init receipt share one observation vocabulary."""
        controller = self.fleet_layout(self.mixed_pins())
        rows = json.loads(self.run_installed_ctl(
            controller, "currency", "--json", expect=3).stdout)
        for row in rows:
            self.assertEqual(set(row), self.ROW_FIELDS, row["plugin"])

    def test_currency_text_neutralises_control_bytes_in_registry_strings(self):
        """A control byte in a registry string cannot forge a text row (S3-R1-01).

        A plugin key carrying a newline printed a fabricated line that read
        as another plugin's all-clear row while only `--json` and the exit
        code stayed honest; controls must render inert in text mode.
        """
        controller = self.fleet_layout(
            {plugin: self.HEAD for plugin in self.FLEET})
        registry = os.path.join(self.dir, "plugins-root",
                                "installed_plugins.json")
        with open(registry, encoding="utf-8") as handle:
            payload = json.load(handle)
        install = payload["plugins"]["hexaemeron@wildcat-labs"][0][
            "installPath"]
        forged = ("zzz\nhexaemeron 9.9.9 git-backed "
                  f"{self.HEAD} {self.HEAD} current")
        payload["plugins"][forged + "@wildcat-labs"] = [{
            "installPath": install,
            "version": "1.0\n0",
            "gitCommitSha": self.PIN,
        }]
        with open(registry, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        proc = self.run_installed_ctl(controller, "currency", expect=3)
        rows = json.loads(self.run_installed_ctl(
            controller, "currency", "--json", expect=3).stdout)
        lines = [line for line in proc.stdout.splitlines() if line]
        self.assertEqual(len(lines), len(rows),
                         "control bytes forged extra report lines")
        self.assertEqual(
            sum(1 for line in lines if line.startswith("hexaemeron ")), 1,
            "a forged line impersonates another plugin's row")

    def test_currency_text_survives_separator_and_surrogate_bytes(self):
        """Non-ASCII hostile registry bytes neither forge nor crash (S3-R2-01).

        A Unicode line separator in a key forged a row for any `splitlines`
        consumer, and a lone surrogate in a version crashed the text encoder
        mid-report with a traceback; both must render inert while `--json`
        keeps carrying the raw values.
        """
        controller = self.fleet_layout(
            {plugin: self.HEAD for plugin in self.FLEET})
        registry = os.path.join(self.dir, "plugins-root",
                                "installed_plugins.json")
        with open(registry, encoding="utf-8") as handle:
            payload = json.load(handle)
        install = payload["plugins"]["hexaemeron@wildcat-labs"][0][
            "installPath"]
        forged = ("zzz\u2028hexaemeron 9.9.9 git-backed "
                  f"{self.HEAD} {self.HEAD} current")
        payload["plugins"][forged + "@wildcat-labs"] = [{
            "installPath": install,
            "version": "1.0\ud800",
            "gitCommitSha": self.HEAD,
        }]
        with open(registry, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        proc = self.run_installed_ctl(controller, "currency")
        self.assertNotIn("Traceback", proc.stderr,
                         "a hostile registry byte crashed the report")
        rows = json.loads(self.run_installed_ctl(
            controller, "currency", "--json").stdout)
        lines = [line for line in proc.stdout.splitlines() if line]
        self.assertEqual(len(lines), len(rows),
                         "separator bytes forged extra report lines")
        self.assertEqual(
            sum(1 for line in lines if line.startswith("hexaemeron ")), 1,
            "a forged line impersonates another plugin's row")
        hostile = next(row for row in rows
                       if row["plugin"].startswith("zzz"))
        self.assertEqual(hostile["version"], "1.0\ud800",
                         "--json no longer carries the raw registry value")
