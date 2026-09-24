#!/usr/bin/env python3
"""Recheck the preserved archives and derive the observed participant keys."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(generation, staging, archive, repository):
    relative = f'plugins/alexandria/examples/wildcat-{generation}-interval-v0/staging-manifest.json'
    expected_input = next(item for item in json.loads((ROOT / 'evidence/inputs.json').read_text())
                          if item['path'] == relative)
    manifest_path = repository / relative
    if sha256(manifest_path) != expected_input['sha256']:
        raise ValueError('staging manifest differs from the pinned input')
    manifest = json.loads(manifest_path.read_text())
    if sha256(archive) != manifest['archive']['sha256'] or archive.stat().st_size != manifest['archive']['bytes']:
        raise ValueError('archive differs from the pinned manifest')
    if staging.is_symlink():
        raise ValueError('staging root is a symlink')
    files = {}
    for path in staging.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('staging contains a symlink or special file')
        if path.is_file():
            files[path.relative_to(staging).as_posix()] = path
    expected_files = {item['path']: item for item in manifest['files']}
    if set(files) != set(expected_files):
        raise ValueError('staging file set differs')
    for relative, path in files.items():
        entry = expected_files[relative]
        if path.stat().st_size != entry['bytes'] or sha256(path) != entry['sha256']:
            raise ValueError('staging file bytes differ: ' + relative)
    scope = json.loads((ROOT / 'scope.json').read_text())
    anchor = scope['anchors'][generation]
    topics = json.loads((ROOT / 'evidence/topics.json').read_text())
    batch_topics = {value for name, value in topics.items() if name.startswith('Withdrawal')}
    account_topics = {topics[name] for name in ('WithdrawalQueued(uint256,address,uint256,uint256)',
                                               'WithdrawalExecuted(uint256,address,uint256)')}
    markets = {entry['address'] for entry in scope['subjects'][generation] if entry['role'] == 'market'}
    population = {market: {'batch_expiries': set(), 'accounts': set(), 'account_batches': set()}
                  for market in markets}
    seen = set()
    repayment_count = 0
    for journal in sorted((staging / 'journals').glob('logs.*.jsonl')):
        for line in journal.open():
            row = json.loads(line)
            for event_record in json.loads(row['response']).get('result', []):
                market = event_record['address'].lower()
                if market not in markets:
                    continue
                locator = (event_record['blockHash'], event_record['transactionHash'], event_record['logIndex'])
                if locator in seen or event_record.get('removed') is not False:
                    raise ValueError('duplicate or removed market log')
                if not anchor['start'] <= int(event_record['blockNumber'], 16) <= anchor['number']:
                    raise ValueError('market log outside interval')
                seen.add(locator)
                values = population[market]
                ts = event_record['topics']
                if ts[0] in batch_topics:
                    expiry = int(ts[1], 16)
                    if not 0 < expiry < 2**32:
                        raise ValueError('batch expiry outside uint32')
                    values['batch_expiries'].add(expiry)
                    if ts[0] in account_topics:
                        account = '0x' + ts[2][-40:]
                        values['accounts'].add(account)
                        values['account_batches'].add((expiry, account))
                if ts[0] == topics['Transfer(address,address,uint256)']:
                    values['accounts'].update('0x' + value[-40:] for value in ts[1:3] if int(value, 16))
                repayment_count += ts[0] == topics['DebtRepaid(address,uint256)']
    actual = {market: {'batch_expiries': sorted(value['batch_expiries']), 'accounts': sorted(value['accounts']),
                       'account_batches': [{'expiry': expiry, 'account': account}
                                           for expiry, account in sorted(value['account_batches'])]}
              for market, value in sorted(population.items())}
    if actual != json.loads((ROOT / 'population.json').read_text())[generation]:
        raise ValueError('derived participant population differs')
    for specimen in json.loads((ROOT / 'evidence/repayment-specimens.json').read_text()):
        if specimen['generation'] != generation:
            continue
        if specimen['journal'] not in files:
            raise ValueError('specimen journal outside checked file set')
        line = files[specimen['journal']].read_text().splitlines()[specimen['line'] - 1]
        response = json.loads(line)['response']
        if hashlib.sha256(response.encode()).hexdigest() != specimen['response_sha256']:
            raise ValueError('specimen response differs')
        if json.loads(response)['result'][specimen['response_index']] != specimen['log']:
            raise ValueError('specimen log differs')
    return {'result': 'pass', 'generation': generation, 'files': len(files),
            'market_logs': len(seen), 'repayment_logs': repayment_count,
            'population_equal': True, 'specimen_equal': True, 'release_rebuilt': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generation', choices=('v1', 'v2'))
    parser.add_argument('--staging', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.generation, args.staging, args.archive, args.repository), indent=2))
