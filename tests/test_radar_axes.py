"""Profile radar: six own scouting axes from ONE table (gui/pw_widgets.py RADAR_OUT / RADAR_GK). Plain script."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
from gui.player_window import (GKA, HIDD, LOWER_BETTER, MENT, PHYS, TECH, PlayerWindow,  # noqa: E402
                               _GROUPS)
from gui.pw_widgets import RADAR_GK, RADAR_OUT, radar_axes  # noqa: E402

IDX = {n: i for g in _GROUPS.values() for n, i in g}
LOWER = {n for n, i in IDX.items() if i in LOWER_BETTER}


def names(table):
    return [a for _n, attrs, _i in table for a in attrs]


# -- partition ---------------------------------------------------------------------------------------------------
out = names(RADAR_OUT)
assert len(out) == len(set(out)) == 41, len(out)
assert set(out) == {n for n, _ in TECH + MENT + PHYS + HIDD}, 'outfield: every attribute exactly once'
gk = names(RADAR_GK)
assert len(gk) == len(set(gk)) == 36, len(gk)      # Athleticism 8 + Mentality 11 + 4 + 4 + 4 + 5
assert {n for n, _ in GKA} <= set(gk), 'all 11 GK attributes are used'
assert not {'Finishing', 'Versatility', 'Vision', 'Crossing'} & set(gk), 'attacking/creative/Versatility unused for a keeper'
assert [a for a, _x, _y in RADAR_GK] == ['Shot-stopping', 'Command', 'Athleticism', 'Distribution', 'Reliability', 'Mentality']
assert [a for a, _x, _y in RADAR_OUT] == ['Attacking', 'Creativity', 'Athleticism', 'Defending', 'Reliability', 'Mentality']
for tbl in (RADAR_OUT, RADAR_GK):
    assert all(a in IDX for a in names(tbl)), 'unknown attribute name'
    assert {a for _n, _t, inv in tbl for a in inv} == {a for a in names(tbl) if a in LOWER}, 'inverted set == LOWER_BETTER'
    assert all(set(inv) <= set(attrs) for _n, attrs, inv in tbl)

# -- hand-computed means ------------------------------------------------------------------------------------------
v = {a: 10 for a in IDX}
v.update({'Finishing': 20, 'Long Shots': 14, 'Dribbling': 17, 'Penalties': 5, 'Free Kick': 8, 'Off the Ball': 12, 'Flair': 10})
v.update({'Injury Prone': 4, 'Dirtiness': 1, 'Consistency': 15, 'Important Matches': 13, 'Versatility': 7, 'Eccentricity': 19})
ax = {n: m for n, m, _t in radar_axes(v, False)}
assert abs(ax['Attacking'] - 86 / 7) < 1e-9
assert abs(ax['Reliability'] - (15 + 13 + 17 + 20 + 7) / 5) < 1e-9          # (21-4) and (21-1)
assert ax['Athleticism'] == 10 and len(ax) == 6
g = {n: m for n, m, _t in radar_axes(v, True)}
assert list(g) == [a for a, _x, _y in RADAR_GK] and 'Attacking' not in g
assert abs(g['Reliability'] - (15 + 13 + 17 + 20 + 2) / 5) < 1e-9           # Eccentricity 19 -> 2
assert abs(radar_axes(v, False)[4][1] - ax['Reliability']) < 1e-9
assert 'Injury Prone (21-v)' in radar_axes(v, False)[4][2] and radar_axes(v, False)[0][2].startswith('Attacking = mean of 7:')
assert [x[0] for x in radar_axes({'Pace': 9}, False)] == ['Athleticism'], 'axes without data are dropped'


# -- window: follows Current | Full Potential -------------------------------------------------------------------------
def person(is_gk):
    pos = [1] * 15
    pos[0 if is_gk else 3] = 20
    return {'id': 1, 'name': 'T', 'nation': 0, 'ca': 100, 'pa': 160, 'birth_year': 2006, 'birth_day': 100, 'positions': pos,
            'raw_attrs': [8 + (i * 7) % 9 for i in range(60)], 'personality': [10] * 7, 'trait_mask': 0}


for is_gk in (False, True):
    w = PlayerWindow(person(is_gk), {'squads': {}, 'clubs': []}, 0, None, can_patch=True, data={})
    w.show()
    cur = w._radar_axes()
    assert [a[0] for a in cur] == [a for a, _x, _y in (RADAR_GK if is_gk else RADAR_OUT)]
    assert len(w._radar._rects) == 6
    w._set_pot(True)
    pot = w._radar_axes()
    assert [a[1] for a in pot] != [a[1] for a in cur], 'Full Potential changes the axis means'
    assert all(1 <= a[1] <= 20 for a in pot)
    w.close()
print('radar axes OK')

# -- per-axis tooltip hit-test (label rect / dot) --------------------------------------------------------------------
from PyQt6.QtCore import QEvent, QPoint  # noqa: E402
from PyQt6.QtGui import QHelpEvent  # noqa: E402
from PyQt6.QtWidgets import QToolTip  # noqa: E402
w = PlayerWindow(person(False), {'squads': {}, 'clubs': []}, 0, None, can_patch=True, data={})
w.show()
rd = w._radar
assert rd.hasMouseTracking(), 'tooltips on hover need mouse tracking'
r0 = rd._rects[0][4]
QApplication.sendEvent(rd, QHelpEvent(QEvent.Type.ToolTip, QPoint(int(r0.center().x()), int(r0.center().y())), QPoint(5, 5)))
assert QToolTip.text().startswith('Attacking = mean of 7:'), QToolTip.text()
from PyQt6.QtWidgets import QWidget  # noqa: E402
assert 'own' in w.findChildren(QWidget, 'pwHead')[-1].toolTip() or any('own' in h.toolTip() for h in w.findChildren(QWidget, 'pwHead'))
print('radar tooltips OK')

# -- Compare page 'Detailed' axes (fm_editor/radar_axes.py) -------------------------------------------------------
from fm_editor.radar_axes import DETAILED_GK, DETAILED_OUT, OVERVIEW_GK, OVERVIEW_OUT, axis_table, axis_values  # noqa: E402

assert OVERVIEW_OUT is RADAR_OUT and OVERVIEW_GK is RADAR_GK
d_out = names(DETAILED_OUT)
assert len(DETAILED_OUT) == 12 and len(d_out) == len(set(d_out)) == 41
assert set(d_out) == {n for n, _ in TECH + MENT + PHYS + HIDD}, 'detailed outfield: every attribute exactly once'
d_gk = names(DETAILED_GK)
assert len(DETAILED_GK) == 11 and len(d_gk) == len(set(d_gk)), 'detailed GK: 11 axes, no attribute twice'
assert {n for n, _ in GKA} <= set(d_gk) and 'Finishing' not in d_gk
for tbl in (DETAILED_OUT, DETAILED_GK):
    assert all(a in IDX for a in names(tbl)), 'unknown attribute name'
    assert {a for _n, _t, inv in tbl for a in inv} == {a for a in names(tbl) if a in LOWER}, 'inverted set == LOWER_BETTER'
assert axis_table(False, 'detailed') is DETAILED_OUT and axis_table(True, 'overview') is OVERVIEW_GK
dv = {n: m for n, m, _t in axis_values(v, False, 'detailed')}
assert abs(dv['Shooting'] - (20 + 14 + 5) / 3) < 1e-9 and abs(dv['Reliability'] - ax['Reliability']) < 1e-9
assert len(dv) == 12 and len(axis_values(v, True, 'detailed')) == 11
print('detailed radar axes OK')
