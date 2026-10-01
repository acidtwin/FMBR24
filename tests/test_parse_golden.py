"""Golden fingerprint of the parser stages on the real save (guards perf rewrites).

Run: python3 tests/test_parse_golden.py   (skips if the save is absent; ~40 s)
First run creates tests/golden_parse.json from the current code; later runs compare.
Delete the json to re-baseline after an INTENDED output change. The save is only read.

The hashes cover offset-INDEPENDENT fields only (ids, names, nation, birth, ca/pa, attributes, hgp, ...) so a
re-save by the app (an HGC/HGP insert shifts every later byte offset) does not break them. Offsets
(offset / end / identity_offset / he) are not pinned; offset_problems() checks they are self-consistent instead.
FMBR24_GOLDEN_SAVE=<path> runs the same check on another copy of the save.
"""
import copy
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
GOLDEN = os.path.join(ROOT, 'tests', 'golden_parse.json')

SAVE = os.environ.get('FMBR24_GOLDEN_SAVE') or os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')
OFFSET_KEYS = {'offset', 'end', 'identity_offset', 'he'}  # byte positions: drift after any insert, never hashed


def _strip(v):
    """Drop OFFSET_KEYS from a dict / list of dicts / dict of dicts (offset-independent view)."""
    if isinstance(v, dict):
        return {k: _strip(x) for k, x in v.items() if k not in OFFSET_KEYS}
    if isinstance(v, (list, tuple)):
        return [_strip(x) for x in v]
    return v


def fingerprint(raw):
    """{stage: [count, hash]} over offset-independent fields only."""
    out = {}
    for k, v in raw.items():
        if k == 'identities':
            v = [(i, u) for i, u, _off in v]
        elif isinstance(v, dict):
            v = {str(a): _strip(x) for a, x in v.items()}
        else:
            v = _strip(v)
        out[k] = [len(v), _h(v)]
    return out


def offset_problems(b, people):
    """Self-consistency of the byte offsets instead of pinning them: every record must still look like
    find_people's own shape (name block length, birth day/year, nation at `end`), in strictly increasing order."""
    import struct
    bad, last = [], -1
    for p in people:
        o, e = p['offset'], p['end']
        ok = (o > last and e == o + 19 + struct.unpack_from('<I', b, o + 15)[0]
              and struct.unpack_from('<H', b, e)[0] == p['birth_day']
              and struct.unpack_from('<H', b, e + 2)[0] == p['birth_year']
              and struct.unpack_from('<H', b, e + 9)[0] == p['nation']
              and (p.get('identity_offset') is None or p['identity_offset'] >= e))
        if not ok:
            bad.append(p['id'])
        last = o
    return bad


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def collect(save=SAVE, timings=None):
    """Run the parser stages in GUI order; return (b, {stage: raw structure})."""
    from fm_editor.archive import parse_archive, get_member
    from fm_editor import gamedb as G
    from fm_editor.patch import is_homegrown
    from fm_editor.playerstats import parse_player_stats

    def t(name, fn, *a):
        s = time.perf_counter(); r = fn(*a)
        if timings is not None: timings[name] = time.perf_counter() - s
        return r

    _, members, _, aname, _, _ = parse_archive(save)
    b = get_member(save, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, ns, ne = G.find_names(b)
    clubs = G.find_clubs(b, ns)
    G.add_club_finance(b, clubs, ns)
    people = t('find_people', G.find_people, b, fn, ln, ne)
    people_snap_obj = copy.deepcopy(people)  # snapshot before identities / abilities mutate the dicts
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
    import datetime
    from fm_editor.saveinfo import parse_save_info
    im = next((m for m in members if m['name'] == 'injury_manager.dat'), None)
    today = datetime.date.fromisoformat(str(parse_save_info(save, members, aname)['in_game_date']))
    G.find_injuries(b, people, pids, G.parse_injury_manager(get_member(save, im)) if im else None, today)
    G.find_staff_extras(b, people, pids)
    ps = next((m for m in members if m['name'] == 'rgman/player_stats.dat'), None)
    stats = parse_player_stats(get_member(save, ps), {p['id'] for p in people if p['id'] != -1}) if ps else {}

    raw = dict(people_raw=people_snap_obj, identities=identities, abilities=abil, clubs=clubs, squads=squads,
               sub_squads=sub, employment=emp, contracts=contracts, club_staff=staff, people_final=people,
               stats=stats)
    return b, raw


def test_golden():
    if not os.path.exists(SAVE):
        print('SKIPPED (save not found): test_parse_golden'); return
    tm = {}
    b, raw = collect(timings=tm)
    print({k: round(v, 1) for k, v in tm.items()})
    bad_off = offset_problems(b, raw['people_final'])
    assert not bad_off, f'{len(bad_off)} people with inconsistent offsets, e.g. ids {bad_off[:5]}'
    got = fingerprint(raw)
    if not os.path.exists(GOLDEN):
        with open(GOLDEN, 'w') as f:
            json.dump(got, f, indent=1, sort_keys=True)
        print('golden CREATED (tests/golden_parse.json did not exist): nothing was compared'); return
    want = json.load(open(GOLDEN))
    bad = {k: (want.get(k), got.get(k)) for k in set(want) | set(got) if want.get(k) != got.get(k)}
    assert not bad, bad
    print('golden OK')


if __name__ == '__main__':
    test_golden()
