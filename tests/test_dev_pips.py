"""Dev pips (style B) + Best by Role rating ring (style D) delegates: lit count, tier colour, ring arc monotonic, tooltip,
Numbers/Stars modes, raw sort. Synthetic data, no save.
FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_dev_pips.py"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtCore import Qt, QRect  # noqa: E402
from PyQt6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem, QTableWidget  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.player_window import TIER_HEX, tier  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
assert M.DevDelegate.mode == 'graphic'

tb = QTableWidget(20, 1)
for v in range(1, 21):
    tb.setItem(v - 1, 0, M._SortItem(str(v), v))
tb.setItem(0, 0, M._SortItem('?', -1))


def paint(d, row, w=76):
    img = QImage(w, 24, QImage.Format.Format_ARGB32)
    img.fill(QColor('#14151A'))
    p = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, w, 24)
    opt.widget = tb
    d.paint(p, opt, tb.model().index(row, 0))
    p.end()
    return img


def near(c, hexs):
    t = QColor(hexs)
    return abs(c.red() - t.red()) + abs(c.green() - t.green()) + abs(c.blue() - t.blue()) < 12


dd = M.DevDelegate(tb)
assert paint(dd, 0) == paint(M._RowMarkDelegate(tb), 0), 'unknown value paints nothing'
for v in range(2, 21):
    img = paint(dd, v - 1)
    lit = 0
    for i in range(5):
        c = QColor(img.pixel(10 + i * 10 + 4, 12))   # pip centre
        if near(c, TIER_HEX[tier(v)]):
            lit += 1
        else:
            assert near(c, '#3A4050'), (v, i, c.name())
    assert lit == -(-v // 4), (v, lit)
assert dd.tip(tb.model().index(13, 0)) == 'Dev 14 of 20'
# stars mode = the dev_stars row (gold), numbers mode = plain text cell, no tooltip
M.DevDelegate.mode = 'stars'
gold = sum(1 for x in range(76) for y in range(24) if QColor(paint(dd, 15).pixel(x, y)).red() > 200 > QColor(paint(dd, 15).pixel(x, y)).blue())
assert gold > 20 and dd.tip(tb.model().index(13, 0)) == 'Dev 14 of 20'
M.DevDelegate.mode = 'numbers'
assert paint(dd, 13) == paint(M._RowMarkDelegate(tb), 13) and dd.tip(tb.model().index(13, 0)) is None
M.DevDelegate.mode = 'graphic'

# ring: arc pixels grow monotonically with the value, full ring at 20; tier colour of the arc
rd = M.RoleRingDelegate(tb)
assert paint(rd, 0) == paint(M._RowMarkDelegate(tb), 0)
areas = []
for v in range(2, 21):
    img = paint(rd, v - 1, 56)
    n = sum(1 for x in range(10, 24) for y in range(5, 19) if near(QColor(img.pixel(x, y)), TIER_HEX[tier(v)]))
    areas.append(n)
assert all(a <= b for a, b in zip(areas, areas[1:])), areas
assert areas[-1] > areas[0] * 4, areas
# 12 o'clock start, clockwise: v=10 (half) fills the right side, not the left
img = paint(rd, 9, 56)
assert near(QColor(img.pixel(22, 12)), TIER_HEX[tier(10)]) and near(QColor(img.pixel(11, 12)), '#3A4050')
assert rd._raw(tb.model().index(9, 0)) == 10
print('OK: dev_pips')
