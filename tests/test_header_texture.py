"""Header texture (Settings > Header texture): generators, cache, glow layers, live switch, setting default/validation/Reset.

Run: python3 tests/test_header_texture.py   (offscreen, temp config dir)
"""
import json
import os
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp(prefix='fmbr24_tex_')  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox

from fm_editor import settings
from gui import header_net
from gui.main_window import HERO_GLOW, MainWindow

app = QApplication.instance() or QApplication([])

# -- setting: default, validation, merge-save, registry in sync ---------------------------------------------------
assert settings.DEFAULTS['header_texture'] == 'diamond'
assert settings.HEADER_TEXTURES == header_net.TEXTURES == tuple(header_net.LABELS) == tuple(header_net.SPEC)
for bad in ('nope', 5, None, True, ''):
    json.dump({'header_texture': bad}, open(settings.settings_path(), 'w'))
    assert settings.load()['header_texture'] == 'diamond', bad
for tid in settings.HEADER_TEXTURES:
    assert settings.save({'header_texture': tid}) and settings.load()['header_texture'] == tid
json.dump({'other_key': 7}, open(settings.settings_path(), 'w'))
assert settings.save({'header_texture': 'honeycomb'}) and json.load(open(settings.settings_path()))['other_key'] == 7
os.remove(settings.settings_path())

# -- generators: every texture, both dpr: non-empty, right size / DPR, under the time budget ----------------------
W, H = 1920, 186
for tex in header_net.TEXTURES:
    for dpr in (1.0, 2.0):
        t0 = time.perf_counter()
        px = header_net.texture_pixmap(tex, W, H, dpr)
        dt = (time.perf_counter() - t0) * 1000
        assert (px.width(), px.height()) == (round(W * dpr), round(H * dpr)) and px.devicePixelRatio() == dpr, (tex, dpr)
        img = px.toImage()
        step = 3   # coprime with the pitch grid (lines at 37-38 mod 40)
        n = sum(1 for y in range(0, img.height(), step) for x in range(0, img.width(), step) if img.pixelColor(x, y).alpha() > 0)
        assert n > 50, (tex, 'texture is empty')
        top = max(c.alpha() for c in (img.pixelColor(x, y) for y in range(0, img.height(), 2) for x in range(0, img.width(), 2))
                  if c.red() > 128)   # the white strands only (C's corner shadow is black)
        assert top <= (0.45 if tex == 'honeycomb' else 0.25) * 255, (tex, 'texture too strong for title legibility', top)  # D's post/crossbar corner stacks to ~.41
        assert dt < 150, (tex, dpr, 'build time ms', dt)
        core, halo = header_net.glow_pixmaps(tex, W, H, dpr, HERO_GLOW['tint'], HERO_GLOW['halo_widths'])
        for gp in (core, halo):
            assert (gp.width(), gp.height()) == (round(W * dpr), round(H * dpr)) and gp.devicePixelRatio() == dpr
            gi = gp.toImage()
            assert any(gi.pixelColor(x, y).alpha() > 0 for y in range(0, gi.height(), 3) for x in range(0, gi.width(), 3)), (tex, 'glow empty')
        print(f'{tex:11s} dpr {dpr}: texture {dt:5.1f} ms')

# -- the app: default, cache hit, live switch, glow layers per texture, glow stop leaves nothing --------------------
w = MainWindow()
w.resize(1200, 800)
w.show()
app.processEvents()
h = w._hero
assert h._texture == 'diamond'
a = h._texture_pixmap()
assert h._texture_pixmap() is a, 'cache hit on the second call'
assert (a.width(), a.height()) == (round(h.width() * h.devicePixelRatioF()), round(h.height() * h.devicePixelRatioF()))
for tex in header_net.TEXTURES:
    if tex != h._texture:
        h.set_texture(tex)
        assert h._t_cache is None and h._g_cache is None, 'switching drops both caches'
    px = h._texture_pixmap()
    assert px.width() == round(h.width() * h.devicePixelRatioF()) and px.height() == round(h.height() * h.devicePixelRatioF())
    h.set_texture(tex)
    assert h._t_cache is not None, 'setting the same texture keeps the cache'
    core, halo = h._glow_layers()
    assert h._glow_layers()[0] is core and core.size() == px.size()
    h._g_state = 'run'
    h._g_t = 4.5 * HERO_GLOW['period_ms']
    img = h.grab()   # paints texture + glow without raising
    assert not img.isNull()
    h.glow_stop()
    assert not h.glow_active() and not h._g_timer.isActive() and not h._g_delay.isActive() and h.glow_intensity() == 0.0
h.set_texture('bogus')
assert h._texture == 'diamond', 'unknown id falls back to the default'

# a resize rebuilds (key has w/h)
h.set_texture('honeycomb')
p1 = h._texture_pixmap()
w.resize(1300, 800)
app.processEvents()
assert h._texture_pixmap() is not p1 and h._texture_pixmap().width() >= 1300 * 0.5

# -- Settings page: row exists, Reset restores diamond, Save applies LIVE to the open header -----------------------
sp = w._settings_page
sp.load_from_disk()
assert sp._htex.count() == len(header_net.TEXTURES) and sp._htex.currentData() == 'diamond'
sp._htex.setCurrentIndex(sp._htex.findData('squareknot'))
assert sp.is_dirty() and sp._values()['header_texture'] == 'squareknot'
sp._save()
assert settings.load()['header_texture'] == 'squareknot'
assert h._texture == 'squareknot', 'saved Settings applies to the open header without a restart'
sp._htex.setCurrentIndex(sp._htex.findData('pitch'))
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
sp._reset()
assert sp._htex.currentData() == 'diamond' and sp._values()['header_texture'] == 'diamond'
sp._save()
assert h._texture == 'diamond'

print('OK: header texture (setting, 5 generators, cache, glow layers, live switch, Reset)')
