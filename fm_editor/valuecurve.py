"""Estimated transfer value by age (no Qt). Tables: fm_editor/data/value_model.json, built offline by
scripts/build_value_model.py from pairs of simulated FM24 saves (aggregated tables only, no player data).

This is an ESTIMATE of the TREND, not FM's formula: the level of a value depends on the hidden player reputation
(not in the save), so every line is anchored on the stored current value and only its change over time is modelled
(individual errors are a factor 2-3 at 3-9 years; the band holds about half of real outcomes).

curve(age, ca, pa, is_gk, value, years_left) -> ValueCurve with, for each age Now .. Now+11 (capped at 37):
  expected  value with the median CA path;  lo / hi  25-75% band;  full  value if CA reaches PA by 27 and then ages
  like a peak player (None unless age <= 28 and CA < 97% of PA).  Lines assume the contract is renewed after Now
  (`years_left` only shapes the first point's contract effect, which cancels in the anchoring).
"""
import json
import os
from dataclasses import dataclass, field

import numpy as np

NOT_FOR_SALE = 300_000_000
POT_PEAK = 27            # full-potential line: CA reaches PA at this age (or Now + 3, whichever is later)
FULL_MAX_AGE = 28        # no full-potential line from age 29 ...
FULL_MAX_RHO = 0.97      # ... or when CA >= 97% of PA
MAX_AGE, HORIZON = 37, 11

_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        with open(os.path.join(os.path.dirname(__file__), 'data', 'value_model.json')) as f:
            m = json.load(f)
        m['h']['table'] = np.array(m['h']['table'])
        m['gk_by_age'] = np.array(m['gk_by_age'])
        for g in m['path'].values():
            g['table'] = np.array(g['table'])
        _MODEL = m
    return _MODEL


@dataclass
class ValueCurve:
    ages: list = field(default_factory=list)       # displayed ages: int(age) + i
    expected: list = field(default_factory=list)   # GBP; expected[0] == the stored value
    lo: list = field(default_factory=list)
    hi: list = field(default_factory=list)
    full: list = None                              # None = no full-potential line
    years_left: float = None                       # None = unknown / expired
    runs_out: bool = False                         # < 1 year left: the value is lower while the contract runs out

    @property
    def empty(self):
        return not self.ages


def _h(m, E, age, years_left, gk):
    """log-value term: bilinear h(CA, age) + contract bucket + goalkeeper(age)."""
    h = m['h']
    a = min(max(age, h['age0']), h['age0'] + h['table'].shape[0] - 1 - 1e-6) - h['age0']
    ia = int(a)
    ta = a - ia
    e = (min(max(E, h['e0']), h['e0'] + (h['table'].shape[1] - 1) * h['e_step'] - 1e-6) - h['e0']) / h['e_step']
    ie = int(e)
    te = e - ie
    t = h['table']
    v = ((1 - ta) * ((1 - te) * t[ia, ie] + te * t[ia, ie + 1])
         + ta * ((1 - te) * t[ia + 1, ie] + te * t[ia + 1, ie + 1]))
    c = m['contract']
    v += c[3 if years_left is None else 0 if years_left < 0.5 else 1 if years_left < 1 else 2 if years_left < 2 else 3]
    if gk:
        v += m['gk_by_age'][min(max(int(age) - h['age0'], 0), len(m['gk_by_age']) - 1)]
    return float(v)


def _rho_at(m, is_gk, age, rho, k):
    """Expected CA / PA after k years (k float): linear in k between the fitted horizons (clamped beyond the last)."""
    p = m['path']['gk' if is_gk else 'outfield']
    tab, a0 = p['table'], p['age0']
    a = min(max(age, a0), a0 + tab.shape[1] - 1)
    rhos = p['rho0'] + p['rho_step'] * np.arange(tab.shape[2])
    r = min(max(rho, rhos[0]), rhos[-1])
    ages = a0 + np.arange(tab.shape[1])
    vals = [rho] + [float(np.interp(r, rhos, [np.interp(a, ages, T[:, j]) for j in range(T.shape[1])])) for T in tab]
    return float(np.interp(k, [0.0] + p['horizons'], vals))


def _band(m, k):
    return float(np.interp(k, m['band']['years'], m['band']['half_width']))


def curve(age, ca, pa, is_gk, value, years_left=None):
    """Empty ValueCurve for value 0 / sentinels (>= 300M = Not for Sale or none) / missing CA."""
    if not value or value >= NOT_FOR_SALE or not ca or not age:
        return ValueCurve()
    m = model()
    pa = max(pa or ca, ca)
    rho0 = min(ca / pa, 1.0)
    yl = years_left if years_left is not None and years_left >= 0 else None
    n = max(0, min(HORIZON, MAX_AGE - int(age)))
    full_on = age <= FULL_MAX_AGE and rho0 < FULL_MAX_RHO
    peak = max(age + 3, POT_PEAK)
    base = _h(m, ca, age, yl, is_gk)
    out = ValueCurve(ages=[int(age) + i for i in range(n + 1)], years_left=yl, runs_out=yl is not None and yl < 1)
    out.full = [] if full_on else None
    for k in range(n + 1):
        if k == 0:
            cae = caf = ca
        else:
            cae = _rho_at(m, is_gk, age, rho0, k) * pa
            if full_on:
                caf = ca + (pa - ca) * k / (peak - age) if age + k <= peak else _rho_at(m, is_gk, peak, 1.0, age + k - peak) * pa
        yk = yl if k == 0 else 9.0                    # renewal assumed after Now
        ve = value * np.exp(_h(m, cae, age + k, yk, is_gk) - base)
        b = _band(m, k)
        out.expected.append(float(ve))
        out.lo.append(float(ve * np.exp(-b)))
        out.hi.append(float(ve * np.exp(b)))
        if full_on:
            out.full.append(float(value * np.exp(_h(m, caf, age + k, yk, is_gk) - base)))
    out.expected[0] = out.lo[0] = out.hi[0] = float(value)
    if full_on:
        out.full[0] = float(value)
    return out
