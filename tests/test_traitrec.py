"""Plain-script test for fm_editor/traitrec.py (no save needed)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor import traitrec as tr
from fm_editor.traits import TRAIT_TABLE

d = tr._data()
assert len(d['traits']) == 36 and d['default_threshold'] == 11
for t in d['traits']:
    assert t['attrs'] and len(t['attrs']) == len(set(t['attrs'])), t['name']
    assert all(a in tr.ATTR_IDX for a in t['attrs']), t['name']
    assert t['id'] is None or t['id'] in TRAIT_TABLE, t['name']
for t in d['traits']:  # Recommended list shows the verified TRAIT_TABLE name for the same bit
    assert t['name'] == TRAIT_TABLE[t['id']][0], (t['id'], t['name'], TRAIT_TABLE[t['id']])
names = {t['name'] for t in d['traits']}
assert all(a in names and b in names for a, b in d['conflicts'])
assert tr.ATTR_IDX['pace'] == 38 and len(set(tr.ATTR_IDX.values())) == len(tr.ATTR_IDX)

flat = [10] * 54
r = tr.recommend(flat, threshold=11)
assert len(r) <= 36 and not any(x.met for x in r)
r = tr.recommend(flat, threshold=10)
assert all(x.met and x.score == 10 and not x.missing for x in r)
# hand-checked: Shoots With Power = avg(finishing, technique, strength)
a = [10] * 54
a[2], a[23], a[36] = 16, 12, 14
x = {y.name: y for y in tr.recommend(a, 11)}['Shoots With Power']
assert abs(x.score - 14) < 1e-9 and x.met and x.missing == []
a[23] = 8
x = {y.name: y for y in tr.recommend(a, 11)}['Shoots With Power']
assert x.missing == [('technique', 8)] and abs(x.score - 38 / 3) < 1e-9
# ranking is descending; top= truncates
sc = [y.score for y in tr.recommend(a, 11)]
assert sc == sorted(sc, reverse=True) and len(tr.recommend(a, 11, top=5)) == 5
# owned trait marked; its conflicts removed (Stays Back owned -> no Gets Forward)
r = tr.recommend([15] * 54, 11, have_ids={33})
assert next(y for y in r if y.name == 'Stays Back At All Times').has
assert 'Gets Forward Whenever Possible' not in {y.name for y in r}
assert 'Runs With Ball Rarely' not in {y.name for y in tr.recommend([15] * 54, 11)} or \
    'Runs With Ball Often' not in {y.name for y in tr.recommend([15] * 54, 11)}
assert tr.attrs_from_raw([52] * 54) == [10] * 54
print('traitrec ok')
