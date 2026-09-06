"""Historical red guard for issue 453 Step 3 path admission."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

try:
    from .test_hexctl import HexctlCase, hexctl_module
except ImportError:
    from test_hexctl import HexctlCase, hexctl_module


class InoculationLifecycleTests(HexctlCase):
    FIXTURE = Path(__file__).parent / "fixtures/issue-453/path-boundary.json"

    def authority_bytes(self):
        root = Path(self.target)
        controller_root = root / ".hexaemeron"
        controller_files = tuple(
            (path.relative_to(controller_root).as_posix(), path.read_bytes())
            for path in sorted(controller_root.rglob("*"))
            if path.is_file()
        )
        branch_tip = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return controller_files, branch_tip

    def test_kf_453_05_undeclared_product_path_refuses(self):
        fixture = json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(6, len(fixture["allowed_paths"]))

        self.init()
        self.write(".hexaemeron/checkpoints/step-3/probe", "checkpoint bytes\n")
        self.write(
            ".hexaemeron/steps/3/inoculation/reports/existing.report",
            "existing report bytes\n",
        )
        self.write(
            ".hexaemeron/steps/3/inoculation/manifests/existing.json",
            '{"existing":true}\n',
        )
        before = self.authority_bytes()

        controller = hexctl_module()
        validate = getattr(controller, "_validate_guard_delta_rows", None)
        self.assertTrue(
            callable(validate),
            "Fiat does not refuse an undeclared guard-commit product path",
        )

        accepted = validate(fixture["valid_rows"], fixture["allowed_paths"])
        self.assertEqual(fixture["valid_rows"], accepted)
        invalid = fixture["valid_rows"] + [fixture["invalid_extra"]]
        with self.assertRaisesRegex(ValueError, "undeclared guard path"):
            validate(invalid, fixture["allowed_paths"])
        self.assertEqual(before, self.authority_bytes())


if __name__ == "__main__":
    import unittest

    unittest.main()
