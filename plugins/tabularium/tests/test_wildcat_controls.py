"""Versioned market controls retain native fields without financial amounts."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support
from tabularium_lib.core import TabulariumError,canonical_json
from tabularium_lib.release_v2 import validate_event_row,ADAPTERS
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_release import build_wildcat_canonical,verify_wildcat_canonical
from tabularium_lib.wildcat_validation import validate_row
from tabularium_lib.wildcat_versions import SUPPORTED_VERSIONS
from wildcat_v3_fixtures import ACCOUNT,OTHER,MARKET,ZERO,constructed_inputs,log,record
from test_wildcat_v3_release import constructed_release
from test_wildcat_v3_schema_parity import locked_oracle


def inputs(venue):
    contexts,_=constructed_inputs(venue);contexts={MARKET:contexts[MARKET]}
    raws=[log("Approval(address,address,uint256)",(ACCOUNT,OTHER),(2**256-1,),index=0),
        log("ChangedSpherexEngineAddress(address,address)",(),(ZERO,OTHER),index=1),
        log("ChangedSpherexOperator(address,address)",(),(ACCOUNT,ZERO),index=2)]
    return contexts,[record(r) for r in raws]


class MarketControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oracle=locked_oracle();cls.validator=oracle.Draft202012Validator(support.event_schema(3))

    def test_native_fields_are_state_observations_and_never_amounts(self):
        for venue in ("wildcat-v1","wildcat-v2"):
            contexts,records=inputs(venue);value=map_records(venue,contexts,records,"1.6.0")
            self.assertEqual(len(value["events"]),3)
            self.assertEqual([r["decoded"] for r in value["mapping_records"]],[
                {"owner":ACCOUNT,"spender":OTHER,"value":str(2**256-1)},
                {"oldEngineAddress":ZERO,"newEngineAddress":OTHER},
                {"oldSphereXAdmin":ACCOUNT,"newSphereXAdmin":ZERO}])
            self.assertTrue(all(r["amounts"]==[] and r["event_family"]=="pool-state" for r in value["events"]))
            self.assertEqual([r["role"] for r in value["events"][0]["parties"]],["pool","allowance-owner","allowance-spender"])
            self.assertEqual(value["events"][0]["native_record"],records[0][0])
            for row in value["events"]:
                validate_event_row(row,ADAPTERS[venue],3);validate_row(row,venue,3)
                self.assertEqual(list(self.validator.iter_errors(row)),[])

    def test_every_prior_version_keeps_all_three_controls_unsupported(self):
        for venue in ("wildcat-v1","wildcat-v2"):
            contexts,records=inputs(venue)
            for version in SUPPORTED_VERSIONS:
                if version=="1.6.0":continue
                value=map_records(venue,contexts,records,version)
                self.assertEqual(len(value["events"]),0,(venue,version))
                self.assertEqual([r["native_record"] for r in value["mapping_records"]],[r[0] for r in records])
                self.assertEqual({r["disposition"] for r in value["mapping_records"]},{"unsupported-canonical-meaning"})

    def test_malformed_accepted_control_abi_and_duplicate_log_refuse(self):
        for venue in ("wildcat-v1","wildcat-v2"):
            contexts,records=inputs(venue)
            for index in range(3):
                changed=copy.deepcopy(records);changed[index][0]["data"]="0x"
                with self.assertRaises(TabulariumError):map_records(venue,contexts,changed,"1.6.0")
            with self.assertRaises(TabulariumError):map_records(venue,contexts,records+records[:1],"1.6.0")

    def test_control_rule_cannot_be_relabelled_as_an_earlier_adapter(self):
        contexts,records=inputs("wildcat-v2");value=map_records("wildcat-v2",contexts,records,"1.6.0")
        for original in value["events"]:
            row=copy.deepcopy(original);row["provenance"]["adapter_version"]="1.5.0"
            with self.assertRaises(TabulariumError):validate_event_row(row,ADAPTERS["wildcat-v2"],3)
            self.assertTrue(list(self.validator.iter_errors(row)))

    def test_fresh_release_rebuilds_and_verifies_from_preserved_raw(self):
        for venue in ("wildcat-v1","wildcat-v2"):
            with tempfile.TemporaryDirectory() as temporary:
                base=Path(temporary).resolve();contexts,records=inputs(venue)
                def replace(document,journal,plan):
                    document["contexts"]=[{"address":address,**{key:c[key] for key in ("role","asset","market","abi_variant","concrete_contract")}} for address,c in contexts.items()]
                    item=journal["records"][0];response=json.loads(item["response"]);response["result"]=[r[0] for r in records]
                    request=json.loads(item["request"]);request["params"][0]["address"]=[MARKET]
                    item.update(request=canonical_json(request).decode(),response=canonical_json(response).decode())
                    for capture in plan["captures"]:capture["scope"]["subjects"]=["eip155:1:"+MARKET]
                raw=constructed_release(base,venue,replace)
                for name in ("a","b"):
                    build_wildcat_canonical(raw,base/name,"constructed-market-controls","1.6.0")
                    verify_wildcat_canonical(base/name/"coverage.json")
                for name in ("source.json","capture.json","events.jsonl","coverage.json"):
                    self.assertEqual((base/"a"/name).read_bytes(),(base/"b"/name).read_bytes())


if __name__=="__main__":unittest.main()
