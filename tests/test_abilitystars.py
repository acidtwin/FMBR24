"""Plain-script test for fm_editor/abilitystars.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor.abilitystars import ability_stars, dev_stars  # noqa: E402

for v, want in ((1, 0.5), (10, 0.5), (20, 0.5), (30, 1.0), (40, 1.0), (100, 2.5), (184, 4.5),
                (185, 4.5), (190, 5.0), (195, 5.0), (200, 5.0), (250, 5.0), (0, 0.5)):
    assert ability_stars(v) == want, (v, ability_stars(v), want)
assert ability_stars(None) == 0.0 and ability_stars('x') == 0.0
for v, want in ((1, 0.5), (10, 2.5), (14, 3.5), (20, 5.0), (25, 5.0)):
    assert dev_stars(v) == want, (v, dev_stars(v), want)
assert dev_stars(None) == 0.0
print('ok')
