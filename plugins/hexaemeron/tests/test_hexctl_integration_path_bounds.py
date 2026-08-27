"""Fiat integration path sets keep exact evidence beyond ordinary diff bounds."""

import json
from contextlib import redirect_stderr
from io import StringIO
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import (
        SUITE,
        HexctlCase,
        hexctl_module,
    )
except ModuleNotFoundError:
    from test_hexctl import SUITE, HexctlCase, hexctl_module


class IntegrationPathBoundTests(HexctlCase):
    def to_push(self):
        self.to_steps(("Ship",))
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )

    def to_merge_step(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )

    def to_integrate(self):
        self.to_merge_step()
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        self.write_run_pr()

    def prepare_run_sync(self, sync_sha="7" * 40, base_sha="6" * 40):
        self.to_integrate()
        state = self.state()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        base_before = "4" * 40
        self.fake_refs[state["run_branch"]] = sync_sha
        self.fake_refs[self.integration_base(state)] = base_sha
        self.fake_parents[sync_sha] = [final_merge, base_sha]
        self.env["FAKE_GIT_MERGE_BASE"] = base_before
        return state, sync_sha, base_sha

    def write_integration_revalidation(self, affected_paths):
        return self.write(
            ".hexaemeron/integration-revalidation.json",
            json.dumps(
                {
                    "schema": "fiat-integration-revalidation/v1",
                    "affected_paths": affected_paths,
                    "checks": [
                        {
                            "id": "portable-runtime-suite",
                            "command": "python3 -m unittest discover -s tests",
                            "paths": affected_paths,
                            "exit": 0,
                        }
                    ],
                }
            ),
        )

    def test_sync_run_accepts_dependency_closed_portable_runtime_surface(self):
        state, sync_sha, base_sha = self.prepare_run_sync()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        base_before = "4" * 40
        runtime_paths = [
            ".agents/skills/promise-machine/runtime/"
            f"plugins/example/file-{number:04d}.md"
            for number in range(907)
        ]
        self.env["FAKE_GIT_DIFF_PATHS"] = json.dumps(
            {
                f"{base_before}..{final_merge}": ["product.py"],
                f"{base_before}..{base_sha}": runtime_paths,
                f"{final_merge}..{sync_sha}": runtime_paths,
            }
        )
        revalidation = self.write_integration_revalidation(runtime_paths)

        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )

        sync = self.state()["integrate"]["sync"]
        self.assertEqual(len(sync["revalidation"]["composition_paths"]), 907)
        self.assertEqual(len(sync["revalidation"]["affected_paths"]), 907)

    def test_integration_path_surface_keeps_a_dedicated_bound(self):
        module = hexctl_module()
        self.assertEqual(module.GIT_PATHS_MAX, 500)
        integration_paths_max = getattr(module, "INTEGRATION_PATHS_MAX", None)
        self.assertEqual(integration_paths_max, 4096)
        paths = [
            f"runtime/file-{number:04d}.py"
            for number in range(integration_paths_max + 1)
        ]

        manifest_error = StringIO()
        with redirect_stderr(manifest_error), self.assertRaises(SystemExit):
            module._manifest_paths(paths, "affected_paths")
        self.assertIn("at most 4096 paths", manifest_error.getvalue())

        diff_error = StringIO()
        raw = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
        with mock.patch.object(module, "bounded_git", return_value=raw):
            with redirect_stderr(diff_error), self.assertRaises(SystemExit):
                module.git_diff_paths(self.dir, "a" * 40, "b" * 40)
        self.assertIn("exceeds 4096 paths", diff_error.getvalue())
