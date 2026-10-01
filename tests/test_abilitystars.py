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
# half-up boundaries (round() ties-to-even used to give uneven bins: 1.5/2.5/3.5/4.5 dev stars each covered one value)
for v, want in ((9, 0.5), (29, 0.5), (30, 1.0), (49, 1.0), (50, 1.5), (70, 2.0), (90, 2.5), (110, 3.0), (130, 3.5), (170, 4.5)):
    assert ability_stars(v) == want, (v, ability_stars(v), want)
widths = {}
for v in range(10, 190):  # interior CA bins are all 20 wide now
    widths[ability_stars(v)] = widths.get(ability_stars(v), 0) + 1
assert all(n == 20 for st, n in widths.items() if 1.0 <= st <= 4.5), widths
for v, want in ((1, 0.5), (2, 0.5), (3, 1.0), (4, 1.0), (5, 1.5), (7, 2.0), (9, 2.5), (11, 3.0), (13, 3.5), (15, 4.0), (17, 4.5), (19, 5.0)):
    assert dev_stars(v) == want, (v, dev_stars(v), want)
from fm_editor.clubextra import rep_stars  # noqa: E402
for rep, want in ((None, 0.0), (1, 0.0), (499, 0.0), (500, 0.5), (750, 0.5), (1499, 0.5), (1500, 1.0), (3947, 2.0),
                  (4349, 2.0), (6153, 3.0), (8046, 4.0), (9005, 4.5), (9053, 4.5), (9124, 4.5), (9125, 5.0), (9197, 5.0), (10000, 5.0)):
    assert rep_stars(rep) == want, (rep, rep_stars(rep), want)
print('ok')
