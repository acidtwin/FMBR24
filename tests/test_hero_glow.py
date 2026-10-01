"""Welcome-hero loading glow: grid-line mask, slow pulse, tied to the first load only (no veil), no idle timer.

Run: python3 tests/test_hero_glow.py   (offscreen)
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

from gui.main_window import HERO_GLOW, MainWindow

app = QApplication.instance() or QApplication([])
w = MainWindow()
w.resize(1200, 800)
w.show()
app.processEvents()
h = w._hero
assert h._page == 'welcome'
assert not h.glow_active() and not h._g_timer.isActive() and h.glow_intensity() == 0.0

# mask = the hero's grid lines in the tint, nothing between them
core, halo = h._glow_layers()
img = core.toImage()
assert img.pixelColor(38, 100).alpha() > 200, 'vertical grid line (x=38) must be in the mask'
assert img.pixelColor(100, 58).alpha() > 200, 'horizontal grid line (y=58) must be in the mask'
assert img.pixelColor(58, 90).alpha() == 0, 'between lines must stay empty'
assert halo.toImage().pixelColor(42, 100).alpha() > 0, 'halo reaches beside the line'
assert (h._glow_layers()[0] is core), 'cached per size'

# first load: glow starts, timer runs, pulse varies with phase, starts and returns to a trough
w._ui_snap = None
w._set_busy(True, 'Parsing save file')
assert h.glow_active() and h._g_timer.isActive()
vals = []
for t in range(0, 2401, 300):
    h._g_t = float(t)
    vals.append(h.glow_intensity())
assert vals[0] == 0.0, vals                         # eases in from 0
h._g_t = 3000.0                                     # past the fade-in
quarter, trough = [], []
for t in (1200 + 2400, 0 + 2400):                   # top / bottom of the pulse (period 2400)
    h._g_t = float(t)
    (quarter if t == 3600 else trough).append(h.glow_intensity())
assert quarter[0] - trough[0] > HERO_GLOW['pulse_depth'] * 0.9, (quarter, trough)
# glow rises with progress
h._g_t = 4800.0
h.set_glow_progress(0.0); lo = h.glow_intensity()
h.set_glow_progress(1.0); hi = h.glow_intensity()
assert hi > lo + HERO_GLOW['progress_gain'] * 0.9, (lo, hi)
w._tick_shimmer()  # wires the bar's progress into the glow
assert 0.0 <= h._g_prog <= 1.0
h.update(); app.processEvents(); h.grab()           # paints without error while active

# finish: continuous (no jump), brighter flash, fades to 0, then the timer is stopped
before = h.glow_intensity()
w._set_busy(False)
assert h._g_state == 'end'
assert abs(h.glow_intensity() - before) < 1e-6, 'finish must not jump'
h.glow_step(HERO_GLOW['flash_ms'])
assert h.glow_intensity() >= max(before, 0.99 * HERO_GLOW['flash'])
h.glow_step(HERO_GLOW['fade_ms'])
assert not h.glow_active() and not h._g_timer.isActive() and h.glow_intensity() == 0.0

# error: no flash, fades from the current level, stops
w._set_busy(True, 'Parsing save file')
h._g_t = 5000.0
cur = h.glow_intensity()
w._set_busy(False, failed=True)
assert h._g_state == 'end' and h.glow_intensity() <= cur + 1e-9
h.glow_step(HERO_GLOW['fade_ms'])
assert not h.glow_active() and not h._g_timer.isActive()

# hidden window: tick stops the timer
w._set_busy(True, 'Parsing save file')
assert h._g_timer.isActive()
w.hide(); app.processEvents()
assert not h._g_timer.isActive()
w.show(); app.processEvents()
assert h._g_timer.isActive()
w._set_busy(False); h.glow_stop()

# reload / save (veil) never glow
for snap, word in (({'dummy': 1}, 'Parsing save file'), (None, 'Saving')):
    w._ui_snap = snap
    w._set_busy(True, word)
    assert w._veil_word and not h.glow_active() and not h._g_timer.isActive(), word
    w._set_busy(False)
    assert not h.glow_active()
w._ui_snap = None

# other pages never start the glow
for key in ('club', 'squad', 'settings', 'save_info'):
    h.set_page(key)
    w._set_busy(True, 'Parsing save file')
    assert not h.glow_active() and not h._g_timer.isActive(), key
    w._set_busy(False)
h.set_page('welcome')
print('OK: hero glow (grid mask, pulse, progress tie, first-load only, timer stops)')
