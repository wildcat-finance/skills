"""Evaluate bounded design models; production conformance remains pending."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
COMMAND = 'python3.14 .hexaemeron/design/build_design_evidence.py'
CANDIDATES = ('block-only', 'position-boundary')

def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def assign(candidate, position, upgrade=(20, 5, 9)):
    if candidate == 'block-only':
        return 'old' if position[0] < upgrade[0] else 'new'
    if position[0] == upgrade[0] and position[1] == upgrade[1] and position != upgrade:
        return 'refuse'
    return 'old' if position < upgrade else 'new'


def criterion(name, concern, kind='gate', stage='selection', owner='protasis'):
    return dict(id=name, concern=concern, kind=kind, stage=stage, owner=owner,
                unit='count' if kind == 'metric' else 'boolean',
                comparator='minimise' if kind == 'metric' else 'equals',
                threshold=None if kind == 'metric' else True,
                blocks='integration' if stage == 'conformance' else 'design-lock')


def main():
    criteria = [criterion('before-and-after-model', 'correctness'),
                criterion('ambiguous-emission-model', 'recovery'),
                criterion('preserved-inputs-retained', 'compatibility'),
                criterion('extra-rpc-methods', 'time', 'metric', owner='metron'),
                criterion('extra-release-components', 'space', 'metric', owner='metron')]
    future = [('production-attribution', 'correctness'), ('legacy-release-identity', 'compatibility'),
              ('offline-rederivation', 'correctness'), ('resume-and-refusal', 'recovery')]
    criteria += [criterion(name, concern, stage='conformance') for name, concern in future]
    manifest = {'schema': 'protasis-design-evidence/v1',
                'candidates': [{'id': name, 'summary': 'Executable model using '+name+' attribution.'} for name in CANDIDATES],
                'criteria': criteria, 'results': [],
                'selection': {'candidate': 'position-boundary', 'rule': 'unique-frontier', 'policy_ref': None}}
    observations = {}
    cases = [((19, 8, 10), 'old'), ((20, 4, 8), 'old'), ((20, 5, 9), 'new'), ((20, 6, 10), 'new'), ((21, 0, 0), 'new')]
    for candidate in CANDIDATES:
        spec = {'rpc_methods_added': [], 'components_added': [], 'preserved_inputs_rewritten': []}
        results = [(position, expected, assign(candidate, position)) for position, expected in cases]
        values = {'before-and-after-model': all(expected == actual for _, expected, actual in results),
                  'ambiguous-emission-model': all(assign(candidate, p) == 'refuse' for p in [(20, 5, 8), (20, 5, 10)]),
                  'preserved-inputs-retained': not spec['preserved_inputs_rewritten'],
                  'extra-rpc-methods': len(spec['rpc_methods_added']),
                  'extra-release-components': len(spec['components_added'])}
        observations[candidate] = {'spec': spec, 'cases': results, 'values': values}
        for item in criteria:
            name = item['id']
            if item['stage'] == 'conformance':
                manifest['results'].append(dict(candidate=candidate, criterion=name, state='pending',
                    resolver=f'python3.14 .hexaemeron/design/conformance.py {name}',
                    report=f'reports/conformance/{candidate}-{name}.json', blocks='integration'))
                continue
            value = values[name]
            report = dict(schema='protasis-design-report/v1', candidate=candidate, criterion=name,
                          value=value, unit=item['unit'], command=COMMAND, exit=0)
            relative = f'reports/selection/{candidate}-{name}.json'
            payload = encode(report)
            (ROOT / relative).write_bytes(payload)
            manifest['results'].append(dict(candidate=candidate, criterion=name,
                state='fail' if value is False else 'pass',
                report={'path': relative, 'sha256': hashlib.sha256(payload).hexdigest()}))
    (ROOT/'design/model-observations.json').write_bytes(encode(observations))
    (ROOT/'design-evidence.json').write_bytes(encode(manifest))
    print(json.dumps({name: data['values'] for name, data in observations.items()}, sort_keys=True))

if __name__ == '__main__':
    main()
