"""Network policy and report fixtures retain separate evidence boundaries."""
from dataclasses import replace
import fcntl
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
from checkpoint_authority import native_io, network, network_policy, release_conformance
from checkpoint_authority.canonical import Refusal
import test_checkpoint_authority_release_conformance as report_fixtures


class Fixture(unittest.TestCase):
    def test_fixture_pure(self):
        specimen = report_fixtures.ReleaseConformanceTests("test_a_peak_above_the_declared_ceiling_refuses")
        specimen.setUp()
        self.addCleanup(specimen.doCleanups)
        with patch.object(network, "prepare", side_effect=AssertionError("fixture prepared host sandbox")):
            self.assertIsInstance(specimen.value()["demonstration"]["network_boundary"], dict)

    def test_validation_pure(self):
        specimen = report_fixtures.ReleaseConformanceTests("test_a_peak_above_the_declared_ceiling_refuses")
        specimen.setUp()
        self.addCleanup(specimen.doCleanups)
        with patch.object(network, "prepare", side_effect=AssertionError("validation prepared host sandbox")):
            self.assertEqual(specimen.execute(specimen.value())[0], specimen.value())

    def test_exact_fields(self):
        boundary = network.Boundary("a" * 64, network_policy.for_host("linux", "x86_64"))
        expected = boundary.expected()
        for key, original in expected.items():
            for changed in (None, True, original + "x" if isinstance(original, str) else original + 1):
                with self.subTest(key=key, changed=changed), self.assertRaises(Refusal):
                    network.validate_observation({**expected, key: changed}, expected)
            with self.subTest(missing=key), self.assertRaises(Refusal):
                network.validate_observation({k: v for k, v in expected.items() if k != key}, expected)
        for value in ([], None, {**expected, "extra": 1}):
            with self.subTest(value=value), self.assertRaises(Refusal):
                network.validate_observation(value, expected)

    def test_require_host(self):
        with patch.object(network, "prepare", side_effect=Refusal("network-denial-unavailable", "demonstration")), \
                patch.object(native_io, "execute") as child, self.assertRaises(Refusal):
            release_conformance.execute(Path.cwd())
        child.assert_not_called()


class Policy(unittest.TestCase):
    def test_unsupported(self):
        for system, machine in (("linux", "aarch64"), ("linux", "i686"),
                                ("linux", ""), ("win32", "x86_64"), ("darwin", "unknown")):
            with self.subTest(system=system, machine=machine), self.assertRaises(Refusal) as caught:
                network_policy.for_host(system, machine)
            self.assertEqual(caught.exception.code, "network-denial-unavailable")

    def test_macos_policy(self):
        for abi in ("arm64", "x86_64"):
            policy = network_policy.for_host("darwin", abi)
            self.assertEqual(policy.launcher, "/usr/bin/sandbox-exec")
            self.assertEqual(policy.argv, ("-p", "(version 1)(allow default)(deny network*)"))
            self.assertEqual(policy.filter_bytes, b"")

    def test_policy_identity(self):
        policy = network_policy.for_host("linux", "x86_64")
        mutations = ({"abi": "aarch64"}, {"platform": "darwin"}, {"mechanism": "other"},
                     {"launcher": "/other"}, {"argv": policy.argv[:-1]},
                     {"filter_bytes": policy.filter_bytes[:-8]})
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertNotEqual(replace(policy, **mutation).sha256, policy.sha256)
        self.assertEqual(hashlib.sha256(policy.filter_bytes).hexdigest(),
                         "8b97e4880f19e22990d9994580127bd38249e9f51594f1e3f63218edcd286412")

    def test_filter_abi(self):
        # Interpret the emitted Linux classic-BPF subset against independent
        # seccomp_data inputs; this checks jump behavior without executing x32.
        instructions = list(struct.iter_unpack("<HBBI", network_policy.linux_filter()))

        def action(arch, number):
            pc, accumulator = 0, 0
            for _ in range(len(instructions)):
                opcode, yes, no, value = instructions[pc]
                pc += 1
                if opcode == 0x20:
                    accumulator = {0: number, 4: arch}[value]
                elif opcode == 0x15:
                    pc += yes if accumulator == value else no
                elif opcode == 0x35:
                    pc += yes if accumulator >= value else no
                elif opcode == 0x06:
                    return value
                else:
                    self.fail("unreviewed BPF instruction")
            self.fail("unterminated BPF program")

        for arch in (0x40000003, 0xc00000b7, 0):
            self.assertEqual(action(arch, 41), 0x80000000)
        for number in (0x40000000, 0x40000029, 0xffffffff):
            self.assertEqual(action(0xc000003e, number), 0x80000000)
        for number in (*range(41, 56), 288, 299, 307, 425, 426, 427):
            self.assertEqual(action(0xc000003e, number), 0x00050001)
        for number in (0, 1, 2, 3, 39, 60, 231):
            self.assertEqual(action(0xc000003e, number), 0x7fff0000)

    def test_no_launcher(self):
        with patch.object(native_io, "hash_file", side_effect=OSError("unavailable")), \
                patch.object(network.signatures, "_run") as child, self.assertRaises(Refusal) as caught:
            network.prepare()
        child.assert_not_called()
        self.assertEqual(caught.exception.code, "network-denial-unavailable")


class Native(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="checkpoint-network-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        path = str(Path(sys.executable).resolve(strict=True))
        self.python = native_io.NativeTool("python", path, native_io.hash_file(path, 268435456)[0])
        self.boundary = network.prepare()

    def run_python(self, source, timeout=10):
        return self.boundary.run(self.python, ["-I", "-c", source], self.root, timeout=timeout)

    def test_direct_exec_denial(self):
        observed = self.boundary.probe(self.root)
        network.validate_observation(observed, self.boundary.expected())
        self.assertEqual(observed["probe_operations"], 4)
        self.assertEqual(observed["descendant_probe_operations"], 4)
        self.assertEqual(observed["descendant_probe_exit"], 0)

    def test_allow_all_refuses(self):
        if sys.platform == "linux":
            weak = patch.object(network_policy, "linux_filter", return_value=struct.pack("<HBBI", 0x06, 0, 0, 0x7fff0000))
        else:
            weak = patch.object(network_policy, "MACOS_POLICY", "(version 1)(allow default)")
        specimens = [weak]
        if sys.platform == "linux":
            # Permit socket and bind while retaining the rest of the denied set.
            # This independent specimen must fail even though connect stays denied.
            specimens.append(patch.object(network_policy, "DENIED_X86_64",
                                           tuple(n for n in network_policy.DENIED_X86_64 if n not in (41, 49))))
        for specimen in specimens:
            with self.subTest(specimen=specimen), specimen:
                boundary = network.prepare()
                with self.assertRaises(Refusal) as caught:
                    boundary.probe(self.root)
                self.assertEqual(caught.exception.code, "network-denial-probe")

    def test_policy_mutation(self):
        for mutation in ({"argv": ()}, {"abi": "foreign"}, {"filter_bytes": b"allow"},
                         {"mechanism": "other"}, {"launcher": "/different"}):
            changed = replace(self.boundary, policy=replace(self.boundary.policy, **mutation))
            with self.subTest(mutation=mutation), patch.object(network.signatures, "_run") as child, self.assertRaises(Refusal) as caught:
                changed.run(self.python, ["-c", "pass"], self.root, timeout=1)
            child.assert_not_called()
            self.assertEqual(caught.exception.code, "network-denial-changed")

    def test_pin_mutations(self):
        changed = replace(self.boundary, launcher_sha256="0" * 64)
        with self.assertRaises(Refusal) as caught:
            changed.run(self.python, ["-c", "pass"], self.root, timeout=1)
        self.assertEqual(caught.exception.code, "network-denial-changed")
        with self.assertRaises(Refusal):
            self.boundary.run(replace(self.python, sha256="0" * 64), ["-c", "pass"], self.root, timeout=1)

    def test_exec_required(self):
        complete = (0, network.PROBE_OUTPUT, b"")
        for incomplete in ((0, b"", b""), (1, network.PROBE_OUTPUT, b""),
                           (0, network.PROBE_OUTPUT, b"unexpected diagnostic")):
            with self.subTest(result=incomplete), \
                    patch.object(network.Boundary, "run", side_effect=[complete, incomplete]), \
                    self.assertRaises(Refusal) as caught:
                self.boundary.probe(self.root)
            self.assertEqual(caught.exception.code, "network-denial-probe")

    def test_output_limit(self):
        with self.assertRaises(Refusal) as caught:
            self.run_python("import sys; sys.stdout.write('x' * 70000)")
        self.assertEqual(caught.exception.code, "tool-output-limit")

    def assert_lock_released(self):
        # Signal delivery and namespace teardown finish asynchronously. Retain
        # the existing descendant guard's two-second observation bound.
        deadline = time.monotonic() + 2
        with (self.root / "lock").open("rb") as held:
            while True:
                try:
                    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        self.fail("verifier descendant survived bounded cleanup")
                    time.sleep(0.01)

    def descendant(self, leader):
        return """import fcntl, os, time
read, write = os.pipe()
child = os.fork()
if child == 0:
    os.close(read)
    held = open('lock', 'w')
    fcntl.flock(held, fcntl.LOCK_EX)
    os.write(write, b'x')
    os.close(write)
    time.sleep(30)
    os._exit(0)
os.close(write)
assert os.read(read, 1) == b'x'
os.close(read)
""" + leader

    def test_leader_exit_cleanup(self):
        # Direct execution retains the pipe-holder on Linux too; its PID
        # namespace would otherwise hide the Darwin leader-exit failure.
        source = self.descendant("print('complete', flush=True)\nos._exit(0)\n")
        for sandboxed in (False, True):
            with self.subTest(sandboxed=sandboxed):
                if sandboxed:
                    result = self.run_python(source, timeout=2)
                else:
                    result = network.signatures._run(self.python, ["-I", "-c", source],
                                                     self.root, timeout=2)
                self.assertEqual(result, (0, b"complete\n", b""))
                self.assert_lock_released()

    def test_timeout_cleanup(self):
        start = time.monotonic()
        with self.assertRaises(Refusal) as caught:
            self.run_python(self.descendant("time.sleep(30)\n"), timeout=0.3)
        self.assertEqual(caught.exception.code, "tool-timeout")
        self.assertLess(time.monotonic() - start, 5)
        self.assert_lock_released()


if __name__ == "__main__":
    unittest.main()
