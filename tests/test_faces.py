"""Face pictures: synthetic facepacks (config.xml layout + folder-per-id layout), priority, settings, cache, Qt layer.
Plain script: FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_faces.py
The real-pack check at the end prints SKIPPED when the user's FM24 folder is absent. Temp dirs only; the game folder is
never written to."""
import json
import os
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
tmp = tempfile.mkdtemp(prefix='fmbr24_faces_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')
os.environ.pop('FMBR24_FM_DIR', None)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtGui import QColor, QImage  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
from fm_editor import cache, faces, settings  # noqa: E402

cache_dir = os.path.join(tmp, 'cache')


def png(path, w=260, h=310, ext=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = QImage(w, h, QImage.Format.Format_ARGB32)
    im.fill(QColor(200, 120, 60))
    assert im.save(path, ext or ('JPG' if path.lower().endswith(('.jpg', '.jpeg')) else 'PNG')), path


def rec(frm, key):
    return f'<record from="{frm}" to="graphics/pictures/person/{key}/portrait"/>\n'


# ---------------------------------------------------------------- synthetic FM24 folder
fm = os.path.join(tmp, 'Football Manager 2024')
g = os.path.join(fm, 'graphics')
A = os.path.join(g, 'A Pack')          # config.xml layout
B = os.path.join(g, 'B Pack')          # folder-per-id layout (no config.xml)
L = os.path.join(g, 'Logos')           # not a facepack
for n in (100, 200, 400):
    png(os.path.join(A, f'{n}.png'))
png(os.path.join(A, '250.PNG'))                       # upper-case extension (real DF11 has 82 of these)
png(os.path.join(A, '300.jpg'))
png(os.path.join(A, '400.2.png'))                     # stem with a dot: from="400.2"
png(os.path.join(A, 'r500.png'))                      # newgen key r-500 from file r500
png(os.path.join(A, 'sub', '600.png'))                # from="sub/600"
png(os.path.join(A, 'AT&T.png'))                      # from="AT&amp;T"
with open(os.path.join(A, 'config.xml'), 'w') as f:
    f.write('<record>\n<boolean id="amap" value="false"/>\n<list id="maps">\n')
    f.write(rec('100', '100') + rec('200', '200') + rec('250', '250') + rec('300', '300') + rec('400.2', '400'))
    f.write(rec('r500', 'r-500') + rec('sub/600', '600') + rec('AT&amp;T', '800') + rec('999', '999'))  # 999: file missing
    f.write('</list>\n</record>\n')
png(os.path.join(B, 'pictures', 'person', '100', 'portrait.png'))   # duplicate of A's 100
png(os.path.join(B, 'pictures', 'person', '700', 'portrait.png'))
png(os.path.join(B, 'pictures', 'person', '701', 'portrait.jpg'))
os.makedirs(L)
with open(os.path.join(L, 'config.xml'), 'w') as f:
    f.write('<record><list id="maps"><record from="1" to="graphics/pictures/clubs/1/icon"/></list></record>')

# ---------------------------------------------------------------- discovery
assert faces.is_facepack(A) and faces.is_facepack(B) and not faces.is_facepack(L)
assert [p.name for p in faces.discover_packs(fm)] == ['A Pack', 'B Pack']                      # alphabetical default
assert [p.name for p in faces.discover_packs(fm, ['B Pack'])] == ['B Pack', 'A Pack']          # user order first
assert [p.name for p in faces.discover_packs(os.path.join(tmp, 'nope'))] == []

# ---------------------------------------------------------------- resolution (both layouts, priority, misses)
idx = faces.FaceIndex(fm, cache_dir=cache_dir)
assert idx.path(100) is None and not idx.ready          # not loaded: never blocks, never raises
idx.load()
assert idx.ready and [p.name for p in idx.packs] == ['A Pack', 'B Pack']

def rel(uid, i=idx):
    p = i.path(uid)
    return os.path.relpath(p, g) if p else None


assert rel(100) == os.path.join('A Pack', '100.png')                    # priority: alphabetical, A before B
assert rel(200) == os.path.join('A Pack', '200.png')
assert rel(250) == os.path.join('A Pack', '250.PNG')                    # case-insensitive extension
assert rel(300) == os.path.join('A Pack', '300.jpg')
assert rel(400) == os.path.join('A Pack', '400.2.png')                  # from != id
assert rel(500) == os.path.join('A Pack', 'r500.png')                   # r-<uid> newgen key
assert rel(600) == os.path.join('A Pack', 'sub', '600.png')
assert rel(800) == os.path.join('A Pack', 'AT&T.png')                   # XML-escaped from
assert rel(700) == os.path.join('B Pack', 'pictures', 'person', '700', 'portrait.png')   # folder-per-id layout
assert rel(701).endswith('portrait.jpg')
assert rel(999) is None and rel(123456) is None and rel(0) is None and rel(None) is None     # missing file / unknown
idx_b = faces.FaceIndex(fm, ['B Pack'], cache_dir=os.path.join(tmp, 'cache2'))
idx_b.load()
assert rel(100, idx_b) == os.path.join('B Pack', 'pictures', 'person', '100', 'portrait.png')   # setting order wins
os.remove(os.path.join(A, '200.png'))
assert idx.path(200) is None                                             # file vanished after indexing: None, no crash
png(os.path.join(A, '200.png'))

# ---------------------------------------------------------------- disk cache
fidx = [f for f in os.listdir(cache_dir) if f.endswith('.fidx')]
assert len(fidx) == 2 and not [f for f in os.listdir(cache_dir) if f.endswith('.json')], os.listdir(cache_dir)   # not *.json: Clear cache keeps them
faces.FaceIndex(fm, cache_dir=cache_dir).load()                          # the delete / re-create above touched the folder: re-cache
real_build = faces._build_pack
faces._build_pack = lambda *a, **k: (_ for _ in ()).throw(AssertionError('rebuilt despite a valid cache'))
c2 = faces.FaceIndex(fm, cache_dir=cache_dir)
c2.load()
assert rel(250, c2) == os.path.join('A Pack', '250.PNG') and c2.count() == idx.count()
faces._build_pack = real_build
time.sleep(0.01)
with open(os.path.join(A, 'config.xml'), 'a') as f:                      # config changed -> signature differs -> rebuilt
    f.write('<!-- touched -->')
built = []
faces._build_pack = lambda *a, **k: built.append(1) or real_build(*a, **k)
faces.FaceIndex(fm, cache_dir=cache_dir).load()
assert built == [1], built                                               # only A rebuilt, B still cached
faces._build_pack = real_build
open(os.path.join(cache_dir, fidx[0]), 'w').write('{corrupt')            # corrupt cache -> rebuilt, no crash
faces.FaceIndex(fm, cache_dir=cache_dir).load()

# ---------------------------------------------------------------- FM dir discovery
assert faces.find_fm_dir('/definitely/not/here') is None                 # explicit but wrong: not silently auto-detected
assert faces.find_fm_dir(fm) == fm
os.environ['FMBR24_FM_DIR'] = fm
assert faces.find_fm_dir('/definitely/not/here') == fm                   # env wins over Settings
os.environ['FMBR24_FM_DIR'] = '/nope'
assert faces.find_fm_dir(fm) is None
del os.environ['FMBR24_FM_DIR']
os.makedirs(os.path.join(fm, 'games'), exist_ok=True)
assert faces.find_fm_dir('', os.path.join(fm, 'games', 's.fm')) == fm    # derived from the loaded save
assert all(c.endswith(os.path.join('Sports Interactive', 'Football Manager 2024')) for c in faces.candidate_dirs())
fm_st, names = faces.status(fm)
assert fm_st == fm and names == ['A Pack', 'B Pack']

# ---------------------------------------------------------------- settings: defaults, validation, reset, enabled flag
d = settings.DEFAULTS
assert d['faces_enabled'] is True and d['faces_dir'] == '' and d['faces_pack_order'] == []
assert settings.load() == d
os.makedirs(settings.config_dir(), exist_ok=True)
json.dump({'faces_enabled': 'yes', 'faces_dir': 5, 'faces_pack_order': [1, 2]}, open(settings.settings_path(), 'w'))
assert settings.load()['faces_enabled'] is True and settings.load()['faces_dir'] == '' and settings.load()['faces_pack_order'] == []
assert settings.save({'faces_enabled': False, 'faces_dir': fm, 'faces_pack_order': ['B Pack']})
assert settings.load()['faces_enabled'] is False and settings.load()['faces_pack_order'] == ['B Pack']
settings.load()['faces_pack_order'].append('x')
assert settings.load()['faces_pack_order'] == ['B Pack'] and settings.DEFAULTS['faces_pack_order'] == []   # no shared list

# disabled -> None everywhere (club badges share the index: both switches off)
assert settings.save({'logos_enabled': False, 'flags_enabled': False})
assert faces.configure(cache_dir=cache_dir) is None
assert faces.ensure_loaded() is None and faces.face_path(100) is None
# enabled + dir -> resolves (blocking load only via ensure_loaded), kind other than person -> None
assert settings.save({'faces_enabled': True, 'logos_enabled': True, 'faces_dir': fm, 'faces_pack_order': []})
assert faces.configure(cache_dir=cache_dir) is not None
assert faces.face_path(100) is None                                      # configured but not loaded yet: never blocks
faces.ensure_loaded()
assert faces.face_path(100).endswith(os.path.join('A Pack', '100.png'))
assert faces.face_path(100, 'staff') is None and faces.face_path(0) is None and faces.face_path(None) is None

# ---------------------------------------------------------------- parse cache keeps the identity uid
cache._CACHE_DIR = os.path.join(tmp, 'pcache')
sv = os.path.join(tmp, 's.fm')
open(sv, 'wb').write(b'x')
cache.save_cache(sv, [], {}, {}, [{'id': 1, 'uid': 67268221, 'name': 'A', 'nation': 1, 'birth_year': 2000, 'end': 5, 'offset': 1},
                                 {'id': 2, 'name': 'B', 'nation': 1, 'birth_year': 2000, 'end': 5, 'offset': 1}])
pp = cache.load_cache(sv)['people']
assert pp[0]['uid'] == 67268221 and 'uid' not in pp[1]

# ---------------------------------------------------------------- Qt layer: pixmaps, DPR, crop, LRU bound
from gui import faces as gf  # noqa: E402

svc = gf.FaceService()
fired = []
svc.ready.connect(lambda: fired.append(1))
svc.start()                                                              # background load
t0 = time.time()
while svc.loading() and time.time() - t0 < 10:
    app.processEvents()
    time.sleep(0.01)
app.processEvents()
assert fired == [1], fired
px = svc.pixmap(100, 54, 64, 1.0, radius=3)
assert px is not None and (px.width(), px.height()) == (54, 64)
assert QImage(px.toImage()).pixelColor(27, 32).red() == 200              # picture drawn
assert px.toImage().pixelColor(0, 0).alpha() < 60                        # radius-3 corner is (almost) transparent
px2 = svc.pixmap(100, 54, 64, 2.0, radius=3)
assert (px2.width(), px2.height()) == (108, 128) and px2.devicePixelRatio() == 2.0   # DPR aware
png(os.path.join(tmp, 'sq.png'), 256, 256)                               # NEWGAN-style square fills the 54x64 box (crops, never distorts)
sqpx = gf._render(os.path.join(tmp, 'sq.png'), 54, 64, 1.0, 0, False)
assert (sqpx.width(), sqpx.height()) == (54, 64) and sqpx.toImage().pixelColor(0, 63).alpha() == 255
assert svc.pixmap(999, 54, 64) is None and svc.pixmap(None, 54, 64) is None
fit = svc.pixmap(100, 190, 119, 1.0, fit=True)
assert fit is not None and (fit.width(), fit.height()) == (190, 119)
assert fit.toImage().pixelColor(0, 60).alpha() == 0 and fit.toImage().pixelColor(95, 60).alpha() == 255   # letterboxed, centred
gf.LRU_SIZE = 3
svc._lru.clear()
for w in range(40, 50):
    svc.pixmap(100, w, 64)
assert len(svc._lru) == 3, len(svc._lru)
svc.pixmap(100, 49, 64)                                                  # hit keeps it fresh
assert list(svc._lru)[-1][1] == 49
gf.LRU_SIZE = 256

# ---------------------------------------------------------------- PlayerWindow: with a face, without, then the face arrives
from gui import player_window as pw  # noqa: E402
gf._service = svc


def person(uid):
    pos = [1] * 15
    pos[3] = 20
    return {'id': 1, 'uid': uid, 'name': 'Test Player', 'nation': 0, 'ca': 140, 'pa': 160, 'birth_year': 2000, 'birth_day': 100,
            'positions': pos, 'raw_attrs': [60 + (i * 7) % 40 for i in range(60)], 'personality': [10] * 7, 'trait_mask': 0}


w_face = pw.PlayerWindow(person(100), {'squads': {}, 'clubs': []}, 0, None)
w_none = pw.PlayerWindow(person(123456), {'squads': {}, 'clubs': []}, 0, None)
w_nouid = pw.PlayerWindow({'id': 1, 'name': 'No uid', 'nation': 0}, {'squads': {}, 'clubs': []}, 0, None)
for w, face in ((w_face, True), (w_none, False), (w_nouid, False)):
    assert w._avatar.size().width() == 54 and w._avatar.size().height() == 64
    got = w._avatar.pixmap().toImage()
    is_face = got.size().width() == 54 and got.pixelColor(27, 32).red() == 200   # silhouette pixmap is 30x30
    assert is_face == face, (w._person['name'], is_face)
w_none.close(); w_nouid.close(); w_face.close()
# face off in Settings -> silhouette
settings.save({'faces_enabled': False})
svc.start()
app.processEvents()
w_off = pw.PlayerWindow(person(100), {'squads': {}, 'clubs': []}, 0, None)
assert w_off._avatar.pixmap().toImage().size().width() == 30      # silhouette
w_off.close()
settings.save({'faces_enabled': True})

# ---------------------------------------------------------------- Settings page rows: defaults + Reset
from gui.settings_page import SettingsPage  # noqa: E402
page = SettingsPage()
v = page._values()
assert v['faces_enabled'] is True and v['faces_dir'] == fm          # read from the saved settings
page._faces_on.setChecked(False)
page._faces_dir.setText(fm)
assert page._values()['faces_enabled'] is False and page._values()['faces_dir'] == fm
assert page._faces_state == 'ok' and 'Found 2 facepacks' in page._faces_msg.text(), page._faces_msg.text()
page._faces_dir.setText(os.path.join(tmp, 'missing'))
assert page._faces_state == 'missing' and not page._save_btn.isEnabled()          # typed folder that does not exist blocks Save
page._apply_values(dict(settings.DEFAULTS))                                       # what Reset to defaults does
assert page._values()['faces_enabled'] is True and page._values()['faces_dir'] == ''

# ---------------------------------------------------------------- real packs (user's machine only)
real = faces.find_fm_dir()
if not real or not faces.discover_packs(real):
    print('SKIPPED real-pack check (no FM24 folder with facepacks found)')
else:
    ri = faces.FaceIndex(real, cache_dir=os.path.join(tmp, 'realcache'))
    t0 = time.time()
    ri.load()
    cold = time.time() - t0
    t0 = time.time()
    faces.FaceIndex(real, cache_dir=os.path.join(tmp, 'realcache')).load()
    warm = time.time() - t0
    assert ri.count() > 1000, ri.count()
    for uid in (7458500, 37084591):                                       # Messi, Micky van de Ven (DF11)
        p = ri.path(uid)
        if p:
            assert not QImage(p).isNull()
    print(f'real packs: {[p.name for p in ri.packs]}, {ri.count()} pictures, index cold {cold:.2f}s / cached {warm:.2f}s')
print('OK: faces')
