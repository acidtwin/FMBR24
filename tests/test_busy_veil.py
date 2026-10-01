"""While a save / reload / load runs, the main content is dimmed and click-blocked (the _BusyVeil layer).

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
w._set_busy(True, 'Saving')
app.processEvents()
assert v.isVisible() and not w._main_stack.isEnabled()
assert v.geometry() == w._main_stack.rect(), (v.geometry(), w._main_stack.rect())
w.resize(1000, 700)                       # veil follows the content when the window resizes
app.processEvents()
assert v.geometry() == w._main_stack.rect()
assert v._base == 'Saving' and v._dots == 1
seen = []
for _ in range(8):                      # dots bounce 1 2 3 4 3 2 1 2 ...
    w._tick_dots(); seen.append(v._dots)
assert seen == [1, 2, 3, 4, 3, 2, 1, 2], seen
w._on_progress('Parsing archive...')
assert v._base == 'Parsing archive' and v._dots == 1
w._set_busy(False)
app.processEvents()
assert not v.isVisible() and w._main_stack.isEnabled()
print('OK: busy veil dims + blocks the main content only while busy')
