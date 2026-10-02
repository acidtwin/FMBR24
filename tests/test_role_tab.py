"""Role Rating tab: fm_editor/rolepos.py logic + the tab on synthetic players (no save needed).
Plain script: FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_role_tab.py"""
import os
import random
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtCore import QPoint, Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication, QScrollArea  # noqa: E402

app = QApplication.instance() or QApplication([])
from fm_editor import rolepos, weights  # noqa: E402
from fm_editor.rolepos import POS_ROLES, best_by_position, position_roles, role_score, score_to_rating  # noqa: E402
from gui.player_window import POS_DISPLAY, PlayerWindow, TABS  # noqa: E402
from gui.pw_roles import RoleTab  # noqa: E402
from gui.roles import _ROLE_INDEX, FM_ROLES, role_rating  # noqa: E402
from gui.stars import _StarWidget  # noqa: E402


def old_role_rating(raw, role, w):
    """The pre-percent implementation of gui.roles.role_rating, kept here to prove the report did not change."""
    key = _ROLE_INDEX.get(role)
    if not key or len(raw) < 54:
        return None
    if w:
        tw = sum(w.get(i, 0) for i in key)
        if tw > 0:
            return max(1, min(20, round(sum(raw[i] * w.get(i, 0) for i in key) / tw / 5)))
    return max(1, min(20, round(sum(raw[i] for i in key) / len(key) / 5)))


# --- 1. data: every POS_ROLES name is a real FM_ROLES role; all 15 pitch codes have a list --------------------------------
names = {n for n, _, _ in FM_ROLES}
for pos, lst in POS_ROLES.items():
    assert lst and len(set(lst)) == len(lst), (pos, 'empty or duplicate')
    for n in lst:
        assert n in names, (pos, n)
assert set(POS_ROLES) == set(POS_DISPLAY) == set(rolepos.POS_CODES), 'POS_ROLES must cover the 15 pitch positions'
assert rolepos.split_role('Winger (S)') == ('Winger', 'Support')
assert rolepos.split_role('Central Defender (Cover)') == ('Central Defender', 'Cover')
assert rolepos.split_role('No-Nonsense Full Back') == ('No-Nonsense Full Back', 'Defend')

# --- 2. role_rating == clamp(round(role_score / 5)) for every role / preset / random attributes; unchanged vs the old formula
rng = random.Random(7)
presets = [None] + [weights.load_preset(p['path']) for p in weights.list_presets()]
assert len(presets) >= 5
for _ in range(40):
    raw = [rng.randint(1, 100) for _ in range(54)]
    for preset in presets:
        for name in names:
            w = weights.get_role_weights(preset, name)
            s = role_score(raw, name, w)
            assert 0 < s <= 100
            assert role_rating({'raw_attrs': raw}, name, w) == max(1, min(20, round(s / 5))) == score_to_rating(s)
            assert role_rating({'raw_attrs': raw}, name, w) == old_role_rating(raw, name, w), (name,)
assert role_score([50] * 54, 'Poacher (A)') == 50.0 and role_score([50] * 54, 'Poacher (A)', {2: 7}) == 50.0
assert role_score([1] * 10, 'Poacher (A)') is None and role_score(None, 'Poacher (A)') is None and role_score([1] * 54, 'nope') is None
assert role_rating({'raw_attrs': [1] * 10}, 'Poacher (A)') is None and role_rating({}, 'Poacher (A)') is None
# a weight dict that misses every key attribute falls back to equal weight (as before)
assert role_score([40] * 54, 'Poacher (A)', {0: 5}) == 40.0

# --- 3. sorting + best row ---------------------------------------------------------------------------------------------
raw = [rng.randint(20, 95) for _ in range(54)]
for pos in POS_DISPLAY:
    g = position_roles(pos, raw, presets[2])
    assert sum(len(r) for _, r in g) == len(POS_ROLES[pos])
    for fam, rows in g:
        sc = [r[2] for r in rows]
        assert sc == sorted(sc, reverse=True), (pos, fam)
    firsts = [r[0][2] for _, r in g]
    assert firsts == sorted(firsts, reverse=True), (pos, 'groups sorted by their best row')
    bp = best_by_position(raw, presets[2], [pos])[pos]
    assert bp == (g[0][1][0][1], g[0][1][0][2]) and bp[1] == max(r[2] for _, rows in g for r in rows)
assert best_by_position(None) == {} and position_roles('DC', None) == []
assert set(best_by_position(raw)) == set(POS_DISPLAY)


# --- 4. the tab -----------------------------------------------------------------------------------------------------
def person(gk=False, pos_hi='DC', attrs=None, ca=120, pa=170):
    from gui.player_window import POS_ORDER
    pos = [1] * 15
    pos[POS_ORDER.index('GK' if gk else pos_hi)] = 20
    pos[POS_ORDER.index('DM')] = 14 if not gk else 1       # an accomplished position that is not the best
    return {'id': 1, 'name': 'Test Player', 'nation': 0, 'ca': ca, 'pa': pa, 'birth_year': 2005, 'birth_day': 100,
            'positions': pos, 'raw_attrs': attrs or [30 + (i * 7) % 50 for i in range(54)], 'personality': [10] * 7,
            'trait_mask': 0, 'stats': {}}


def window(p):
    w = PlayerWindow(p, {'squads': {}, 'clubs': []}, 0, None)
    w.show()
    w._select_tab('role')
    app.processEvents()
    app.processEvents()
    return w


assert 'role' in [t[0] for t in TABS] and dict((t[0], t[2]) for t in TABS)['role'] == '_page_role'
w = window(person())
tab = w._role_tab
assert isinstance(tab, RoleTab)
assert w._stack.currentWidget() is w._stack.widget(w._tab_keys.index('role'))
page = w._stack.currentWidget()
assert page.findChildren(_StarWidget) == [], 'no star widget on the Role Rating tab (percentages are not converted to stars)'
assert tab.pitch.hasMouseTracking(), 'hover tooltips need mouse tracking'
assert tab.sel == 'DC' == tab.best_pos, 'default selection = the best position'
assert page.verticalScrollBar().maximum() == 0, 'Role Rating scrolls'
# outfielder: every dot except GK is live, GK dashed; dim = unfamiliar (< 10) live positions
assert tab.pitch._info['GK'] is None and all(tab.pitch._info[q] for q in POS_DISPLAY if q != 'GK')
assert tab.pitch._dim['ST'] and not tab.pitch._dim['DC'] and not tab.pitch._dim['DM'] and not tab.pitch._dim['GK']
assert 'goalkeeper roles are only rated for goalkeepers' in tab.pitch._tips['GK']
assert 'Best role:' in tab.pitch._tips['DC'] and '(best position)' in tab.pitch._tips['DC'] and '%' in tab.pitch._tips['DC']
assert 'Dimmed' in tab.pitch._tips['ST'] and 'Dimmed' not in tab.pitch._tips['DC']
# the list shows the selected position's roles, best first, and the rows' percent text is 2 decimals
groups = position_roles('DC', tab.attrs(), tab.preset)
assert tab.rolelist.row_count() == sum(1 if len(r) == 1 else 1 + len(r) for _, r in groups)
assert tab.pitch._info['DC'] == (groups[0][1][0][1], groups[0][1][0][2])
# click selects (live dot), a click on the disabled GK dot does nothing
x, y = tab.pitch._pt('MC')
QTest.mouseClick(tab.pitch, Qt.MouseButton.LeftButton, pos=QPoint(round(x), round(y)))
assert tab.sel == 'MC', tab.sel
assert tab.rolelist.row_count() == sum(1 if len(r) == 1 else 1 + len(r) for _, r in position_roles('MC', tab.attrs(), tab.preset))
x, y = tab.pitch._pt('GK')
QTest.mouseClick(tab.pitch, Qt.MouseButton.LeftButton, pos=QPoint(round(x), round(y)))
assert tab.sel == 'MC', 'GK is not selectable for an outfielder'
tab.select('GK')
assert tab.sel == 'MC'
# every live position fits without scrolling (the longest list is MC), also at Full Potential
for pot in (False, True):
    w._set_pot(pot)
    for q in tab.live:
        tab.select(q)
        app.processEvents()
        assert page.verticalScrollBar().maximum() == 0, ('page scrolls', q, pot)
        lst = tab.rolelist.parentWidget().parentWidget()
        assert isinstance(lst, QScrollArea) and lst.verticalScrollBar().maximum() == 0, ('list scrolls', q, pot)
# pot toggle changes the values (PA > CA) and keeps both Current | Full Potential controls in sync
w._set_pot(False)
tab.select('DC')
cur = dict(tab.pitch._info)
w._set_pot(True)
pot = dict(tab.pitch._info)
assert all(pot[q][1] > cur[q][1] for q in cur if cur[q]), 'Full Potential should raise every rating'
w._set_pot(False)
assert tab.pitch._info == cur
w.close()

# goalkeeper: only GK is live, the outfield dots are dashed; default = GK; GK roles only
g = window(person(gk=True))
gt = g._role_tab
assert gt.sel == 'GK' and gt.live == ['GK']
assert gt.pitch._info['GK'] and all(gt.pitch._info[q] is None for q in POS_DISPLAY if q != 'GK')
assert 'outfield roles are not rated for goalkeepers' in gt.pitch._tips['DC']
assert gt.rolelist.row_count() == (1 + 2) + (1 + 3), 'Goalkeeper D/S + Sweeper Keeper D/S/A'
QTest.mouseClick(gt.pitch, Qt.MouseButton.LeftButton, pos=QPoint(*map(round, gt.pitch._pt('DC'))))
assert gt.sel == 'GK'
assert g._stack.currentWidget().verticalScrollBar().maximum() == 0
g.close()

# default selection follows the best position rating (not always the same position)
w2 = window(person(pos_hi='AML'))
assert w2._role_tab.sel == 'AML'
w2.close()

# weight preset: Equal Weight vs another preset give different percentages; the footer names the preset
vals = {}
for name in ('Equal Weight', 'Direct Play'):
    weights.set_active_preset_name(name)
    wp = window(person())
    vals[name] = {q: v[1] for q, v in wp._role_tab.pitch._info.items() if v}
    assert name in wp._role_tab._foot.text()
    wp.close()
assert vals['Equal Weight'] != vals['Direct Play']
weights.set_active_preset_name('FMScout Community')

# missing attribute data: no crash, nothing rated, message shown
bare = PlayerWindow({'id': 1, 'name': 'Bare', 'nation': 0}, {'squads': {}, 'clubs': []}, 0, None)
bare.show()
bare._select_tab('role')
app.processEvents()
assert all(v is None for v in bare._role_tab.pitch._info.values()) and bare._role_tab.rolelist.row_count() == 0
bare.close()
print('test_role_tab OK')
