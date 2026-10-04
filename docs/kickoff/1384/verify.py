#!/usr/bin/env python3
"""Check the frozen inventory and finite requests without contacting a provider."""

import hashlib
import json
from pathlib import Path
import re

from capture_requests import encoded_requests, requests


ROOT = Path(__file__).resolve().parent


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def check(root=ROOT):
    manifest = json.loads((root / 'evidence/outputs.json').read_text())
    for item in manifest['files']:
        relative = Path(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe output path')
        path = root / relative
        require(not path.is_symlink(), 'output is a symlink')
        content = path.read_bytes()
        require(hashlib.sha256(content).hexdigest() == item['sha256'], f'output digest differs: {relative}')
        require(len(content) == item['bytes'], f'output size differs: {relative}')
    scope = json.loads((root / 'scope.json').read_text())
    values = json.loads((root / 'values.json').read_text())
    rows = values['rows']
    require(len(rows) == 61, 'field denominator differs')
    ids = [row['id'] for row in rows]
    require(len(ids) == len(set(ids)), 'duplicate field')
    credit = {'asset', 'totalAssets', 'totalDebt', 'totalLenderClaims', 'reservedAssets',
              'borrowableAssets', 'accruedFees', 'observedAt'}
    require({i.removeprefix('credit.') for i in ids if i.startswith('credit.')} == credit,
            'ICreditObservables coverage differs')
    queue = {'claimCount', 'claimAt.owed', 'claimAt.paid', 'payableThrough', 'queueObserved'}
    require({i.removeprefix('withdrawal.') for i in ids if i.startswith('withdrawal.')} == queue,
            'withdrawal coverage differs')
    fields = {'isClosed', 'maxTotalSupply', 'accruedProtocolFees', 'normalizedUnclaimedWithdrawals',
              'scaledTotalSupply', 'scaledPendingWithdrawals', 'pendingWithdrawalExpiry',
              'isDelinquent', 'timeDelinquent', 'protocolFeeBips', 'annualInterestBips',
              'reserveRatioBips', 'scaleFactor', 'lastInterestAccruedTimestamp'}
    require({i.removeprefix('state.') for i in ids if i.startswith('state.')} == fields,
            'MarketState coverage differs')
    for row in rows:
        for key in ('meaning', 'units', 'rounding', 'generations', 'chain_id', 'address_scope',
                    'block_scope', 'source', 'initial_state', 'producer', 'consumer', 'status', 'acquisition_issue'):
            require(bool(row.get(key)), f'missing {key}: {row["id"]}')
        require(row['chain_id'] == 1, 'wrong chain')
        require(row['status'] in ('requires-capture', 'requires-header') or row['status'].startswith('unsupported'),
                'mapping is not captured state')
        require('value' not in row, 'inventory must not manufacture values')
    population = json.loads((root / 'population.json').read_text())
    spec = json.loads((root / 'request-spec.json').read_text())
    summary = {}
    for gen in ('v1', 'v2'):
        anchor = scope['anchors'][gen]
        require(anchor == spec['anchors'][gen], 'anchor differs')
        subjects = scope['subjects'][gen]
        addresses = {entry['address'] for entry in subjects}
        markets = {entry['address'] for entry in subjects if entry['role'] == 'market'}
        require(len(addresses) == len(subjects), 'duplicate subject')
        require(len(markets) == {'v1': 7, 'v2': 80}[gen], 'market denominator differs')
        require(set(population[gen]) == markets, 'population market denominator differs')
        for members in population[gen].values():
            for expiry in members['batch_expiries']:
                require(type(expiry) is int and 0 < expiry < 2**32, 'invalid batch expiry')
            for account in members['accounts']:
                require(re.fullmatch('0x[0-9a-f]{40}', account) is not None and int(account, 16) != 0,
                        'invalid account')
            for pair in members['account_batches']:
                require(pair['expiry'] in members['batch_expiries'] and pair['account'] in members['accounts'],
                        'account-batch key outside population')
        generated = requests(gen, root)
        require(len(generated) == scope['counts'][gen]['requests'], 'request count differs')
        raw = encoded_requests(gen, root)
        expected = spec['expanded_requests'][gen]
        require(hashlib.sha256(raw).hexdigest() == expected['sha256'], 'expanded request digest differs')
        require(len(raw) == expected['bytes'], 'expanded request size differs')
        identities = set()
        for request in generated:
            identity = json.dumps([request['method'], request['params']], sort_keys=True)
            require(identity not in identities, 'duplicate exact request')
            identities.add(identity)
            method, params = request['method'], request['params']
            require(request['evidence'] == 'recorded-rpc', 'capture requires recorded-rpc request entries')
            if method == 'eth_call':
                require(request['evidence'] == 'recorded-rpc', 'eth_call proof elevation')
                require(request['required'] is False, 'getter errors must remain recordable')
                require(params[0]['to'] in markets, 'call outside market set')
                require(params[-1] == {'blockHash': anchor['hash'], 'requireCanonical': True}, 'call at wrong block')
            elif method in ('eth_getCode', 'eth_getProof'):
                require(request['required'] is True, 'proof and code requests must be required')
                require(params[0] in addresses, 'invalid proof subject')
                require(params[-1] == {'blockHash': anchor['hash'], 'requireCanonical': True}, 'proof at wrong block')
                if method == 'eth_getProof':
                    require(params[1] == [], 'unreviewed storage slot')
            else:
                require(request['required'] is True, 'header request must be required')
                require(method == 'eth_getBlockByHash' and params == [anchor['hash'], False], 'unbound header request')
        summary[gen] = {'requests': len(generated), 'sha256': hashlib.sha256(raw).hexdigest()}
    return {'result': 'pass', 'value_rows': len(rows), 'expanded_requests': summary,
            'rpc_requests_executed': 0, 'state_values_proved': 0}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
