"""Club badges: uid -> logo id rule, synthetic logo packs (nested config.xml + folder-per-id), index/cache, settings, Qt layer,
PlayerWindow / header / Save Info badge, real-pack check. Plain script:
    FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_logos.py
The real-pack check prints SKIPPED when the user's FM24 folder (or its install DB) is absent. Temp dirs only; the game folders
are never written to."""
import json
import os
import struct
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
tmp = tempfile.mkdtemp(prefix='fmbr24_logos_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')
os.environ.pop('FMBR24_FM_DIR', None)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtGui import QColor, QImage  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
from fm_editor import cache, clublogo, faces, gamedb, settings  # noqa: E402

cache._CACHE_DIR = os.path.join(tmp, 'pcache')       # history/clublogo caches never land in the user's real cache dir
cache_dir = os.path.join(tmp, 'cache')


def png(path, w=180, h=180, color=(30, 90, 200)):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = QImage(w, h, QImage.Format.Format_ARGB32)
    im.fill(QColor(*color))
    assert im.save(path, 'PNG'), path


def rec(frm, key, kind='club', role='logo'):
    return f'<record from="{frm}" to="graphics/pictures/{kind}/{key}/{role}"/>\n'


def cfg(path, *records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<record>\n<boolean id="amap" value="false"/>\n<list id="maps">\n' + ''.join(records) + '</list>\n</record>\n')


# ---------------------------------------------------------------- the id rule: logo id = next uid of the full list
uids = [600, 601, 602, 604, 727, 728, 729, 913, 915, 1733, 1736]
assert clublogo.logo_id(uids, 727) == 728 and clublogo.logo_id(uids, 913) == 915 and clublogo.logo_id(uids, 1733) == 1736
assert clublogo.logo_id(uids, 602) == 604                  # the gap is skipped: the NEXT club, not uid + 1
assert clublogo.logo_id(uids, 1736) is None and clublogo.logo_id(uids, 5) == 600 and clublogo.logo_id([], 5) is None
assert clublogo.merged_uids([3, 1], [2, 1]) == [1, 2, 3] and clublogo.merged_uids([], None) == []
assert clublogo.merged_uids([5], (), '/definitely/not/an/install') == [5]          # unreadable install DB: save-only list

# ---------------------------------------------------------------- club record layouts (save game_db and install table_3)


def club_rec(cid, uid, layout, nation=139):
    head = struct.pack('<III', cid, uid, uid) + b'\x00'
    if layout == 1:       # find_clubs: nation at +13, ffffffff at +17, nation, nation
        return head + struct.pack('<I', nation) + b'\xff' * 4 + struct.pack('<II', nation, nation) + b'\x00' * 20
    return head + b'\xff' * 4 + struct.pack('<III', nation, nation, nation) + b'\x00' * 20     # layout 2: ffffffff at +13


blob = b'\x07' * 40 + club_rec(1, 601, 1) + b'\x01' * 9 + club_rec(2, 603, 2) + b'\x02' * 7 + club_rec(3, 700, 2, nation=300) \
    + b'\x03' * 5 + club_rec(4, 1871, 2, nation=173) + b'\x00' * 40
assert gamedb.find_hidden_club_uids(blob, len(blob)) == [603, 1871]                # layout 2 only; nation 300 rejected
assert clublogo._scan_table(blob) == {601, 603, 1871}                              # both layouts

# ---------------------------------------------------------------- synthetic FM folder with logo packs
fm = os.path.join(tmp, 'Football Manager 2024')
g = os.path.join(fm, 'graphics')
A = os.path.join(g, 'A Logos')           # FMG layout: <pack>/Clubs/Normal/Normal/config.xml, 3 levels deep
B = os.path.join(g, 'B Logos')           # folder-per-id layout
F = os.path.join(g, 'Faces')             # facepack only
N = os.path.join(g, 'Deep Logos')        # config 4 levels deep: not reached
for n in (728, 729, 915):
    png(os.path.join(A, 'Clubs', 'Normal', 'Normal', f'{n}.png'))
png(os.path.join(A, 'Clubs', 'Normal', 'Normal', '1736.PNG'), 120, 60, (200, 120, 60))   # wide logo, upper-case extension
png(os.path.join(A, 'Clubs', 'Normal', 'Normal', '@2x', '728.png'), 512, 512, (255, 0, 0))   # never entered
png(os.path.join(A, 'Clubs', 'Normal', 'Small', '1000.png'), 25, 18)
png(os.path.join(A, 'Clubs', 'Alternatives', 'Normal', '728alt.png'))               # no config.xml: FM does not map it either
cfg(os.path.join(A, 'Clubs', 'Normal', 'Normal', 'config.xml'),
    rec('728', '728'), rec('729', '729'), rec('915', '915'), rec('1736', '1736'), rec('777', '777'))  # 777: file missing
cfg(os.path.join(A, 'Clubs', 'Normal', 'Small', 'config.xml'), rec('1000', '1000', role='icon'))   # icons: ignored
cfg(os.path.join(A, 'Nations', 'Normal', 'Normal', 'config.xml'), rec('728', '728', 'nation'))     # other kind: ignored
png(os.path.join(B, 'pictures', 'club', '728', 'logo.png'), 180, 180, (10, 200, 10))   # duplicate of A's 728 (A wins: alphabetical)
png(os.path.join(B, 'pictures', 'club', '900', 'logo.jpg'))
png(os.path.join(F, '100.png'))
cfg(os.path.join(F, 'config.xml'), rec('100', '100', 'person', 'portrait'))
png(os.path.join(N, 'a', 'b', 'c', 'd', '5.png'))
cfg(os.path.join(N, 'a', 'b', 'c', 'd', 'config.xml'), rec('5', '5'))

assert [p.name for p in faces.discover_packs(fm, kind='club')] == ['A Logos', 'B Logos']
assert [p.name for p in faces.discover_packs(fm)] == ['Faces']                      # default kind = person: unchanged behaviour
assert [p.name for p in faces.discover_packs(fm, kind=None)] == ['A Logos', 'B Logos', 'Faces']
kinds = {p.name: set(p.kinds) for p in faces.discover_packs(fm, kind=None)}
assert kinds == {'A Logos': {'club', 'nation'}, 'B Logos': {'club'}, 'Faces': {'person'}}, kinds   # nations count as a kind now, `icon`s do not
assert [os.path.relpath(c, A) for c in faces._configs(A)] == [
    os.path.join('Clubs', 'Normal', 'Normal', 'config.xml'), os.path.join('Clubs', 'Normal', 'Small', 'config.xml'),
    os.path.join('Nations', 'Normal', 'Normal', 'config.xml')]
assert faces.status(fm, kind='club') == (fm, ['A Logos', 'B Logos']) and faces.status(fm) == (fm, ['Faces'])

idx = faces.FaceIndex(fm, cache_dir=cache_dir)
assert idx.club_path(728) is None and not idx.ready
idx.load()
assert idx.club_count() == 6 and idx.count() == 1, (idx.club_count(), idx.count())      # per pack: 728 729 915 1736 (A) + 728 900 (B)


def rel(lid, i=idx):
    p = i.club_path(lid)
    return os.path.relpath(p, g) if p else None


assert rel(728) == os.path.join('A Logos', 'Clubs', 'Normal', 'Normal', '728.png')     # priority: alphabetical, not the @2x / alt
assert rel(1736).endswith('1736.PNG')
assert rel(900) == os.path.join('B Logos', 'pictures', 'club', '900', 'logo.jpg')      # folder-per-id layout
assert rel(777) is None and rel(1000) is None and rel(5) is None and rel(0) is None and rel(None) is None
idx_b = faces.FaceIndex(fm, ['B Logos'], cache_dir=os.path.join(tmp, 'cache2'))
idx_b.load()
assert rel(728, idx_b) == os.path.join('B Logos', 'pictures', 'club', '728', 'logo.png')    # setting order wins
assert idx.path(100) is not None and idx.path(728) is None                                     # persons unaffected, ids not mixed
fidx = [f for f in os.listdir(cache_dir) if f.endswith('.fidx')]
assert len(fidx) == 3 and not [f for f in os.listdir(cache_dir) if f.endswith('.json')], os.listdir(cache_dir)
assert json.load(open(os.path.join(cache_dir, fidx[0])))['v'] == faces._INDEX_VERSION == 3
real_build = faces._build_pack
faces._build_pack = lambda *a, **k: (_ for _ in ()).throw(AssertionError('rebuilt despite a valid cache'))
c2 = faces.FaceIndex(fm, cache_dir=cache_dir)
c2.load()
assert rel(728, c2) == rel(728) and c2.club_count() == idx.club_count()
faces._build_pack = real_build
old = {'v': 1, 'sig': [], 'map': {'1': ''}}                                          # a v1 (faces-only) index file is rebuilt, not read
for f in fidx:
    json.dump(old, open(os.path.join(cache_dir, f), 'w'))
c3 = faces.FaceIndex(fm, cache_dir=cache_dir)
c3.load()
assert rel(728, c3) and c3.club_count() == 6

# ---------------------------------------------------------------- settings: default, validation, switches
d = settings.DEFAULTS
assert d['logos_enabled'] is True and settings.load()['logos_enabled'] is True
os.makedirs(settings.config_dir(), exist_ok=True)
json.dump({'logos_enabled': 'yes'}, open(settings.settings_path(), 'w'))
assert settings.load()['logos_enabled'] is True                                      # wrong type -> default
assert settings.save({'faces_dir': fm, 'logos_enabled': False, 'faces_enabled': True})
assert faces.configure(cache_dir=cache_dir) is not None                             # faces still need the index
faces.ensure_loaded()
faces.set_club_uids([727, 728, 729])
assert faces.club_logo_path(727) is None and faces.face_path(100) is not None       # badges off, faces on
assert settings.save({'logos_enabled': True, 'faces_enabled': False})
faces.configure(cache_dir=cache_dir)
assert faces.club_logo_path(727) is None                                             # configured, not loaded yet: never blocks
faces.ensure_loaded()
faces.set_club_uids(None)
assert faces.club_logo_path(727) is None                                             # no key table yet
faces.set_club_uids([727, 728, 729])
assert faces.club_logo_path(727).endswith(os.path.join('Normal', '728.png'))         # 727 -> 728 (next uid)
assert faces.club_logo_path(728).endswith('729.png') and faces.club_logo_path(729) is None   # last uid has no next club
assert faces.club_logo_path(0) is None and faces.club_logo_path(None) is None
assert faces.club_logo_path(900) is None                                             # not in the table; the raw uid is never used as an id
assert faces.face_path(100) is None                                                  # faces off, badges on
assert settings.save({'logos_enabled': False, 'faces_enabled': False, 'flags_enabled': False})
assert faces.configure(cache_dir=cache_dir) is None                                  # all off: no index at all
assert settings.save({'logos_enabled': True, 'faces_enabled': True, 'flags_enabled': True})

# ---------------------------------------------------------------- Qt layer
from gui import faces as gf  # noqa: E402

svc = gf.FaceService()
gf._service = svc
clubs = [{'id': 10, 'uid': 727, 'name': 'Test FC'}, {'id': 11, 'uid': 1735, 'name': 'Wide FC'}, {'id': 12, 'uid': 5, 'name': 'No Logo'}]
svc.set_clubs(clubs, [], None)
svc.start()
import time  # noqa: E402
t0 = time.time()
while svc.loading() and time.time() - t0 < 10:
    app.processEvents()
    time.sleep(0.01)
app.processEvents()
faces.set_club_uids([727, 728, 729, 1735, 1736])      # install DB absent in CI: pin the table for the pixmap checks
px = svc.club_pixmap(727, 18, 1.0)
assert px is not None and (px.width(), px.height()) == (18, 18)
assert px.toImage().pixelColor(9, 9).blue() == 200 and px.toImage().pixelColor(9, 9).alpha() == 255
px2 = svc.club_pixmap(727, 18, 2.0)
assert (px2.width(), px2.height()) == (36, 36) and px2.devicePixelRatio() == 2.0
wide = svc.club_pixmap(1735, 20, 1.0)                  # 120x60 logo -> 20x10 centred in a 20x20 transparent box
wi = wide.toImage()
assert (wide.width(), wide.height()) == (20, 20) and wi.pixelColor(10, 10).alpha() == 255 and wi.pixelColor(10, 1).alpha() == 0 \
    and wi.pixelColor(10, 18).alpha() == 0
assert svc.club_pixmap(5, 18) is None and svc.club_pixmap(None, 18) is None and svc.club_pixmap(729, 18) is None

# ---------------------------------------------------------------- PlayerWindow: with / without a club badge, badge arrives late
from gui import player_window as pw  # noqa: E402


def person(pid=1):
    pos = [1] * 15
    pos[3] = 20
    return {'id': pid, 'uid': 42, 'name': 'Test Player', 'nation': 0, 'ca': 140, 'pa': 160, 'birth_year': 2000, 'birth_day': 100,
            'positions': pos, 'raw_attrs': [60 + (i * 7) % 40 for i in range(60)], 'personality': [10] * 7, 'trait_mask': 0}


sd = {'clubs': clubs, 'squads': {1: 10, 2: 11, 3: 12}}
w1 = pw.PlayerWindow(person(1), sd, 0, None)          # club with a logo
w2 = pw.PlayerWindow(person(3), sd, 0, None)          # club without one
w3 = pw.PlayerWindow(person(9), sd, 0, None)          # no club at all
assert not w1._club_badge.isHidden() and w1._club_badge.size().width() == 16 and w1._club_badge.size().height() == 16
assert w1._club_badge.pixmap().width() == 16 and w1._club_badge.pixmap().toImage().pixelColor(8, 8).blue() == 200
assert w2._club_badge.isHidden() and w2._club_name() == 'No Logo'
assert not hasattr(w3, '_club_badge') and w3._club_name() == ''
settings.save({'logos_enabled': False})
svc.start()                                            # Settings saved with badges off: ready fires, the badge goes away
t0 = time.time()
while svc.loading() and time.time() - t0 < 10:
    app.processEvents()
    time.sleep(0.01)
app.processEvents()
assert w1._club_badge.isHidden()
for w in (w1, w2, w3):
    w.close()
settings.save({'logos_enabled': True})

# ---------------------------------------------------------------- page header circle + Save Info rail (MainWindow)
import gui.main_window as M  # noqa: E402

svc.start()
t0 = time.time()
while svc.loading() and time.time() - t0 < 10:
    app.processEvents()
    time.sleep(0.01)
faces.set_club_uids([727, 728, 729, 1735, 1736])
mw = M.MainWindow()
mw._set_header('Test FC', 'x', icon='club', club=clubs[0])
lbl = mw._header_badge_lbl
assert lbl.size().width() == 56 and lbl.pixmap().width() == 50 and lbl.pixmap().toImage().pixelColor(25, 25).blue() == 200   # logo, no circle behind it
assert 'transparent' in lbl.styleSheet() and 'border: none' in lbl.styleSheet()
mw._set_header('Test FC', 'x', icon='club', club=clubs[2])                        # no logo: the page icon exactly as before
assert lbl.pixmap().width() == mw._page_icon('club').width()
mw._set_header('Squads', 'x', icon='squads')                                      # no club given: page icon
assert lbl.pixmap().width() == mw._page_icon('squads').width()
mw._si_badge_club = clubs[0]
mw._refresh_si_badge()
assert not mw._si_badge.isHidden() and mw._si_badge.pixmap().width() == 22
mw._si_badge_club = clubs[2]
mw._refresh_si_badge()
assert mw._si_badge.isHidden()                                                    # unemployed / no logo: no badge
mw._si_badge_club = None
mw._refresh_si_badge()
assert mw._si_badge.isHidden()
mw.close()

# ---------------------------------------------------------------- Settings page: row, reset, status lines
from gui.settings_page import SettingsPage  # noqa: E402

settings.save({'faces_dir': fm, 'logos_enabled': True, 'faces_enabled': True})
page = SettingsPage()
v = page._values()
assert v['logos_enabled'] is True and page._logos_on.isChecked()
page._logos_on.setChecked(False)
assert page._values()['logos_enabled'] is False and page.is_dirty()
assert 'Found 1 facepack' in page._faces_msg.text() and 'Found 2 logo packs' in page._logos_msg.text(), page._logos_msg.text()
page._apply_values(dict(settings.DEFAULTS))                                       # Reset to defaults
assert page._values()['logos_enabled'] is True
page._faces_dir.setText(os.path.join(tmp, 'missing'))
assert page._faces_state == 'missing' and 'not found' in page._logos_msg.text()

# ---------------------------------------------------------------- real packs / install DB (user's machine only)
real = faces.find_fm_dir()
packs = faces.discover_packs(real, kind='club') if real else []
if not packs:
    print('SKIPPED real logo-pack check (no FM24 folder with a club logo pack found)')
else:
    ri = faces.FaceIndex(real, cache_dir=os.path.join(tmp, 'realcache'))
    ri.load()
    assert ri.club_count() > 1000, ri.club_count()
    p = ri.club_path(728)                                  # Tottenham Hotspur (sortitoutsi team 728)
    assert p is None or QImage(p).size().width() > 0
    print(f"real logo packs: {[x.name for x in packs]}, {ri.club_count()} club logos, 728 -> {p and os.path.relpath(p, real)}")
from fm_editor import history  # noqa: E402

idir = history.install_db_dir()
if not idir:
    print('SKIPPED install-DB check (no FM24 install database found)')
else:
    full = clublogo.install_club_uids(idir)
    assert len(full) > 50000 and len(set(full)) == len(full), len(full)
    for uid, lid in ((601, 602), (727, 728), (913, 915), (1733, 1736), (1870, 1871), (679, 680)):   # Arsenal Spurs Bayern R.Madrid Galatasaray ManUtd
        assert clublogo.logo_id(full, uid) == lid, (uid, clublogo.logo_id(full, uid), lid)
    print(f'install DB: {len(full)} club uids, logo ids of the 6 known clubs OK')
print('OK: logos')
