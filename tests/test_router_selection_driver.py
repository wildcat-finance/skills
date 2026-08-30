"""Guards for the router-selection grading driver.

The dangerous direction is outward. `expect`, `deciding_sentence` and
`not_established` sit in the same object as `request`, so the emitter is one
careless serialisation away from handing a graded context the answer it is
about to be graded on. The leak guard therefore reads every emitted byte of
every case rather than sampling one.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests import router_selection_driver as driver


def corpus() -> dict:
    return driver.load_corpus()


class PacketEmissionTests(unittest.TestCase):
    """What `emit` writes, and what it must never write."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="rs-packet-")) / "packet"
        self.addCleanup(shutil.rmtree, self.out.parent, ignore_errors=True)

    def test_one_prompt_per_case_and_a_manifest(self):
        manifest = driver.emit(self.out)
        cases = corpus()["cases"]
        self.assertEqual(len(manifest["cases"]), len(cases))
        for case in cases:
            self.assertTrue(
                (self.out / f"{case['id']}.txt").is_file(),
                f"no prompt emitted for {case['id']}",
            )
        self.assertTrue((self.out / driver.MANIFEST_NAME).is_file())

    def test_a_prompt_is_the_pinned_template_with_one_request_substituted(self):
        driver.emit(self.out)
        template = driver.prompt_template()
        for case in corpus()["cases"]:
            written = (self.out / f"{case['id']}.txt").read_text(encoding="utf-8")
            self.assertEqual(
                written,
                template.replace("{request}", case["request"]),
                f"{case['id']} is not the template with its request substituted",
            )
            self.assertNotIn("{request}", written)

    def test_no_emitted_byte_carries_any_field_but_the_request(self):
        """The leak guard. Every case, every emitted file, every other field.

        Two classes of string are not leaks and are excluded by provenance
        rather than by length. A string already in the unsubstituted template
        cannot have been introduced by the emitter and is case-independent, so
        it says nothing about which case a context is grading: the template
        names `.agents/skills/promise-machine/SKILL.md` in its own read list,
        and several cases cite that file as their deciding sentence's path. A
        string that is some case's request is emitted on purpose.

        Everything else must be absent, including `expect.canonical`, which is
        short enough that a length floor would have skipped exactly the field
        that matters most.
        """
        driver.emit(self.out)
        blob = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(self.out.glob("*.txt"))
        )
        template = driver.prompt_template()
        requests = {case["request"] for case in corpus()["cases"]}
        checked = 0
        for case in corpus()["cases"]:
            for field, value in case.items():
                if field in driver.EMITTABLE_CASE_FIELDS:
                    continue
                for leaked in self._strings(value):
                    if leaked in template or any(leaked in r for r in requests):
                        continue
                    checked += 1
                    self.assertNotIn(
                        leaked,
                        blob,
                        f"{case['id']} leaked {field}: {leaked!r}",
                    )
        self.assertGreater(
            checked, 0, "the leak guard asserted nothing, so it proves nothing"
        )

    def test_the_leak_guard_catches_a_deliberately_leaky_emitter(self):
        """The guard fails when the emitter leaks, or it is not a guard."""
        original = driver.render_prompt
        cases = corpus()["cases"]
        answer = cases[0]["expect"].get("canonical") or "refuse"
        driver.render_prompt = lambda request: original(request) + f"\nhint: {answer}\n"
        self.addCleanup(setattr, driver, "render_prompt", original)
        leaky = self.out.parent / "leaky"
        driver.emit(leaky)
        blob = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(leaky.glob("*.txt"))
        )
        self.assertIn(answer, blob, "the leaky emitter did not leak, so this proves nothing")

    def _strings(self, value):
        """Every string a case field carries, at any depth.

        No length floor: `expect.canonical` is a short skill name and is the
        single most damaging thing that could reach a graded context.
        """
        if isinstance(value, str):
            if value.strip():
                yield value.strip()
        elif isinstance(value, dict):
            for item in value.values():
                yield from self._strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from self._strings(item)

    def test_the_manifest_pins_the_corpus_and_template_digests(self):
        manifest = driver.emit(self.out)
        document = corpus()
        self.assertEqual(manifest["contract"], driver.CONTRACT)
        self.assertEqual(manifest["corpus_sha256"], driver.corpus_digest(document["cases"]))
        self.assertEqual(manifest["prompt_template_sha256"], driver.prompt_template_digest())
        self.assertEqual(
            manifest["cases"], sorted(case["id"] for case in document["cases"])
        )

    def test_the_manifest_on_disk_matches_what_emit_returned(self):
        manifest = driver.emit(self.out)
        written = json.loads((self.out / driver.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(written, manifest)

    def test_a_non_empty_output_directory_refuses(self):
        self.out.mkdir(parents=True)
        (self.out / "already-here.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(driver.DriverError) as caught:
            driver.emit(self.out)
        self.assertIn("already holds files", str(caught.exception))

    def test_a_refused_emit_leaves_the_directory_as_it_found_it(self):
        self.out.mkdir(parents=True)
        (self.out / "already-here.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(driver.DriverError):
            driver.emit(self.out)
        self.assertEqual(
            [path.name for path in self.out.iterdir()],
            ["already-here.txt"],
            "a refused emit wrote into the directory it refused",
        )

    def test_an_empty_directory_that_exists_is_accepted(self):
        self.out.mkdir(parents=True)
        manifest = driver.emit(self.out)
        self.assertTrue(manifest["cases"])


class RenderTests(unittest.TestCase):
    """The substitution itself."""

    def test_a_brace_in_a_request_is_not_read_as_a_field(self):
        rendered = driver.render_prompt("count the {braces} in this")
        self.assertIn("count the {braces} in this", rendered)

    def test_the_template_placeholder_is_required(self):
        original = driver.prompt_template
        driver.prompt_template = lambda: "no placeholder here"
        self.addCleanup(setattr, driver, "prompt_template", original)
        with self.assertRaises(driver.DriverError) as caught:
            driver.render_prompt("anything")
        self.assertIn("placeholder", str(caught.exception))


class CorpusReadingTests(unittest.TestCase):
    """The fixed-path read, and the shapes it refuses."""

    def test_the_digest_matches_the_checker_over_the_same_cases(self):
        cases = corpus()["cases"]
        self.assertEqual(len(driver.corpus_digest(cases)), 64)
        self.assertEqual(driver.corpus_digest(cases), driver.corpus_digest(list(cases)))

    def test_a_case_without_a_request_refuses_by_id(self):
        with self.assertRaises(driver.DriverError) as caught:
            driver.case_request({"id": "RS-99"}, "fixture")
        self.assertIn("RS-99", str(caught.exception))

    def test_a_malformed_case_id_refuses(self):
        with self.assertRaises(driver.DriverError) as caught:
            driver.case_request({"id": "nope", "request": "x" * 20}, "fixture")
        self.assertIn("case id", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
