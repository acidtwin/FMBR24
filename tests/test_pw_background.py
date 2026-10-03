"""Player window background: folder scan, random pick, cover scaling, settings key (synthetic images, no real folder)."""
import os, sys, tempfile, random
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QColor
app = QApplication.instance() or QApplication([])
from gui import pw_background as B
from fm_editor import settings

d = tempfile.mkdtemp()
assert B.list_backgrounds(d) == [] and B.pick_background(d) is None          # empty / missing folder: no background
assert B.list_backgrounds(os.path.join(d, 'nope')) == []
for i, c in enumerate((QColor(200, 0, 0), QColor(0, 200, 0)), 1):
    im = QImage(400, 200, QImage.Format.Format_RGB32); im.fill(c); im.save(os.path.join(d, f'a{i}.png'))
open(os.path.join(d, 'broken.png'), 'wb').write(b'not an image')
open(os.path.join(d, 'notes.txt'), 'w').write('x')
assert len(B.list_backgrounds(d)) == 3                                         # txt ignored, broken still listed
seen = set()
for s in range(40):
    px = B.pick_background(d, random.Random(s))
    assert px is not None                                                      # a broken file never wins
    seen.add(px.toImage().pixelColor(5, 5).name())
assert seen == {'#c80000', '#00c800'}, seen                                    # both pictures get picked
c = B.cover(B.pick_background(d), 300, 300)
assert (c.width(), c.height()) == (300, 300) and B.cover(None, 10, 10) is None and B.cover(px, 0, 5) is None
assert 0 < B.OPACITY < 0.3
assert settings.load()['player_background'] is True
settings.save({'player_background': False}); assert settings.load()['player_background'] is False
print('OK: pw_background')
