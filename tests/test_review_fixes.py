"""Regression tests for the data-safety review (record caps, backup rotation, busy lock, Squads toolbar).
Plain script: FMBR24_CONFIG_DIR=/tmp/fmx QT_QPA_PLATFORM=offscreen python3 tests/test_review_fixes.py"""
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('FMBR24_CONFIG_DIR', '/tmp/fmbr24_test_review')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from fm_editor import patch as P  # noqa: E402
from fm_editor import savefile as S  # noqa: E402
from test_savefile import build_archive, load, rd  # noqa: E402


def rec(val, b10, b11):
    return bytes([val, 0, 0, 0, 0, 0, 0, 0, 0, 0, b10, b11, 1, 255, 0, 255])


# --- 5. record scans are not capped at 40 ------------------------------------------------------------------------
FILL = rec(1, 0x00, 0x10)  # unrelated record
N = 60


def mk(idx, record):
    b = bytearray(b'\x07' * 10)
    end = len(b) + 0
    b += bytes(34) + bytes([N]) + b''.join(FILL if i != idx else record for i in range(N)) + bytes(40)
    return b, {'end': end}


b, p = mk(50, rec(P.ENGLAND_NATION_ID, 0x08, 0x46))
assert P.is_homegrown(b, p), 'HGP record at index 50 is seen'
b, p = mk(50, rec(5, 0x08, 0x46))
assert not P.is_homegrown(b, p) and P.patch_to_homegrown(b, p) and P.is_homegrown(b, p), 'rewritten in place, no insert'
assert b[p['end'] + 34] == N
b, p = mk(50, rec(5, 0x08, 0x46))
assert P.hgp_in_place(b, [p]) == [p] and P.is_homegrown(b, p)
b, p = mk(45, rec(7, 0x01, 0x48))
assert P.is_hgc(b, p, 7)
n0 = len(b)
assert P.patch_to_hgc(b, [p], 7) == 0 and len(b) == n0, 'already HGC for that club: no duplicate'
assert P.patch_to_hgc(b, [p], 9) == 1 and len(b) == n0 and b[p['end'] + 34] == N and P.is_hgc(b, p, 9), \
    'existing 0x48 beyond record 40 is rewritten, nothing inserted'
b, p = mk(55, rec(12, 0x01, 0x6a))
assert P.find_club_entity_id(b, [p]) == 12
b, p = mk(50, rec(5, 0x08, 0x46))
assert P.apply_queue(b, [(p, 'hgp')], lambda q: None) == (1, 0) and len(b) == 10 + 34 + 1 + 16 * N + 40, 'no insert'

# --- 4 / 6. savefile: backup rotation failure, lone bk2, space estimate ------------------------------------------
base = {'game_db.dat': os.urandom(50_000), 'other.bin': os.urandom(3000)}
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, 'S.fm')
    build_archive(path, base)
    orig = rd(path)
    bk1, bk2 = S.backup_paths(path)
    # 4. commit_backups raises after os.replace: save is done, warning reported, no .tmp left
    sd = load(path)
    sd['b'][5] ^= 1
    real = S.commit_backups
    S.commit_backups = lambda st: (_ for _ in ()).throw(OSError('rename boom'))
    try:
        info = S.save_in_place(sd, path)
    finally:
        S.commit_backups = real
    assert 'rename boom' in info['backup_error'], info
    assert rd(path) != orig and bytes(load(path)['b']) == bytes(sd['b']), 'the save itself was written'
    assert sorted(os.listdir(d)) == ['S.fm'], os.listdir(d)  # no .bk*.tmp, no half-rotated backups
    assert sd['disk_sig'] == S.file_signature(path)
    # 6a. lone bk2 (bk1 deleted) is the pristine original: not a first save, bk2 never overwritten
    with open(bk2, 'wb') as f:
        f.write(b'PRISTINE')
    assert S.backup_state(path) == (False, None)
    cur = rd(path)
    sd['b'][9] ^= 1
    info = S.save_in_place(sd, path)
    assert info['first'] is False and rd(bk2) == b'PRISTINE' and rd(bk1) == cur and 'backup_error' not in info
    assert sorted(os.listdir(d)) == ['S.fm', 'S.fm.bk1', 'S.fm.bk2'], os.listdir(d)
    # nothing at all -> first
    os.remove(bk1); os.remove(bk2)
    assert S.backup_state(path) == (True, None)
    # 6b. legacy bk1-<name>.fm needs 3 copies of free space
    with open(S.legacy_bk1_path(path), 'wb') as f:
        f.write(b'old')
    size = os.path.getsize(path)
    real_du = S.shutil.disk_usage
    S.shutil.disk_usage = lambda p: type('U', (), {'free': 2 * size + 16 * 1024 * 1024 + 1})()
    try:
        sd['b'][11] ^= 1
        try:
            S.save_in_place(sd, path)
            raise AssertionError('should need 3 copies')
        except S.SaveError as e:
            assert 'free disk space' in str(e)
    finally:
        S.shutil.disk_usage = real_du

# --- cache.clear_cache swallows any OSError ----------------------------------------------------------------------
from fm_editor import cache as C  # noqa: E402
real_rm = os.remove
os.remove = lambda p: (_ for _ in ()).throw(PermissionError('nope'))
try:
    C.clear_cache('/tmp/does/not/matter.fm')
finally:
    os.remove = real_rm

# --- ParseWorker puts the signature it took before reading into the result, as (size, mtime_ns) ------------------
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, 'W.fm')
    build_archive(path, {'game_db.dat': os.urandom(5000)})
    C._CACHE_DIR = os.path.join(d, 'cache')
    C.save_cache(path, [], {}, {}, [], {}, {}, {})
    from gui.workers import ParseWorker  # noqa: E402
    got = []
    wk = ParseWorker(path, True)
    wk.done.connect(got.append)
    wk.error.connect(lambda m: got.append(('error', m)))
    wk.run()
    assert got and isinstance(got[0], dict), got
    assert got[0]['disk_sig'] == S.file_signature(path), (got[0]['disk_sig'], S.file_signature(path))

# --- GUI: busy lock, unlock on failure, Squads toolbar -----------------------------------------------------------
from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402
from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402

app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)
shown = []
QMessageBox.critical = lambda *a, **k: shown.append(a[2])
H, OTHER = 6, 20  # human club id / another club id


class FakeWorker:
    started = 0

    def __init__(self, *a):
        class Sig:
            def connect(self, f): pass
        self.progress = self.pct = self.done = self.error = Sig()

    def start(self): FakeWorker.started += 1

    def wait(self): pass


M.ParseWorker = M.SaveWorker = FakeWorker


def person(i, end):
    return {'id': i, 'name': f'P{i}', 'end': end, 'ca': 100, 'pa': 120, 'nation': 0, 'birth_year': 2000,
            'birth_day': 1, 'positions': [1] * 15, 'raw_attrs': [10] * 60, 'personality': [10] * 7,
            'trait_mask': 0, 'hgp': False}


def make_window():
    # 0,1 in the human club, 2,3 in another club; HGC records carry club id + 1; a 0x6a vote disagrees (entity 99)
    b = bytearray(10)
    people = []
    for i in range(4):
        end = len(b)
        ent = (H if i < 2 else OTHER) + 1
        recs = [rec(5, 0x08, 0x46), rec(99, 0x01, 0x6a)] + ([rec(ent, 0x01, 0x48)] if i in (0, 2) else [])
        b += bytes(34) + bytes([len(recs)]) + b''.join(recs) + bytes(20)
        people.append(person(i, end))
    w = M.MainWindow()
    w._save_data = {'b': b, 'people': people, 'clubs': [{'id': H, 'name': 'Mine'}, {'id': OTHER, 'name': 'Other'}],
                    'squads': {0: H, 1: H, 2: OTHER, 3: OTHER}, 'human_clubs': {H}}
    w._save_path = '/tmp/does-not-matter.fm'
    w._squad = people
    w._table_mode = 'squad'
    return w, people


w, people = make_window()
# 3. Squads toolbar: human-club players only; HGC display = club id + 1, also for a non-human club (read-only)
w._current_club = {'id': OTHER, 'name': 'Other'}
w._populate_squad_table(people[2:])
col = {w._table.item(r, 0).text(): w._table.item(r, 9).text() for r in range(w._table.rowCount())}
assert col == {'P2': 'HGC', 'P3': ''}, col  # the entity vote (99) would have shown nothing
w._get_selected_persons = lambda: people[2:]
w._queue_selected('hgp')
w._queue_selected('hgc')
assert w.queue_count() == 0, 'players of a non-human club are never queued'
w._update_patch_btns()
assert not w._patch_hgp_btn.isEnabled() and not w._patch_hgc_btn.isEnabled()
w._get_selected_persons = lambda: people[:2]
w._update_patch_btns()
assert w._patch_hgp_btn.isEnabled() and w._patch_hgc_btn.isEnabled()
w._get_selected_persons = lambda: people  # mixed: only the human ones go in (P1 lacks HGC, P0 has it)
w._queue_selected('hgc')
assert sorted(w._queue) == [(1, 'hgc')], w._queue
w._queue.clear()
w._queue_changed()

# 1. busy lock: nothing re-enables Save / Reload / Search / nav / gear until _set_busy(False)
w._current_club = {'id': H, 'name': 'Mine'}
w._queue_selected = M.MainWindow._queue_selected.__get__(w)
w.queue_toggle(people[1], 'hgc')
w._nav_history, w._nav_pos = [(0, {}), (1, {})], 1
w._nav_back_btn_update()
assert w._save_btn.isEnabled() and w._back_btn.isEnabled() and w._settings_btn.isEnabled()
w._set_busy(True, 'Saving')
assert w._busy
w._update_ui_state()   # what Back / Forward -> _show_squad ends up calling
w._nav_back_btn_update()
w._on_selection_changed()
for btn in (w._save_btn, w._reload_btn, w._search_box, w._back_btn, w._fwd_btn, w._settings_btn, w._players_nav_btn,
            w._nav_btns['club'], w._nav_btns['squad'], w._nav_btns['shortlist'], w._patch_hgp_btn, w._patch_hgc_btn):
    assert not btn.isEnabled(), btn
FakeWorker.started = 0
w._do_save(confirm=False)
w._reload_save()
w._load_path('/tmp/other.fm')
assert FakeWorker.started == 0 and w._save_path == '/tmp/does-not-matter.fm', 'no second Save / Reload / Load while busy'
w._queue_selected('hgp')
assert (1, 'hgp') not in w._queue
w._set_busy(False)
assert not w._busy and w._save_btn.isEnabled() and w._reload_btn.isEnabled() and w._settings_btn.isEnabled()
assert w._back_btn.isEnabled() and not w._fwd_btn.isEnabled(), 'history state restored'
w._reload_save()
assert FakeWorker.started == 1 and w._busy
w._set_busy(False)

# disk_sig comes from THIS parse's result, not from shared state overwritten by a later reload
sd = {'people': [], 'clubs': [], 'squads': {}, 'sub_squads': {}, 'save_info': {}, 'human_clubs': set(),
      'employment': {}, 'club_staff': {}, 'disk_sig': (123, 456)}
w._reload_save()
w._on_parse_done(sd)
for _ in range(2000):
    app.processEvents()
    if w._save_data is sd:
        break
assert w._save_data is sd and sd['disk_sig'] == (123, 456) and not w._busy

# 2. a failing slot must not leave the lock / veil up
w._ui_snap = {'x': 1}
w._set_busy(True, 'Saving')
real_cc = M.clear_cache
M.clear_cache = lambda p: (_ for _ in ()).throw(RuntimeError('cache boom'))
w._worker, w._last_applied, w._after_save = FakeWorker(), (0, 0), None
w._reload_save = lambda use_cache=False: None
try:
    w._on_save_done({'first': False})
except RuntimeError:
    pass
finally:
    M.clear_cache = real_cc
assert not w._busy and w._main_stack.isEnabled() and not w._busy_veil.isVisible()
# backup rotation warning: the save counts as done, queue cleared, reload runs
w._set_busy(True, 'Saving')
w._queue_selected  # (queue empty) nothing pending
w._after_reload_status = None
reloaded = []
w._reload_save = lambda use_cache=False: reloaded.append(1)
w._on_save_done({'first': False, 'backup_error': 'rename boom'})
assert reloaded == [1] and w._after_reload_status.startswith('Saved ') and 'backup rotation failed: rename boom' in w._after_reload_status
assert not w._busy and not w._dirty
# preload done() throwing -> error shown, unlocked
w._set_busy(True, 'Parsing save file')
shown.clear()
def bad_done(): raise RuntimeError('finish boom')
w._preload_gen += 1
w._step_preload(iter(()), w._preload_gen, bad_done)
assert not w._busy and shown and 'finish boom' in shown[0], shown
# _finish_load throwing midway
w._set_busy(True, 'Parsing save file')
w._land_after_load = lambda: (_ for _ in ()).throw(RuntimeError('land boom'))
w._ui_snap = None
try:
    w._finish_load(dict(sd, disk_sig=None))
except RuntimeError:
    pass
assert not w._busy
# an error clears the one-shot post-save status
w._after_reload_status = 'Saved X'
w._on_error('boom')
assert w._after_reload_status is None and not w._busy
print('OK: record scans, backup rotation failure, lone bk2, space estimate, busy lock, unlock on failure, Squads gating')
