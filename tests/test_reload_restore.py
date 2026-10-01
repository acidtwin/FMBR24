"""Reload / post-save reload puts the user back where they were (gui/main_window.py _capture_ui_state / _apply_ui_state).
Synthetic saves, no real save needed: FMBR24_CONFIG_DIR=/tmp/fmx QT_QPA_PLATFORM=offscreen python3 tests/test_reload_restore.py"""
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp()  # landing page = default (Save Info), real settings untouched
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication, QAbstractItemView  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)


class _Sig:
    def connect(self, f): pass


class FakeWorker:  # _reload_save starts a worker; the test feeds _on_parse_done itself
    def __init__(self, *a): self.progress = self.pct = self.done = self.error = _Sig()
    def start(self): pass


M.ParseWorker = FakeWorker
CLUBS = (7, 8)


def person(i):
    return {'id': i, 'name': f'P{i:03d}', 'ca': 50 + i, 'pa': 120 + i, 'nation': 0, 'birth_year': 2000, 'birth_day': 1,
            'positions': [1] * 15, 'raw_attrs': [10] * 60, 'personality': [10] * 7, 'trait_mask': 0, 'hgp': False}


def make_save(club_ids=CLUBS):
    """Fresh dicts every call (a reload re-parses). Club 7 first team = ids 0-9, its U21 = ids 100-159."""
    people = [person(i) for i in list(range(10)) + list(range(100, 160)) + list(range(200, 205))]
    return {'people': people, 'clubs': [{'id': c, 'name': f'Club{c}', 'nation': 0} for c in club_ids],
            'squads': {**{i: 7 for i in range(10)}, **{i: 8 for i in range(200, 205)}},
            'sub_squads': {7: {21: list(range(100, 160))}}, 'save_info': {'manager_club_id': 8},
            'club_staff': {}, 'employment': {}, 'human_clubs': set()}


w = M.MainWindow()
w.resize(1300, 560)
w.show()
PATH = os.path.join(tempfile.mkdtemp(), 'fake_reload_restore.fm')
w._save_path = PATH


def parse(sd):
    """Finish a parse the way ParseWorker.done does and wait for the time-sliced list preload."""
    w._on_parse_done(sd)
    for _ in range(2000):
        app.processEvents()
        if w._save_data is sd:
            break
    assert w._save_data is sd
    app.processEvents()


def reload_with(sd=None, path=None):
    w._reload_save()  # the real hook: takes the snapshot
    if path:
        w._save_path = path
    sd = sd or make_save()
    parse(sd)
    return sd


def view():
    return next(k for k, v in w._VIEW_INDEX.items() if v == w._main_stack.currentIndex())


parse(make_save())
assert view() == 'save_info'  # first load: landing page, nothing to restore

# -- Squads view of club 7, U21 tab, sorted by CA descending, scrolled, one row selected ----------------------
w._show_squad(w._save_data['clubs'][0])
w._squad_tab_btns[1].click()
w._nav_to_squad_view()
t = w._table
assert t.rowCount() == 60
t.sortByColumn(3, Qt.SortOrder.DescendingOrder)
app.processEvents()
top_pid = t.item(30, 0).data(Qt.ItemDataRole.UserRole)
t.scrollTo(t.model().index(30, 0), QAbstractItemView.ScrollHint.PositionAtTop)
sel_pid = t.item(35, 0).data(Qt.ItemDataRole.UserRole)
t.selectRow(35)
app.processEvents()
assert t.rowAt(0) == 30, t.rowAt(0)
w._search_box.blockSignals(True); w._search_box.setText('Club7'); w._search_box.blockSignals(False)
old_clubs = [c for _i, c in w._nav_history if 'club' in c]
assert old_clubs

sd = reload_with()
app.processEvents()
t = w._table
assert view() == 'squad'
assert w._current_club is sd['clubs'][0] and len(w._squad) == 60
assert [b.isChecked() for b in w._squad_tab_btns] == [False, True]
assert t.rowCount() == 60
hdr = t.horizontalHeader()
assert (hdr.sortIndicatorSection(), hdr.sortIndicatorOrder()) == (3, Qt.SortOrder.DescendingOrder)
cas = [int(t.item(r, 3).text()) for r in range(t.rowCount())]
assert cas == sorted(cas, reverse=True)
assert t.item(t.rowAt(0), 0).data(Qt.ItemDataRole.UserRole) == top_pid
assert [t.item(i.row(), 0).data(Qt.ItemDataRole.UserRole) for i in t.selectionModel().selectedRows()] == [sel_pid]
assert w._search_box.text() == 'Club7'
# history survives, clubs re-resolved by id to the NEW objects
new_clubs = [c['club'] for _i, c in w._nav_history if 'club' in c]
assert len(new_clubs) == len(old_clubs) and all(c is sd['clubs'][0] for c in new_clubs)
w.grab().save(os.path.join(tempfile.gettempdir(), 'reload_restore_squad.png'))

# -- Players view with a search subset + filters + sort + selection ---------------------------------------
subset = [p for p in w._save_data['people'] if p['id'] in (3, 4, 5, 120, 121, 200)]
w._open_players_view(players=subset)
w._players_ca_filter.setValue(55)  # CA >= 55 drops 3 and 4 (CA 53, 54)
w._players_table.sortByColumn(3, Qt.SortOrder.DescendingOrder)
app.processEvents()
before = [w._players_model.person(r)['id'] for r in range(w._players_model.rowCount())]
assert before == [200, 121, 120, 5], before
w._players_table.selectRow(2)
reload_with()
app.processEvents()
assert view() == 'players'
m = w._players_model
assert [m.person(r)['id'] for r in range(m.rowCount())] == before
assert w._players_ca_filter.value() == 55
assert w._players_subset is not None and {p['id'] for p in w._players_subset} == {3, 4, 5, 120, 121, 200}
assert all(p is next(q for q in w._save_data['people'] if q['id'] == p['id']) for p in w._players_subset)
assert [m.person(i.row())['id'] for i in w._players_table.selectionModel().selectedRows()] == [120]
hdr = w._players_table.horizontalHeader()
assert (hdr.sortIndicatorSection(), hdr.sortIndicatorOrder()) == (3, Qt.SortOrder.DescendingOrder)
assert w._current_club is not None and w._nav_btns['club'].isEnabled()  # club context kept while on Players

# -- Reports with a position / filter -----------------------------------------------------------------------
w._report_pos_combo.setCurrentIndex(2)
pos_text = w._report_pos_combo.currentText()
w._report_ca_filter.setValue(60)
w._run_report('best_pos')
n_rows = w._reports_table.rowCount()
assert n_rows > 0
reload_with()
assert view() == 'reports' and w._current_report_key == 'best_pos'
assert w._report_pos_combo.currentText() == pos_text and w._report_ca_filter.value() == 60
assert w._reports_table.rowCount() == n_rows
w._report_ca_filter.setValue(0)

# -- Club no longer exists: fall back to the landing page ------------------------------------------------
w._show_squad(w._save_data['clubs'][0])
w._nav_to_squad_view()
assert view() == 'squad'
reload_with(make_save(club_ids=(8,)))
assert view() == 'save_info', view()

# -- Loading a different file ignores the snapshot ------------------------------------------------------------
w._show_squad(w._save_data['clubs'][0])
assert view() == 'club'
reload_with(path=os.path.join(os.path.dirname(PATH), 'another_save.fm'))
assert view() == 'save_info', view()

# -- First load of a save (Load button path: _save_data cleared) never restores ----------------------------------
w._show_squad(w._save_data['clubs'][0])
w._save_data = None
w._ui_snap = None
w._reload_save()
assert w._ui_snap is None
print('OK')
