"""Pictures in the player / staff lists: one pack index for person / club / nation / comp / kit (synthetic packs in every layout),
nation uid table, competition uid on the league, kit lookup, flags setting, and the list rows (face tile, Dev stars, club badge
column, nation flag): delegate paints, tooltips, sorting, widths, Settings switch without reload, 78k-row paint budget.
Plain script, synthetic data, no save needed:
    FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_list_media.py
The real-pack part prints SKIPPED when the user's FM24 folder is absent. Temp dirs only; game folders are never written to."""
import json
import os
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
tmp = tempfile.mkdtemp(prefix='fmbr24_media_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')
os.environ.pop('FMBR24_FM_DIR', None)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtCore import Qt, QRect  # noqa: E402
from PyQt6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem  # noqa: E402

app = QApplication.instance() or QApplication([])
from gui.theme import QSS  # noqa: E402
app.setStyleSheet(QSS)     # the app's item padding (10 px) is part of the geometry under test
from fm_editor import cache, clubextra, faces, nationuid, settings  # noqa: E402
from fm_editor.abilitystars import dev_stars  # noqa: E402
from fm_editor import patch as P  # noqa: E402

P.is_hgc = lambda b, pp, e: False
cache._CACHE_DIR = os.path.join(tmp, 'pcache')


def png(path, w=180, h=180, color=(30, 90, 200)):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = QImage(w, h, QImage.Format.Format_ARGB32)
    im.fill(QColor(*color))
    assert im.save(path, 'PNG'), path


def rec(frm, key, kind, role):
    return f'<record from="{frm}" to="graphics/pictures/{kind}/{key}/{role}"/>\n'


def cfg(path, *records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<record>\n<boolean id="amap" value="false"/>\n<list id="maps">\n' + ''.join(records) + '</list>\n</record>\n')


# ---------------------------------------------------------------- nation uid table (install DB nation table, ordinal -> UniqueID)
nu = nationuid.NATION_UID
assert len(nu) == 251 and len(set(nu)) == 251, 'one unique uid per nation ordinal 0..250'
assert nationuid.nation_uid(139) == 765 and nationuid.nation_uid(170) == 796 and nationuid.nation_uid(189) == 1651   # England, Spain, Brazil
assert nationuid.nation_uid(0) == 5 and nationuid.nation_uid(104) == 373 and nationuid.nation_uid(105) == 374    # Africa start, CONCACAF is NOT +offset
assert nationuid.nation_uid(247) == 62002127 and nationuid.nation_uid(219) == 217945                           # Montenegro, Kosovo
assert nationuid.nation_uid(251) is None and nationuid.nation_uid(-1) is None and nationuid.nation_uid(None) is None

# ---------------------------------------------------------------- competition uid on the league (rgman/comp_<id>.dat number)
tabs = [{1: (2, 2, 0, 0, 5, 1, 6), 2: (2, 0, 1, 1, 2, 3, 1), 3: (2, 0, 1, 1, 1, 4, 1)}, {1: (1, 1, 0, 0, 1, 0, 3), 2: (1, 0, 0, 1, 0, 1, 0)}]
cl = [{'team': 1}, {'team': 2}, {'team': 3}]
clubextra.add_league_positions(cl, tabs, None, [11, 2000000001])
assert cl[0]['league']['comp_uid'] == 11 and cl[0]['league']['pos'] == 1 and cl[0]['league']['comp'] == 0 and cl[2]['league']['of'] == 3
cl2 = [{'team': 1}, {'team': 2}, {'team': 3}]
clubextra.add_league_positions(cl2, tabs, None)
assert 'comp_uid' not in cl2[0]['league'], 'older callers without uids: key absent, nothing else changes'

# ---------------------------------------------------------------- synthetic packs: every layout, every kind
fm = os.path.join(tmp, 'FM')
g = os.path.join(fm, 'graphics')
# 1. facepack with a config (person)
png(os.path.join(g, 'Faces', '100.png'), 260, 310, (200, 40, 40))
cfg(os.path.join(g, 'Faces', 'config.xml'), rec('100', '100', 'person', 'portrait'))
# 2. logo pack: clubs, nations, competitions nested 3 deep like FMG Standard Logos; Small icons + 3D kit records ignored
A = os.path.join(g, 'A Logos')
png(os.path.join(A, 'Clubs', 'Normal', 'Normal', '728.png'))
cfg(os.path.join(A, 'Clubs', 'Normal', 'Normal', 'config.xml'), rec('728', '728', 'club', 'logo'))
png(os.path.join(A, 'Clubs', 'Normal', 'Small', '728.png'), 25, 18)
cfg(os.path.join(A, 'Clubs', 'Normal', 'Small', 'config.xml'), rec('728', '728', 'club', 'icon'))
png(os.path.join(A, 'Nations', 'Normal', 'Normal', '765.png'), 180, 180, (200, 20, 20))
png(os.path.join(A, 'Nations', 'Normal', 'Normal', '796.png'), 180, 180, (230, 200, 0))
cfg(os.path.join(A, 'Nations', 'Normal', 'Normal', 'config.xml'), rec('765', '765', 'nation', 'logo'), rec('796', '796', 'nation', 'logo'))
png(os.path.join(A, 'Competitions', 'Normal', 'Normal', '11.png'), 180, 180, (60, 20, 90))
png(os.path.join(A, 'Competitions', 'Normal', 'Normal', '12.png'), 180, 180, (90, 20, 20))
cfg(os.path.join(A, 'Competitions', 'Normal', 'Normal', 'config.xml'), rec('11', '11', 'comp', 'logo'), rec('12', '12', 'comp', 'logo'),
    rec('12', '12', 'comp', 'logo/huge'))
# 3. folder-per-id pack: nation + comp + club trees
B = os.path.join(g, 'B Tree')
png(os.path.join(B, 'pictures', 'nation', '765', 'logo.jpg'), 180, 180, (5, 5, 250))      # loses against A (alphabetical priority)
png(os.path.join(B, 'pictures', 'nation', '374', 'logo.png'), 180, 180, (0, 150, 0))     # Guyana: only here
png(os.path.join(B, 'pictures', 'comp', '99', 'logo.png'))
png(os.path.join(B, 'pictures', 'club', '900', 'logo.png'))
# 4. kit packs live in graphics/kits/<pack>/ : config form (team/<id>/kits/<variant>) and folder-per-id form
K = os.path.join(g, 'kits')
png(os.path.join(K, 'Kit Config', 'arsenal1.png'), 300, 400, (200, 0, 0))
png(os.path.join(K, 'Kit Config', 'arsenal2.png'), 300, 400, (255, 255, 0))
png(os.path.join(K, 'Kit Config', 'arsenal3.png'), 300, 400, (0, 0, 0))
cfg(os.path.join(K, 'Kit Config', 'config.xml'), rec('arsenal1', '602', 'team', 'kits/home'), rec('arsenal2', '602', 'team', 'kits/away'),
    rec('arsenal3', '602', 'team', 'kits/third'), rec('arsenal1', '602', 'team', 'kits_textures/goalkeeper home'))
png(os.path.join(K, 'Kit Tree', 'pictures', 'team', '728', 'kits', 'home.png'), 300, 400, (10, 10, 120))
png(os.path.join(K, 'Kit Tree', 'pictures', 'team', '728', 'kits', 'Away.PNG'), 300, 400, (10, 120, 10))
os.makedirs(os.path.join(g, 'art', 'shared_textures'), exist_ok=True)                    # unrelated folder: not a pack
cache_dir = os.path.join(tmp, 'cache')

kinds = {p.name: set(p.kinds) for p in faces.discover_packs(fm, kind=None)}
assert kinds == {'A Logos': {'club', 'nation', 'comp'}, 'B Tree': {'nation', 'comp', 'club'}, 'Faces': {'person'},
                 'kits/Kit Config': {'kit'}, 'kits/Kit Tree': {'kit'}}, kinds         # the 'kits' container itself is not a pack
assert [p.name for p in faces.discover_packs(fm)] == ['Faces'] and [p.name for p in faces.discover_packs(fm, kind='kit')] == \
    ['kits/Kit Config', 'kits/Kit Tree']
assert [p.name for p in faces.discover_packs(fm, kind='nation')] == ['A Logos', 'B Tree']
assert faces.status(fm, kind='comp') == (fm, ['A Logos', 'B Tree'])

idx = faces.FaceIndex(fm, cache_dir=cache_dir)
idx.load()
rel = lambda p: os.path.relpath(p, g) if p else None
assert idx.kind_count('person') == 1 and idx.kind_count('club') == 2 and idx.kind_count('nation') == 4 and idx.kind_count('comp') == 3, \
    {k: idx.kind_count(k) for k in faces.KINDS}
assert idx.kind_count('kit') == 5, idx.kind_count('kit')                               # 3 + 2; kits_textures / `icon` / `logo/huge` ignored
assert rel(idx.nation_path(765)) == os.path.join('A Logos', 'Nations', 'Normal', 'Normal', '765.png')   # config pack first (alphabetical)
assert rel(idx.nation_path(374)) == os.path.join('B Tree', 'pictures', 'nation', '374', 'logo.png')    # folder-per-id
assert idx.nation_path(1) is None and idx.nation_path(None) is None
assert rel(idx.comp_path(11)) == os.path.join('A Logos', 'Competitions', 'Normal', 'Normal', '11.png')
assert rel(idx.comp_path('12')).endswith('12.png') and rel(idx.comp_path(99)) == os.path.join('B Tree', 'pictures', 'comp', '99', 'logo.png')
assert rel(idx.kit_path(602, 'home')) == os.path.join('kits', 'Kit Config', 'arsenal1.png')
assert rel(idx.kit_path(602, 'away')).endswith('arsenal2.png') and rel(idx.kit_path(602, 'third')).endswith('arsenal3.png')
assert idx.kit_path(602, 'goalkeeper home') is None, '3D kit textures are not 2D kits'
assert rel(idx.kit_path(728)) == os.path.join('kits', 'Kit Tree', 'pictures', 'team', '728', 'kits', 'home.png')   # default variant = home
assert rel(idx.kit_path(728, 'away')).endswith('Away.PNG') and idx.kit_path(728, 'third') is None and idx.kit_path(1, 'home') is None
assert rel(idx.path(100)) == os.path.join('Faces', '100.png') and idx.club_path(728) and idx.club_path(900)         # old API unchanged
assert idx.club_path(5) is None and idx.path(728) is None, 'ids of different kinds are never mixed'
assert idx.find('club', 728, check=False) and idx.find('nation', 765, check=False)

# index cache: one .fidx per pack (not *.json), version 3, a v2 file is rebuilt not read, a valid one is not rebuilt
fidx = sorted(f for f in os.listdir(cache_dir) if f.endswith('.fidx'))
assert len(fidx) == 5 and not [f for f in os.listdir(cache_dir) if f.endswith('.json')], os.listdir(cache_dir)
assert faces._INDEX_VERSION == 3 and all(json.load(open(os.path.join(cache_dir, f)))['v'] == 3 for f in fidx)
real_build = faces._build_pack
faces._build_pack = lambda *a, **k: (_ for _ in ()).throw(AssertionError('rebuilt despite a valid cache'))
c2 = faces.FaceIndex(fm, cache_dir=cache_dir)
c2.load()
assert c2.kind_count('nation') == 4 and rel(c2.kit_path(602)) == rel(idx.kit_path(602))
faces._build_pack = real_build
for f in fidx:
    json.dump({'v': 2, 'sig': [], 'map': {'1': ''}, 'club': {}}, open(os.path.join(cache_dir, f), 'w'))
c3 = faces.FaceIndex(fm, cache_dir=cache_dir)
c3.load()
assert c3.kind_count('nation') == 4 and c3.kind_count('kit') == 5, 'a v2 (person/club only) index is rebuilt'
png(os.path.join(B, 'pictures', 'nation', '777', 'logo.png'))                              # a new picture invalidates the pack's index
c4 = faces.FaceIndex(fm, cache_dir=cache_dir)
c4.load()
assert rel(c4.nation_path(777)) and c4.kind_count('nation') == 5
os.remove(os.path.join(B, 'pictures', 'nation', '777', 'logo.png'))
os.rmdir(os.path.join(B, 'pictures', 'nation', '777'))

# ---------------------------------------------------------------- settings: flags_enabled
d = settings.DEFAULTS
assert d['flags_enabled'] is True and settings.load()['flags_enabled'] is True
os.makedirs(settings.config_dir(), exist_ok=True)
json.dump({'flags_enabled': 'yes'}, open(settings.settings_path(), 'w'))
assert settings.load()['flags_enabled'] is True                                        # wrong type -> default
assert settings.save({'faces_dir': fm, 'flags_enabled': False, 'faces_enabled': False, 'logos_enabled': False})
assert faces.configure(cache_dir=cache_dir) is None                                    # all three off: no index
assert settings.save({'flags_enabled': True})
assert faces.configure(cache_dir=cache_dir) is not None                                # flags alone need the index
faces.ensure_loaded()
faces.set_club_uids([601, 602, 727, 728, 729])
assert faces.has_kind('nation') and faces.has_kind('comp') and not faces.has_kind('person') and not faces.has_kind('club')
assert faces.nation_logo_path(139).endswith('765.png') and faces.nation_logo_path(170).endswith('796.png')   # England, Spain
assert faces.nation_logo_path(104) is None and faces.nation_logo_path(105).endswith(os.path.join('374', 'logo.png'))   # Guatemala 373 no file; Guyana 374
assert faces.nation_logo_path(0) is None and faces.nation_logo_path(None) is None and faces.nation_logo_path(300) is None
assert faces.comp_logo_path(11).endswith('11.png') and faces.comp_logo_path(5) is None and faces.comp_logo_path(None) is None
assert faces.club_logo_path(727) is None and faces.face_path(100) is None              # badges / faces off
assert faces.kit_path(601, 'home').endswith('arsenal1.png') and faces.kit_path(601, 'third').endswith('arsenal3.png')   # 601 -> logo id 602
assert faces.kit_path(727, 'away').endswith('Away.PNG') and faces.kit_path(728, 'home') is None and faces.kit_path(0) is None   # 728 -> 729: no kit
assert settings.save({'flags_enabled': False, 'logos_enabled': True})
faces.configure(cache_dir=cache_dir)
faces.ensure_loaded()
assert faces.nation_logo_path(139) is None and faces.comp_logo_path(11) is None and not faces.has_kind('nation')   # flags off
assert faces.kit_path(601) is not None, 'kits have no switch: lookup only'
assert settings.save({'faces_enabled': True, 'logos_enabled': True, 'flags_enabled': True})

# ---------------------------------------------------------------- Qt service + the lists
import gui.faces as gf  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui import people_model as PM  # noqa: E402

faces.configure(cache_dir=cache_dir)       # the service's start() uses cache.cache_dir() = tmp/pcache: fine, a fresh index
gf._service = None
svc = gf.get_service()
clubs = [{'id': 10, 'uid': 727, 'name': 'Test FC'}, {'id': 11, 'uid': 5, 'name': 'No Badge United'}, {'id': 12, 'uid': 601, 'name': 'Arsenal-ish'}]
svc.set_clubs(clubs, [], None)


def wait(s):
    t0 = time.time()
    while s.loading() and time.time() - t0 < 10:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


assert not svc.active('person'), 'not started: nothing active'
svc.start()
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])    # install DB absent in CI: pin the key table
svc._act = {}
assert svc.active('person') and svc.active('club') and svc.active('nation') and svc.active('comp') and svc.active('kit')
nx = svc.nation_pixmap(139, 22, 1.0)                                   # England: red 180x180 -> 22x22
assert nx is not None and (nx.width(), nx.height()) == (22, 22) and nx.toImage().pixelColor(11, 11).red() == 200
assert svc.nation_pixmap(104, 22) is None and svc.nation_pixmap(None, 22) is None
cx = svc.comp_pixmap(11, 16, 2.0)
assert cx is not None and (cx.width(), cx.height()) == (32, 32) and cx.devicePixelRatio() == 2.0
assert svc.comp_pixmap(5, 16) is None
fx = svc.pixmap(100, 20, 24, 1.0, radius=2)                            # 260x310 cutout filled into 20x24
assert fx is not None and (fx.width(), fx.height()) == (20, 24) and fx.toImage().pixelColor(10, 12).red() == 200
assert svc.pixmap(999, 20, 24) is None
assert svc.path(727, 'club').endswith('728.png') and svc.path(100, 'person') and svc.path(1, 'nation') is None
bad = os.path.join(tmp, 'gone.png')
png(bad)
svc._bad.discard(bad)
assert svc.pixmap.__func__ is gf.FaceService.pixmap

CAS = [100, 9, 150, 20, 70]


def person(i, ca, uid, nation):
    return {'id': i, 'uid': uid, 'name': f'P{i}', 'ca': ca, 'pa': ca + 20, 'nation': nation, 'birth_year': 2000, 'birth_day': 1,
            'positions': [1] * 15, 'raw_attrs': [10 + 5 * i] * 60, 'personality': [10] * 7, 'trait_mask': 0}


# faces for uid 100 only; nations England / Spain / Guyana (no England-less pack file) / unknown
people = [person(0, 100, 100, 139), person(1, 9, 555, 170), person(2, 150, 100, 105), person(3, 20, 556, 104), person(4, 70, 557, 0)]
w = M.MainWindow()
w._save_data = {'b': b'x', 'people': people, 'squads': {p['id']: 10 + (p['id'] % 3) for p in people},
                'clubs': clubs, 'human_clubs': {10}}
w._squad = people
w._club_entity_id = 11
w._current_club = clubs[0]
w._table_mode = 'squad'
w._current_report_key = 'prospects'
w._populate_squad_table(people)
w._populate_reports_table(people)
w._shortlist = list(people[:3])
w._populate_shortlist()
m = w._players_model
club_uid_by_id = {c['id']: c['uid'] for c in clubs}
club_by_id = {c['id']: c['name'] for c in clubs}
rows = [w._player_row(p, w._save_data['squads'], club_by_id, club_uid_by_id) for p in people]
m.set_data(people, rows)
w._refresh_media_cols()
app.processEvents()

F = M._FaceNameDelegate
C = M._ClubBadgeDelegate
FL = M._FlagDelegate
D = M.StarsDelegate

# --- delegates on the right columns ------------------------------------------------------------------------------------
LISTS = ((w._table, 0, None, 7), (w._reports_table, 0, 9, 7), (w._players_table, 0, 9, 7), (w._shortlist_table, 0, 1, 7),
         (w._staff_shortlist_table, 0, 1, 2), (w._staff_table, 0, 1, 2), (w._club_staff_table, 0, None, 1))
for t, nc, cc, fc in LISTS:
    assert isinstance(t.itemDelegateForColumn(nc), F) and isinstance(t.itemDelegateForColumn(nc), M._RowMarkDelegate)
    assert isinstance(t.itemDelegateForColumn(fc), FL)
    assert cc is None or isinstance(t.itemDelegateForColumn(cc), C)
    assert t.hasMouseTracking()
assert M.faces_active() and M.badges_active() and M.flags_active()

# --- widths: Name +28 for the tile, Club column 40 (was 160), header label hidden in the badge column ----------------------
assert w._players_table.columnWidth(0) == 150 + 25 and w._staff_table.columnWidth(0) == 200 + 25 and w._club_staff_table.columnWidth(0) >= 25
for t, nc, cc, fc in LISTS:      # (tables with rows) the item style reserves exactly the tile + gap (QTableWidget lists fit their columns to content)
    if not t.model().rowCount():
        continue
    o = QStyleOptionViewItem()
    ix = t.model().index(0, nc)
    dd_ = t.itemDelegateForColumn(nc).sizeHint(o, ix).width() - M._RowMarkDelegate(t).sizeHint(o, ix).width()
    assert dd_ == 25, (LISTS.index((t, nc, cc, fc)), dd_)
assert w._reports_table.columnWidth(9) == 40 and w._players_table.columnWidth(9) == 40 and w._shortlist_table.columnWidth(1) == 40
assert w._staff_table.columnWidth(1) == 40
assert w._reports_table.horizontalHeaderItem(9).text() == '' and w._reports_table.horizontalHeaderItem(9).toolTip() == 'Club'
assert m.headerData(9, Qt.Orientation.Horizontal) == '' and m.headerData(9, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole) == 'Club'
assert m.headerData(0, Qt.Orientation.Horizontal) == 'Name'


def paint(table, col, row=0, w_=None, h=30):
    """Paint cell (row, col) with its own delegate into a w_ x 30 image (column width by default)."""
    idx = table.model().index(row, col)
    d = table.itemDelegateForColumn(col)
    img = QImage(w_ or table.columnWidth(col), h, QImage.Format.Format_ARGB32)
    img.fill(QColor('#14151A'))
    p = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, img.width(), h)
    opt.widget = table
    d.paint(p, opt, idx)
    p.end()
    return img


def px(img, x, y):
    c = QColor(img.pixel(x, y))
    return (c.red(), c.green(), c.blue())


def find(table, col, text):
    return next(r for r in range(table.model().rowCount()) if table.model().index(r, col).data() == text)


# --- face tile: picture for uid 100, silhouette (tile bg) for others; tile at x 10..30, y 3..27 --------------------------------
t = w._reports_table
r100, r555 = find(t, 0, 'P0'), find(t, 0, 'P1')
img = paint(t, 0, r100)
assert px(img, 20, 15) == (200, 40, 40), px(img, 20, 15)                 # the picture fills the tile (centre pixel)
assert px(img, 9, 15) == (0x14, 0x15, 0x1A) and px(img, 31, 15) == (0x14, 0x15, 0x1A), 'tile is exactly x 10..30'
assert px(img, 20, 2) == (0x14, 0x15, 0x1A) and px(img, 20, 27) == (0x14, 0x15, 0x1A), 'tile is exactly y 3..27 (24 px high)'
img = paint(t, 0, r555)
assert px(img, 12, 5) == (0x29, 0x2B, 0x32), 'no picture: the avatar tile background'
assert any(px(img, x, y) not in ((0x29, 0x2B, 0x32), (0x14, 0x15, 0x1A)) for x in range(14, 27) for y in range(10, 20)), 'silhouette glyph drawn'
# the text starts after the tile: the Name cell grows by exactly 25 px (text start 13 -> 38 = tile end 30 + 8)
hint_on = t.itemDelegateForColumn(0).sizeHint(QStyleOptionViewItem(), t.model().index(0, 0)).width()
# --- club badge: 22x22 at x 10; tooltip = name; no badge = small elided name text ---------------------------------------------
cname = lambda r: t.model().index(r, 9).data()
rA = next(r for r in range(5) if cname(r) == 'Test FC')               # logo id 728 -> the blue 180x180 logo
rB = next(r for r in range(5) if cname(r) == 'No Badge United')       # uid 5 -> logo id 601? not in packs -> text
img = paint(t, 9, rA)
assert px(img, 20, 15) == (30, 90, 200) and px(img, 8, 15) == (0x14, 0x15, 0x1A) and px(img, 33, 15) == (0x14, 0x15, 0x1A)
assert t.model().index(rA, 9).data(Qt.ItemDataRole.ToolTipRole) == 'Test FC'
img = paint(t, 9, rB)
assert any(px(img, x, y) != (0x14, 0x15, 0x1A) for x in range(4, 36) for y in range(8, 22)), 'club without a badge: its name as text'
assert t.model().index(rB, 9).data(Qt.ItemDataRole.ToolTipRole) == 'No Badge United'
assert C.sizeHint(t.itemDelegateForColumn(9), QStyleOptionViewItem(), t.model().index(rA, 9)).width() == 40
# --- nation flag: England picture, Guyana (folder tree), no picture for uid-less ids = the old emoji / text cell, tooltip = name -----------
rEng, rGuy, rNo = find(t, 0, 'P0'), find(t, 0, 'P2'), find(t, 0, 'P3')
img = paint(t, 7, rEng)
assert px(img, 20, 15) == (200, 20, 20) and px(img, 8, 15) == (0x14, 0x15, 0x1A) and px(img, 33, 15) == (0x14, 0x15, 0x1A)
assert t.model().index(rEng, 7).data(Qt.ItemDataRole.ToolTipRole) == 'England'
assert px(paint(t, 7, rGuy), 20, 15) == (0, 150, 0)
assert t.model().index(rNo, 7).data(Qt.ItemDataRole.ToolTipRole) == 'Guatemala'
img_no = paint(t, 7, rNo)                                              # Guatemala: no picture in the packs -> the unchanged text cell
assert px(img_no, 20, 15) != (200, 20, 20)
assert t.item(rEng, 7).data(M.NATION_ROLE) == 139 and t.item(rEng, 0).data(M.MEDIA_UID_ROLE) == 100

# --- the same cells through the virtualised model (Players) ------------------------------------------------------------------
pt = w._players_table
assert m.data(m.index(0, 0), M.MEDIA_UID_ROLE) == m.person(0)['uid'] and m.data(m.index(0, 7), M.NATION_ROLE) == m.person(0)['nation']
assert m.data(m.index(0, 9), M.CLUB_UID_ROLE) in (727, 5, 601)
assert m.data(m.index(0, 9), Qt.ItemDataRole.ToolTipRole) == m.data(m.index(0, 9)) != ''
assert m.data(m.index(0, 7), Qt.ItemDataRole.ToolTipRole) in ('England', 'Spain', 'Guyana', 'Guatemala', 'Algeria')
rp = next(r for r in range(5) if m.data(m.index(r, 9)) == 'Test FC')
assert px(paint(pt, 9, rp), 20, 15) == (30, 90, 200)
rp0 = next(r for r in range(5) if m.person(r)['uid'] == 100)
assert px(paint(pt, 0, rp0), 20, 15) == (200, 40, 40)

# --- sorting by the Club column sorts by club NAME (both list kinds) ---------------------------------------------------------
t.setSortingEnabled(True)
t.sortItems(9, Qt.SortOrder.AscendingOrder)
names = [t.model().index(r, 9).data() for r in range(t.rowCount())]
assert names == sorted(names) and len(set(names)) == 3, names
t.sortItems(9, Qt.SortOrder.DescendingOrder)
names = [t.model().index(r, 9).data() for r in range(t.rowCount())]
assert names == sorted(names, reverse=True), names
m.sort(9, Qt.SortOrder.AscendingOrder)
names = [m.data(m.index(r, 9)) for r in range(m.rowCount())]
assert names == sorted(names), names
st = w._shortlist_table
st.sortItems(1, Qt.SortOrder.AscendingOrder)
names = [st.item(r, 1).text() for r in range(st.rowCount())]
assert names == sorted(names), names

# --- Dev graphic (five pips, Settings > Development rate display): raw sort, tooltip, Ability display independent, Best by Role ring ----
for tb, dev in ((w._table, 5), (w._reports_table, 5), (w._players_table, 5)):
    dl = tb.itemDelegateForColumn(dev)
    assert isinstance(dl, M.DevDelegate) and dl._label == 'Dev' and dl._stars_fn is dev_stars and tb.columnWidth(dev) == 76, (tb, dev)
assert not isinstance(w._shortlist_table.itemDelegateForColumn(5), M.DevDelegate)
dd = w._reports_table.itemDelegateForColumn(5)
ridx = w._reports_table.model().index(0, 5)
shown = ridx.data()
assert dd.tip(ridx) == f'Dev {shown} of 20'
w._reports_table.sortItems(5, Qt.SortOrder.AscendingOrder)
raw = [int(w._reports_table.item(r, 5).text()) for r in range(w._reports_table.rowCount())]
assert raw == sorted(raw), raw
w._current_report_key = 'best_role'
w._report_ratings = {p['id']: 40 + p['id'] for p in people}
w._populate_reports_table(people)
rd = w._reports_table.itemDelegateForColumn(5)
assert isinstance(rd, M.RoleRingDelegate) and w._reports_table.columnWidth(5) >= 56
rdx = w._reports_table.model().index(0, 5)
assert rd._raw(rdx) is not None
w._current_report_key = 'prospects'
w._populate_reports_table(people)
assert isinstance(w._reports_table.itemDelegateForColumn(5), M.DevDelegate)
# Ability display = Numbers: CA/PA go to 45 px, Dev (own setting, graphic) stays 76; then Dev = Numbers: 45
w._settings_page.saved.emit(dict(settings.load(), ability_display='numbers'))
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
for tb in (w._table, w._reports_table, w._players_table):
    assert tb.columnWidth(5) == 76 and tb.columnWidth(3) == 45, tb.columnWidth(5)
w._settings_page.saved.emit(dict(settings.load(), ability_display='numbers', dev_display='numbers'))
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
for tb in (w._table, w._reports_table, w._players_table):
    assert tb.columnWidth(5) == 45 and tb.columnWidth(3) == 45, tb.columnWidth(5)
assert w._reports_table.itemDelegateForColumn(5).tip(w._reports_table.model().index(0, 5)) is None
w._settings_page.saved.emit(dict(settings.load(), ability_display='stars', dev_display='graphic'))
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
for tb in (w._table, w._reports_table, w._players_table):
    assert tb.columnWidth(5) == 76
w._current_report_key = 'best_role'
w._populate_reports_table(people)
rating_w = w._reports_table.columnWidth(5)
w._settings_page.saved.emit(dict(settings.load(), ability_display='numbers'))
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
w._settings_page.saved.emit(dict(settings.load(), ability_display='stars'))
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
assert w._reports_table.columnWidth(5) == rating_w, 'the Rating column keeps its width while the list is Best by Role'
w._current_report_key = 'prospects'
w._populate_reports_table(people)

# --- queued / selected rows keep their pictures (the tint comes from the row-mark base) ---------------------------------------
r100 = find(t, 0, 'P0')
t.item(r100, 0).setData(M.ROWQ_ROLE, True)
img = paint(t, 0, r100)
assert px(img, 20, 15) == (200, 40, 40) and px(img, 1, 15) != (0x14, 0x15, 0x1A), 'queued bar at the left edge, picture on top'
t.item(r100, 0).setData(M.ROWQ_ROLE, False)

# --- picture settings off: layouts return to the text cells, no reload -------------------------------------------------------------
r100, rEng, rA = find(t, 0, 'P0'), find(t, 0, 'P0'), next(r for r in range(5) if t.model().index(r, 9).data() == 'Test FC')
settings.save({'faces_enabled': False, 'logos_enabled': False, 'flags_enabled': False})
w._settings_page.saved.emit(settings.load())
wait(svc)
assert not M.faces_active() and not M.badges_active() and not M.flags_active()
assert w._reports_table.columnWidth(9) == 160 and w._players_table.columnWidth(9) == 160 and w._staff_table.columnWidth(1) == 160
assert w._players_table.columnWidth(0) == 150 and w._reports_table.horizontalHeaderItem(9).text() == 'Club'
assert m.headerData(9, Qt.Orientation.Horizontal) == 'Club'
img = paint(t, 0, r100)
assert px(img, 20, 15) != (200, 40, 40), 'no tile'
img = paint(t, 7, rEng)
assert px(img, 20, 15) != (200, 20, 20), 'no flag picture: the emoji / text cell'
assert any(px(paint(t, 9, rA), x, 15) != (0x14, 0x15, 0x1A) for x in range(10, 120)), 'club name text again'
# ... and back on
settings.save({'faces_enabled': True, 'logos_enabled': True, 'flags_enabled': True})
w._settings_page.saved.emit(settings.load())
wait(svc)
faces.set_club_uids([601, 602, 727, 728, 729])
svc._act = {}
w._refresh_media_cols()
assert M.faces_active() and w._reports_table.columnWidth(9) == 40 and w._players_table.columnWidth(0) == 150 + 25

# --- Settings page: the flags row, defaults, reset --------------------------------------------------------------------------------
from gui.settings_page import SettingsPage  # noqa: E402

settings.save({'faces_dir': fm})
page = SettingsPage()
assert page._values()['flags_enabled'] is True and page._flags_on.isChecked()
page._flags_on.setChecked(False)
assert page._values()['flags_enabled'] is False and page.is_dirty()
page._apply_values(dict(settings.DEFAULTS))                                          # Reset to defaults
assert page._values()['flags_enabled'] is True
page.close()

# --- competition logo on the Club page --------------------------------------------------------------------------------------------
clubs[0]['league'] = {'pos': 2, 'of': 20, 'P': 24, 'W': 16, 'D': 5, 'L': 3, 'GF': 65, 'GA': 29, 'PTS': 53, 'comp': 0, 'comp_uid': 11}
w._current_club = clubs[0]
w._club_info_vals['League position'].setText('x')
w._club_info_vals['League position'].show()
w._refresh_league_logo()
assert not w._club_league_logo.isHidden() and w._club_league_logo.pixmap().width() == 16
clubs[0]['league']['comp_uid'] = 5                                                   # competition the pack has no logo for
w._refresh_league_logo()
assert w._club_league_logo.isHidden()
del clubs[0]['league']
w._refresh_league_logo()
assert w._club_league_logo.isHidden()

# --- 78k rows: one viewport page under budget with every picture kind on; sort by Club is by name; LRU bounded ----------------------
N = 78000
src = [{'id': i, 'uid': 100 + (i % 7), 'name': f'N{i}', 'nation': (139, 170, 105, 0)[(i // 5) % 4]} for i in range(N)]
rows = [(f'N{i}', False, 'ST', (i * 7) % 200 + 1, (i * 13) % 200 + 1, (i % 20) + 1, 25, '', False,
         ('Test FC', 'No Badge United', 'Arsenal-ish', '')[(i // 3) % 4], '', (727, 5, 601, None)[(i // 3) % 4]) for i in range(N)]
pm = w._players_model
pm.set_data(src, rows)
pt.resize(1300, 900)
pt.show()
for hc in (1, 2, 3, 4, 5, 6, 8):         # narrow table: Name, Nation, Club, CtrE all inside the viewport
    pt.setColumnHidden(hc, True)
pt.grab()
t0 = time.perf_counter()
for _ in range(5):
    pt.viewport().grab()
dt = (time.perf_counter() - t0) / 5
pm.sort(0, Qt.SortOrder.AscendingOrder)       # N0, N1, ...: Test FC / uid 100 / England on the first rows
pt.horizontalScrollBar().setValue(0)
vimg = pt.viewport().grab().toImage()
cols = {(vimg.pixelColor(x, y).red(), vimg.pixelColor(x, y).green(), vimg.pixelColor(x, y).blue())
        for x in range(vimg.width()) for y in range(0, vimg.height(), 2)}
assert (200, 40, 40) in cols and (30, 90, 200) in cols and (200, 20, 20) in cols, 'face, badge and flag pixels are in the viewport grab'
print(f'78k-row players viewport repaint with faces + badges + flags + Dev stars: {dt * 1000:.0f} ms')
assert dt < 0.5, dt
t0 = time.perf_counter()
pm.sort(9, Qt.SortOrder.AscendingOrder)
print(f'78k sort by Club (name): {(time.perf_counter() - t0) * 1000:.0f} ms')
assert pm.data(pm.index(0, 9)) == '' and pm.data(pm.index(N - 1, 9)) == 'Test FC' and pm.data(pm.index(N // 2 + 5, 9)) in ('Arsenal-ish', 'No Badge United')
for hc in (1, 2, 3, 4, 5, 6, 8):
    pt.setColumnHidden(hc, False)
assert len(svc._lru) <= gf.LRU_SIZE
bar = pt.verticalScrollBar()
t0 = time.perf_counter()
for i in range(40):                                                                   # scroll through 40 pages (pictures repeat in the synthetic set)
    bar.setValue(i * (bar.maximum() // 40))
    pt.viewport().grab()
print(f'40 scrolled pages: {(time.perf_counter() - t0) / 40 * 1000:.0f} ms per page')
assert (time.perf_counter() - t0) / 40 < 0.5

# --- real packs (skipped without the user's FM folder): hit rates of every kind --------------------------------------------------------
real = faces.find_fm_dir('', None)
real_ok = bool(real and faces.discover_packs(real, kind='nation') and os.environ.get('FMBR24_FM_DIR_TEST', '1') == '1')
if not real_ok:
    print('SKIPPED real packs: no FM24 folder with a nation pack')
else:
    settings.save({'faces_dir': '', 'faces_enabled': True, 'logos_enabled': True, 'flags_enabled': True})
    faces.configure(cache_dir=os.path.join(tmp, 'realcache'))
    ri = faces.ensure_loaded()
    n_nat = sum(1 for i in range(251) if faces.nation_logo_path(i))
    assert faces.nation_logo_path(139) and faces.nation_logo_path(170) and faces.nation_logo_path(189), 'England, Spain, Brazil'
    assert n_nat >= 230, n_nat
    assert faces.comp_logo_path(11) and faces.comp_logo_path(32), 'Premier League, Serie A'
    print(f'real packs: {[p.name for p in ri.packs]}; nation pictures for {n_nat}/251 ordinals; '
          f'{ {k: ri.kind_count(k) for k in faces.KINDS} }')
print('OK: list_media')
