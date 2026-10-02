"""The page header's right slot holds ONLY the current page's widget: Squads stats strip after Squads, club
reputation stars after Club, nothing elsewhere. Regression: a cleared widget stayed a visible child of the slot
until the event loop ran deleteLater, so Club's stars were drawn over Squads' leftover '24 players ...' strip;
and re-entering Squads via _update_header_for_view (e.g. restore after a reload) dropped the strip.

Run: python3 tests/test_header_slot.py   (offscreen, no save needed)
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from gui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
w = MainWindow()
w.resize(1300, 800)
w.show()
app.processEvents()
w._current_club = {'name': 'Test FC', 'rep': 7000}
w._squad_info.setText('<b>24</b> players &nbsp; <b>10</b> HGP &nbsp; <b>11</b> HGC')  # what _populate_squad_table leaves
slot = w._header_right_slot


def shown():
    """Direct children of the slot that would paint (no event-loop pass in between, as in a grab())."""
    return [c for c in slot.children() if isinstance(c, QWidget) and c.isVisibleTo(slot)]


def check(key, expect_text=None):
    w._update_header_for_view(key)       # deliberately no processEvents: stale deleteLater'd widgets must already be gone
    kids = shown()
    if expect_text is None:
        assert not slot.isVisibleTo(w) and not kids, (key, kids)
        return
    assert slot.isVisibleTo(w) and len(kids) == 1, (key, kids, slot.isVisibleTo(w), slot.children())
    texts = [l.text() for l in kids[0].findChildren(QLabel)] + ([kids[0].text()] if isinstance(kids[0], QLabel) else [])
    assert any(expect_text in t for t in texts), (key, texts)


for _ in range(2):   # repeat: second pass proves nothing accumulates
    check('squad', 'players')
    check('club', 'CLUB REPUTATION')
    check('squad', 'players')
    check('club_staff')
    check('club', 'CLUB REPUTATION')
    check('staff')
    check('squad', 'players')
    check('save_info')
    check('squad', 'players')
    check('club', 'CLUB REPUTATION')
    check('players')

# direct _set_header calls swap cleanly too
lbl = QLabel('x')
w._set_header('A', '', lbl)
w._set_header('B', '', QLabel('y'))
assert len(shown()) == 1 and lbl.parent() is None
app.processEvents()
print('OK')
