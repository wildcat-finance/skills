"""Full-key routing, independent cardinalities and unchanged native claims."""

from copy import deepcopy
import itertools
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wildcat_sanctions_fixtures import (ESCROWED, QUEUED, QUEUE, TRANSFER, inputs)
from wildcat_v3_fixtures import ACCOUNT, ESCROW, MARKET, OTHER, ZERO, log, record, word
from tabularium_lib.core import TabulariumError, canonical_json
from tabularium_lib.wildcat_rows import map_records


class SanctionsSemanticTests(unittest.TestCase):
    def mapped(self, venue="wildcat-v2", records=None, contexts=None):
        original_contexts, original_records = inputs(venue)
        return map_records(venue, original_contexts if contexts is None else contexts,
                           original_records if records is None else records)

    def test_constructed_positive_branches_keep_native_parties_and_units(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            result = self.mapped(venue)
            self.assertEqual(len(result['events']), 1 if venue.endswith('v1') else 3)
            companions = [m for m in result['mapping_records'] if m['signature'] in (QUEUED, ESCROWED)]
            self.assertEqual(len(companions), 1 if venue.endswith('v1') else 2)
            for m in companions:
                self.assertEqual(m['disposition'], 'supporting-routing')
                self.assertEqual(len(m['routing_joins']), 1)
            transfer = next(e for e in result['events'] if e['action'].endswith('.transfer'))
            self.assertEqual(transfer['parties'], [{'role':'from','address':ACCOUNT},{'role':'to','address':ESCROW}])
            self.assertEqual(transfer['amounts'], [{'kind':'market-token-claims','base_units':'40','asset':MARKET}])
            if venue.endswith('v2'):
                queued = next(e for e in result['events'] if e['action'].endswith('.withdrawal-queued'))
                self.assertEqual(queued['parties'], [{'role':'withdrawing-account','address':ACCOUNT}])
                self.assertEqual(queued['amounts'], [{'kind':'normalized-claims','base_units':'80','asset':MARKET},
                                                    {'kind':'scaled-claims','base_units':'70','asset':None}])

    def test_closed_relations_and_complete_conditions_are_reciprocal(self):
        result = self.mapped()
        mappings = {m['source_selector']:m for m in result['mapping_records']}
        events = {e['provenance']['source_selector']:e for e in result['events']}
        for companion in (m for m in mappings.values() if m['signature'] in (QUEUED, ESCROWED)):
            relation, = companion['routing_joins']
            self.assertEqual(set(relation), {'evidence_class','rule','primary_selector','companion_selector','conditions'})
            self.assertEqual(relation['evidence_class'], 'join-inference')
            primary = mappings[relation['primary_selector']]
            self.assertEqual(primary['routing_joins'], [relation])
            self.assertEqual(relation['companion_selector'], companion['source_selector'])
            self.assertIn(primary['source_selector'],companion['supporting_selectors'])
            self.assertIn(companion['source_selector'],primary['supporting_selectors'])
            self.assertIn(companion['source_selector'],events[primary['source_selector']]['provenance']['supporting_selectors'])
            self.assertEqual(relation['rule'], 'same-market-transaction-account-expiry-scaled-normalized' if companion['signature']==QUEUED else 'same-market-transaction-account-escrow-amount')
            keys = {'generation','market','transaction_hash','account'}
            keys |= {'expiry','scaled_amount','normalized_amount'} if companion['signature']==QUEUED else {'escrow','amount'}
            self.assertEqual(set(relation['conditions']),keys)
            self.assertEqual(relation['conditions']['generation'],'wildcat-v2')

    def test_every_queue_native_field_is_required(self):
        for field in ('account','expiry','scaled','normalized'):
            contexts, records=inputs()
            raw=deepcopy(records[-1][0])
            if field=='account': raw['topics'][1]='0x'+word(OTHER)
            else:
                values={'expiry':124,'scaled':71,'normalized':81}
                data=[123,70,80];data[('expiry','scaled','normalized').index(field)]=values[field]
                raw['data']='0x'+''.join(word(v) for v in data)
            records[-1]=record(raw)
            with self.subTest(field=field): self.assert_unmatched(self.mapped(records=records),QUEUED,'missing-primary')

    def test_every_escrow_native_field_is_required_in_both_generations(self):
        for venue,field in itertools.product(('wildcat-v1','wildcat-v2'),('account','escrow','amount')):
            contexts,records=inputs(venue);raw=deepcopy(records[1][0])
            if field=='account': raw['topics'][1]='0x'+word(OTHER)
            else: raw['data']='0x'+word(OTHER if field=='escrow' else ESCROW)+word(41 if field=='amount' else 40)
            records[1]=record(raw)
            with self.subTest(venue=venue,field=field):self.assert_unmatched(self.mapped(venue,records),ESCROWED,'missing-primary')

    def assert_unmatched(self,result,signature,reason,count=1):
        companions=[m for m in result['mapping_records'] if m['signature']==signature]
        self.assertEqual(len(companions),count)
        prefix='routing:sanctioned-assets-'+('queued-for-withdrawal' if signature==QUEUED else 'sent-to-escrow')
        for companion in companions:
            self.assertEqual(companion['routing_joins'],[])
            self.assertEqual(companion['disposition'],'supporting-routing')
            disposition=next(d for d in result['dispositions'] if d['source_selector']==companion['source_selector'])
            self.assertEqual(disposition['gaps'],[prefix+':'+reason])
            self.assertTrue(companion['limitations'])
        self.assertEqual(result['unsupported_counts'][prefix+':'+reason],count)

    def test_duplicate_primary_refuses_arbitrary_pairing(self):
        for signature,position in ((ESCROWED,0),(QUEUED,2)):
            contexts,records=inputs();raw=deepcopy(records[position][0]);raw['logIndex']='0x14'
            records.append(record(raw))
            with self.subTest(signature=signature):self.assert_unmatched(self.mapped(records=records),signature,'ambiguous-match')

    def test_duplicate_companion_counts_one_gap_per_companion(self):
        for signature,position in ((ESCROWED,1),(QUEUED,4)):
            contexts,records=inputs();raw=deepcopy(records[position][0]);raw['logIndex']='0x14';records.append(record(raw))
            with self.subTest(signature=signature):self.assert_unmatched(self.mapped(records=records),signature,'ambiguous-match',2)

    def test_absent_primary_and_ordinary_unaccompanied_primary_are_distinct(self):
        for signature,position in ((ESCROWED,0),(QUEUED,2)):
            contexts,records=inputs();records.pop(position)
            self.assert_unmatched(self.mapped(records=records),signature,'missing-primary')
        contexts,records=inputs();result=self.mapped(records=[records[0],records[2]])
        self.assertFalse(any(k.startswith('routing:') for k in result['unsupported_counts']))
        self.assertTrue(all(m['routing_joins']==[] for m in result['mapping_records']))

    def test_primary_transfer_value_and_queue_amounts_must_match(self):
        for position,signature,data in ((0,ESCROWED,(41,)), (2,QUEUED,(71,80)), (2,QUEUED,(70,81))):
            contexts,records=inputs();raw=deepcopy(records[position][0])
            raw['data']='0x'+''.join(word(value) for value in data)
            records[position]=record(raw)
            with self.subTest(position=position,data=data):
                self.assert_unmatched(self.mapped(records=records),signature,'missing-primary')

    def test_market_and_transaction_are_both_required(self):
        for signature,position,field in itertools.product((ESCROWED,QUEUED),(0,),('market','transaction')):
            contexts,records=inputs();position=1 if signature==ESCROWED else 4
            raw=deepcopy(records[position][0])
            if field=='market':
                contexts[OTHER]=deepcopy(contexts[MARKET]);raw['address']=OTHER
            else:raw['transactionHash']='0x'+'cc'*32;raw['transactionIndex']='0x3'
            records[position]=record(raw)
            with self.subTest(signature=signature,field=field):self.assert_unmatched(self.mapped(records=records,contexts=contexts),signature,'missing-primary')

    def test_generation_and_wrong_emitter_roles_do_not_join(self):
        contexts,records=inputs()
        result=map_records('wildcat-v1',*inputs('wildcat-v1'))
        self.assertFalse(any(m['signature']==QUEUED for m in result['mapping_records']))
        v1contexts,_=inputs('wildcat-v1')
        queued_only=[records[2],records[4]]
        result=map_records('wildcat-v1',v1contexts,queued_only)
        self.assertFalse(any(m['routing_joins'] for m in result['mapping_records']))
        wrapper=next(address for address,c in contexts.items() if c['role']=='wrapper')
        raw=deepcopy(records[0][0]);raw['address']=wrapper;records[0]=record(raw)
        self.assert_unmatched(self.mapped(records=records,contexts=contexts),ESCROWED,'missing-primary')
        contexts[MARKET]['role']='wrapper'
        with self.assertRaises(TabulariumError):self.mapped(contexts=contexts)

    def test_permutations_and_intervening_logs_leave_identical_bytes(self):
        contexts,records=inputs();expected=canonical_json(self.mapped())
        for permutation in itertools.permutations(records):
            self.assertEqual(canonical_json(self.mapped(records=list(permutation))),expected)

    def test_batch_burn_and_sanctions_relations_both_survive(self):
        for venue in ('wildcat-v1','wildcat-v2'):
            result=map_records(venue,*inputs(venue,overlap=True))
            transfer=next(m for m in result['mapping_records'] if m['signature']==TRANSFER)
            self.assertEqual(transfer['join']['rule'],'adjacent-market-burn')
            routing,=transfer['routing_joins'];self.assertEqual(routing['rule'],'same-market-transaction-account-escrow-amount')
            self.assertIn(transfer['join']['primary_selector'],transfer['supporting_selectors'])
            self.assertIn(routing['companion_selector'],transfer['supporting_selectors'])
            event=next(e for e in result['events'] if e['action'].endswith('.transfer'))
            self.assertIn(routing['companion_selector'],event['provenance']['supporting_selectors'])
            self.assertIn(transfer['join']['primary_selector'],event['provenance']['supporting_selectors'])
            self.assertEqual(len(result['events']),2)

    def test_legacy_sanctions_control_is_byte_identical_to_parent_mapper(self):
        golden=json.loads((Path(__file__).parent/'fixtures/wildcat-sanctions-legacy-v1.json').read_bytes())
        for venue in ('wildcat-v1','wildcat-v2'):
            result=map_records(venue,*inputs(venue),adapter_version='1.0.0')
            self.assertEqual(canonical_json(result),canonical_json(golden[venue]))
            self.assertTrue(all('routing_joins' not in m for m in result['mapping_records']))

    def test_unknown_versions_refuse(self):
        for version in ('1.1.0','1.2.0','1.3','1.3.1',None,[],True):
            with self.subTest(version=version),self.assertRaises(TabulariumError):
                map_records('wildcat-v2',*inputs(),adapter_version=version)
