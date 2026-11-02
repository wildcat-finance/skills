"""Assert native parameter meaning against every frozen concrete declaration."""

from copy import deepcopy
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from unittest import mock

from wildcat_parameter_fixtures import inputs, suffix
from wildcat_v3_fixtures import MARKET, ZERO, record, word
from tabularium_lib.core import TabulariumError
from tabularium_lib.wildcat_abi import VARIANTS
from tabularium_lib.wildcat_parameters import NATIVE_RULES, UNSUPPORTED_REASONS
from tabularium_lib.wildcat_rows import map_records

VENUES = ("wildcat-v1", "wildcat-v2")


class ParameterMappingTests(unittest.TestCase):
    def test_all_58_concrete_declarations_and_29_contexts_map_exact_native_fields(self):
        observed = set()
        count = 0
        for venue in VENUES:
            contexts, records, expected = inputs(venue)
            result = map_records(venue, contexts, records)
            self.assertEqual(len(result["events"]), len(expected))
            for event, mapping, (entry, emitter, values) in zip(result["events"], result["mapping_records"], expected):
                with self.subTest(venue=venue, variant=entry["variant"], signature=entry["signature"]):
                    count += 1
                    observed.add((venue, entry["role"], entry["signature"]))
                    self.assertEqual(mapping["decoded"], values)
                    self.assertEqual(set(mapping["decoded"]), {f["name"] for f in entry["fields"]})
                    self.assertEqual(mapping["signature"], entry["signature"])
                    self.assertEqual(event["action"], venue + "." + suffix(entry))
                    self.assertEqual(event["event_family"], "pool-state")
                    self.assertEqual(event["amounts"], [])
                    self.assertEqual(event["instrument"], {"type": venue + "-" + entry["role"], "id": emitter})
                    self.assertEqual(event["provenance"]["adapter_version"], "1.2.0")
                    self.assertEqual(event["provenance"]["mapping_rule"], event["action"] + ".v1")
                    self.assertEqual(event["native_record"], mapping["native_record"])
        self.assertEqual((count, len(observed)), (58, 29))
        self.assertEqual(len(NATIVE_RULES), 29)

    def test_only_emitter_and_emitted_accounts_markets_providers_are_parties(self):
        for venue in VENUES:
            contexts, records, expected = inputs(venue)
            result = map_records(venue, contexts, records)
            for event, (entry, emitter, values) in zip(result["events"], expected):
                parties = [{"role": "pool" if entry["role"] == "market" else entry["role"], "address": emitter}]
                if entry["role"] != "market" and "market" in values:
                    parties.append({"role": "pool", "address": values["market"]})
                for field in ("account", "accountAddress", ""):
                    if field in values:
                        parties.append({"role": "affected-account", "address": values[field]})
                if "providerAddress" in values:
                    parties.append({"role": "role-provider", "address": values["providerAddress"]})
                self.assertEqual(event["parties"], parties)
                if entry["role"] != "market" and "market" not in values:
                    self.assertNotIn("pool", [party["role"] for party in event["parties"]])
                    self.assertNotIn(MARKET, [party["address"] for party in event["parties"]])

    def test_zero_addresses_and_maximum_widths_keep_exact_native_state(self):
        for venue in VENUES:
            for options in ({"maximum": True}, {"zero": True}):
                contexts, records, expected = inputs(venue, **options)
                result = map_records(venue, contexts, records)
                for mapping, (_, _, values) in zip(result["mapping_records"], expected):
                    self.assertEqual(mapping["decoded"], values)
                self.assertTrue(all(not row["amounts"] for row in result["events"]))
                if options.get("zero"):
                    self.assertTrue(any(party["address"] == ZERO for event in result["events"] for party in event["parties"]))

    def test_unnamed_and_unusual_keys_do_not_gain_normalised_aliases_or_role_enum(self):
        contexts, records, _ = inputs("wildcat-v1", maximum=True)
        result = map_records("wildcat-v1", contexts, records)
        by_signature = {mapping["signature"]: mapping["decoded"] for mapping in result["mapping_records"]}
        self.assertEqual(set(by_signature['LenderAuthorized(address)']), {""})
        self.assertEqual(by_signature['AuthorizationStatusUpdated(address,uint8)']["role"], "255")
        for signature, key in (("AnnualInterestBipsUpdated(uint256)", "annualInterestBipsUpdated"),
                               ("ReserveRatioBipsUpdated(uint256)", "reserveRatioBipsUpdated"),
                               ("MaxTotalSupplyUpdated(uint256)", "assets")):
            self.assertEqual(set(by_signature[signature]), {key})

    def test_dynamic_hook_names_include_empty_unicode_and_multislot_text(self):
        for name in ("", "鉤𓁟", "x" * 65):
            contexts, records, expected = inputs("wildcat-v2", name=name)
            result = map_records("wildcat-v2", contexts, records)
            names = [mapping["decoded"]["name"] for mapping in result["mapping_records"] if mapping["signature"] == "NameUpdated(string)"]
            self.assertTrue(names)
            self.assertEqual(set(names), {name})

    def test_every_last_group_concrete_variant_has_its_exact_signature_reason(self):
        signatures = set()
        for venue in VENUES:
            contexts, records, expected = inputs(venue, "last_group")
            result = map_records(venue, contexts, records)
            self.assertEqual(result["events"], ())
            for mapping, (entry, _, _) in zip(result["mapping_records"], expected):
                signature = entry["signature"]
                signatures.add(signature)
                self.assertEqual(mapping["disposition"], "unsupported-canonical-meaning")
                self.assertEqual(mapping["limitations"], [signature + ": " + UNSUPPORTED_REASONS[signature]])
                self.assertIn("canonical:%s:%s" % (entry["role"], signature), result["unsupported_counts"])
        self.assertEqual(signatures, set(UNSUPPORTED_REASONS))

    def test_hooks_template_never_inherits_instance_meaning(self):
        contexts, records, _ = inputs("wildcat-v2")
        selected = next((address, context) for address, context in contexts.items() if context["role"] == "hooks-instance")
        address, context = selected
        variant = next((key, item) for key, item in VARIANTS.items() if item["contract"] == context["concrete_contract"] and
                       {"generation": "wildcat-v2", "role": "hooks-template"} in item["bindings"])
        template = deepcopy(context)
        template.update(role="hooks-template", abi_variant=variant[0])
        raw = next(raw for raw, _ in records if raw["address"] == address)
        result = map_records("wildcat-v2", {address: template}, [record(raw)])
        self.assertFalse(result["events"])
        self.assertEqual(result["mapping_records"][0]["disposition"], "unsupported-canonical-meaning")

    def test_generation_and_role_mismatches_refuse_before_mapping(self):
        contexts, records, _ = inputs("wildcat-v1")
        for change in ("generation", "role"):
            wrong = deepcopy(contexts)
            venue = "wildcat-v2" if change == "generation" else "wildcat-v1"
            if change == "role":
                next(iter(wrong.values()))["role"] = "factory"
            with self.assertRaises(TabulariumError):
                map_records(venue, wrong, records)

    def test_malformed_width_padding_topic_count_and_dynamic_offsets_refuse(self):
        contexts, records, expected = inputs("wildcat-v2")
        for original, entry in zip(records, expected):
            raw, _ = original
            for change in ("extra-topic", "truncated", "trailing"):
                changed = deepcopy(raw)
                if change == "extra-topic": changed["topics"].append("0x" + "00" * 32)
                if change == "truncated": changed["data"] = "0x"
                if change == "trailing": changed["data"] += "00" * 32
                if change == "truncated" and raw["data"] == "0x": continue
                with self.subTest(signature=entry[0]["signature"], change=change), self.assertRaises(TabulariumError):
                    map_records("wildcat-v2", contexts, [record(changed)])

    def test_overwidth_addresses_integers_and_noncanonical_string_tails_refuse(self):
        for venue in VENUES:
            contexts, records, expected = inputs(venue)
            for original, (entry, _, _) in zip(records, expected):
                raw = original[0]
                indexed_position = 1
                data_position = 0
                for field in entry["fields"]:
                    changed = deepcopy(raw)
                    kind = field["type"]
                    width = 160 if kind == "address" else int(kind[4:]) if kind.startswith("uint") else None
                    if width is not None and width < 256:
                        if field["indexed"]:
                            changed["topics"][indexed_position] = "0x" + word(1 << width)
                        else:
                            start = 2 + data_position * 64
                            changed["data"] = changed["data"][:start] + word(1 << width) + changed["data"][start + 64:]
                        with self.subTest(signature=entry["signature"], field=field["name"]), self.assertRaises(TabulariumError):
                            map_records(venue, contexts, [record(changed)])
                    if kind == "string":
                        for string_change in ("offset", "padding", "utf8"):
                            changed = deepcopy(raw)
                            data = bytearray.fromhex(raw["data"][2:])
                            if string_change == "offset": data[:32] = (64).to_bytes(32, "big")
                            if string_change == "padding": data[-1] = 1
                            if string_change == "utf8": data[64] = 255
                            changed["data"] = "0x" + data.hex()
                            with self.subTest(change=string_change), self.assertRaises(TabulariumError):
                                map_records(venue, contexts, [record(changed)])
                    if field["indexed"]: indexed_position += 1
                    else: data_position += 1

    def test_changed_or_duplicate_native_field_names_refuse(self):
        contexts, records, expected = inputs("wildcat-v2")
        chosen = next(i for i, (entry, _, _) in enumerate(expected) if entry["signature"] == "AccountAccessGranted(address,address,uint32)")
        entry = expected[chosen][0]
        for name in ("renamed", "providerAddress"):
            changed = deepcopy(VARIANTS)
            target = next(value for value in changed[entry["variant"]]["events"].values() if value["signature"] == entry["signature"])
            target["abi"]["inputs"][1]["name"] = name
            with mock.patch.dict(VARIANTS, changed), self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [records[chosen]])

    def test_input_container_order_is_irrelevant_native_positions_are_not(self):
        contexts, records, _ = inputs("wildcat-v2")
        original = map_records("wildcat-v2", contexts, records)
        self.assertEqual(map_records("wildcat-v2", contexts, list(reversed(records))), original)
        changed = deepcopy(records)
        changed[0][0]["logIndex"], changed[1][0]["logIndex"] = changed[1][0]["logIndex"], changed[0][0]["logIndex"]
        changed = [record(raw, index) for index, (raw, _) in enumerate(changed)]
        self.assertNotEqual(map_records("wildcat-v2", contexts, changed)["events"], original["events"])

    def test_legacy_selector_never_acquires_native_parameter_meaning(self):
        for venue in VENUES:
            contexts, records, expected = inputs(venue)
            result = map_records(venue, contexts, records, "1.0.0")
            self.assertEqual(result["events"], ())
            self.assertTrue(all(mapping["limitations"] == ["The concrete ABI is decoded; no canonical meaning is admitted for this event."] for mapping in result["mapping_records"]))
            for version in ("1.1.0", "1.3.0", "2.0.0", None, True, [], {}):
                with self.assertRaises(TabulariumError):
                    map_records(venue, contexts, records, version)
