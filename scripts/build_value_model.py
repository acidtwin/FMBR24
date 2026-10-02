"""Offline: fit the value-by-age model and write fm_editor/data/value_model.json (aggregated tables only).

Usage:
    python scripts/build_value_model.py [--out PATH] EARLY.fm:LATE.fm [EARLY.fm:LATE.fm ...]

Each argument is one PAIR of saves of the SAME simulated world (same player ids), the later one some years
further on. The shipped file was built from 7 pairs of the author's own FM24 saves (0.6 .. 12.6 years apart);
pass your own pairs to rebuild it. Saves are only read (never written). The output has NO player ids / names:
only smoothed tables.

Method (see mockups/player-window.html, 'VALUE BY AGE CHART'):
  1. LEVEL of a player's value is not predictable from the save (hidden player reputation), so the curve is
     anchored on the stored current value and only its SHAPE over time is modelled.
  2. Value shape: within-player (first-difference) regression over players present in both saves (matched by id +
     birth year, value in (0, 300M), age >= 16 in the early save):
         log V_B - log V_A = h(E_B, age_B) - h(E_A, age_A) + c(contract bucket B) - c(bucket A) + gk(age_B) - gk(age_A)
     E = CA (h is a smooth age x CA table, bilinear, second-difference smoothness penalties along both axes),
     c = 4 contract buckets (<6 months, 6-12 months, 1-2 years, >= 2 years = reference 0), gk(age) = goalkeeper offset.
     Solved by IRLS with weights 1/max(|residual|, 0.4) (approximates a median regression). Only pairs <= 10 years apart.
  3. CA path: for every pair (all gaps), kernel-smoothed mean of CA_B / PA_A on a (age, CA_A/PA_A) grid, one table per
     distinct horizon in years (rounded to 0.1) and separately for outfield players and goalkeepers.
  4. Band: half-width (log units) of the 25-75% range by years ahead, from leave-one-lineage-out errors (hand-copied
     constants below: BAND).
Accuracy (honest): a TREND, not a price. Individual errors are a factor 2-3 at 3-9 years; the band covers ~half of
real outcomes.
"""
import argparse
import json
import os
import sys
from datetime import date

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AG0, AG1, E0, E1, ES = 15, 40, 30, 200, 5            # h table: ages 15..40 x CA 30..200 step 5
NA, NE, NB = AG1 - AG0 + 1, (E1 - E0) // ES + 1, 4
NTH, NG = NA * NE, NA
NP = NTH + NB + NG
RAGES = np.arange(15, 40)                              # CA-path table axes
RHOS = np.round(np.arange(0.30, 1.0001, 0.025), 3)
BAND = {0: 0, 1: 0.5, 2: 0.7, 3: 0.8, 5: 0.82, 9: 1.2, 11: 1.3}   # years ahead -> 25-75% half-width, log units
MAX_VALUE_GAP_Y = 10.0


# --- reading saves (read-only) ----------------------------------------------------------------------
def panel_from_save(path):
    """-> {'date': 'YYYY-MM-DD', 'rows': [(id, birth_year, birth_day, ca, pa, value, squad, contract_end, nation, group)]}"""
    sys.path.insert(0, ROOT)
    from fm_editor.archive import get_member, parse_archive
    from fm_editor.gamedb import (find_abilities, find_clubs, find_contract_blocks, find_names, find_people,
                                  find_squads, match_identities)
    from fm_editor.potential import group_of
    from fm_editor.saveinfo import parse_save_info
    _, members, _, name, _, _ = parse_archive(path)
    b = get_member(path, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, ns, ne = find_names(b)
    people = find_people(b, fn, ln, ne)
    match_identities(b, people, ne)
    ab = find_abilities(b, ne)
    squads, _ = find_squads(b, find_clubs(b, ns), ns, people)
    con = find_contract_blocks(b, people)
    si = parse_save_info(path, members, name, gdb=b)
    rows = []
    for p in people:
        i = p.get('id', -1)
        a = ab.get(i)
        if a:
            rows.append((i, p['birth_year'], p.get('birth_day', 0), a['ca'], a['pa'], a['value_est'], squads.get(i, -1),
                         con.get(i, {}).get('contract_end'), p['nation'], group_of(a['positions'])))
    return {'date': si.get('in_game_date'), 'rows': rows}


def _arrays(panel):
    d, rows = date.fromisoformat(panel['date']), panel['rows']
    col = lambda j, dt=float: np.array([r[j] for r in rows], dt)
    by, bd = col(1), col(2)
    bdate = np.array([date(int(y), 1, 1).toordinal() + max(int(x), 1) - 1 for y, x in zip(by, bd)])
    yl = np.array([(int(r[7][:4]) - d.year) + (int(r[7][5:7]) - d.month) / 12 if r[7] else -1 for r in rows])
    return dict(d=d, ids=col(0, int), by=by, ca=col(3), pa=col(4), v=col(5), age=(d.toordinal() - bdate) / 365.2425,
                yl=yl, gk=np.array([r[9] == 'GK' for r in rows]))


def match_pair(pa_, pb_):
    """Players present in both panels with the same birth year -> (A, B, idx_a, idx_b, years apart)."""
    A, B = _arrays(pa_), _arrays(pb_)
    ia = {int(i): j for j, i in enumerate(A['ids'])}
    sel = [(ia[int(i)], j) for j, i in enumerate(B['ids']) if int(i) in ia and A['by'][ia[int(i)]] == B['by'][j]]
    a, b = np.array([s[0] for s in sel]), np.array([s[1] for s in sel])
    return A, B, a, b, (B['d'] - A['d']).days / 365.2425


# --- value shape: within-player h(CA, age) ------------------------------------------------------------
def bucket(yl):
    yl = np.asarray(yl, float)
    return np.where(yl < 0, 3, np.digitize(yl, [0.5, 1.0, 2.0]))


def _interp_idx(E, age):
    a = np.clip(age, AG0, AG1 - 1e-6) - AG0
    ia = np.floor(a).astype(int)
    ta = a - ia
    e = (np.clip(E, E0, E1 - 1e-6) - E0) / ES
    ie = np.floor(e).astype(int)
    te = e - ie
    idx, wt = [], []
    for da, wa in ((0, 1 - ta), (1, ta)):
        for de, we in ((0, 1 - te), (1, te)):
            idx.append((ia + da) * NE + ie + de)
            wt.append(wa * we)
    return idx, wt


def _rowvec(E, age, yl, gk, sign):
    idx, wt = _interp_idx(E, age)
    idx = idx + [NTH + bucket(yl)]
    wt = wt + [np.ones(len(E))]
    idx = idx + [NTH + NB + np.clip(np.floor(age).astype(int) - AG0, 0, NA - 1)]
    wt = wt + [gk.astype(float)]
    return idx, [sign * w for w in wt]


def fit_value(A, B, delta, lam_e=30.0, lam_a=30.0, iters=4):
    """A / B = dicts of arrays (ca, age, yl, gk) for the early / late observation of each player; delta = dlog value."""
    iA, wA = _rowvec(A['ca'], A['age'], A['yl'], A['gk'], -1.0)
    iB, wB = _rowvec(B['ca'], B['age'], B['yl'], B['gk'], +1.0)
    I, W = iA + iB, wA + wB
    P = np.zeros((NP, NP))

    def add2(ix, lam):
        for j in range(1, len(ix) - 1):
            r = np.zeros(NP)
            r[ix[j - 1]], r[ix[j]], r[ix[j + 1]] = 1, -2, 1
            P[:] += lam * np.outer(r, r)
    for ia in range(NA):
        add2([ia * NE + ie for ie in range(NE)], lam_e)
    for ie in range(NE):
        add2([ia * NE + ie for ia in range(NA)], lam_a)
    add2([NTH + NB + ia for ia in range(NA)], lam_a)
    P += 1e-3 * np.eye(NP)
    r = np.ones(len(delta))
    for _ in range(iters):
        AtA, Atb = P.copy(), np.zeros(NP)
        for p in range(len(I)):
            for q in range(len(I)):
                np.add.at(AtA, (I[p], I[q]), r * W[p] * W[q])
            np.add.at(Atb, I[p], r * W[p] * delta)
        AtA[NTH + 3, :] = 0
        AtA[:, NTH + 3] = 0
        AtA[NTH + 3, NTH + 3] = 1
        Atb[NTH + 3] = 0                                    # contract bucket >= 2 years = reference
        th = np.linalg.solve(AtA, Atb)
        res = delta - sum(th[I[p]] * W[p] for p in range(len(I)))
        r = 1.0 / np.maximum(np.abs(res), 0.4)              # IRLS ~ median regression
    return th


# --- CA path: mean CA_B / PA_A by (age, CA_A / PA_A, horizon) ----------------------------------------------
def fit_path(age, ca, pa, cb, k, sig_age=1.5, sig_rho=0.04, min_n=15):
    rho, rb = np.minimum(ca / pa, 1.0), np.minimum(cb / pa, 1.0)
    ks = np.array(sorted(set(np.round(k, 1))))
    tabs = []
    for kk in ks:
        m = np.round(k, 1) == kk
        T = np.full((len(RAGES), len(RHOS)), np.nan)
        for ia, a in enumerate(RAGES):
            wa = np.exp(-0.5 * ((age[m] - a) / sig_age) ** 2)
            sel = wa > 1e-3
            for ir, r in enumerate(RHOS):
                w = wa[sel] * np.exp(-0.5 * ((rho[m][sel] - r) / sig_rho) ** 2)
                if w.sum() >= min_n:
                    T[ia, ir] = (w * rb[m][sel]).sum() / w.sum()
        for ia in range(T.shape[0]):                         # fill unsupported cells: along rho, then along age
            ok = ~np.isnan(T[ia])
            if ok.any():
                T[ia] = np.interp(RHOS, RHOS[ok], T[ia][ok])
        for ir in range(T.shape[1]):
            ok = ~np.isnan(T[:, ir])
            if ok.any():
                T[:, ir] = np.interp(RAGES, RAGES[ok], T[:, ir][ok])
        tabs.append(T)
    return ks, np.array(tabs)


# --- assemble -------------------------------------------------------------------------------------------
def model_dict(th, path):
    """th = fitted vector, path = {'outfield': (ks, tables), 'gk': (ks, tables)} -> the JSON-able model."""
    r3 = lambda a: np.round(np.asarray(a, float), 3).tolist()
    return {
        'version': 1,
        'h': {'age0': AG0, 'e0': E0, 'e_step': ES, 'table': r3(th[:NTH].reshape(NA, NE))},
        'contract': r3(th[NTH:NTH + NB]),                    # <6m, 6-12m, 1-2y, >=2y
        'gk_by_age': r3(th[NTH + NB:]),
        'path': {g: {'age0': int(RAGES[0]), 'rho0': float(RHOS[0]), 'rho_step': 0.025, 'horizons': r3(ks),
                     'table': np.round(t, 4).tolist()} for g, (ks, t) in path.items()},
        'band': {'years': sorted(BAND), 'half_width': [BAND[x] for x in sorted(BAND)]},
    }


def build(panel_pairs):
    """panel_pairs = [(early_panel, late_panel)] -> model dict."""
    parts = [match_pair(*p) for p in panel_pairs]
    # value fit: pairs <= MAX_VALUE_GAP_Y years apart, plausible values only
    early, late, delta = [], [], []
    for A, B, a, b, k in parts:
        if k > MAX_VALUE_GAP_Y:
            continue
        ok = ((A['v'][a] > 0) & (A['v'][a] < 300e6) & (B['v'][b] > 0) & (B['v'][b] < 300e6)
              & (A['age'][a] >= 16) & (A['ca'][a] > 0) & (B['ca'][b] > 0))
        a, b = a[ok], b[ok]
        early.append({x: A[x][a] for x in ('ca', 'age', 'yl', 'gk')})
        late.append({x: B[x][b] for x in ('ca', 'age', 'yl', 'gk')})
        delta.append(np.log(B['v'][b]) - np.log(A['v'][a]))
    cat = lambda L: {x: np.concatenate([d[x] for d in L]) for x in L[0]}
    th = fit_value(cat(early), cat(late), np.concatenate(delta))
    path = {}
    for name, gk in (('outfield', False), ('gk', True)):
        cols = []
        for A, B, a, b, k in parts:
            m = (A['ca'][a] > 0) & (B['ca'][b] > 0) & (A['gk'][a] == gk) & (A['age'][a] >= 15)
            a2, b2 = a[m], b[m]
            cols.append((A['age'][a2], A['ca'][a2], A['pa'][a2], B['ca'][b2], np.full(len(a2), k)))
        path[name] = fit_path(*[np.concatenate(x) for x in zip(*cols)])
    return model_dict(th, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pairs', nargs='+', help='EARLY.fm:LATE.fm (same simulated world)')
    ap.add_argument('--out', default=os.path.join(ROOT, 'fm_editor', 'data', 'value_model.json'))
    args = ap.parse_args()
    panel_pairs = []
    for s in args.pairs:
        e, l = s.rsplit(':', 1)
        panel_pairs.append((panel_from_save(e), panel_from_save(l)))
    model = build(panel_pairs)
    with open(args.out, 'w') as f:
        json.dump(model, f, separators=(',', ':'))
    print('wrote', args.out, os.path.getsize(args.out), 'bytes')


if __name__ == '__main__':
    main()
