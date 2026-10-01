"""Homegrown QUEUE (HGP/HGC pills + Squads buttons queue, Save Changes applies): queue model, safe apply order on a
synthetic game_db, save-applies-queue end to end on a synthetic archive (re-parse shows both flags, backups, auto
reload), failure injection leaves the file byte-identical, player-window pill states, action strip.
Plain script: python3 tests/test_patch_queue.py (no real save needed)."""
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('FMBR24_CONFIG_DIR', '/tmp/fmbr24_test_queue')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from PyQt6.QtCore import QEventLoop, QTimer  # noqa: E402
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.player_window import PlayerWindow  # noqa: E402
from fm_editor import patch as P  # noqa: E402
from fm_editor import savefile as S  # noqa: E402
from fm_editor.patch import ENGLAND_NATION_ID, is_hgc, is_homegrown  # noqa: E402
from test_savefile import build_archive, load, rd  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
CLUB = 7  # club entity id (club id 6 + 1)


def rec(nation, b10, b11):
    return bytes([nation, 0, 0, 0, 0, 0, 0, 0, 0, 0, b10, b11, 1, 255, 0, 255])


HGP_NEEDED = rec(5, 0x08, 0x46)
HGP_DONE = rec(ENGLAND_NATION_ID, 0x08, 0x46)
HGC_DONE = rec(CLUB, 0x01, 0x48)
PAD = 40
# 0 neither, 1 HGP only, 2 HGC only (and HGP needed), 3 both, 4 neither
LAYOUTS = [[HGP_NEEDED], [HGP_DONE], [HGP_NEEDED, HGC_DONE], [HGP_DONE, HGC_DONE], [HGP_NEEDED]]


def build(layouts):
    b = bytearray(b'\x07' * 100)  # leading filler so the archive member is not trivially small
    people = []
    for i, recs in enumerate(layouts):
        end = len(b) + 10
        b += bytes(10 + 34) + bytes([len(recs)]) + b''.join(recs) + bytes(PAD)
        people.append({'id': i, 'name': f'P{i}', 'end': end, 'hgp': False, 'ca': 100, 'pa': 120, 'nation': 0,
                       'birth_year': 2000, 'birth_day': 1, 'positions': [1] * 15, 'raw_attrs': [10] * 60,
                       'personality': [10] * 7, 'trait_mask': 0})
    for p in people:
        p['hgp'] = is_homegrown(b, p)
    return b, people


def relocate(layouts, b, inserted=None):
    """Person offsets after the inserts (a record block grows by 16 bytes when HGC was added)."""
    ends, pos = [], 100
    for i, recs in enumerate(layouts):
        ends.append(pos + 10)
        pos += 10 + 34 + 1 + 16 * (len(recs) + (1 if (i in inserted if inserted is not None else not any(r[11] == 0x48 for r in recs)) else 0)) + PAD
    return [{'end': e} for e in ends]


# --- 1. apply_queue on a synthetic buffer ----------------------------------------------------------------------
b, people = build(LAYOUTS)
size0 = len(b)
ent = lambda p: CLUB  # noqa: E731
# queue given HGC first, then HGP, in scrambled order: the apply order must not depend on it
queue = [(people[4], 'hgc'), (people[2], 'hgc'), (people[0], 'hgc'), (people[1], 'hgc'), (people[3], 'hgc'),
         (people[4], 'hgp'), (people[0], 'hgp'), (people[2], 'hgp'), (people[1], 'hgp')]
calls = []
real_hgc = P.patch_to_hgc
P.patch_to_hgc = lambda b_, ps, e: calls.append(ps[0]['end']) or real_hgc(b_, ps, e)
real_hip = P.hgp_in_place
P.hgp_in_place = lambda b_, ps: calls.append('HGP') or real_hip(b_, ps)
try:
    n_hgp, n_hgc = P.apply_queue(b, queue, ent)
finally:
    P.patch_to_hgc, P.hgp_in_place = real_hgc, real_hip
assert calls[0] == 'HGP' and calls[1:] == sorted(calls[1:], reverse=True), calls  # HGP first, inserts descending
assert len(calls) == 1 + 3, 'HGC inserted for P0, P1, P4 only; P2 / P3 already had it'
assert (n_hgp, n_hgc) == (3, 3), (n_hgp, n_hgc)  # P1 already HGP, P3 not queued for HGP
assert len(b) == size0 + 3 * 16
moved = relocate(LAYOUTS, b)
assert all(is_hgc(b, p, CLUB) for p in moved), 'HGC on everyone (offsets correct after the inserts)'
assert [is_homegrown(b, p) for p in moved] == [True, True, True, True, True], 'HGP: queued ones now set, others already'
# partial: HGC only for one player leaves HGP untouched
b2, people2 = build(LAYOUTS)
assert P.apply_queue(b2, [(people2[4], 'hgc')], ent) == (0, 1)
m2 = relocate(LAYOUTS, b2, {4})
assert is_hgc(b2, m2[4], CLUB) and not is_homegrown(b2, m2[4]) and not is_hgc(b2, m2[0], CLUB)
# unknown club -> skipped
b3, people3 = build(LAYOUTS)
assert P.apply_queue(b3, [(people3[0], 'hgc')], lambda p: None) == (0, 0) and bytes(b3) == bytes(build(LAYOUTS)[0])

# --- 2. main-window queue model ---------------------------------------------------------------------------------
seen = []
QMessageBox.information = lambda *a, **k: seen.append(('info', a[1:]))
QMessageBox.critical = lambda *a, **k: seen.append(('critical', a[1:]))


def new_window(b, people, path='/tmp/does-not-matter.fm'):
    w = M.MainWindow()
    w._save_data = {'b': b, 'people': people, 'squads': {p['id']: CLUB - 1 for p in people}, 'clubs': [],
                    'human_clubs': {CLUB - 1}}
    w._save_path = path
    w._squad = people
    w._club_entity_id = CLUB
    return w


b, people = build(LAYOUTS)
orig_bytes = bytes(b)
w = new_window(b, people)
assert not w._dirty and w.queue_count() == 0
w.queue_toggle(people[0], 'hgp')
w.queue_toggle(people[0], 'hgc')   # HGC without HGP is fine; no auto-queue of the other part
assert w.queue_has(people[0], 'hgp') and w.queue_has(people[0], 'hgc') and w.queue_count() == 2
assert w._dirty and w._pending == ['HGP: 1 player(s)', 'HGC: 1 player(s)'], w._pending
assert w._save_btn.isEnabled() and 'Unsaved' in w._sb_status.text()
assert bytes(b) == orig_bytes, 'queueing never touches the game_db bytes'
w.queue_toggle(people[0], 'hgp')   # undo
assert not w.queue_has(people[0], 'hgp') and w.queue_count() == 1 and w._dirty
w.queue_toggle(people[0], 'hgc')
assert w.queue_count() == 0 and not w._dirty and w._pending == [] and not w._save_btn.isEnabled()
# Squads buttons queue the selection (no confirm dialog), skipping players that already have the flag
w._get_selected_persons = lambda: people
w._queue_selected('hgp')
assert sorted(pid for pid, k in w._queue if k == 'hgp') == [0, 2, 4], 'P1, P3 already HGP'
w._queue_selected('hgc')
assert sorted(pid for pid, k in w._queue if k == 'hgc') == [0, 1, 4], 'P2, P3 already HGC'
assert not hasattr(w, '_patch_both_btn') and not hasattr(w, '_do_patch_both') and not hasattr(w, '_patch_allowed')
it = M._SortItem('')
M._hg_apply(it, 'hgp', False, True)
assert (it.text(), it.data(M.HG_ROLE)) == ('+ HGP', 'queued')
M._hg_apply(it, 'hgc', True, False)
assert (it.text(), it.data(M.HG_ROLE)) == ('HGC', 'set')
w._queue.clear()
w._queue_changed()

# --- 3. Save applies the queue (synthetic archive), re-parse shows the flags, backups, auto reload ------------------
def wait(cond, ms=20000):
    loop = QEventLoop()
    t = QTimer()
    t.timeout.connect(lambda: loop.quit() if cond() else None)
    t.start(20)
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    t.stop()
    assert cond(), 'timed out'


def archive_window(d, tag):
    b, people = build(LAYOUTS)
    path = os.path.join(d, f'{tag}.fm')
    build_archive(path, {'game_db.dat': bytes(b), 'other.bin': os.urandom(5000)})
    w = new_window(None, people, path)
    sd = load(path)
    assert bytes(sd['b']) == bytes(b)
    sd.update(people=people, squads=w._save_data['squads'], clubs=[], human_clubs={CLUB - 1})
    w._save_data = sd
    w._squad = people
    return w, people, path


with tempfile.TemporaryDirectory() as d:
    w, people, path = archive_window(d, 'ok')
    reloads = []
    w._reload_save = lambda use_cache=False: reloads.append(1)   # the real one re-parses; stubbed here
    before = rd(path)
    for p, k in ((people[4], 'hgc'), (people[0], 'hgc'), (people[0], 'hgp'), (people[1], 'hgc'), (people[4], 'hgp')):
        w.queue_toggle(p, k)   # HGC queued before HGP on purpose
    assert w.queue_count() == 5
    w._do_save(confirm=False)
    wait(lambda: reloads)
    assert reloads == [1], 'save is followed by exactly one automatic reload'
    assert w._queue == {} and not w._dirty
    assert w._after_reload_status.endswith('HGP 2, HGC 3') and w._after_reload_status.startswith('Saved ok.fm'), \
        w._after_reload_status
    bk1, bk2 = S.backup_paths(path)
    assert rd(bk1) == before and rd(bk2) == before, 'first save: both backups = the original'
    nb = load(path)['b']
    moved = relocate(LAYOUTS, nb)
    assert [is_homegrown(nb, p) for p in moved] == [True, True, False, True, True], 'only the queued HGP (P0, P4) added'
    assert [is_hgc(nb, p, CLUB) for p in moved] == [True, True, True, True, True]
    assert len(nb) == len(build(LAYOUTS)[0]) + 3 * 16
    # a second save rotates the backups
    w2 = None

# --- 4. failure injection: the file on disk stays byte-identical -------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    w, people, path = archive_window(d, 'bad')
    reloads = []
    w._reload_save = lambda use_cache=False: reloads.append(1)
    before, buf_before = rd(path), bytes(w._save_data['b'])
    for p, k in ((people[0], 'hgp'), (people[0], 'hgc'), (people[1], 'hgc'), (people[4], 'hgc')):
        w.queue_toggle(p, k)
    # (a) the apply step dies midway (second HGC insert)
    n = []
    real = P.patch_to_hgc
    P.patch_to_hgc = lambda b_, ps, e: (n.append(1), real(b_, ps, e))[1] if len(n) < 1 else (_ for _ in ()).throw(
        RuntimeError('boom'))
    seen.clear()
    try:
        w._do_save(confirm=False)
    finally:
        P.patch_to_hgc = real
    assert seen and seen[0][0] == 'critical' and 'could not apply the queued changes' in seen[0][1][1], seen
    assert rd(path) == before, 'file untouched'
    assert bytes(w._save_data['b']) == buf_before, 'in-memory buffer restored (never touched)'
    assert w.queue_count() == 4 and w._dirty and not reloads
    assert [x for x in os.listdir(d)] == ['bad.fm'], os.listdir(d)   # no tmp, no backups
    # (b) the write/verify step dies in the worker thread
    real_v = S.verify_archive
    S.verify_archive = lambda *a, **k: (_ for _ in ()).throw(S.SaveError('verify boom'))
    seen.clear()
    try:
        w._do_save(confirm=False)
        wait(lambda: seen)
    finally:
        S.verify_archive = real_v
    assert 'verify boom' in str(seen[0]) and rd(path) == before
    assert w.queue_count() == 4 and w._dirty and bytes(w._save_data['b']) == buf_before and not reloads
    assert os.listdir(d) == ['bad.fm'], os.listdir(d)
    # (c) retry succeeds with the queue still intact
    w._do_save(confirm=False)
    wait(lambda: reloads)
    assert rd(path) != before and w.queue_count() == 0

# --- 5. player window: pills = controls, strip = Add to Shortlist + Close ----------------------------------------
b, people = build(LAYOUTS)
w = new_window(b, people)


def pw(person, can=True, **kw):
    win = PlayerWindow(person, w._save_data, kw.pop('ent', CLUB), None, can_patch=can, queue=w, **kw)
    w._pw_open = win
    win.show()
    app.processEvents()
    return win


def pill(win, k):
    return win._pill_btns[k]


win = pw(people[0])   # neither set, patchable
assert [(pill(win, k).text(), pill(win, k).property('state')) for k in ('hgp', 'hgc')] == [('HGP', 'go'), ('HGC', 'go')]
assert pill(win, 'hgp').toolTip() == 'Click to make HGP'
assert win._q_n.text() == '0' and win._q_s.text() == 'Nothing queued'
pill(win, 'hgc').click()   # HGC queued without HGP
assert pill(win, 'hgc').text() == '+ HGC' and pill(win, 'hgc').property('state') == 'queued'
assert pill(win, 'hgp').property('state') == 'go' and pill(win, 'hgc').toolTip() == 'Queued - click to undo'
assert w.queue_has(people[0], 'hgc') and w._dirty and win._q_n.text() == '1' and win._q_s.text() == 'Save to take effect'
assert win.isVisible(), 'the window stays open'
pill(win, 'hgc').click()   # undo
assert pill(win, 'hgc').property('state') == 'go' and not w._dirty and win._q_n.text() == '0'
# queue changed elsewhere (Squads buttons / another player) shows live in the open window
w.queue_toggle(people[4], 'hgp')
assert win._q_n.text() == '1' and win._q_s.text() == 'Save to take effect' and 'elsewhere' in win._q_w.toolTip()
w.queue_toggle(people[4], 'hgp')
# strip: Add to Shortlist + Close only (no Make buttons)
strip = [x.text() for x in win.findChildren(QPushButton) if x.parentWidget().objectName() == 'actionStrip']
assert strip == ['Add to Shortlist', 'Close'], strip
win.close()
# SET pills: lit, not clickable
win = pw(people[3])
assert [pill(win, k).property('state') for k in ('hgp', 'hgc')] == ['set', 'set']
pill(win, 'hgp').click()
pill(win, 'hgc').click()
assert w.queue_count() == 0
win.close()
# HGP set, HGC not: HGC clickable
win = pw(people[1])
assert [pill(win, k).property('state') for k in ('hgp', 'hgc')] == ['set', 'go']
win.close()
# not patchable: display-only with the tooltip
for tip in ('Not your club', 'Open from Squads to patch'):
    win = pw(people[0], can=False, patch_tip=tip)
    assert [pill(win, k).property('state') for k in ('hgp', 'hgc')] == ['plain', 'plain']
    assert pill(win, 'hgp').toolTip() == tip
    pill(win, 'hgp').click()
    assert w.queue_count() == 0
    win.close()
# club unknown: the HGC pill is hidden (no '?'), HGP stays clickable
win = pw(people[0], ent=0)
assert pill(win, 'hgc').property('state') == 'unk' and pill(win, 'hgc').isHidden() and '?' not in pill(win, 'hgc').text()
pill(win, 'hgc').click()
assert w.queue_count() == 0
pill(win, 'hgp').click()
assert w.queue_has(people[0], 'hgp')
win.close()
w._pw_open = None
print('OK: queue model, safe apply order, save applies queue + reload + backups, failure leaves file identical, pills, strip')
