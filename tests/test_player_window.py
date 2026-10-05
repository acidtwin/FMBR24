"""PlayerWindow on a synthetic player (no save needed): every tab builds, Close is the LAST button, the Profile has
no foot words, Positions fits the viewport without a scrollbar, the History 'Youth loan' cell is not clipped,
ElideLabel shows full text when it fits. Plain script: python3 tests/test_player_window.py"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea  # noqa: E402

app = QApplication.instance() or QApplication([])
from gui.player_window import TABS, PlayerWindow, _ElideLabel  # noqa: E402


def person(gk=False):
    pos = [1] * 15
    pos[0 if gk else 3] = 20
    return {'id': 1, 'name': 'Test Player', 'nation': 0, 'ca': 140, 'pa': 160, 'birth_year': 2000, 'birth_day': 100,
            'positions': pos, 'raw_attrs': [60 + (i * 7) % 40 for i in range(60)], 'personality': [10, 14, 8, 12, 15, 9, 13],
            'trait_mask': 5, 'wage_week': 100000, 'value_est': 50_000_000, 'height_cm': 190, 'weight_kg': 80,
            'contract_end': '2030-06-30', 'stats': {'apps': 10, 'starts': 8, 'subs': 2, 'goals': 1, 'assists': 2, 'pom': 1, 'rating': 7.1}}


def check(gk):
    w = PlayerWindow(person(gk), {'squads': {}, 'clubs': []}, 0, None, can_patch=True,
                     data={'history': {'status': 'ok', 'rows': [
                         {'season': '2024/25', 'club': 'Tottenham U21', 'club_raw': 1, 'kind': 'youth loan', 'apps': 3,
                          'goals': 0, 'fee': None}]}})
    w.show()
    for key, *_ in TABS:
        w._select_tab(key)
        app.processEvents()
        page = w._stack.currentWidget()
        if key == 'positions':
            assert isinstance(page, QScrollArea) and page.verticalScrollBar().maximum() == 0, 'Positions scrolls'
    # action strip: Add to Shortlist then Close, Close always last (the HGP / HGC pills live in the header)
    strip = w.findChild(QPushButton, 'pwGhost').parentWidget()
    texts = [b.text() for b in strip.findChildren(QPushButton)]
    assert texts[-1] == 'Close' and texts[-2] == 'Add to Shortlist', texts
    # Profile: no foot words anywhere
    w._select_tab('profile')
    txt = ' '.join(lb.text() for lb in w._stack.currentWidget().findChildren(QLabel))
    for bad in ('Left-footed', 'Right-footed', 'Very Strong', 'Fairly Strong', 'Reasonable', 'Very Weak'):
        assert bad not in txt, bad
    # History: 'Youth loan' fully visible
    w._select_tab('history')
    app.processEvents()
    cell = next(lb for lb in w._stack.currentWidget().findChildren(QLabel) if lb.text().startswith('Youth'))
    assert cell.text() == 'Youth loan' and cell.fontMetrics().horizontalAdvance('Youth loan') <= cell.width(), cell.text()
    # header: club/nation labels are not elided when they fit
    for lb in w.findChildren(_ElideLabel):
        assert lb._full == lb.text() or lb.fontMetrics().horizontalAdvance(lb._full) > lb.width(), lb._full
    # themed surfaces are wired (pw_themes)
    from gui.pw_themes import ActiveTabButton, ThemedFrame
    assert {type(w.findChild(QFrame, n)) for n in ('pwHeader', 'pwTabStrip', 'actionStrip')} == {ThemedFrame}
    assert all(isinstance(b, ActiveTabButton) for b in w._tab_btns.values())
    assert w.findChild(QFrame, 'actionStrip').halo_for.text() == 'Add to Shortlist'
    w.close()


check(False)
check(True)
# a person without raw_attrs / ca / pa / positions must not raise in the Full Potential slot
bare = PlayerWindow({'id': 1, 'name': 'Bare', 'nation': 0}, {'squads': {}, 'clubs': []}, 0, None)
bare._set_pot(True)
assert bare._projection().target == 0
bare.close()


def listed_positions(pos):
    q = person()
    q['positions'] = pos
    w = PlayerWindow(q, {'squads': {}, 'clubs': []}, 0, None)
    w.show()
    w._select_tab('positions')
    app.processEvents()
    page = w._stack.currentWidget()
    codes = [lb.text() for lb in page.findChildren(QLabel, 'pwBadge')]
    assert page.verticalScrollBar().maximum() == 0, 'Positions scrolls'
    w.close()
    return codes


from gui.player_window import POS_ORDER  # noqa: E402
few = [1] * 15
few[POS_ORDER.index('DC')], few[POS_ORDER.index('DM')], few[POS_ORDER.index('SW')], few[POS_ORDER.index('ST')] = 20, 14, 17, 0
assert listed_positions(few) == ['SW', 'D(C)', 'DM'], 'rows rated 0 or 1 are not listed, order kept'
assert len(listed_positions([1] * 15)) == 1, 'all <= 1: the single best row stays'
print('OK: player window tabs, Close last, no foot words in Profile, Positions fits, History kind column')

# click on the player's name copies it to the clipboard (header)
from PyQt6.QtCore import QPoint, Qt as _Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication as _QA  # noqa: E402
cw = PlayerWindow(person(False), {'squads': {}, 'clubs': []}, 0, None)
cw.show()
app.processEvents()
nm = cw.findChild(QLabel, 'pwName')
assert nm is not None and nm.toolTip() == 'Click to copy name' and nm.cursor().shape() == _Qt.CursorShape.PointingHandCursor
_QA.clipboard().setText('before')
QTest.mouseClick(nm, _Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
assert _QA.clipboard().text() == 'Test Player', _QA.clipboard().text()
QTest.mouseClick(nm, _Qt.MouseButton.RightButton, pos=QPoint(5, 5))        # other buttons do not touch it
assert _QA.clipboard().text() == 'Test Player'
cw.close()
print('OK: click on the player name copies it')
