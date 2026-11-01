"""Compare bounded fee-mapping models; no product implementation is exercised."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'plugins/tabularium/tests'))
sys.path.insert(0, str(ROOT / 'plugins/tabularium/scripts'))
from wildcat_v3_fixtures import constructed_inputs, log, record, MARKET
from tabularium_lib.wildcat_rows import map_records

CANDIDATES = ('versioned-native', 'in-place-native', 'repayment-reuse')
CRITERIA = ('native-separation', 'legacy-reconstruction', 'missing-context-gap', 'peer-lookups', 'auxiliary-records')

def model(candidate, venue, version, asset):
    # This small model compares representation and dispatch choices only.
    if version == '1.0.0' and candidate != 'in-place-native':
        return {'disposition': 'unsupported-canonical-meaning'}
    action = 'debt-repaid' if candidate == 'repayment-reuse' else 'fees-collected'
    return {'disposition': 'primary', 'action': venue + '.' + action,
            'event_family': 'repayment' if candidate == 'repayment-reuse' else 'fee-collection',
            'parties': [{'role': 'pool', 'address': MARKET}],
            'amounts': [{'kind': 'assets', 'base_units': '37', 'asset': asset}],
            'gaps': ['attribution:fees-collected:recipient'] +
                    (['attribution:fees-collected:asset'] if asset is None else []),
            'peer_lookups': 0, 'auxiliary_records': 0}

def probe(candidate, criterion):
    if criterion == 'native-separation':
        return all(model(candidate, venue, '1.1.0', None)['action'] == venue + '.fees-collected' and
                   model(candidate, venue, '1.1.0', None)['event_family'] == 'fee-collection'
                   for venue in ('wildcat-v1', 'wildcat-v2'))
    if criterion == 'legacy-reconstruction':
        for venue in ('wildcat-v1', 'wildcat-v2'):
            contexts, _ = constructed_inputs(venue)
            raw = log('FeesCollected(uint256)', (), (37,))
            baseline = map_records(venue, contexts, [record(raw)])
            assert len(baseline['events']) == 0
            assert baseline['dispositions'][0]['disposition'] == 'unsupported-canonical-meaning'
            if model(candidate, venue, '1.0.0', None) != {'disposition': 'unsupported-canonical-meaning'}:
                return False
        return True
    if criterion == 'missing-context-gap':
        row = model(candidate, 'wildcat-v2', '1.1.0', None)
        return row['amounts'][0]['asset'] is None and 'attribution:fees-collected:asset' in row['gaps'] and row['parties'] == [{'role': 'pool', 'address': MARKET}]
    if criterion == 'peer-lookups':
        return model(candidate, 'wildcat-v2', '1.1.0', None)['peer_lookups']
    if criterion == 'auxiliary-records':
        return model(candidate, 'wildcat-v2', '1.1.0', None)['auxiliary_records']
    raise ValueError(criterion)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=CANDIDATES, required=True)
    parser.add_argument('--criterion', choices=CRITERIA, required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    value = probe(args.candidate, args.criterion)
    unit = 'count' if args.criterion in ('peer-lookups', 'auxiliary-records') else 'boolean'
    payload = {'schema': 'protasis-design-report/v1', 'candidate': args.candidate,
               'criterion': args.criterion, 'value': value, 'unit': unit,
               'command': shlex.join(['python3', '.hexaemeron/design/fee_probe.py', *sys.argv[1:]]), 'exit': 0}
    path = Path(args.report)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write('\n')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
