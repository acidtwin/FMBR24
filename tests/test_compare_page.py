"""Compare Players page (gui/compare_page.py, gui/player_picker.py): attributes-won rules, page states, Overview / Detailed radar,
Stars / Numbers, picker lists + search + keeper rule, player-window action strip + popup, nav button + busy lock.
Synthetic people, no save needed: FMBR24_CONFIG_DIR=/tmp/fmx QT_QPA_PLATFORM=offscreen python3 tests/test_compare_page.py"""
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton  # noqa: E402

from fm_editor import settings as S  # noqa: E402
from fm_editor.recents import RecentPlayers  # noqa: E402
from gui.theme import QSS  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
import gui.main_window as M  # noqa: E402
from gui.compare_page import ComparePage, CompareSide, DiffCell, EdgeRow, attrs_won, good, key_facts  # noqa: E402
from gui.player_picker import PickerContext, PlayerCombo, PlayerPicker, PlayerRowDelegate  # noqa: E402
from gui.player_window import GKA, HIDD, MENT, PHYS, TECH, PlayerWindow  # noqa: E402
from gui.pw_widgets import CompareRadar  # noqa: E402

IDX = {n: i for g in (TECH, MENT, PHYS, GKA, HIDD) for n, i in g}
ALL = ('tech', TECH), ('ment', MENT), ('phys', PHYS), ('hid', HIDD), ('gk', GKA)


def pump(n=4):
    for _ in range(n):
        app.processEvents()


def person(i, name, v=10, gk=False, ca=120, over=None, value=None, end='2030-06'):
    """raw_attrs = value * 5 (the game's 1-100 scale / 5 -> 1-20); `over` {attribute name: value}."""
    raw = [5] * 60
    for _n, ix in TECH + MENT + PHYS + HIDD:
        raw[ix] = 5 * v
    for _n, ix in GKA:
        raw[ix] = 5 * (v if gk else 2)
    raw[24] = raw[25] = 5 * 12
    for n, val in (over or {}).items():
        raw[IDX[n]] = 5 * val
    pos = [1] * 15
    pos[0 if gk else 7] = 20
    return {'id': i, 'name': name, 'uid': 1000 + i, 'nation': 0, 'ca': ca, 'pa': ca + 20, 'birth_year': 2000, 'birth_day': 100,
            'positions': pos, 'raw_attrs': raw, 'personality': [10] * 7, 'trait_mask': 0, 'value_est': value, 'contract_end': end,
            'wage_week': 50000, 'height_cm': 180, 'weight_kg': 75}


# -- pure rules ---------------------------------------------------------------------------------------------------
A = person(1, 'Ann Able', 10, over={'Finishing': 15, 'Dirtiness': 3, 'Injury Prone': 10})
B = person(2, 'Bob Baker', 10, over={'Finishing': 12, 'Dirtiness': 12, 'Passing': 14})
sa, sb = CompareSide(A), CompareSide(B)
assert good(3, True) == 18 and good(3, False) == 3
wa, wb, lv = attrs_won(sa, sb)
# A better: Finishing (15 > 12), Dirtiness (3 inverted -> 18 > 9); B better: Passing 14 > 10; Footedness (12 = 12) is not counted anyway
assert (wa, wb) == (2, 1), (wa, wb, lv)
assert wa + wb + lv == 14 + 14 + 8 + 5, 'outfield: Technical + Mental + Physical + Hidden, no Footedness, no GK attributes'
assert attrs_won(sa, sa) == (0, 0, 41)
g1, g2 = person(3, 'Gus Keeper', 10, gk=True, over={'Reflexes': 18, 'Eccentricity': 4}), person(4, 'Hal Keeper', 10, gk=True)
ga, gb = CompareSide(g1), CompareSide(g2)
assert ga.gk and not sa.gk
gw = attrs_won(ga, gb)
assert gw[:2] == (2, 0) and sum(gw) == 11 + 14 + 8 + 5, 'keeper: Goalkeeping + Mental + Physical + Hidden, outfield Technical not counted (Eccentricity 4 inverted wins)'
# Full Potential: values come from potential.project_attrs; for A (ca 120 / pa 140, age 28) they must not be lower than Current
cur, pot = sa.values(False), sa.values(True)
assert set(pot) == set(cur) and all(1 <= v <= 20 for v in pot.values()), 'Full Potential values come from potential.project_attrs'
kf = {t: (x, y, d) for t, x, y, d, _tip in key_facts(sa, sb)}
assert kf['Age'][2] == 'same age' and kf['Contract'][0] == 'Jun 2030' and kf['Contract'][2] == 'same length'
assert kf['Transfer value'][:2] == ('-', '-'), 'no value stored'
A['value_est'], B['value_est'] = 52_000_000, 300_000_000
kf = {t: (x, y, d) for t, x, y, d, _tip in key_facts(CompareSide(A), CompareSide(B))}
assert kf['Transfer value'] == ('£52M', 'Not for sale', ''), kf['Transfer value']
B['value_est'] = 38_000_000
kf = {t: (x, y, d) for t, x, y, d, _tip in key_facts(CompareSide(A), CompareSide(B))}
assert kf['Transfer value'] == ('£52M', '£38M', '£14M apart')
assert kf['Wage p/w'][0] == '£50K' and kf['cm / kg'][0] == '180 · 75'

# -- picker context / search / keeper rule -------------------------------------------------------------------------
people = [A, B, g1, g2, person(5, 'Anna Able', 11), person(6, 'Carl Anders', 12), person(7, 'Dan Dane', 9)]
sd = {'people': people, 'clubs': [{'id': 7, 'name': 'Club7', 'uid': 7}], 'squads': {1: 7, 2: 7, 5: 7, 3: 7}, 'human_clubs': {7}}
index = [(p['name'].lower(), p['name'], 2, p) for p in people]
rec = RecentPlayers('/x.fm', persist=False)
for pid in (6, 5, 3, 7, 4):
    rec.push(pid)
short = [people[5]]
ctx = PickerContext(sd, lambda: index, rec, lambda: short)
assert [p['id'] for p in ctx.recent()] == [4, 7, 3, 5, 6]
assert {p['id'] for p in ctx.squad()} == {1, 2, 3, 5} and ctx.squad()[0]['ca'] >= ctx.squad()[-1]['ca']
hits, hidden = ctx.search('an', (1,), keeper=False)
assert [p['name'] for p in hits] == ['Anna Able', 'Carl Anders', 'Dan Dane'], hits          # prefix, word start, substring
assert hidden == 0
hits, hidden = ctx.search('keeper', (), keeper=False)
assert hits == [] and hidden == 2, 'keepers are hidden from an outfield comparison and counted'

# -- the page -----------------------------------------------------------------------------------------------------
page = ComparePage()
page.resize(1008, 572)
page.show()
msgs = []
page.message.connect(msgs.append)
page.set_context(ctx)
pump()
assert page.players() == (None, None)
assert all(isinstance(c, PlayerCombo) for c in page._combo.values())
assert not page._swap.isEnabled() and not page._both.isVisible(), 'empty state: nothing to swap / shortlist'
assert page.findChildren(QLabel, 'cmpEmptyT')[0].text() == 'Pick two players to compare'
page.grab()
page.set_players(A, None)
pump()
assert page.findChildren(QLabel, 'cmpEmptyT')[0].text() == 'Now pick the second player'
page.set_players(A, B)
pump(6)
assert page.subtitle() == 'Ann Able vs Bob Baker' and page._swap.isEnabled() and page._both.isVisible()
assert len(page.findChildren(CompareRadar)) == 1 and len(page.findChildren(CompareRadar)[0]._ax) == 6
n_diff = len(page.findChildren(DiffCell))
assert n_diff == 14 + 14 + 8 + 5 + 2, f'{n_diff} diff cells = every listed attribute + the two Footedness rows'
assert len(page.findChildren(EdgeRow)) == 6
tally = [lb for lb in page.findChildren(QLabel) if 'level' in lb.text() and '●' in lb.text()][0]
assert '>2<' in tally.text() or '2</b>' in tally.text()
png = os.path.join(tempfile.gettempdir(), 'compare_outfield.png')
page.grab().save(png)
# Detailed mode: 12 outfield axes, 12 difference rows; back to Overview
page.set_mode('detailed')
pump(6)
assert len(page.findChildren(CompareRadar)[0]._ax) == 12 and len(page.findChildren(EdgeRow)) == 12 and page.mode() == 'detailed'
page.grab().save(os.path.join(tempfile.gettempdir(), 'compare_detailed.png'))
page.set_mode('overview')
pump()
assert len(page.findChildren(EdgeRow)) == 6
# Current | Full Potential redraws (the radar polygon changes: pot values are higher for a 28-year-old with PA > CA)
before = [a[1] for a in page.findChildren(CompareRadar)[0]._ax]
page._set_pot(True)
pump()
assert [a[1] for a in page.findChildren(CompareRadar)[0]._ax] != before, 'Full Potential changes the radar'
page._set_pot(False)
# keepers
page.set_players(g1, g2)
pump(6)
assert len(page.findChildren(DiffCell)) == 11 + 14 + 8 + 5 + 2
page.set_mode('detailed')
pump()
assert len(page.findChildren(CompareRadar)[0]._ax) == 11 and len(page.findChildren(EdgeRow)) == 11
page.set_mode('overview')
# a keeper next to an outfield player clears the other side (and says so)
page.set_players(A, g1)
assert page.players() == (A, None)
page._chosen('b', B)
page._chosen('a', g1)
assert page.players() == (g1, None)
assert any('goalkeepers are only compared' in m for m in msgs), msgs
page.set_players(A, B)
page.set_players(page.players()[1], page.players()[0])
assert page.players() == (B, A)

# -- Ability display: stars (default) vs numbers -------------------------------------------------------------------
assert S.ability_as_stars()
assert not [lb for lb in page.findChildren(QLabel) if lb.text() == '120']
S.save({'ability_display': 'numbers'})
page.refresh()
pump(4)
assert [lb for lb in page.findChildren(QLabel) if lb.text() == '120'], 'numbers mode: the raw CA'
S.save({'ability_display': 'stars'})
page.refresh()

# -- picker popup ---------------------------------------------------------------------------------------------------
host = page.window()
cb = page._combo['b']
page.set_players(A, None)
pump()
cb.open_picker()
pump(3)
pk = page._picker
assert isinstance(pk, PlayerPicker) and pk.isVisible()
rows = [p['id'] for p in pk.rows()]
assert rows == [7, 5, 6], rows          # recents newest first, without the keepers (A is outfield) and without A
assert 1 not in rows and not any(p['positions'][0] == 20 for p in pk.rows()), 'current player excluded, keepers hidden'
pk.set_source('short')
assert [p['id'] for p in pk.rows()] == [6]
# regression: the app-level filter sees a press on the QWindow (not a QWidget) first; a click over the popup (tab, row)
# must NOT close it, a click outside must
from PyQt6.QtCore import QEvent as _QE, QPointF as _QP, Qt as _Qt
from PyQt6.QtGui import QMouseEvent as _QM
def _press(obj, global_pt):
    ev = _QM(_QE.Type.MouseButtonPress, _QP(0, 0), _QP(global_pt), _Qt.MouseButton.LeftButton, _Qt.MouseButton.LeftButton, _Qt.KeyboardModifier.NoModifier)
    pk.eventFilter(obj, ev)
_win = host.windowHandle()
_inside = pk.mapToGlobal(pk.rect().center())
_press(_win, _inside)
assert pk.isVisible(), 'click over the popup (delivered at window level) closed it'
_press(_win, host.mapToGlobal(host.rect().bottomRight()) - __import__('PyQt6.QtCore', fromlist=['QPoint']).QPoint(2, 2))
assert not pk.isVisible(), 'click outside must close it'
cb.open_picker()
pump(3)
pk.set_source('short')
pk.set_source('squad')
assert {p['id'] for p in pk.rows()} == {2, 5}, 'human squad without A and without the keeper'
pk.set_query('ca')
assert [p['name'] for p in pk.rows()] == ['Carl Anders']
pk.set_query('ann')
assert [p['name'] for p in pk.rows()] == ['Anna Able']
assert pk.current_person()['id'] == 5
pk._pick()
pump()
assert page.players()[1]['id'] == 5 and not pk.isVisible(), 'Enter / click picks and closes'
# the row delegate paints without a facepack (silhouette) in stars and numbers mode
pk.set_query('')

# -- player window: action strip order + popup ----------------------------------------------------------------------
w = PlayerWindow(A, sd, None, None, picker=ctx)
w.show()
pump()
btns = [b.text() for b in w.findChildren(QPushButton) if b.objectName() in ('pwGhost', 'pwPrimary', 'pwShortOn')]
assert btns[-3:] == ['Compare to…  ▴', 'Add to Shortlist', 'Close'], btns
w._toggle_compare_popup()
pump()
ppk = w._picker
assert ppk.isVisible() and [p['id'] for p in ppk.rows()] == [7, 5, 6]
assert 1 not in [p['id'] for p in ppk.rows()], 'excludes the current player'
assert all(p['positions'][0] != 20 for p in ppk.rows()), 'outfield player: no keepers'
ppk.set_query('anna')
ppk._pick()
assert w._compare_with is not None and w._compare_with['id'] == 5 and w.result() == 1
w2 = PlayerWindow(A, sd, None, None)
assert 'Compare to…  ▴' not in [b.text() for b in w2.findChildren(QPushButton)], 'no picker context: no Compare button'
w2.close()

# -- main window: nav button, busy lock, reload restore ----------------------------------------------------------------
class _Sig:
    def connect(self, f): pass


class FakeWorker:
    def __init__(self, *a): self.progress = self.pct = self.done = self.error = _Sig()
    def start(self): pass


M.ParseWorker = FakeWorker


def make_save():
    ppl = [person(i, f'P{i:03d}', 10 + i % 5, ca=100 + i) for i in range(30)] + [person(100, 'Keeper One', gk=True), person(101, 'Keeper Two', gk=True)]
    return {'people': ppl, 'clubs': [{'id': 7, 'name': 'Club7', 'nation': 0, 'uid': 7}], 'squads': {i: 7 for i in range(30)},
            'sub_squads': {}, 'save_info': {'manager_club_id': 7}, 'club_staff': {}, 'employment': {}, 'human_clubs': {7}}


win = M.MainWindow()
win.resize(1200, 780)
win.show()
win._save_path = os.path.join(tempfile.mkdtemp(), 'fake.fm')
sd1 = make_save()
win._on_parse_done(sd1)
for _ in range(2000):
    app.processEvents()
    if win._save_data is sd1:
        break
btn = win._nav_btns['compare']
assert btn.text().strip() == 'Compare Players' and btn.isEnabled()
keys = list(win._nav_btns)
assert keys[-1] == 'compare' and keys[-2] == 'staff_shortlist', 'registered after the MAIN items'
win._set_busy(True, 'Saving')
assert not btn.isEnabled(), 'busy lock covers the new nav button'
win._set_busy(False)
win._update_ui_state()
assert btn.isEnabled()
# recents: opening a player window pushes the id; Compare to... lands on the page
win._recents.push(3)
win._open_compare(sd1['people'][1], sd1['people'][2])
pump()
assert win._main_stack.currentIndex() == win._VIEW_INDEX['compare'] and btn.isChecked()
assert win._compare_page.players()[0]['id'] == 1 and win._compare_page.players()[1]['id'] == 2
assert win._header_title_lbl.text() == 'Compare Players' and 'P001' in win._header_subtitle_lbl.text()
win._compare_page.set_mode('detailed')
win.grab().save(os.path.join(tempfile.gettempdir(), 'compare_main.png'))
# reload of the same save: both players + radar mode come back (resolved by id against the re-parsed people)
win._reload_save()
sd2 = make_save()
win._on_parse_done(sd2)
for _ in range(2000):
    app.processEvents()
    if win._save_data is sd2:
        break
pump()
a, b = win._compare_page.players()
assert a is sd2['people'][1] and b is sd2['people'][2], 'new objects, same ids'
assert win._compare_page.mode() == 'detailed'
assert win._main_stack.currentIndex() == win._VIEW_INDEX['compare']
# -- recents: every path that shows a player feeds ONE function; open pickers / the empty state read live ---------------------
def rids():
    return win._recents.ids()


def by(i):
    return next(q for q in win._save_data['people'] if q['id'] == i)


pg = win._compare_page
win._recents.set_save(win._save_path + '.recents-test')   # clean list
assert rids() == []
win._note_player_viewed(by(10))
win._note_player_viewed(None)                                 # tolerated
win._note_player_viewed(by(11))
assert rids() == [11, 10]
win._recents.push(type('N', (int,), {})(12))                  # int subclasses accepted (numpy ints: numbers.Integral)
assert rids()[0] == 12
# 1) player window path (all of _open_player_detail / _by_pid / shortlist / reports funnel into _run_player_window)
M.PlayerWindow.exec = lambda self: 0                          # do not block
win._run_player_window(by(13))
win._open_player_detail_by_pid(14)
assert rids()[:2] == [14, 13], rids()
win._run_player_window(by(10))
assert rids()[:3] == [10, 14, 13], 'an existing id moves to the front, no duplicate'
assert len(set(rids())) == len(rids())
# 2) Compare page picks (picker + empty-state list) are recorded
win._open_compare(by(20), None)
assert rids()[0] == 20, rids()
pg._chosen('b', by(21))
assert rids()[:2] == [21, 20], rids()
pg._empty_pick(by(22)) if pg.players()[0] is None or pg.players()[1] is None else None
# 3) Compare from a player window: both players recorded, A newest
win._open_compare(by(23), by(24))
assert rids()[:2] == [23, 24], rids()
# 4) search pick of a player
win._sg_pick(2, by(25), by(25)['name'])
assert rids()[0] == 25
# 5) the empty state's RECENTLY VIEWED list is re-read on navigation (not only at the last rebuild)
pg.set_players(None, None)
shown = lambda: [it.data(PlayerRowDelegate.PERSON)['id'] for lw in pg.findChildren(type(make_row_list()))
                 for it in (lw.item(i) for i in range(lw.count()))]
from gui.player_picker import make_row_list  # noqa: E402
assert shown()[:1] == [25], shown()
win._recents.push(26)                                         # e.g. a player window opened from another page
win._nav_to('compare')
pump()
assert shown()[:1] == [26], 'empty state shows the new recent after navigating back'
# 6) the shared picker, created once and left closed, shows the update on its next open (both Recent tab and re-switching tabs)
pk = pg._picker_for(pg._combo['a'])
pg._combo['a'].open_picker('recent')
assert [q['id'] for q in pk.rows()][0] == 26
pk.close_popup()
win._recents.push(27)
pg._combo['a'].open_picker('recent')
assert [q['id'] for q in pk.rows()][0] == 27, 'reopened picker re-reads the recents'
win._recents.push(28)
pk.set_source('squad')
pk.set_source('recent')
assert [q['id'] for q in pk.rows()][0] == 28, 'tab switch re-reads the recents'
pk.close_popup()
# 7) the 'Compare to...' popup of a player window, same rules (excludes the window's own player)
pw = PlayerWindow(by(1), win._save_data, None, None, picker=win._picker_context())
pw._toggle_compare_popup()
assert [q['id'] for q in pw._picker.rows()][0] == 28 and 1 not in [q['id'] for q in pw._picker.rows()]
pw._picker.close_popup()
win._note_player_viewed(by(1))
win._note_player_viewed(by(29))
pw._toggle_compare_popup()
assert [q['id'] for q in pw._picker.rows()][:1] == [29] and 1 not in [q['id'] for q in pw._picker.rows()], 'own player excluded, new recent shown'
pw._picker.close_popup()
pw.close()
print('compare page OK')
