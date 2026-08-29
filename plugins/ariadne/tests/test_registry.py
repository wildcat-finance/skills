"""The predicate registry, and the predicates the package ships."""

import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import gates, registry  # noqa: E402


class Fake(object):
    TYPE = "https://ariadne.wildcat.finance/fake/v1"
    SUMMARY = "a predicate registered by a test and nowhere else"


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = registry.Registry()

    def test_a_module_registers_and_is_found_by_type(self):
        self.registry.register(Fake)
        self.assertIs(self.registry.get(Fake.TYPE), Fake)
        self.assertTrue(self.registry.knows(Fake.TYPE))
        self.assertEqual(len(self.registry), 1)

    def test_an_unknown_type_is_reported_rather_than_raised(self):
        self.assertIsNone(self.registry.get("https://example.test/unknown/v1"))
        self.assertFalse(self.registry.knows("https://example.test/unknown/v1"))

    def test_registering_the_same_module_twice_is_harmless(self):
        self.registry.register(Fake)
        self.registry.register(Fake)
        self.assertEqual(len(self.registry), 1)

    def test_a_second_module_claiming_the_same_type_is_refused(self):
        class Impostor(object):
            TYPE = Fake.TYPE
            SUMMARY = "a different module under the same type URI"

        self.registry.register(Fake)
        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Impostor)
        self.assertIn("already registered", str(caught.exception))

    def test_a_module_without_a_summary_is_refused(self):
        class Bare(object):
            TYPE = "https://example.test/bare/v1"

        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Bare)
        self.assertIn("SUMMARY", str(caught.exception))

    def test_a_type_that_is_not_a_uri_is_refused(self):
        class Loose(object):
            TYPE = "solidity-release"
            SUMMARY = "a predicate naming itself without a URI"

        with self.assertRaises(registry.RegistryError) as caught:
            self.registry.register(Loose)
        self.assertIn("type URI", str(caught.exception))

    def test_entries_are_sorted_by_type(self):
        class Other(object):
            TYPE = "https://ariadne.wildcat.finance/aardvark/v1"
            SUMMARY = "sorts first"

        self.registry.register(Fake)
        self.registry.register(Other)
        self.assertEqual(
            [type_uri for type_uri, _ in self.registry.entries()],
            [Other.TYPE, Fake.TYPE],
        )


class DefaultRegistryTests(unittest.TestCase):
    def test_the_default_registry_holds_the_predicates_that_ship(self):
        """Importing the package is what registers them, so this also asserts
        that the side effect happened. Derived from the modules rather than a
        literal list, so a third predicate does not need this test edited."""
        from ariadne_lib import predicates

        shipped = sorted(
            module.TYPE
            for module in vars(predicates).values()
            if getattr(module, "TYPE", None) and getattr(module, "SUMMARY", None)
        )
        self.assertEqual(
            [type_uri for type_uri, _ in registry.DEFAULT.entries()], shipped
        )
        self.assertTrue(len(shipped) >= 2)

    def test_the_default_registry_holds_all_five_public_contracts(self):
        from ariadne_lib import predicates

        expected = {
            predicates.dataset.TYPE,
            predicates.grounded_agent.TYPE,
            predicates.solidity_release.TYPE,
            predicates.state_fixture.TYPE,
            predicates.state_fixture_v2.TYPE,
        }
        self.assertEqual(
            {type_uri for type_uri, _ in registry.DEFAULT.entries()}, expected
        )
        self.assertEqual(len(registry.DEFAULT), 5)

    def test_all_five_shipped_checks_declare_their_complete_result_set(self):
        from ariadne_lib import predicates

        shipped = (
            predicates.dataset,
            predicates.grounded_agent,
            predicates.solidity_release,
            predicates.state_fixture,
            predicates.state_fixture_v2,
        )
        for module in shipped:
            with self.subTest(predicate_type=module.TYPE):
                declared = getattr(module, "EXPECTED_RESULTS", None)
                self.assertIsInstance(declared, tuple)
                self.assertEqual(
                    tuple(number for number, _ in declared if number is not None),
                    gates.PREDICATE_GATES,
                )
                names = tuple(name for _, name in declared)
                self.assertEqual(len(names), len(set(names)))

    def test_state_fixture_versions_are_distinct_registered_contracts(self):
        from ariadne_lib import predicates

        self.assertIs(registry.DEFAULT.get(predicates.state_fixture.TYPE),
                      predicates.state_fixture)
        self.assertIs(registry.DEFAULT.get(predicates.state_fixture_v2.TYPE),
                      predicates.state_fixture_v2)
        self.assertIsNot(predicates.state_fixture, predicates.state_fixture_v2)


if __name__ == "__main__":
    unittest.main()
