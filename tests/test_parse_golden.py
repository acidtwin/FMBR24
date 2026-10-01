"""Golden fingerprint of the parser stages on the real save (guards perf rewrites).

Run: python3 tests/test_parse_golden.py   (skips if the save is absent; ~40 s)
First run creates tests/golden_parse.json from the current code; later runs compare.
Delete the json to re-baseline after an INTENDED output change. The save is only read.
"""
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
GOLDEN = os.path.join(ROOT, 'tests', 'golden_parse.json')

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def run_stages(save=SAVE, timings=None):
    """Run the parser stages in GUI order; return {stage: (count, hash)}."""
    from fm_editor.archive import parse_archive, get_member
    from fm_editor import gamedb as G
    from fm_editor.patch import is_homegrown
    from fm_editor.playerstats import parse_player_stats

    def t(name, fn, *a):
        s = time.perf_counter(); r = fn(*a)
        if timings is not None: timings[name] = time.perf_counter() - s
        return r

    _, members, _, _, _, _ = parse_archive(save)
    b = get_member(save, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, ns, ne = G.find_names(b)
    clubs = G.find_clubs(b, ns)
    G.add_club_finance(b, clubs, ns)
    people = t('find_people', G.find_people, b, fn, ln, ne)
    people_snap = _h(people)  # before identities / abilities mutate the dicts
    t('match_identities', G.match_identities, b, people, ne)
    identities = [(p['id'], p.get('uid'), p.get('identity_offset')) for p in people]
    squads, sub = t('find_squads', G.find_squads, b, clubs, ns, people)
    for p in people:
        p['hgp'] = is_homegrown(b, p)
    abil = t('find_abilities', G.find_abilities, b, ne)
    for p in people:
        a = abil.get(p.get('id', -1))
        if a:
            p.update(ca=a['ca'], pa=a['pa'], positions=a['positions'], raw_attrs=a['raw_attrs'],
                     height_cm=a['height_cm'], weight_kg=a['weight_kg'])
    emp = G.find_employment(b, people)
    contracts = G.find_contract_blocks(b, people)
    for p in people:
        p.update(contracts.get(p.get('id', -1), {}))
    staff = G.find_club_staff(b, clubs, people, abil, ns)
    pids = set(abil)
    G.find_coaching_attrs(b, people, pids)
    G.find_injuries(b, people, pids)
    G.find_staff_extras(b, people, pids)
    ps = next((m for m in members if m['name'] == 'rgman/player_stats.dat'), None)
    stats = parse_player_stats(get_member(save, ps), {p['id'] for p in people if p['id'] != -1}) if ps else {}

    sq = {str(k): v for k, v in squads.items()}
    sb = {str(k): {str(kk): vv for kk, vv in v.items()} for k, v in sub.items()}
    out = {
        'people_raw': (len(people), people_snap),
        'identities': (len(identities), _h(identities)),
        'abilities': (len(abil), _h({str(k): v for k, v in abil.items()})),
        'clubs': (len(clubs), _h([{k: v for k, v in c.items() if k != 'he'} for c in clubs])),
        'squads': (len(sq), _h(sq)), 'sub_squads': (len(sb), _h(sb)),
        'employment': (len(emp), _h({str(k): v for k, v in emp.items()})),
        'contracts': (len(contracts), _h({str(k): v for k, v in contracts.items()})),
        'club_staff': (len(staff), _h({str(k): v for k, v in staff.items()})),
        'people_final': (len(people), _h(people)),
        'stats': (len(stats), _h({str(k): v for k, v in stats.items()})),
    }
    return {k: list(v) for k, v in out.items()}


def test_golden():
    if not os.path.exists(SAVE):
        print('SKIP: save not found'); return
    tm = {}
    got = run_stages(timings=tm)
    print({k: round(v, 1) for k, v in tm.items()})
    if not os.path.exists(GOLDEN):
        with open(GOLDEN, 'w') as f:
            json.dump(got, f, indent=1, sort_keys=True)
        print('golden created'); return
    want = json.load(open(GOLDEN))
    bad = {k: (want.get(k), got.get(k)) for k in set(want) | set(got) if want.get(k) != got.get(k)}
    assert not bad, bad
    print('golden OK')


if __name__ == '__main__':
    test_golden()
