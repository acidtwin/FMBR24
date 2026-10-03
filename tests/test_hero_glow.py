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

# mask = the hero's strands in the tint, nothing between them (pitch texture = the old grid; the nets: test_header_texture.py)
h.set_texture('pitch')
core, halo = h._glow_layers()
img = core.toImage()
assert img.pixelColor(38, 100).alpha() > 200, 'vertical grid line (x=38) must be in the mask'
assert img.pixelColor(100, 58).alpha() > 200, 'horizontal grid line (y=58) must be in the mask'
assert img.pixelColor(58, 90).alpha() == 0, 'between lines must stay empty'
assert halo.toImage().pixelColor(42, 100).alpha() > 0, 'halo reaches beside the line'
assert (h._glow_layers()[0] is core), 'cached per size'

# first load: glow starts, timer runs, smooth pulse between floor and floor+depth, eases in from 0
w._ui_snap = None
# a quick (cached) load ends before the delay: no glow at all, nothing running afterwards
w._set_busy(True, 'Parsing save file')
assert h._g_state == 'wait' and not h._g_timer.isActive() and h.glow_intensity() == 0.0 and h._g_delay.isActive()
w._set_busy(False)
assert h._g_state == 'off' and not h._g_delay.isActive() and not h._g_timer.isActive()
# a long load: after the delay the glow runs
w._set_busy(True, 'Parsing save file')
h._glow_begin()
assert h._g_state == 'run' and h.glow_active() and h._g_timer.isActive()
h._g_t = 0.0
assert h.glow_intensity() == 0.0                    # eases in from 0
period = HERO_GLOW['period_ms']
h._g_t = 4 * period                                 # past the fade-in, bottom of a pulse
trough = h.glow_intensity()
h._g_t = 4.5 * period                               # top of the pulse
top = h.glow_intensity()
assert abs(trough - HERO_GLOW['floor']) < 1e-6 and abs(top - (HERO_GLOW['floor'] + HERO_GLOW['depth'])) < 1e-6, (trough, top)
assert HERO_GLOW['peak_alpha'] <= 0.2, 'the pulse is meant to be subtle'
# smooth: no jump between neighbouring frames (60 fps step) anywhere in one period
step = HERO_GLOW['fps_ms']
prev = None
for k in range(int(period / step) + 1):
    h._g_t = 4 * period + k * step
    v = h.glow_intensity()
    assert prev is None or abs(v - prev) < 0.02, (k, prev, v)
    prev = v
# not tied to the loading bar's value: the bar's progress does not change the glow
h._g_t = 4800.0
lo = h.glow_intensity()
w._progress_displayed = 90.0
w._tick_shimmer()
assert h.glow_intensity() == lo
h.update(); app.processEvents(); h.grab()           # paints without error while active

# finish (bar done): continuous (no jump, no flash), fades to 0, then the timer is stopped
before = h.glow_intensity()
w._set_busy(False)
assert h._g_state == 'end'
assert abs(h.glow_intensity() - before) < 1e-6, 'finish must not jump'
h.glow_step(HERO_GLOW['fade_ms'] / 2)
assert h.glow_intensity() < before
h.glow_step(HERO_GLOW['fade_ms'])
assert not h.glow_active() and not h._g_timer.isActive() and h.glow_intensity() == 0.0

# error: same fade, stops
w._set_busy(True, 'Parsing save file')
h._glow_begin()
h._g_t = 5000.0
cur = h.glow_intensity()
w._set_busy(False, failed=True)
assert h._g_state == 'end' and h.glow_intensity() <= cur + 1e-9
h.glow_step(HERO_GLOW['fade_ms'])
assert not h.glow_active() and not h._g_timer.isActive()

# hidden window: tick stops the timer
w._set_busy(True, 'Parsing save file')
h._glow_begin()
assert h._g_timer.isActive()
w.hide(); app.processEvents()
assert not h._g_timer.isActive()
w.show(); app.processEvents()
assert h._g_timer.isActive()
w._set_busy(False); h.glow_stop()

# the glow never leaks onto the page the load lands on
w._set_busy(True, 'Parsing save file')
h._glow_begin()
assert h.glow_active()
h.set_page('save_info')
assert not h.glow_active() and not h._g_timer.isActive() and h.glow_intensity() == 0.0
w._set_busy(False)
h.set_page('welcome')

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
print('OK: hero glow (grid mask, subtle smooth pulse, ends with the load, first-load only, timer stops)')
