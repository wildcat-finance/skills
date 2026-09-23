import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emitter_declarations.py"
STUDY = ROOT / "docs" / "emitter-declaration-check-study.md"
RUNBOOK = ROOT / "docs" / "emitter-declaration-check-runbook.md"

SPEC = importlib.util.spec_from_file_location("emitter_declarations", SCRIPT)
emitter_declarations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(emitter_declarations)


class KeccakVectorTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_erc20_transfer_signature(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"Transfer(address,address,uint256)").hex(),
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        )

class SubcommandTests(unittest.TestCase):
    def test_build_and_check_refuse_until_implemented(self):
        for command in ("build", "check"):
            with self.subTest(command=command):
                self.assertEqual(emitter_declarations.main([command]), 2)


class SpecificationCopyTests(unittest.TestCase):
    def test_study_and_runbook_copies_are_committed(self):
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
