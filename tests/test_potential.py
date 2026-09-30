"""Potential projection invariants (plain script). Synthetic players + real ones from a scratchpad pickle if present."""
import os, sys, pickle, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor import potential as pt
from fm_editor.agecalc import age_on
from datetime import date

PICKLE = os.environ.get('FMBR24_PLAYERS_PKL',
    '/tmp/claude-1000/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects-FM-Save-Editor/'
    '5f3303a7-1cd6-49f1-9379-e1d9dfec8ad8/scratchpad/players.pkl')
W = pt._data()[1]


def check(raw, ca, pa, age, positions):
    pr = pt.project_attrs(raw, ca, pa, age, positions)
    a = [v / 5 for v in raw]
    w = [x if x >= pt.MIN_W else 0.0 for x in W[pr.group]]
    for i in pt.NEVER + pt.FEET:
        w[i] = 0.0
    assert len(pr.proj) == 54
    for i in range(54):
        assert pr.proj[i] >= a[i] - 1e-9 and pr.proj[i] <= 20 + 1e-9, (i, a[i], pr.proj[i])
    for i in pt.NEVER + pt.FEET:                      # zero-cost / hidden / feet never change
        assert pr.proj[i] == a[i], i
    for i in range(54):                               # tiny / zero-weight attributes never change
        if w[i] == 0:
            assert pr.proj[i] == a[i], i
    gained = sum(w[i] * (pr.proj[i] - a[i]) for i in range(54))
    if pa <= ca:
        assert all(pr.proj[i] == a[i] for i in range(54)) and pr.target <= 0
    elif not pr.saturated:
        assert abs(gained - pr.target) < 1e-6, (gained, pr.target)
    else:
        assert gained < pr.target + 1e-9 and pr.reaches(ca) is not None
    return pr


rnd = random.Random(7)
def synth(kind):
    base = 5 if kind == 'gk' else 8
    raw = [rnd.randint(2, 18) * 5 for _ in range(54)]
    pos = [1] * 15
    pos[0 if kind == 'gk' else rnd.choice([2, 3, 5, 7, 10, 12])] = 20
    return raw, pos

for kind in ('gk', 'out'):
    for _ in range(200):
        raw, pos = synth(kind)
        check(raw, 100, rnd.randint(90, 190), rnd.randint(16, 29), pos)

# PA <= CA: no change
raw, pos = synth('out'); pr = check(raw, 150, 150, 20, pos)
assert pr.proj == [v / 5 for v in raw]
# physical scaling above 24: same player, same target -> physical attrs gain less at 25 than at 24 (relative share)
raw = [50] * 54; pos = [1] * 15; pos[3] = 20
y = pt.project_attrs(raw, 100, 120, 22, pos); o = pt.project_attrs(raw, 100, 120, 27, pos)
for i in pt.PHYS:
    if W['DC'][i] >= pt.MIN_W:
        assert o.proj[i] - 10 < y.proj[i] - 10 - 1e-9, i
        assert o.proj[i] > 10                         # scaled, NOT frozen
# saturation: a player with every weighted attribute at 19 cannot grow 60 CA
raw = [95] * 54; pr = pt.project_attrs(raw, 100, 160, 20, pos)
assert pr.saturated and pr.reaches(100) < 160
# availability rules
assert pt.availability(150, 150, 20) == (False, 'Already at potential.')
assert pt.availability(120, 160, 30)[0] is False and 'Decline' in pt.availability(120, 160, 30)[1]
assert pt.availability(120, 160, 27) == (True, 'PA is rarely reached after 26.')
assert pt.availability(120, 160, 20) == (True, '')

n = 0
if os.path.exists(PICKLE):
    P = pickle.load(open(PICKLE, 'rb'))[0]
    ref = date(2028, 1, 2)
    for p in P[::37]:
        check(p['raw_attrs'], p['ca'], p['pa'], age_on(p, ref), p['positions'])
        n += 1
print('OK', n, 'real players')
