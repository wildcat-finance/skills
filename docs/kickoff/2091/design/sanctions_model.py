"""Evaluate finite join proposals; this does not test production mapping."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

CANDIDATES = ('unique-key', 'first-match', 'adjacent-only')
FIELDS = ('generation', 'market', 'transaction', 'account', 'expiry', 'scaled', 'amount')

OBSERVATIONS = {'work': 0, 'slots': 0}

def pairs(candidate, primaries, companions):
    OBSERVATIONS.update(work=0, slots=0)
    result = []
    if candidate == 'unique-key':
        left, right = defaultdict(list), defaultdict(list)
        for item in primaries:
            left[item['key']].append(item)
            OBSERVATIONS['work'] += 1
            OBSERVATIONS['slots'] += 1
        for item in companions:
            right[item['key']].append(item)
            OBSERVATIONS['work'] += 1
            OBSERVATIONS['slots'] += 1
        for key in left.keys() & right.keys():
            OBSERVATIONS['work'] += 1
            if len(left[key]) == len(right[key]) == 1:
                result.append((left[key][0]['id'], right[key][0]['id']))
    elif candidate == 'first-match':
        for primary in primaries:
            for companion in companions:
                OBSERVATIONS['work'] += 1
                if primary['key'] == companion['key']:
                    result.append((primary['id'], companion['id']))
                    break
    else:
        for primary in primaries:
            matches = []
            for c in companions:
                OBSERVATIONS['work'] += 1
                if c['index'] == primary['index'] + 1 and c['key'] == primary['key']:
                    matches.append(c)
            if len(matches) == 1:
                result.append((primary['id'], matches[0]['id']))
    return sorted(result)

def item(identity, index, key):
    return {'id': identity, 'index': index, 'key': key}

def checks(candidate):
    key = ('v2', 'market', 'tx', 'account', 'expiry', 'scaled', 'amount')
    p, c = item('p', 10, key), item('c', 14, key)
    exact = pairs(candidate, [p], [c]) == [('p', 'c')]
    for i in range(len(key)):
        changed = list(key)
        changed[i] += '-changed'
        exact &= pairs(candidate, [p], [item('x', 11, tuple(changed))]) == []
    recovery = pairs(candidate, [p], []) == []
    recovery &= pairs(candidate, [p], [c, item('c2', 11, key)]) == []
    recovery &= pairs(candidate, [p, item('p2', 13, key)], [c]) == []
    recovery &= pairs(candidate, [p], [item('c0', 11, key), item('c1', 14, key)]) == []
    left = [item('p' + str(i), i * 4, (i,)) for i in range(32)]
    right = [item('c' + str(i), i * 4 + 1, (i,)) for i in range(32)]
    forward = pairs(candidate, left, right)
    work, slots = OBSERVATIONS['work'], OBSERVATIONS['slots']
    reverse = pairs(candidate, list(reversed(left)), list(reversed(right)))
    return {'exact-pairing': bool(exact), 'ambiguous-gap': bool(recovery),
            'stable-primary-count': len(left) == 32 and forward == reverse,
            'key-work': work, 'index-slots': slots}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, choices=CANDIDATES)
    parser.add_argument('--criterion', required=True, choices=('exact-pairing', 'ambiguous-gap', 'stable-primary-count', 'key-work', 'index-slots'))
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    value = checks(args.candidate)[args.criterion]
    report = {'schema':'protasis-design-report/v1','candidate':args.candidate,'criterion':args.criterion,
              'value':value,'unit':'count' if args.criterion in ('key-work','index-slots') else 'boolean',
              'command':f'python3 .hexaemeron/design/sanctions_model.py --candidate {args.candidate} --criterion {args.criterion} --report {args.report}', 'exit':0}
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'candidate':args.candidate,'criterion':args.criterion,'value':value}))

if __name__ == '__main__':
    main()
