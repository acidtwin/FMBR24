"""Make HGP + HGC (combined) on a synthetic game_db buffer, the player-window button, and the stale-offsets
'Save and reload' flow. Plain script: python3 tests/test_patch_both.py (no save needed)."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('FMBR24_CONFIG_DIR', '/tmp/fmbr24_test_both')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.player_window import PlayerWindow  # noqa: E402
from fm_editor.patch import ENGLAND_NATION_ID, is_hgc, is_homegrown  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
CLUB = 7


def rec(nation, b10, b11):
    return bytes([nation, 0, 0, 0, 0, 0, 0, 0, 0, 0, b10, b11, 1, 255, 0, 255])


HGP_NEEDED = rec(5, 0x08, 0x46)             # HGP record with a non-England nation
HGP_DONE = rec(ENGLAND_NATION_ID, 0x08, 0x46)
HGC_DONE = rec(CLUB, 0x01, 0x48)
PAD = 40


def build(layouts):
    """layouts: list of record lists -> (bytearray, persons). Person i: end -> count byte at end+34."""
    b = bytearray()
    people = []
    for i, recs in enumerate(layouts):
        end = len(b) + 10
        b += bytes(10 + 34) + bytes([len(recs)]) + b''.join(recs) + bytes(PAD)
        people.append({'id': i, 'name': f'P{i}', 'end': end, 'hgp': False})
    return b, people


def new_window(b, people):
    w = M.MainWindow()
    w._save_data = {'b': b, 'people': people}
    w._save_path = '/tmp/does-not-matter.fm'
    w._squad = people
    w._club_entity_id = CLUB
    w._confirm_patch_dialog = lambda p, label: seen.append((label, [x['name'] for x in p])) or True
    return w


seen = []
QMessageBox.information = lambda *a, **k: seen.append(('info', a[1:]))  # no modal boxes in a test

# 0 neither, 1 HGP only, 2 HGC only, 3 both, 4 neither (inserted last in file order: offsets must stay valid)
layouts = [[HGP_NEEDED], [HGP_DONE], [HGP_NEEDED, HGC_DONE], [HGP_DONE, HGC_DONE], [HGP_NEEDED]]
b, people = build(layouts)
for p in people:
    p['hgp'] = is_homegrown(b, p)
assert [p['hgp'] for p in people] == [False, True, False, True, False]
assert [is_hgc(b, p, CLUB) for p in people] == [False, False, True, True, False]
size0 = len(b)

w = new_window(b, people)
w._do_patch_both(people)
assert seen[0] == ('HGP + HGC', ['P0', 'P1', 'P2', 'P4']), seen[0]   # P3 already has both: not offered
assert len(seen) == 2 and seen[1][0] == 'info', 'one confirm + one outcome'
assert len(b) == size0 + 3 * 16, 'inserts for P0, P1, P4 only (P2 had an HGC record already)'
assert w._save_data['offsets_stale'] and w._dirty and w._pending == ['HGP + HGC: 4 player(s)'], w._pending
# offsets moved: re-locate each person by walking the buffer, then check both flags
ends, pos = [], 0
for recs in layouts:
    ends.append(pos + 10)
    pos += 10 + 34 + 1 + 16 * (len(recs) + (0 if any(r[11] == 0x48 for r in recs) else 1)) + PAD
moved = [{'end': e} for e in ends]
assert all(is_homegrown(b, p) for p in moved), 'HGP on everyone'
assert all(is_hgc(b, p, CLUB) for p in moved), 'HGC on everyone'

# nothing to do: no dialog change, nothing dirty
seen.clear()
b2, people2 = build([[HGP_DONE, HGC_DONE]])
people2[0]['hgp'] = True
w2 = new_window(b2, people2)
w2._do_patch_both(people2)
assert seen == [('info', ('Nothing to patch', 'All selected players are already HGP and HGC.'))] and not w2._dirty

# stale offsets -> question, 'Save and reload' saves (dirty) then reloads, no auto-repeat of the patch
calls = []
w._do_save = lambda after=None, confirm=True: calls.append(('save', confirm)) or after()
w._reload_save = lambda use_cache=False: calls.append('reload')
QMessageBox.exec = lambda self: 0
QMessageBox.clickedButton = lambda self: next(x for x in self.buttons() if x.text() == 'Save and reload')
seen.clear()
w._do_patch_both(people)
assert calls == [('save', False), 'reload'] and seen == [], (calls, seen)
assert 'again' in w._after_reload_msg
# Cancel: nothing happens
calls.clear()
QMessageBox.clickedButton = lambda self: next(x for x in self.buttons() if x.text() == 'Cancel')
assert w._patch_allowed() is False and calls == []
# stale but clean (saved already): straight to reload
w._dirty = False
QMessageBox.clickedButton = lambda self: next(x for x in self.buttons() if x.text() == 'Save and reload')
assert w._patch_allowed() is False and calls == ['reload']

# toolbar button exists and is wired
assert w._patch_both_btn.text() == 'Make both'


# player window: Make both before Add to Shortlist, Close last; click emits mode 'both'
def pw(hgp, hgc_known, club_hgc):
    b3, p3 = build([[HGP_DONE if hgp else HGP_NEEDED] + ([HGC_DONE] if club_hgc else [])])
    p3[0].update(hgp=hgp, ca=100, pa=120, nation=0, birth_year=2000, birth_day=1, positions=[1] * 15,
                 raw_attrs=[10] * 60, personality=[10] * 7, trait_mask=0)
    return PlayerWindow(p3[0], {'squads': {}, 'clubs': [], 'b': b3}, CLUB if hgc_known else 0, None, can_patch=True)


win = pw(False, True, False)
texts = [x.text() for x in win.findChildren(QPushButton) if x.parentWidget().objectName() == 'actionStrip']
assert texts == ['Make HGP', 'Make HGC', 'Make both', 'Add to Shortlist', 'Close'], texts
both = next(x for x in win.findChildren(QPushButton) if x.text() == 'Make both')
assert both.isEnabled()
both.click()
assert win._patch_mode == 'both'
# partial / unknown / done states: disabled
for args, label in (((True, True, False), 'Make both'), ((False, True, True), 'Make both'),
                    ((False, False, False), 'Make both'), ((True, True, True), 'HGP + HGC set')):
    x = next(x for x in pw(*args).findChildren(QPushButton) if x.text() == label)
    assert not x.isEnabled(), (args, label)
print('OK: combined HGP + HGC (partial players, one confirm, offsets), stale-offset save+reload flow, player window button')
