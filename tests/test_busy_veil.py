"""While a save / reload runs, the main content is dimmed and click-blocked (the _BusyVeil layer) with a
'Saving' / 'Reloading' label and bouncing dots. A first load shows no veil (the Welcome page has its own state).

Run: python3 tests/test_busy_veil.py   (offscreen)
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('FMBR24_CONFIG_DIR', '/tmp/fmbr24_test_veil')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
w = MainWindow()
w.resize(1200, 800)
w.show()
app.processEvents()
v = w._busy_veil
assert not v.isVisible() and w._main_stack.isEnabled()

# first load / another file: no snapshot -> no veil, page stays usable (Welcome shows its own loading state)
w._ui_snap = None
w._set_busy(True, 'Parsing save file')
app.processEvents()
assert not v.isVisible() and w._main_stack.isEnabled() and w._veil_word is None
w._set_busy(False)

# saving
w._set_busy(True, 'Saving')
app.processEvents()
assert v.isVisible() and not w._main_stack.isEnabled() and v._base == 'Saving' and v._dots == 1
assert v.geometry() == w._main_stack.rect(), (v.geometry(), w._main_stack.rect())
seen = []
for _ in range(8):                      # dots bounce 1 2 3 4 3 2 1 2 ...
    w._tick_dots(); seen.append(v._dots)
assert seen == [1, 2, 3, 4, 3, 2, 1, 2], seen
w.resize(1000, 700)                     # veil follows the content when the window resizes
app.processEvents()
assert v.geometry() == w._main_stack.rect()
w._set_busy(False)
app.processEvents()
assert not v.isVisible() and w._main_stack.isEnabled()

# reload (a UI snapshot was taken): 'Reloading', stage messages do not change the word
w._ui_snap = {'dummy': 1}
w._set_busy(True, 'Parsing save file')
w._on_progress('Parsing archive...')
app.processEvents()
assert v.isVisible() and v._base == 'Reloading', v._base
w._set_busy(False)
w._ui_snap = None
print('OK: busy veil (Saving / Reloading, bouncing dots, no veil on first load)')
