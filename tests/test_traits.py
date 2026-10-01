"""Player traits table + decoder checks. Plain script; real-save part runs only if the scratchpad pickle exists."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor.traits import TRAIT_TABLE, trait_ids, trait_names, read_trait_mask

assert sorted(TRAIT_TABLE) == list(range(64))
shown = [n for n, g in TRAIT_TABLE.values() if g in 'AB']
assert all(shown) and len(shown) == len(set(shown)), 'A/B names must exist and be unique'
assert all(g in 'ABCX?' for _, g in TRAIT_TABLE.values())
assert trait_ids(0) == [] and trait_names(0) == []
VDV = 0x1000080000000000
assert trait_ids(VDV) == [43, 60]
assert trait_names(VDV) == ['Tries Long Range Passes', 'Brings Ball Out Of Defence']
for i, (n, g) in TRAIT_TABLE.items():
    if g in 'C?':
        assert trait_names(1 << i) == [f'Trait #{i}'], i
assert read_trait_mask(b'\0' * 4, 3) == 0           # offset < 8 must not raise
assert read_trait_mask((VDV).to_bytes(8, 'little') + b'xyz', 8) == VDV

pk = '/tmp/claude-1000/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects-FM-Save-Editor/5f3303a7-1cd6-49f1-9379-e1d9dfec8ad8/scratchpad/result.pkl'
if os.path.exists(pk):
    import pickle
    R = pickle.load(open(pk, 'rb')); b = R['b']
    by_id = {p['id']: p for p in R['people']}
    assert trait_names(read_trait_mask(b, by_id[39811]['offset'])) == trait_names(VDV)
    for nm in ('Sandro Tonali', 'Alejandro Balde', 'Giorgio Scalvini', 'Pedro Porro', 'Micky van de Ven'):
        p = next((p for p in R['people'] if p['name'] == nm and 'ca' in p), None)
        if p:
            print(nm, trait_names(read_trait_mask(b, p['offset'])))
else:
    print('(real-save checks skipped)')
print('OK')
