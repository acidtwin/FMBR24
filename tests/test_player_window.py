"""PlayerWindow on a synthetic player (no save needed): every tab builds, Close is the LAST button, the Profile has
no foot words, Positions fits the viewport without a scrollbar, the History 'Youth loan' cell is not clipped,
ElideLabel shows full text when it fits. Plain script: python3 tests/test_player_window.py"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('FMBR24_CONFIG_DIR', '/tmp/fmbr24_test_pw')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea  # noqa: E402

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
    # Close is the last button of the action strip; Make HGP / HGC before Add to Shortlist
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
    w.close()


check(False)
check(True)
print('OK: player window tabs, Close last, no foot words in Profile, Positions fits, History kind column')
