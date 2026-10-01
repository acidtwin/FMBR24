"""Plain-script test for gui/pw_themes.py (texture themes) + the player_theme setting. Temp dir only."""
import os
import sys
import tempfile
import time

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tmp = tempfile.mkdtemp(prefix='fmbr24_test_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')

from PyQt6.QtGui import QImage, QPainter  # noqa: E402
from PyQt6.QtWidgets import QApplication, QFrame, QPushButton  # noqa: E402

from fm_editor import settings  # noqa: E402
from gui import pw_themes as T  # noqa: E402

app = QApplication([])

# registry: ids/names in Settings order; settings validates against the same ids
assert list(T.THEMES) == ['steel', 'pitch', 'floodlit', 'plain'] == list(settings.PLAYER_THEMES)
assert [t.name for t in T.THEMES.values()] == ['Steel', 'Pitch lines', 'Floodlit', 'Plain']
assert T.DEFAULT_THEME == 'steel' == settings.DEFAULTS['player_theme']

# every recipe paints every surface without error and actually draws something
SIZES = {'header': (1098, 80), 'strip': (172, 592), 'bar': (1122, 52)}
for tid, th in T.THEMES.items():
    for surf, (w, h) in SIZES.items():
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        th.recipes[surf](p, w, h)
        p.end()
        assert img.pixelColor(w // 2, h // 2).alpha() == 255, (tid, surf)

# fallback for unknown id; active_theme follows the setting
assert T.theme_for('nope') is T.THEMES['steel'] and T.theme_for(None) is T.THEMES['steel']
assert T.active_theme() is T.THEMES['steel']
assert settings.save({'player_theme': 'pitch'}) and T.active_theme() is T.THEMES['pitch']
assert settings.save({'player_theme': 'bogus'}) and settings.load()['player_theme'] == 'steel'

# settings round trip
for tid in T.THEMES:
    assert settings.save({'player_theme': tid}) and settings.load()['player_theme'] == tid
assert settings.load() == dict(settings.DEFAULTS, player_theme='plain')

# ThemedFrame + apply_active_theme + halo + active tab, and a fast paint
settings.save({'player_theme': 'floodlit'})
root = QFrame()
hdr = T.ThemedFrame('bar', root)
hdr.setObjectName('pwHeader')
bar = T.ThemedFrame('header', root)
bar.setObjectName('actionStrip')
btn = QPushButton('Add', bar)
bar.halo_for = btn
tab = T.ActiveTabButton('Profile', root)
tab.setCheckable(True)
tab.setChecked(True)
T.apply_active_theme(root)
assert hdr.surface == 'header' and bar.surface == 'bar' and hdr.theme is T.THEMES['floodlit'] and tab.theme is hdr.theme
hdr.resize(1098, 80)
bar.resize(1122, 52)
tab.resize(160, 40)
for fr in (hdr, bar, tab):
    fr.grab()
for tid in T.THEMES:
    hdr.theme = T.THEMES[tid]
    t0 = time.time()
    for _ in range(200):
        hdr.grab()
    assert time.time() - t0 < 1.0, (tid, time.time() - t0)

print('OK')
