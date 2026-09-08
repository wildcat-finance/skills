"""Production positional ownership, immutable legacy identity and hostile replay."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tests import test_usdc_interval as existing
from tests import test_interval as epoch_fixture
from tests import test_usdc_interval_demo as synthetic
from tests import test_usdc_interval_live_demo as live
from alexandria_lib import interval
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.release import ingest
from usdc_interval import Collector, check_interval


def evidence():
    value = epoch_fixture.epoch_evidence()
    upgrade = value['upgrade_logs'][0]
    value['upgrade_logs'] = [upgrade]
    block = int(upgrade['blockNumber'], 16)
    upgrade['transactionIndex'], upgrade['logIndex'] = '0x2', '0x4'
    before = deepcopy(upgrade)
    before.update(topics=['0x' + 'aa' * 32], transactionIndex='0x1', logIndex='0x3', transactionHash='0x' + '01' * 32)
    after = deepcopy(before)
    after.update(transactionIndex='0x3', logIndex='0x5', transactionHash='0x' + '02' * 32)
    value['upgrade_logs'] = [before, upgrade, after]
    # The legacy API takes upgrades alone; the production opening phase used to
    # perform that filtering before calling discovery.
    return value, block


class ProductionConformanceTests(existing.ReleaseTestCase):
    def derive(self, value):
        return interval.discover_epochs(**value)

    def test_before_and_after_upgrade(self):
        # Exercise the real collector/build path. On the unfixed parent its
        # receipt assigns the before-upgrade event to implementation B.
        upgrade = self.state['logs']['2'][0]
        upgrade['transactionIndex'], upgrade['logIndex'] = '0x2', '0x4'
        before = deepcopy(upgrade)
        before.update(topics=['0x' + 'aa' * 32], transactionIndex='0x1', logIndex='0x3', transactionHash='0x' + '01' * 32)
        after = deepcopy(before)
        after.update(transactionIndex='0x3', logIndex='0x5', transactionHash='0x' + '02' * 32)
        self.state['logs']['2'][0:1] = [before, upgrade, after]
        staging, output = self.pipeline()
        self.build(staging, output)
        receipt = existing.component_document(output, 'epoch-table')
        epochs = receipt['epochs']
        if 'log_attributions' in receipt:
            rows = {row['transaction_hash']: row for row in receipt['log_attributions']}
            before_owner = epochs[rows[before['transactionHash']]['epoch_index']]['implementation']
            after_owner = epochs[rows[after['transactionHash']]['epoch_index']]['implementation']
            self.assertEqual(rows[upgrade['transactionHash']]['kind'], 'upgrade-boundary')
        else:
            block = int(before['blockNumber'], 16)
            owner = next(epoch for epoch in epochs if int(epoch['start_block']) <= block <= int(epoch['end_block']))
            before_owner = after_owner = owner['implementation']
        self.assertEqual(before_owner, existing.IMPLEMENTATION_A)
        self.assertEqual(after_owner, existing.IMPLEMENTATION_B)
        self.assertEqual(check_interval(output)['receipt_semantics'], 'v2-positional')

    def test_upgrade_in_last_block(self):
        value, block = evidence()
        value['interval']['end'] = str(block)
        epochs = self.derive(value)
        self.assertEqual(epochs[-1]['end_position'], {'block_number':str(block+1),'transaction_index':None,'log_index':None})
        self.assertEqual([row['epoch_index'] for row in interval.attribute_logs(value['upgrade_logs'], value['proxy'], value['interval'], epochs)], [0,1,1])

    def test_first_block_upgrade_refuses(self):
        value, block = evidence()
        value['interval']['start'] = str(block)
        with self.assertRaisesRegex(AlexandriaError, 'first-block'):
            self.derive(value)

    def same_transaction(self, offset):
        value, _ = evidence()
        ordinary, upgrade = value['upgrade_logs'][offset], value['upgrade_logs'][1]
        ordinary['transactionIndex'] = upgrade['transactionIndex']
        ordinary['transactionHash'] = upgrade['transactionHash']
        with self.assertRaisesRegex(AlexandriaError, 'upgrade transaction'):
            self.derive(value)

    def test_same_transaction_before_upgrade_refuses(self):
        self.same_transaction(0)

    def test_same_transaction_after_upgrade_refuses(self):
        self.same_transaction(2)

    def test_multiple_upgrades_refuse(self):
        value, _ = evidence()
        value['upgrade_logs'][2]['topics'] = value['upgrade_logs'][1]['topics']
        with self.assertRaisesRegex(AlexandriaError, 'multiple upgrades'):
            self.derive(value)

    def test_malformed_coordinates_refuse(self):
        for field in ('blockNumber','transactionIndex','logIndex'):
            for bad in (None, True, -1, '0x-1', '0x01', '0x', '7'):
                with self.subTest(field=field, bad=bad):
                    value, _ = evidence()
                    value['upgrade_logs'][0][field] = bad
                    with self.assertRaises(AlexandriaError):
                        self.derive(value)
        for edit in ('duplicate','reversed','log-regression','missing'):
            with self.subTest(edit=edit):
                value, _ = evidence()
                logs = value['upgrade_logs']
                if edit == 'duplicate': logs.insert(1,deepcopy(logs[0]))
                if edit == 'reversed': logs.reverse()
                if edit == 'log-regression': logs[2]['logIndex']='0x1'
                if edit == 'missing': del logs[0]['transactionIndex']
                with self.assertRaises(AlexandriaError): self.derive(value)

    def test_contradictory_hash_index_pairs_refuse(self):
        for field, replacement in (('transactionHash','0x'+'01'*32),('transactionIndex','0x1'),('blockHash','0x'+'03'*32)):
            with self.subTest(field=field):
                value, _ = evidence()
                value['upgrade_logs'][2][field] = replacement
                with self.assertRaises(AlexandriaError): self.derive(value)

    def historical(self, module, name):
        output = self.root/name
        summary = module.demo().build(output)
        expected = json.loads((module.EXAMPLE/'expected.json').read_text())
        self.assertEqual(summary['release_id'], expected['release_id'])
        return output/'release'

    def test_historical_live_release_identity(self):
        self.historical(live, 'live')

    def test_historical_synthetic_release_identity(self):
        self.historical(synthetic, 'synthetic')

    def test_v1_has_no_positional_claim(self):
        output = self.historical(live, 'legacy')
        receipt = existing.component_document(output,'epoch-table')
        self.assertNotIn('log_attributions',receipt)
        self.assertNotIn('start_position',receipt['epochs'][0])
        self.assertEqual(check_interval(output)['receipt_semantics'],'v1-block-only')

    def test_offline_rederives_attributions(self):
        staging, output = self.pipeline()
        self.build(staging,output)
        receipt = existing.component_document(output,'epoch-table')
        rows = receipt['log_attributions']
        self.assertEqual(len(rows),sum(map(len,self.state['logs'].values())))
        self.assertEqual(check_interval(output)['receipt_semantics'],'v2-positional')

    def rebound(self, edit, reason='does not match|do not match'):
        staging, original = self.pipeline()
        self.build(staging,original)
        manifest=json.loads((original/'manifest.json').read_text())
        source=self.root/'rebound-source';source.mkdir()
        components=[]
        for component in manifest['components']:
            document=existing.component_document(original,component['name'])
            if component['name']=='epoch-table': edit(document)
            filename=component['name']+'.json'
            (source/filename).write_bytes(canonical_bytes(document))
            components.append({key:component[key] for key in ('name','access','media_type','redistribution','role')} | {'path':filename})
        plan={'format':'alexandria-capture-plan/v1','release':manifest['release'],'captures':[{key:value for key,value in capture.items() if key!='component_sha256'} for capture in manifest['captures']],'components':components}
        (source/'plan.json').write_bytes(canonical_bytes(plan))
        output=self.root/'rebound'
        ingest(source/'plan.json',output)
        with self.assertRaisesRegex(AlexandriaError, reason):
            check_interval(output)

    def test_rebound_owner_tampering_refuses(self):
        self.rebound(lambda receipt:receipt['log_attributions'][0].__setitem__('epoch_index',1))

    def test_rebound_boundary_tampering_refuses(self):
        def edit(receipt):
            receipt['epochs'][0]['end_position']['log_index'] += 1
            receipt['epochs'][1]['start_position']['log_index'] += 1
            receipt['epochs'][1]['upgrade']['log_index'] += 1
        self.rebound(edit)

    def test_interrupted_collection_preserves_journals(self):
        clean=self.scratch('clean')
        Collector(self.plan,clean,existing.FixtureTransport(self.state)).collect()
        resumed=self.scratch('resumed')
        with self.assertRaises(existing._Killed):
            Collector(self.plan,resumed,existing.KillingTransport(self.state,kill_at='shard 2 boundary-blocks')).collect()
        Collector(self.plan,resumed,existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.journals(clean),existing.journals(resumed))

    def test_unsupported_positions_leave_refusal(self):
        self.state['logs']['0'][0]['transactionIndex']=True
        staging=self.scratch('refusal')
        with self.assertRaises(AlexandriaError):
            Collector(self.plan,staging,existing.FixtureTransport(self.state)).collect()
        receipts=list((staging/'receipts').glob('*.jsonl'))
        self.assertTrue(receipts)
        self.assertIn('malformed-upgrade-log', ''.join(path.read_text() for path in receipts))

    def test_rebound_boolean_owner_refuses(self):
        self.rebound(lambda receipt: receipt['log_attributions'][0].__setitem__('epoch_index', False), 'non-negative integers')

    def test_rebound_boolean_upgrade_index_refuses(self):
        self.rebound(lambda receipt: receipt['epochs'][1]['upgrade'].__setitem__('transaction_index', False), 'indexes must')

    def test_malformed_interval_refuses_without_key_error(self):
        for bad in (None, [], {}, {'start':'0'}, {'start':True,'end':'2'}):
            with self.subTest(interval=bad):
                value, _ = evidence()
                value['interval'] = bad
                with self.assertRaises(AlexandriaError): self.derive(value)

    def test_original_secondary_extra_log_specimen_refuses(self):
        class OriginalSecondary(existing.FixtureTransport):
            def logs(self, shard):
                records = super().logs(shard)
                return records + existing.second_fixture()['extra_logs'].get(str(shard['index']), [])
        staging = self.scratch('secondary-refusal')
        Collector(self.plan, staging, existing.FixtureTransport(self.state)).collect()
        result = existing.Reconciler(self.plan, staging, OriginalSecondary(self.state), 'second fixture').reconcile()
        self.assertEqual(result['reconciliation']['status'], 'unreconciled')

    def test_maximum_block_keeps_exclusive_end_sentinel(self):
        value, _ = evidence()
        first = value['interval']['start']
        value['interval']['end'] = str(interval.MAX_BLOCK)
        value['block_hashes'][str(interval.MAX_BLOCK)] = value['block_hashes'][first]
        epochs = self.derive(value)
        self.assertEqual(epochs[-1]['end_position']['block_number'], str(interval.MAX_BLOCK + 1))
