"""Pos column sorts by _POS_SORT_ORDER (GK, D, M, ST), not alphabetically, in the player lists.
Plain script, synthetic rows, no save needed."""
import os, sys
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.theme import QSS
import gui.main_window as M
from fm_editor.gamedb import POSITIONS

app = QApplication([]); app.setStyleSheet(QSS)
w = M.MainWindow()
rank = lambda v: M._POS_SORT_ORDER.get(v, 99)
codes = ['ST', 'AMR', 'DC', 'GK', 'DM', 'WBL', 'DL', 'MC', 'DR', 'AMC']
want = sorted(rank(c) for c in codes)


def person(i, code):
    pos = [1] * len(POSITIONS); pos[POSITIONS.index(code)] = 20
    return {'id': i, 'name': f'p{i}', 'ca': 100, 'pa': 120, 'positions': pos}


# Shortlist (QTableWidget + _SortItem)
w._populate_shortlist([person(i, c) for i, c in enumerate(codes)])
t = w._shortlist_table
t.sortByColumn(3, Qt.SortOrder.AscendingOrder)
got = [t.item(i, 3).text() for i in range(t.rowCount())]
assert [rank(c) for c in got] == want, got

# Players view (PeopleModel own sort)
src = [person(i, c) for i, c in enumerate(codes)]
m = w._make_players_model()
m.set_data(src, [w._player_row(p, {}, {}) for p in src])
m.sort(2, Qt.SortOrder.AscendingOrder)
got = [m.data(m.index(i, 2)) for i in range(m.rowCount())]
assert [rank(c) for c in got] == want, got
print('ok')
