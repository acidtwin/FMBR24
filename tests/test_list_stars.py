"""CA / PA stars in the player lists (Squads, Reports, Shortlist, Players view): StarsDelegate paint, raw sort order,
tooltips, Numbers mode unchanged, Settings switch without reload, 78k-row paint budget.
Plain script, synthetic people, no save needed: FMBR24_CONFIG_DIR=/tmp/fmx QT_QPA_PLATFORM=offscreen python3 tests/test_list_stars.py"""
import os
import sys
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtCore import Qt, QEvent, QPoint, QRect  # noqa: E402
from PyQt6.QtGui import QColor, QHelpEvent, QImage, QPainter  # noqa: E402
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem, QTableWidget  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.stars import star_row_pixmap, _ROW_CACHE  # noqa: E402
from fm_editor.abilitystars import ability_stars  # noqa: E402
from fm_editor import settings as S  # noqa: E402
from fm_editor import patch as P  # noqa: E402

P.is_hgc = lambda b, pp, e: False

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
D = M.StarsDelegate
assert D.stars_on and S.ability_as_stars(), 'default = stars'

CAS = [100, 9, 150, 20, 70]


def person(i, ca):
    return {'id': i, 'name': f'P{i}', 'ca': ca, 'pa': ca + 20, 'nation': 0, 'birth_year': 2000, 'birth_day': 1,
            'positions': [1] * 15, 'raw_attrs': [10] * 60, 'personality': [10] * 7, 'trait_mask': 0}


people = [person(i, c) for i, c in enumerate(CAS)]
w = M.MainWindow()
w._save_data = {'b': b'x', 'people': people, 'squads': {p['id']: 6 for p in people},
                'clubs': [{'id': 6, 'name': 'C'}], 'human_clubs': {6}}
w._squad = people
w._club_entity_id = 7
w._current_club = {'id': 6, 'name': 'C'}
w._table_mode = 'squad'
w._current_report_key = 'prospects'
w._populate_squad_table(people)
w._populate_reports_table(people)
w._shortlist = list(people)
w._populate_shortlist()
m = w._players_model
m.set_data(people, [w._player_row(p, w._save_data['squads'], {6: 'C'}) for p in people])

# --- delegates installed on the right columns, widths fit the stars ---------------------------------------------------
TABLES = ((w._table, 3, 4), (w._reports_table, 3, 4), (w._players_table, 3, 4), (w._shortlist_table, 4, 5))
for t, ca, pa in TABLES:
    assert isinstance(t.itemDelegateForColumn(ca), D) and isinstance(t.itemDelegateForColumn(pa), D)
    assert t.itemDelegateForColumn(ca)._label == 'CA' and t.itemDelegateForColumn(pa)._label == 'PA'
    assert t.columnWidth(ca) == t.columnWidth(pa) == 76
    assert isinstance(t.itemDelegateForColumn(ca), M._RowMarkDelegate)   # composes with the row tint / queued bar
# Dev Rate is stars too (tests/test_list_media.py covers it in detail); the Player Shortlist has no Dev column
for t in (w._table, w._reports_table, w._players_table):
    assert isinstance(t.itemDelegateForColumn(5), D) and t.itemDelegateForColumn(5)._label == 'Dev'


def gold(img, x0=0, x1=None):
    n = 0
    for y in range(img.height()):
        for x in range(x0, x1 or img.width()):
            c = QColor(img.pixel(x, y))
            n += c.red() > 200 and c.green() > 150 and c.blue() < 90
    return n


def paint(table, col, row=0, selected=False):
    """Paint the cell (row, col) of a table with its own delegate into a 76x30 image."""
    idx = table.model().index(row, col)
    d = table.itemDelegateForColumn(col)
    img = QImage(76, 30, QImage.Format.Format_ARGB32)
    img.fill(QColor('#14151A'))
    p = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, 76, 30)
    opt.widget = table
    if selected:
        opt.state |= opt.state.__class__.State_Selected
    d.paint(p, opt, idx)
    p.end()
    return img


# --- delegate paints stars for known values: gold area == the reference pixmap for ability_stars(value) --------------
ref = lambda s: gold(star_row_pixmap(s).toImage())
assert [ability_stars(v) for v in (1, 100, 149, 170, 200)] == [0.5, 2.5, 3.5, 4.5, 5.0]
areas = []
for t, ca, pa in TABLES[:3]:
    for r, p in enumerate(people):          # row order = population order (sorting off in the offscreen populate? use texts)
        pass
t = w._table
t.setSortingEnabled(False)
w._populate_squad_table(people)             # sorting off: row r == people[r]
for r, p in enumerate(people):
    for col, key in ((3, 'ca'), (4, 'pa')):
        img = paint(t, col, r)
        want = ref(ability_stars(p[key]))
        assert abs(gold(img) - want) <= 2, (p[key], gold(img), want)
        areas.append((ability_stars(p[key]), gold(img)))
areas.sort()
assert all(a[1] < b[1] for a, b in zip(areas, areas[1:]) if a[0] < b[0]), 'more stars = more gold'
# vertically centred, left inset 8, nothing past 8+58 px
img = paint(t, 3, 2)   # CA 150 -> 4 stars... wait: 150/40 = 3.75 -> 4.0
ys = [y for y in range(30) for x in range(76) if QColor(img.pixel(x, y)).red() > 200 and QColor(img.pixel(x, y)).blue() < 90]
xs = [x for y in range(30) for x in range(76) if QColor(img.pixel(x, y)).red() > 200 and QColor(img.pixel(x, y)).blue() < 90]
assert abs((min(ys) + max(ys)) / 2 - 14.5) <= 1.5, (min(ys), max(ys))
assert 10 <= min(xs) <= 12 and max(xs) <= 10 + 58, (min(xs), max(xs))
# selected row: stars still gold on top of the selection fill
img = paint(t, 3, 2, selected=True)
assert gold(img) > 60 and QColor(img.pixel(74, 2)).name().upper() == '#2A1B4A', QColor(img.pixel(74, 2)).name()
# the row-mark tint composes: a queued row keeps its stars
t.item(2, 0).setData(M.ROWQ_ROLE, True)
img = paint(t, 3, 2)
assert gold(img) > 60 and QColor(img.pixel(74, 2)).red() > 0x14 + 10, 'tint under the stars'
t.item(2, 0).setData(M.ROWQ_ROLE, False)
# a '?' / '-' cell (unknown rating, staff row in the shortlist) paints no stars
unk = M._SortItem('?', -1)
t.setItem(0, 3, unk)
assert gold(paint(t, 3, 0)) == 0
w._populate_squad_table(people)

# --- tooltips: raw number in stars mode ----------------------------------------------------------------------------------
idx = w._table.model().index(0, 3)
assert w._table.itemDelegateForColumn(3).tip(idx) == 'CA 100'
assert w._table.itemDelegateForColumn(4).tip(w._table.model().index(2, 4)) == 'PA 170'
assert w._players_table.itemDelegateForColumn(3).tip(m.index(0, 3)).startswith('CA ')
opt = QStyleOptionViewItem()
ev = QHelpEvent(QEvent.Type.ToolTip, QPoint(5, 5), QPoint(5, 5))
assert w._table.itemDelegateForColumn(3).helpEvent(ev, w._table, opt, idx) is True

# --- raw sort order unchanged (a stars cell sorts by the number, 9 < 20 < 70 < 100 < 150, not lexically) -----------------
raw = lambda t, c: [int(t.item(r, c).text()) for r in range(t.rowCount())]
for t, ca, pa in (TABLES[0], TABLES[1], TABLES[3]):
    t.setSortingEnabled(True)
    t.sortItems(ca, Qt.SortOrder.AscendingOrder)
    assert raw(t, ca) == sorted(CAS), (t is w._table, raw(t, ca))
    t.sortItems(pa, Qt.SortOrder.DescendingOrder)
    assert raw(t, pa) == sorted((c + 20 for c in CAS), reverse=True), raw(t, pa)
m.sort(3, Qt.SortOrder.AscendingOrder)
assert [int(m.data(m.index(r, 3))) for r in range(m.rowCount())] == sorted(CAS)
m.sort(4, Qt.SortOrder.DescendingOrder)
assert [int(m.data(m.index(r, 4))) for r in range(m.rowCount())] == sorted((c + 20 for c in CAS), reverse=True)
# the model still hands out the number as display text (the delegate's raw value), no star text
assert m.data(m.index(0, 3)).isdigit()

# --- Numbers mode: identical to the plain cell, no stars, no tooltip, narrower columns ----------------------------------
w._populate_squad_table(people)
R100 = next(r for r in range(5) if w._table.item(r, 3).text() == '100')   # row order follows the last sort
stars_img = paint(w._table, 3, R100)
w._settings_page.saved.emit(dict(S.load(), ability_display='numbers'))   # the real Settings > Save path
assert not D.stars_on
for t, ca, pa in TABLES:
    assert t.columnWidth(ca) == t.columnWidth(pa) == 45, (t, t.columnWidth(ca))
num_img = paint(w._table, 3, R100)
assert gold(num_img) == 0 and num_img != stars_img
old = M._RowMarkDelegate(w._table)           # what the column had before this feature
w._table.setItemDelegateForColumn(3, old)
img = paint(w._table, 3, R100)
w._table.setItemDelegateForColumn(3, D('CA', w._table))
assert num_img == img, 'numbers mode paints exactly like the old text cell'
assert w._table.itemDelegateForColumn(3).tip(w._table.model().index(0, 3)) is None
assert w._table.itemDelegateForColumn(3).helpEvent(ev, w._table, opt, idx) is False
assert w._table.item(R100, 3).text() == '100'

# --- ... and back to stars without a reload ---------------------------------------------------------------------------------
w._settings_page.saved.emit(dict(S.load(), ability_display='stars'))
assert D.stars_on and w._table.columnWidth(3) == 76 and gold(paint(w._table, 3, R100)) > 0
assert paint(w._table, 3, R100) == stars_img

# --- 78k rows: paint one viewport page under budget, no per-row work, tiny pixmap cache -----------------------------------
N = 78000
src = [{'id': i, 'name': f'N{i}'} for i in range(N)]
rows = [(f'N{i}', False, 'ST', (i * 7) % 200 + 1, (i * 13) % 200 + 1, 10, 25, '', False, 'C', '') for i in range(N)]
pm = w._players_model
pm.set_data(src, rows)
pt = w._players_table
pt.resize(1300, 900)
pt.show()
pt.grab()                                   # warm: layout + pixmap cache
t0 = time.perf_counter()
for _ in range(5):
    img = pt.viewport().grab().toImage()
dt = (time.perf_counter() - t0) / 5
print(f'78k-row players viewport grab: {dt * 1000:.0f} ms')
assert dt < 0.5, dt
assert gold(img, 150 + 35 + 55, 150 + 35 + 55 + 144) > 0, 'stars visible in the CA/PA columns'
assert len(_ROW_CACHE) <= 12 * 2, len(_ROW_CACHE)
t0 = time.perf_counter()
pm.sort(3, Qt.SortOrder.DescendingOrder)    # raw CA key, 78k rows
assert int(pm.data(pm.index(0, 3))) == 200 and int(pm.data(pm.index(N - 1, 3))) == 1
print(f'78k sort by CA: {(time.perf_counter() - t0) * 1000:.0f} ms')
print('OK: list_stars')
