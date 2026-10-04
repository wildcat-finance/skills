#!/usr/bin/env python3
"""Expand this record's finite request inventory; performs no network access."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def requests(generation, root=ROOT):
    scope = json.loads((root / 'scope.json').read_text())
    population = json.loads((root / 'population.json').read_text())[generation]
    specification = json.loads((root / 'request-spec.json').read_text())
    selectors = json.loads((root / 'selectors.json').read_text())
    anchor = scope['anchors'][generation]
    block = {'blockHash': anchor['hash'], 'requireCanonical': True}
    result = []

    def add(method, params):
        result.append({'name': f'r{len(result):05d}', 'method': method,
                       'params': params, 'required': method != 'eth_call', 'evidence': 'recorded-rpc'})

    def call(address, signature, *arguments):
        words = [f'{int(arg, 16) if isinstance(arg, str) else arg:064x}' for arg in arguments]
        data = selectors[signature] + ''.join(words)
        add('eth_call', [{'to': address, 'data': data}, block])

    for entry in scope['subjects'][generation]:
        address = entry['address']
        add('eth_getCode', [address, block])
        add('eth_getProof', [address, [], block])
        if entry['role'] != 'market':
            continue
        for signature in specification['no_argument_methods'][generation]:
            call(address, signature)
        members = population[address]
        for expiry in members['batch_expiries']:
            call(address, 'getWithdrawalBatch(uint32)', expiry)
        for account in members['accounts']:
            call(address, 'scaledBalanceOf(address)', account)
            call(address, 'balanceOf(address)', account)
        for pair in members['account_batches']:
            call(address, 'getAccountWithdrawalStatus(address,uint32)', pair['account'], pair['expiry'])
            call(address, 'getAvailableWithdrawalAmount(address,uint32)', pair['account'], pair['expiry'])
    add('eth_getBlockByHash', [anchor['hash'], False])
    return result


def encoded_requests(generation, root=ROOT):
    return ''.join(json.dumps(row, separators=(',', ':')) + '\n'
                   for row in requests(generation, root)).encode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generation', choices=('v1', 'v2'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with args.out.open('xb') as output:
        output.write(encoded_requests(args.generation))
