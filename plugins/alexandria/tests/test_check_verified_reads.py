"""`check` reads only the bytes `verify` accepted, and one capture per component.

Issue #1902. `check_interval` held a split release to the manifest `verify`
accepted, but read an unsplit one by path again after `verify` returned. It
also keyed the captures by id and read only the one filed under each
component's own name, so a second capture beside it was never read. Every case
runs the constructed Wildcat path in process over
`fixtures/wildcat-interval-transport.json`; none opens a socket or starts a
child process.

A case that changes a release after verification patches `verify` to return
the identifier it accepted. A case that reaches one of `check`'s own refusals
re-ingests the release after its edit, so `verify` accepts it.
"""

from contextlib import redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import shutil
import unittest
from unittest import mock

from tests import test_usdc_interval as existing
from tests.test_log_attribution_parts import V4_SEMANTICS, PartCase
from alexandria_lib.canonical import canonical_bytes
import usdc_interval
from usdc_interval import PART_CLASS, check_interval


V3_SEMANTICS = "v3-subject-positional"
CHANGED_MANIFEST = (
    "the manifest check read does not hash to the release identity verification "
    "accepted, so the release changed after it was verified"
)


def changed_component(name):
    return re.escape(
        f"component {name} does not carry the size and SHA-256 the verified manifest "
        "records, so it changed after the release was verified"
    )


class VerifiedReadTests(PartCase):
    """Every read `check` makes after `verify` is of the bytes `verify` accepted, on either path."""

    def released_pair(self, name):
        """A split release and its unsplit twin over one staging state, each checking clean."""
        split, _plan = self.split(f"{name}-split")
        twin, _plan = self.split(f"{name}-twin", parts=False)
        self.assertEqual(check_interval(split)["receipt_semantics"], V4_SEMANTICS)
        self.assertEqual(check_interval(twin)["receipt_semantics"], V3_SEMANTICS)
        return split, twin

    def test_an_unsplit_twin_swapped_in_after_verification_refuses_by_name(self):
        split, twin = self.released_pair("twin")
        release_id = self.manifest(split)["release_id"]
        self.assertNotEqual(self.manifest(twin)["release_id"], release_id)
        shutil.rmtree(split)
        shutil.copytree(twin, split)
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            self.refuses(split, re.escape(CHANGED_MANIFEST))

    def test_a_manifest_rewritten_after_verification_refuses_without_a_traceback(self):
        def listed(manifest):
            return [manifest]

        def text_count(manifest):
            manifest["components"][0]["bytes"] = str(manifest["components"][0]["bytes"])
            return manifest

        rewrites = {"a JSON list": listed, "a text byte count": text_count}
        for layout, parts in (("split", True), ("unsplit", False)):
            output, _plan = self.split(f"rewritten-{layout}", parts=parts)
            path = Path(output) / "manifest.json"
            saved = path.read_bytes()
            release_id = json.loads(saved)["release_id"]
            for case, rewrite in rewrites.items():
                with self.subTest(layout=layout, rewritten_as=case):
                    path.write_bytes(canonical_bytes(rewrite(json.loads(saved))))
                    try:
                        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
                            self.refuses(output, re.escape(CHANGED_MANIFEST))
                            stderr = io.StringIO()
                            with redirect_stderr(stderr):
                                code = usdc_interval.main(["check", str(output)])
                        self.assertEqual(code, 1)
                        self.assertEqual(stderr.getvalue(), f"usdc-interval: {CHANGED_MANIFEST}\n")
                    finally:
                        path.write_bytes(saved)

    def test_a_component_changed_after_verification_refuses_by_name_on_either_path(self):
        for layout, parts in (("split", True), ("unsplit", False)):
            output, _plan = self.split(f"changed-{layout}", parts=parts)
            release_id = self.manifest(output)["release_id"]
            for name in ("interval-plan", "epoch-table", "registry", "logs.0"):
                with self.subTest(layout=layout, component=name):
                    path = existing.component_path(output, name)
                    saved = path.read_bytes()
                    # The same document, indented: every value `check` reads
                    # is unchanged, so only the binding to the verified
                    # manifest can tell these bytes from the ones it records.
                    path.write_bytes(json.dumps(json.loads(saved), indent=2).encode())
                    try:
                        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
                            self.refuses(output, changed_component(name))
                    finally:
                        path.write_bytes(saved)
            self.assertEqual(
                check_interval(output)["receipt_semantics"], V4_SEMANTICS if parts else V3_SEMANTICS,
            )


class OneCapturePerComponentTests(PartCase):
    """Each component carries one capture, filed under its own name; any other refuses by name."""

    def test_an_extra_complete_capture_refuses_by_name(self):
        output, _plan = self.split("extra")
        cases = {
            f"{PART_CLASS}.1": f"{PART_CLASS}.1 (shards 1 to 1)",
            "epoch-table": "epoch-table",
            "logs.0": "logs.0",
        }
        for name, label in cases.items():
            extra = f"{name}-complete"

            def add(by_id, name=name, extra=extra):
                copied = deepcopy(by_id[name])
                copied["id"] = extra
                copied["coverage"]["gaps"] = []
                copied["coverage"]["status"] = "complete"
                copied["coverage"]["unsupported_collections"] = []
                by_id[extra] = copied

            with self.subTest(component=name):
                self.refuses(
                    self.reissued(output, extra, captures=add),
                    re.escape(
                        f"capture {extra} preserves the {label} component, which its "
                        "own-named capture already carries"
                    ),
                )

    def test_a_capture_filed_under_another_components_name_refuses_by_name(self):
        output, _plan = self.split("misfiled")

        def misfile(by_id):
            # The plan and the reconciliation record each count their shard
            # table under `/shards`, so this capture's counts hold for the
            # plan's bytes and `verify` accepts it.
            by_id["reconciliation"]["component"] = "interval-plan"

        self.refuses(
            self.reissued(output, "misfiled-reconciliation", captures=misfile),
            re.escape(
                "the reconciliation capture preserves the interval-plan component, not its own"
            ),
        )


if __name__ == "__main__":
    unittest.main()
