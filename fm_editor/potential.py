"""'At potential' attribute projection (no Qt). DISPLAY ONLY: never feed these values to patch/save code.

Data: data/ca_weights.json = per-position-group linear fit CA ~ intercept + sum(w_i * attr_i)
(attr on the 1-20 scale = raw/5, index = raw_attrs index), least squares over every player in a real
FM24 save grouped by best position (GK, DC(+SW), FB(DL/DR/WBL/WBR), DM, MC, WM(ML/MR/AML/AMR), AM, ST;
n 2.6k-16k per group, RMSE ~3 CA, weights sum to ~20, i.e. the game's CA = 20x - 120 map).

Algorithm ('headroom'): the player gains target = PA - CA. Growth attributes are those with CA weight
>= MIN_W (zero-cost attributes and hidden/personality/foot attributes excluded). Attribute i gets a
share s_i = 20 - a_i (x PHYS_SCALE for physicals when age > PHYS_AGE); delta_i = min(lam * s_i, 20 - a_i)
with lam bisected so that sum(w_i * delta_i) = target. If even lam -> infinity cannot reach the target
(every growth attribute capped) the result is `saturated` and `reaches` is the CA actually reachable.
"""
import json
import os

POS = ['GK', 'SW', 'DL', 'DC', 'DR', 'DM', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'ST', 'WBL', 'WBR']
PHYS = (34, 38, 36, 37, 42, 46, 39)   # accel, pace, strength, stamina, balance, agility, jumping reach
FEET = (24, 25)
# Zero CA cost (aggression, determination, natural fitness, eccentricity, rushing out, punching) and
# hidden / personality-like attributes (dirtiness, consistency, big matches, injury prone, versatility).
NEVER = (45, 51, 50, 31, 32, 33, 41, 44, 47, 48, 49)
MIN_W = 0.15          # CA weights below this are treated as 0
PHYS_AGE = 24         # physical share x PHYS_SCALE above this age (not frozen)
PHYS_SCALE = 0.75
_DATA = None


def _data():
    global _DATA
    if _DATA is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ca_weights.json')) as f:
            d = json.load(f)
        _DATA = ({p: g for g, ps in d['groups'].items() for p in ps}, {g: v['w'] for g, v in d['fit'].items()})
    return _DATA


def group_of(positions):
    """Weight group of the player's best position (`positions` = 15 ratings in POS order)."""
    return _data()[0][POS[positions.index(max(positions))]]


def availability(ca, pa, age):
    """-> (enabled, tooltip/note). `enabled` is False when there is nothing to project (PA <= CA, age 30+). ADVISORY: the
    player window keeps the Full Potential toggle always selectable (session-17 decision) and only shows the note."""
    if pa is None or ca is None or pa <= ca:
        return False, 'Already at potential.'
    if age >= 30:
        return False, 'Age 30+: potential is unlikely to be reached.'
    if age >= 26:
        return True, 'PA is rarely reached after 26.'
    return True, ''


class Projection:
    __slots__ = ('proj', 'group', 'target', 'achieved', 'saturated')

    def __init__(self, proj, group, target, achieved, saturated):
        self.proj, self.group, self.target, self.achieved, self.saturated = proj, group, target, achieved, saturated

    def reaches(self, ca):
        """CA reachable if saturated (rounded), else None."""
        return round(ca + self.achieved) if self.saturated else None


def project_attrs(raw_attrs, ca, pa, age, positions, cap=20.0):
    """-> Projection; proj = 54 floats on the 1-20 scale (== current when nothing grows)."""
    a = [v / 5 for v in raw_attrs[:54]]
    group = group_of(positions)
    w = [x if x >= MIN_W else 0.0 for x in _data()[1][group]]
    for i in NEVER + FEET:
        w[i] = 0.0
    target = (pa or 0) - (ca or 0)
    if target <= 0:
        return Projection(a, group, target, 0.0, False)
    scale = [(PHYS_SCALE if (age > PHYS_AGE and i in PHYS) else 1.0) if w[i] > 0 else 0.0 for i in range(54)]
    room = [max(cap - v, 0.0) for v in a]
    share = [room[i] * scale[i] for i in range(54)]     # s_i, already x physical scale

    def delta(lam):
        return [min(lam * share[i], room[i]) for i in range(54)]

    def gained(d):
        return sum(w[i] * d[i] for i in range(54))

    d = delta(1e3)
    if gained(d) <= target:          # every growth attribute capped
        return Projection([a[i] + d[i] for i in range(54)], group, target, gained(d), True)
    lo, hi = 0.0, 1e3
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if gained(delta(mid)) < target else (lo, mid)
    d = delta(hi)
    return Projection([a[i] + d[i] for i in range(54)], group, target, gained(d), False)


def display_value(x):
    """1-20 display int of a float attribute (half up)."""
    return max(1, min(20, int(x + 0.5)))
