"""Transfer panel availability row: 'Not for sale' (stored value exactly 300,000,000) and 'On loan from <club>'
(squad club != contract club, fm_editor.gamedb.find_loans). Synthetic persons / clubs, plus a real-data count check on the
frozen snapshot (skipped loudly when absent). Plain script:
    FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_transfer_status.py"""
import os
import sys
import unicodedata

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication, QFrame, QLabel  # noqa: E402

app = QApplication.instance() or QApplication([])
from fm_editor.gamedb import find_loans  # noqa: E402
from gui import main_window as mw  # noqa: E402
from gui.player_window import PlayerWindow, transfer_status  # noqa: E402

SNAPSHOT = os.path.expanduser('~/.local/share/fmbr24/test-saves/snapshot-2028-01-02.fm')


def club(cid, name, team, nation=139):
    return {'id': cid, 'uid': cid * 10, 'name': name, 'team': team, 'nation': nation}


CLUBS = [club(1, 'Getafe C.F.', 101, 170), club(2, 'Tottenham Hotspur', 102), club(3, 'C.D. Leganés', 103, 170),
         club(4, 'C.D. Leganés C', 104, 170), club(5, 'Real Madrid C.F.', 105, 170),
         club(6, 'Real Madrid Castilla C.F.', 106, 170), club(7, 'Feeder FC', 107, 170), club(8, 'Farm Town', 108, 170)]


def test_find_loans():
    squads = {1: 1, 2: 1, 3: 4, 4: 6, 5: 1, 6: 1, 7: 8, 8: 8, 9: 8, 10: 8}
    teams = {1: 102,   # squad Getafe, contract Spurs -> loan from Spurs
             2: 101,   # contract club == squad club -> not a loan
             3: 103,   # squad Leganés C, contract Leganés (B / C team of the same club) -> NOT a loan
             4: 105,   # squad Castilla, contract Real Madrid -> NOT a loan
             5: 9999,  # contract team id unknown (hidden affiliate team) -> not a loan
             # 6 has no contract team at all -> not a loan
             7: 107, 8: 107, 9: 107, 10: 102}   # three players Farm Town <- Feeder FC = affiliate, dropped; one from Spurs stays
    assert find_loans(teams, squads, CLUBS) == {1: 2, 10: 2}, find_loans(teams, squads, CLUBS)
    assert find_loans({}, squads, CLUBS) == {} and find_loans(teams, {}, []) == {}   # no club 'team' ids / no squads


def test_transfer_status():
    saved = {'clubs': CLUBS}
    assert transfer_status({'loan_parent': 2, 'value_est': 5_000_000}, saved) == 'On loan from Tottenham Hotspur'
    assert transfer_status({'loan_parent': 777}, saved) == 'On loan'               # parent not in the club list
    assert transfer_status({'loan_parent': 2}, None) == 'On loan'
    assert transfer_status({'value_est': 300_000_000}, saved) == 'Not for sale'
    assert transfer_status({'value_est': 300_000_001}, saved) is None and transfer_status({'value_est': 0}, saved) is None
    assert transfer_status({'value_est': 5_000_000}, saved) is None               # normal player -> PENDING
    assert transfer_status({'loan_parent': 2, 'value_est': 300_000_000}, saved) == 'On loan from Tottenham Hotspur'


def person(**kw):
    p = {'id': 1, 'name': 'Test Player', 'nation': 0, 'ca': 140, 'pa': 160, 'birth_year': 2000, 'birth_day': 100,
         'positions': [1] * 15, 'raw_attrs': [60 + (i * 7) % 40 for i in range(60)], 'personality': [10] * 7,
         'trait_mask': 5, 'wage_week': 100000, 'value_est': 50_000_000, 'height_cm': 190, 'weight_kg': 80,
         'contract_end': '2030-06-30'}
    p.update(kw)
    return p


def transfer_rows(p):
    """-> (window, {row label: (right text, row visible)}) of the Transfer panel on the Contract & Transfer tab."""
    w = PlayerWindow(p, {'squads': {1: 1}, 'clubs': CLUBS}, 0, None)
    w.show()
    w._select_tab('contract')
    app.processEvents()
    page = w._stack.currentWidget()
    panel = next((f for f in page.findChildren(QFrame, 'pwPanel')
                  if any(lb.text() == 'TRANSFER' for lb in f.findChildren(QLabel, 'pwHeadT'))), None)
    rows = {}
    if panel is not None:
        for row in panel.findChildren(QFrame):
            if row.objectName() in ('pwRow', 'pwRowAlt'):
                labs = row.findChildren(QLabel)
                rows[labs[0].text()] = (labs[-1].text(), row.isVisibleTo(panel))
    return w, rows


def test_panel():
    mw._SHOW_PENDING = True
    w, rows = transfer_rows(person(value_est=300_000_000))                    # Not for sale
    assert rows['Transfer / loan status'] == ('Not for sale', True), rows
    assert rows['Market value'] == ('-', True), rows                          # no '£300M', not a PENDING chip
    assert rows['Asking price'] == ('PENDING', True), rows
    assert '300' not in ' '.join(lb.text() for lb in w._stack.currentWidget().findChildren(QLabel) if '£' in lb.text())
    assert w._vchart.curve().empty                                            # value chart: empty state, as before
    w.close()

    w, rows = transfer_rows(person(loan_parent=2))                            # on loan, parent known
    assert rows['Transfer / loan status'] == ('On loan from Tottenham Hotspur', True), rows
    assert rows['Market value'][0] == '£50M', rows
    w.close()

    w, rows = transfer_rows(person(loan_parent=4242))                         # on loan, parent not in the club list
    assert rows['Transfer / loan status'] == ('On loan', True), rows
    w.close()

    w, rows = transfer_rows(person())                                         # normal player: PENDING chip stays
    assert rows['Transfer / loan status'] == ('PENDING', True) and rows['Asking price'] == ('PENDING', True), rows
    w.close()

    mw._SHOW_PENDING = False                                                  # Settings > Show PENDING markers OFF
    try:
        w, rows = transfer_rows(person())
        assert rows['Transfer / loan status'][1] is False and rows['Asking price'][1] is False, rows
        assert rows['Market value'] == ('£50M', True), rows
        w.close()
        w, rows = transfer_rows(person(loan_parent=2))                        # real data stays visible
        assert rows['Transfer / loan status'] == ('On loan from Tottenham Hotspur', True), rows
        assert rows['Asking price'][1] is False, rows
        w.close()
        w, rows = transfer_rows(person(value_est=0))                          # nothing stored: the panel is not built
        assert rows == {}, rows
        w.close()
    finally:
        mw._SHOW_PENDING = True


def _ascii(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def test_real_counts():
    if not os.path.exists(SNAPSHOT):
        print('SKIPPED (frozen snapshot not found: ' + SNAPSHOT + '): test_transfer_status real-data counts')
        return
    from fm_editor.archive import get_member, parse_archive
    from fm_editor.clubextra import add_club_status
    from fm_editor.gamedb import (find_abilities, find_clubs, find_contract_blocks, find_names, find_people,
                                  find_squads, match_identities)
    _, members, _, _, _, _ = parse_archive(SNAPSHOT)
    b = get_member(SNAPSHOT, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, ns, ne = find_names(b)
    clubs = find_clubs(b, ns)
    add_club_status(b, clubs)
    people = find_people(b, fn, ln, ne)
    match_identities(b, people, ne)
    squads, _ = find_squads(b, clubs, ns, people)
    ab = find_abilities(b, ne)
    teams = {}
    find_contract_blocks(b, people, teams)
    loans = find_loans(teams, squads, clubs)
    by_id = {c['id']: c for c in clubs}
    nfs = [p for p, a in ab.items() if a['value_est'] == 300_000_000]
    assert len(nfs) == 2025, len(nfs)                                         # Not for sale (value 300,000,000)
    assert len(loans) == 864 and 1.5 < 100 * len(loans) / len(squads) < 2.0, (len(loans), len(squads))
    named = {(_ascii(p['name']), by_id[squads[p['id']]]['name']): by_id[loans[p['id']]]['name']
             for p in people if p.get('id') in loans}
    assert named[('mateus fernandes', 'Getafe C.F.')] == 'Tottenham Hotspur', 'Fernandes'
    assert named[('formose mendy', 'R.C.D. Mallorca')] == 'New York City FC', 'Mendy'
    assert not any(n == 'adam wharton' for n, _ in named), 'Wharton is still a Palace player in this snapshot'
    print(f'transfer status real data OK: {len(nfs)} Not for sale, {len(loans)} on loan of {len(squads)} squad players')


if __name__ == '__main__':
    test_find_loans()
    test_transfer_status()
    test_panel()
    test_real_counts()
    print('test_transfer_status OK')
