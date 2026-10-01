"""HGP / HGC badges + queued-row marking in the player lists (Squads, Reports, Shortlist, Players model).
Plain script, synthetic people, no save needed: FMBR24_CONFIG_DIR=/tmp/fmx QT_QPA_PLATFORM=offscreen python3 tests/test_hg_badges.py"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtCore import Qt, QRect  # noqa: E402
from PyQt6.QtGui import QImage, QPainter, QColor  # noqa: E402
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem  # noqa: E402
from gui.theme import QSS, COLORS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.people_model import HG_ROLE, ROWQ_ROLE, ROW_TINT  # noqa: E402
from fm_editor import patch as P  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
CLUB = 7
HGC_SET = {2, 3}  # 0 neither, 1 HGP only, 2 HGC only, 3 both, 4 neither
P.is_hgc = lambda b, p, e: p['id'] in HGC_SET


def person(i):
    return {'id': i, 'name': f'P{i}', 'ca': 100, 'pa': 120, 'nation': 0, 'birth_year': 2000, 'birth_day': 1,
            'positions': [1] * 15, 'raw_attrs': [10] * 60, 'personality': [10] * 7, 'trait_mask': 0,
            'hgp': i in (1, 3)}


people = [person(i) for i in range(5)]
w = M.MainWindow()
w._save_data = {'b': b'x', 'people': people, 'squads': {p['id']: CLUB - 1 for p in people},
                'clubs': [{'id': CLUB - 1, 'name': 'C'}], 'human_clubs': {CLUB - 1}}
w._squad = people
w._club_entity_id = CLUB
w._current_club = {'id': CLUB - 1, 'name': 'C'}
w._current_report_key = 'prospects'
w._table_mode = 'squad'

# delegates are installed on the badge columns, the name column carries the marker bar
assert isinstance(w._table.itemDelegateForColumn(8), M._HGBadgeDelegate)
assert isinstance(w._table.itemDelegateForColumn(9), M._HGBadgeDelegate)
assert w._table.columnWidth(8) >= 62 and w._table.columnWidth(9) >= 62
assert isinstance(w._reports_table.itemDelegateForColumn(8), M._HGBadgeDelegate)
assert isinstance(w._players_table.itemDelegateForColumn(8), M._HGBadgeDelegate)
for t in (w._table, w._reports_table, w._shortlist_table, w._players_table):
    assert isinstance(t.itemDelegate(), M._RowMarkDelegate)  # tint + name-cell bar for every column
assert issubclass(M._PosBadgeDelegate, M._RowMarkDelegate) and issubclass(M._HGBadgeDelegate, M._RowMarkDelegate)

# the palette: two greens, HGC darker than HGP, white text legible on both
def lum(c):
    c = QColor(c)
    f = lambda v: (v / 255 / 12.92) if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c.red()) + 0.7152 * f(c.green()) + 0.0722 * f(c.blue())
assert lum(COLORS['hgc_badge']) < lum(COLORS['hgp_badge'])
for k in ('hgp_badge', 'hgc_badge'):
    assert 1.05 / (lum(COLORS[k]) + 0.05) >= 4.5, k
    assert QColor(COLORS[k]).green() > QColor(COLORS[k]).red() and QColor(COLORS[k]).green() > QColor(COLORS[k]).blue()


def cell(t, name, col):
    for r in range(t.rowCount()):
        if t.item(r, 0).text() == name:
            return t.item(r, col)


def states(t, col):
    return [t.item(r, col).data(HG_ROLE) for r in range(t.rowCount())]


def text_by_name(t, col):
    return {t.item(r, 0).text(): t.item(r, col).text() for r in range(t.rowCount())}


def marked(t, name):
    return bool(cell(t, name, 0).data(ROWQ_ROLE))


# --- Squads (QTableWidget) -----------------------------------------------------------------------------------------
w._populate_squad_table(people)
t = w._table
assert text_by_name(t, 8) == {'P0': '', 'P1': 'HGP', 'P2': '', 'P3': 'HGP', 'P4': ''}, text_by_name(t, 8)
assert text_by_name(t, 9) == {'P0': '', 'P1': '', 'P2': 'HGC', 'P3': 'HGC', 'P4': ''}
assert cell(t, 'P1', 8).data(HG_ROLE) == 'set' and cell(t, 'P0', 8).data(HG_ROLE) == ''
assert all(not marked(t, f'P{i}') for i in range(5))

w.queue_toggle(people[0], 'hgc')                      # P0: one queued HGC
w.queue_toggle(people[4], 'hgp')                      # P4: queued HGP + HGC
w.queue_toggle(people[4], 'hgc')
assert cell(t, 'P0', 9).text() == '+ HGC' and cell(t, 'P0', 9).data(HG_ROLE) == 'queued'
assert cell(t, 'P0', 8).text() == '' and cell(t, 'P0', 8).data(HG_ROLE) == ''
assert cell(t, 'P4', 8).text() == '+ HGP' and cell(t, 'P4', 9).text() == '+ HGC'
assert cell(t, 'P1', 8).text() == 'HGP', 'set cells stay set'
assert marked(t, 'P0') and marked(t, 'P4')
assert not any(marked(t, n) for n in ('P1', 'P2', 'P3'))

# sort: set before unset, queued counts as set (ascending click order), unknown last
t.sortItems(8, Qt.SortOrder.AscendingOrder)
order = [t.item(r, 0).text() for r in range(t.rowCount())]
assert set(order[:3]) == {'P1', 'P3', 'P4'} and set(order[3:]) == {'P0', 'P2'}, order
t.sortItems(9, Qt.SortOrder.AscendingOrder)
order = [t.item(r, 0).text() for r in range(t.rowCount())]
assert set(order[:4]) == {'P0', 'P2', 'P3', 'P4'} and order[4] == 'P1', order

# unqueue + clear: tint and markers go away
w.queue_toggle(people[0], 'hgc')
assert cell(t, 'P0', 9).text() == '' and not marked(t, 'P0')
w._clear_queue()
assert w.queue_count() == 0 and not any(marked(t, f'P{i}') for i in range(5))
assert cell(t, 'P4', 8).text() == '' and cell(t, 'P4', 9).text() == ''
w.queue_toggle(people[4], 'hgp')
w.queue_toggle(people[0], 'hgc')

# a populate while a queue exists keeps the marks (switching squad tab / reload mid-session)
w._populate_squad_table(people)
assert cell(w._table, 'P0', 9).text() == '+ HGC' and marked(w._table, 'P0') and marked(w._table, 'P4')
assert not marked(w._table, 'P1')

# --- delegate paints a pill: pixel check on the three states ------------------------------------------------------
def render(delegate, state, text, kind_bg=None):
    t.setItemDelegateForColumn(8, delegate)
    img = QImage(70, 30, QImage.Format.Format_ARGB32)
    img.fill(QColor('#14151A'))
    it = M._SortItem('')
    M._hg_apply(it, delegate._kind, state == 'set', state == 'queued')
    probe = QTableWidgetProbe(it)
    p = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, 70, 30)
    opt.widget = t
    delegate.paint(p, opt, probe)
    p.end()
    return img


from PyQt6.QtWidgets import QTableWidget  # noqa: E402
probe_tbl = QTableWidget(1, 1)
probe_tbl.setItemDelegateForColumn(0, M._HGBadgeDelegate('hgp', probe_tbl))


def QTableWidgetProbe(it):
    probe_tbl.setItem(0, 0, it)
    return probe_tbl.model().index(0, 0)


def pill_pixel(img):
    return QColor(img.pixel(10, 15))


hgp_img = render(M._HGBadgeDelegate('hgp', t), 'set', 'HGP')
hgc_img = render(M._HGBadgeDelegate('hgc', t), 'set', 'HGC')
q_img = render(M._HGBadgeDelegate('hgp', t), 'queued', '+ HGP')
none_img = render(M._HGBadgeDelegate('hgp', t), '', '')
assert pill_pixel(hgp_img).name().upper() == COLORS['hgp_badge'].upper(), pill_pixel(hgp_img).name()
assert pill_pixel(hgc_img).name().upper() == COLORS['hgc_badge'].upper()
assert pill_pixel(q_img).red() > pill_pixel(q_img).blue() + 10, 'queued = yellow family'
assert pill_pixel(none_img).name().upper() == '#14151A', 'absent = empty cell'
t.setItemDelegateForColumn(8, M._HGBadgeDelegate('hgp', t))

# row marking is painted by the delegates: name cell = tint + 3px yellow bar, other cell = tint, unmarked = untouched
def paint_cell(col, mark):
    probe_tbl.setColumnCount(2)
    probe_tbl.setItemDelegate(M._RowMarkDelegate(probe_tbl))
    it0, it1 = M._SortItem('Name'), M._SortItem('x')
    it0.setData(ROWQ_ROLE, mark)
    probe_tbl.setItem(0, 0, it0)
    probe_tbl.setItem(0, 1, it1)
    img = QImage(70, 30, QImage.Format.Format_ARGB32)
    img.fill(QColor('#14151A'))
    p = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, 70, 30)
    opt.widget = probe_tbl
    probe_tbl.itemDelegate().paint(p, opt, probe_tbl.model().index(0, col))
    p.end()
    return img


im = paint_cell(0, True)
assert QColor(im.pixel(1, 15)).name().upper() == COLORS['queued'].upper() and QColor(im.pixel(4, 15)).name() != '#14151a'
assert QColor(im.pixel(4, 15)).red() > 0x14 + 10, 'tint under the name cell'
assert QColor(im.pixel(2, 0)).name().upper() == COLORS['queued'].upper() and QColor(im.pixel(2, 29)).name().upper() == COLORS['queued'].upper()
im = paint_cell(1, True)
assert QColor(im.pixel(1, 15)).name() != COLORS['queued'].lower() and QColor(im.pixel(60, 3)).red() > 0x14 + 10
im = paint_cell(0, False)
assert QColor(im.pixel(1, 15)).name() == '#14151a' and QColor(im.pixel(60, 3)).name() == '#14151a'

# --- Reports (HGP only) -----------------------------------------------------------------------------------------
w._populate_reports_table(people)
rt = w._reports_table
assert text_by_name(rt, 8) == {'P0': '', 'P1': 'HGP', 'P2': '', 'P3': 'HGP', 'P4': '+ HGP'}, text_by_name(rt, 8)
assert marked(rt, 'P4') and marked(rt, 'P0') and not marked(rt, 'P1')
assert cell(rt, 'P4', 8).data(HG_ROLE) == 'queued' and rt.columnCount() > 9 and rt.horizontalHeaderItem(8).text() == 'HGP'
rt.sortItems(8, Qt.SortOrder.AscendingOrder)
order = [rt.item(r, 0).text() for r in range(rt.rowCount())]
assert set(order[:3]) == {'P1', 'P3', 'P4'}, order
w.queue_toggle(people[2], 'hgp')
assert cell(rt, 'P2', 8).text() == '+ HGP'
w.queue_toggle(people[2], 'hgp')
assert cell(rt, 'P2', 8).text() == '' and not marked(rt, 'P2')

# --- Shortlist (no HGP column: row marking only) ------------------------------------------------------------------
w._shortlist = list(people)
w._populate_shortlist()
st = w._shortlist_table
assert marked(st, 'P0') and marked(st, 'P4') and not marked(st, 'P2')
w.queue_toggle(people[0], 'hgc')
assert not marked(st, 'P0')
w.queue_toggle(people[0], 'hgc')

# --- Players view (virtualised PeopleModel) -----------------------------------------------------------------------------
m = w._players_model
m.set_data(people, [w._player_row(p, w._save_data['squads'], {CLUB - 1: 'C'}) for p in people])
assert m.hg_cols == {8: 'hgp'}
w._clear_queue()
col = lambda c, role=Qt.ItemDataRole.DisplayRole: [m.data(m.index(r, c), role) for r in range(m.rowCount())]
name_of = lambda r: m.person(r)['name']
assert dict(zip(col(0), col(8))) == {'P0': '', 'P1': 'HGP', 'P2': '', 'P3': 'HGP', 'P4': ''}
assert dict(zip(col(0), col(8, HG_ROLE))) == {'P0': '', 'P1': 'set', 'P2': '', 'P3': 'set', 'P4': ''}
assert not any(col(0, ROWQ_ROLE))

changed = []
m.dataChanged.connect(lambda a, b, *_: changed.append((a.row(), b.row(), a.column(), b.column())))
w.queue_toggle(people[0], 'hgp')
assert len(changed) == 1 and changed[0][2:] == (0, m.columnCount() - 1) and changed[0][0] == changed[0][1], changed
w.queue_toggle(people[0], 'hgc')   # second kind on the same player: only that one row again
assert len(changed) == 2
names = col(0)
assert dict(zip(names, col(0, ROWQ_ROLE))) == {'P0': True, 'P1': False, 'P2': False, 'P3': False, 'P4': False}
r0 = names.index('P0')
assert m.data(m.index(r0, 8)) == '+ HGP' and m.data(m.index(r0, 8), HG_ROLE) == 'queued'
assert all(m.data(m.index(r0, c), ROWQ_ROLE) for c in range(m.columnCount()))
assert 'Queued' in m.data(m.index(r0, 8), Qt.ItemDataRole.ToolTipRole)
# a queue change for a player outside the current filter repaints nothing, no error
m.set_base([names.index('P1')])
n = len(changed)
w.queue_toggle(people[3], 'hgp')
assert len(changed) == n
w.queue_toggle(people[3], 'hgp')
m.set_base(list(range(5)))

# sort: set before unset, queued counts as set; re-sorts live when the list is sorted by that column
m.sort(8, Qt.SortOrder.AscendingOrder)
order = col(0)
assert set(order[:3]) == {'P0', 'P1', 'P3'} and set(order[3:]) == {'P2', 'P4'}, order   # P0 queued, P1/P3 set
m.sort(8, Qt.SortOrder.DescendingOrder)
assert set(col(0)[:2]) == {'P2', 'P4'}
m.sort(8, Qt.SortOrder.AscendingOrder)
w.queue_toggle(people[4], 'hgp')
assert 'P4' in col(0)[:4], col(0)
w.queue_toggle(people[0], 'hgp')
w.queue_toggle(people[4], 'hgp')
assert set(col(0)[:2]) == {'P1', 'P3'}, col(0)
w._clear_queue()
assert not any(col(0, ROWQ_ROLE)) and col(8) == [m.data(m.index(r, 8)) for r in range(5)]

# scale: 78k rows, a queue edit touches one row, never walks the whole table
import time  # noqa: E402
big = [{'id': i, 'name': f'N{i}', 'hgp': i % 3 == 0} for i in range(78000)]
bm = M.PeopleModel(['Name', 'HGP'], [(str, None), (lambda v: 'HGP' if v else '', None)])
bm.hg_cols = {1: 'hgp'}
bm.set_data(big, [(p['name'], p['hgp']) for p in big])
ch = []
bm.dataChanged.connect(lambda a, b, *_: ch.append(a.row()))
t0 = time.perf_counter()
bm.set_queue({5: {'hgp'}})
bm.set_queue({})
dt = time.perf_counter() - t0
assert ch == [5, 5] and dt < 0.5, (ch, dt)

print('OK: HGP/HGC badges, queued cells, row marking (Squads, Reports, Shortlist, Players model), sort, 78k fast')
