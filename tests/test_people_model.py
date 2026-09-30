"""PeopleModel: numeric sort, filter subset, selection follows sort. Plain script, no save needed."""
import os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication, QTableView
from PyQt6.QtCore import Qt
from gui.people_model import PeopleModel, num_key

app = QApplication([])
spec = [(str, None), (lambda v: '?' if v is None else str(v), num_key)]
m = PeopleModel(['Name', 'CA', 'Att'], spec, lazy_fn=lambda p, c: p.get('a'))
src = [{'name': n, 'a': a} for n, a in (('b', 9), ('a', 10), ('c', 2), ('d', 100))]
rows = [('b', 9), ('a', 10), ('c', None), ('d', 100)]
m.set_data(src, rows)
tv = QTableView(); tv.setModel(m)
col = lambda c: [m.data(m.index(i, c)) for i in range(m.rowCount())]
m.sort(1, Qt.SortOrder.AscendingOrder)
assert col(1) == ['?', '9', '10', '100'], col(1)            # numeric, not lexical
m.sort(2, Qt.SortOrder.DescendingOrder)
assert col(2) == ['100', '10', '9', '2'], col(2)             # lazy attribute column
tv.selectRow(0)
m.sort(0, Qt.SortOrder.AscendingOrder)
sel = tv.selectionModel().selectedRows()
assert len(sel) == 1 and m.person(sel[0].row())['name'] == 'd'  # selection follows the row
m.set_base([i for i in range(4) if rows[i][1] and rows[i][1] > 9])
assert col(0) == ['a', 'd'] and m.total() == 4
print('OK: people_model')
